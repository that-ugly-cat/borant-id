"""
Sessions, levels, and the access decision behind /verify.

Three things in here carry the whole design, and each one is a bug that was
found by stress-testing the spec before any of this existed (SPEC.md §8, §12):

  - **Path normalisation.** The gate decides the required *level* from a path.
    Caddy decides public-vs-gated from a path. A traversal that fools the gate
    costs a downgrade from two_factor to one_factor; one that fools Caddy costs
    the entire authentication. We normalise here anyway, and we lowercase
    before comparing, because erring toward "this looks like /admin" demands
    more, never less.

  - **Cache invalidation on write, not just on expiry.** The session cache
    exists because the gate sits on the critical path of every gated request in
    the perimeter. But without dropping the entry when a session is *elevated*,
    a user does the TOTP, comes back, reads a stale "one_factor" and gets sent
    to the challenge again — a redirect loop that unsticks itself after thirty
    seconds, which is the worst way for anything to break.

  - **The sliding window.** `expires_at` moves forward on every pass through
    the gate. This is the main mitigation for losing a form POST when a session
    dies mid-edit, and it makes the worst case *better* than the fixed 7-day
    JWTs the apps carry today.
"""
import os
import threading
import time
from datetime import timedelta
from urllib.parse import unquote

import bcrypt

from models import (
    ONE_FACTOR, TWO_FACTOR, App, BackupCode, Grant, Policy, Session, User,
    aware, hash_token, new_token, session_window, utcnow,
)

COOKIE_NAME = "borant_session"
COOKIE_DOMAIN = os.environ.get("COOKIE_DOMAIN", ".borant.eu")
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "1") not in ("0", "false", "no")

CACHE_TTL = 30            # seconds; see the module docstring
SLIDE_EVERY = 60          # don't write last_seen_at/expires_at more often


# ── Passwords ─────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed or not plain:
        return False
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False


# ── Caches ────────────────────────────────────────────────────────────────────

class _SessionCache:
    """token_hash -> (stored_at, session_id, user_id). Anything richer would
    have to be invalidated on more kinds of write than we can keep track of."""

    def __init__(self):
        self._lock = threading.Lock()
        self._by_token: dict[str, tuple[float, int, int]] = {}
        self._tokens_by_user: dict[int, set[str]] = {}

    def get(self, token_hash: str):
        with self._lock:
            row = self._by_token.get(token_hash)
            if row is None:
                return None
            stored_at, sid, uid = row
            if time.time() - stored_at > CACHE_TTL:
                self._forget(token_hash)
                return None
            return sid, uid

    def put(self, token_hash: str, session_id: int, user_id: int):
        with self._lock:
            self._by_token[token_hash] = (time.time(), session_id, user_id)
            self._tokens_by_user.setdefault(user_id, set()).add(token_hash)

    def drop_token(self, token_hash: str):
        with self._lock:
            self._forget(token_hash)

    def drop_user(self, user_id: int):
        with self._lock:
            for t in list(self._tokens_by_user.get(user_id, ())):
                self._forget(t)

    def clear(self):
        with self._lock:
            self._by_token.clear()
            self._tokens_by_user.clear()

    def _forget(self, token_hash: str):
        row = self._by_token.pop(token_hash, None)
        if row:
            self._tokens_by_user.get(row[2], set()).discard(token_hash)


class _AppCache:
    """host -> (stored_at, app_id). Dropped wholesale whenever an app, a policy
    or a grant is written: those tables are tiny and change by hand."""

    def __init__(self):
        self._lock = threading.Lock()
        self._d: dict[str, tuple[float, int | None]] = {}

    def get(self, host: str):
        with self._lock:
            row = self._d.get(host)
            if row is None or time.time() - row[0] > CACHE_TTL:
                return None
            return (row[1],)

    def put(self, host: str, app_id: int | None):
        with self._lock:
            self._d[host] = (time.time(), app_id)

    def clear(self):
        with self._lock:
            self._d.clear()


sessions_cache = _SessionCache()
apps_cache = _AppCache()


def invalidate_user(user_id: int) -> None:
    sessions_cache.drop_user(user_id)


def invalidate_registry() -> None:
    """Call after any write to apps / policies / grants."""
    apps_cache.clear()
    sessions_cache.clear()


# ── Sessions ──────────────────────────────────────────────────────────────────

def create_session(db, user: User, ip: str = "", ua: str = "",
                   elevated: bool = False) -> str:
    """Returns the plaintext token for the cookie. Only the hash is stored."""
    plain, digest = new_token()
    now = utcnow()
    sliding, absolute = session_window(now)
    row = Session(
        token_hash=digest, user_id=user.id, authed_at=now,
        elevated_at=(now if elevated else None),
        expires_at=sliding, absolute_expires_at=absolute,
        last_seen_at=now, ip=ip or "", user_agent=(ua or "")[:400],
    )
    db.add(row)
    user.last_login_at = now
    db.commit()
    return plain


def resolve(db, token: str | None) -> tuple[Session, User] | None:
    """The live (session, user) for a cookie value, or None."""
    if not token:
        return None
    digest = hash_token(token)

    cached = sessions_cache.get(digest)
    if cached:
        sess = db.get(Session, cached[0])
        user = db.get(User, cached[1])
    else:
        sess = db.query(Session).filter(Session.token_hash == digest).first()
        user = sess.user if sess else None

    if sess is None or user is None or not user.is_active or not sess.is_live():
        sessions_cache.drop_token(digest)
        return None

    sessions_cache.put(digest, sess.id, user.id)
    return sess, user


def slide(db, sess: Session, ip: str = "") -> None:
    """Push the sliding expiry forward, at most once a minute per session."""
    now = utcnow()
    if (now - aware(sess.last_seen_at)).total_seconds() < SLIDE_EVERY:
        return
    sess.last_seen_at = now
    new_expiry = now + timedelta(days=30)
    if new_expiry > aware(sess.absolute_expires_at):
        new_expiry = aware(sess.absolute_expires_at)
    sess.expires_at = new_expiry
    if ip:
        sess.ip = ip
    db.commit()


def elevate(db, sess: Session) -> None:
    sess.elevated_at = utcnow()
    db.commit()
    # Without this the user loops back to the challenge for up to CACHE_TTL.
    sessions_cache.drop_token(sess.token_hash)
    sessions_cache.drop_user(sess.user_id)


def revoke(db, sess: Session, reason: str = "logout") -> None:
    sess.revoked_at = utcnow()
    sess.revoked_reason = reason
    db.commit()
    sessions_cache.drop_token(sess.token_hash)


def revoke_all(db, user: User, reason: str = "logout_all",
               keep: Session | None = None) -> int:
    n = 0
    for s in user.sessions:
        if s.revoked_at is None and (keep is None or s.id != keep.id):
            s.revoked_at = utcnow()
            s.revoked_reason = reason
            n += 1
    db.commit()
    sessions_cache.drop_user(user.id)
    return n


# ── Backup codes ──────────────────────────────────────────────────────────────

def consume_backup_code(db, user: User, code: str) -> bool:
    from totp import hash_code
    digest = hash_code(code)
    row = (db.query(BackupCode)
             .filter(BackupCode.user_id == user.id,
                     BackupCode.code_hash == digest,
                     BackupCode.used_at.is_(None))
             .first())
    if row is None:
        return False
    row.used_at = utcnow()
    db.commit()
    return True


# ── Paths and policies ────────────────────────────────────────────────────────

def normalize_path(raw: str) -> str:
    """Query stripped, percent-decoded, dot segments resolved, lowercased.

    Lowercasing is not cosmetic: `/Admin` must not slip past a policy written
    for `/admin`. The failure mode we choose is "demands two factors when it
    did not have to", never the reverse.
    """
    path = (raw or "/").split("?", 1)[0].split("#", 1)[0]
    for _ in range(3):                      # %252e style double encoding
        decoded = unquote(path)
        if decoded == path:
            break
        path = decoded
    parts: list[str] = []
    for seg in path.replace("\\", "/").split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if parts:
                parts.pop()
            continue
        parts.append(seg)
    return ("/" + "/".join(parts)).lower()


def prefix_matches(prefix: str, path: str) -> bool:
    """Segment-aware, so `/admin` does not match `/administrators`."""
    prefix = normalize_path(prefix)
    if prefix == "/":
        return True
    return path == prefix or path.startswith(prefix + "/")


def policy_for(db, app: App, path: str) -> Policy | None:
    """The longest matching path_prefix wins."""
    best, best_len = None, -1
    for p in app.policies:
        if prefix_matches(p.path_prefix, path):
            n = len(normalize_path(p.path_prefix))
            if n > best_len:
                best, best_len = p, n
    return best


def app_for_host(db, host: str) -> App | None:
    host = (host or "").split(":")[0].strip().lower()
    if not host:
        return None
    cached = apps_cache.get(host)
    if cached is not None:
        return db.get(App, cached[0]) if cached[0] else None
    app = db.query(App).filter(App.host == host, App.active.is_(True)).first()
    apps_cache.put(host, app.id if app else None)
    return app


def has_grant(db, user: User, app: App) -> Grant | None:
    return (db.query(Grant)
              .filter(Grant.user_id == user.id, Grant.app_id == app.id)
              .first())


def may_enter(db, user: User, app: App) -> tuple[bool, str]:
    """(allowed, level_hint). Admins bypass grants (SPEC.md §5)."""
    if user.is_admin:
        g = has_grant(db, user, app)
        return True, (g.level_hint if g else "admin")
    g = has_grant(db, user, app)
    if g is not None:
        return True, g.level_hint
    if app.default_access == "any_authenticated":
        return True, ""
    return False, ""


def level_satisfied(sess: Session, policy: Policy | None) -> tuple[bool, str]:
    """(ok, current_level). A policy may also demand that the second factor be
    *recent*, which is what max_age_minutes is for."""
    elevated = aware(sess.elevated_at)
    current = ONE_FACTOR
    if elevated is not None:
        current = TWO_FACTOR

    required = policy.level if policy else ONE_FACTOR
    if required == ONE_FACTOR:
        return True, current
    if elevated is None:
        return False, current
    if policy and policy.max_age_minutes:
        age = (utcnow() - elevated).total_seconds() / 60
        if age > policy.max_age_minutes:
            return False, ONE_FACTOR
    return True, current


# ── The decision ──────────────────────────────────────────────────────────────

class Decision:
    """What /verify concluded. `outcome` is one of:

        ok          — let it through, headers attached
        login       — no live session
        stepup      — session is live but the path wants a second factor
        forbidden   — live session, no grant for this app
        unknown     — no app registered for this host
    """

    def __init__(self, outcome: str, *, user=None, session=None,
                 level=ONE_FACTOR, hint="", app=None):
        self.outcome = outcome
        self.user = user
        self.session = session
        self.level = level
        self.hint = hint
        self.app = app

    @property
    def ok(self) -> bool:
        return self.outcome == "ok"


def decide(db, host: str, uri: str, token: str | None,
           ip: str = "") -> Decision:
    path = normalize_path(uri)
    app = app_for_host(db, host)

    resolved = resolve(db, token)
    if resolved is None:
        return Decision("login", app=app)
    sess, user = resolved

    if app is None:
        # An unregistered host behind the gate is a configuration mistake, not
        # an attack. Fail closed and say so in /admin/audit.
        return Decision("unknown", user=user, session=sess)

    allowed, hint = may_enter(db, user, app)
    if not allowed:
        return Decision("forbidden", user=user, session=sess, app=app)

    policy = policy_for(db, app, path)
    ok, level = level_satisfied(sess, policy)
    if not ok:
        return Decision("stepup", user=user, session=sess, level=level, app=app)

    slide(db, sess, ip=ip)
    return Decision("ok", user=user, session=sess, level=level, hint=hint,
                    app=app)


# ── Rate limiting ─────────────────────────────────────────────────────────────

class RateLimiter:
    """In-memory, per-process, deliberately simple. The gate is the only place
    in the perimeter where this exists at all — none of the twenty-two apps
    rate-limits its own login today."""

    def __init__(self, limit: int = 10, window: int = 900):
        self.limit = limit
        self.window = window
        self._lock = threading.Lock()
        self._hits: dict[str, list[float]] = {}

    def hit(self, key: str) -> bool:
        """True if this attempt is allowed."""
        now = time.time()
        with self._lock:
            hits = [t for t in self._hits.get(key, []) if now - t < self.window]
            hits.append(now)
            self._hits[key] = hits
            return len(hits) <= self.limit

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)


login_limiter = RateLimiter(limit=10, window=900)
totp_limiter = RateLimiter(limit=10, window=300)

# Registrazione: più stretto del login, perché qui il costo di un abuso non è
# entrare ma riempire la tabella utenti, e nessuno legittimo si registra cinque
# volte in un'ora.
register_limiter = RateLimiter(limit=5, window=3600)


# ── Cookie helpers ────────────────────────────────────────────────────────────

def set_cookie(response, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME, token,
        max_age=30 * 24 * 3600,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        domain=COOKIE_DOMAIN or None,
        path="/",
    )


def clear_cookie(response) -> None:
    response.delete_cookie(COOKIE_NAME, domain=COOKIE_DOMAIN or None, path="/")
