"""
Data model for Borant ID.

SQLAlchemy/SQLite, WAL mode. The gate sits on the critical path of every gated
request in the whole perimeter, so reads are cheap and writes are rare by
design (SPEC.md §12).

Two things here are deliberate and easy to get wrong later:

  - `User.subject` is a ULID, not the email and not the ORCID iD. It is what
    every downstream app stores in its own `borant_sub` column. Emails change
    when people change institution and ORCIDs get linked after the fact; a
    key that means nothing can never go stale (SPEC.md §5).

  - Session tokens, invite tokens and reset tokens are stored as sha256
    hashes. The plaintext exists only in the cookie or in the link. A leaked
    database backup does not hand anyone a live session.
"""
import hashlib
import json
import os
import secrets
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, create_engine, event,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("BORANTID_DB", os.path.join(BASE_DIR, "data", "borantid.db"))

Base = declarative_base()

ONE_FACTOR = "one_factor"
TWO_FACTOR = "two_factor"
LEVELS = (ONE_FACTOR, TWO_FACTOR)

SESSION_DAYS = 30           # sliding
SESSION_ABSOLUTE_DAYS = 90  # hard ceiling from first authentication


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def aware(dt: datetime | None) -> datetime | None:
    """SQLite hands back naive datetimes. Compare only through this."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# ── ULID ──────────────────────────────────────────────────────────────────────

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def ulid() -> str:
    """Lexicographically sortable 26-char id: 48-bit ms timestamp + 80 bits of
    randomness. Twenty lines beats a dependency for something this small."""
    n = (int(time.time() * 1000) << 80) | secrets.randbits(80)
    out = []
    for _ in range(26):
        out.append(_CROCKFORD[n & 0x1F])
        n >>= 5
    return "".join(reversed(out))


def hash_token(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()


def new_token(nbytes: int = 32) -> tuple[str, str]:
    """(plaintext, sha256). The plaintext is never stored."""
    plain = secrets.token_urlsafe(nbytes)
    return plain, hash_token(plain)


# ── Tables ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    subject = Column(String, unique=True, nullable=False, default=ulid)
    email = Column(String, unique=True, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    name = Column(String, nullable=False, default="")

    # nullable: an ORCID-only account has no password. See SPEC.md §9 on why
    # there must always be at least one admin who does.
    password_hash = Column(String, nullable=True)

    orcid = Column(String, unique=True, nullable=True)
    orcid_linked_at = Column(DateTime, nullable=True)

    totp_secret = Column(String, nullable=True)      # Fernet-encrypted
    totp_confirmed_at = Column(DateTime, nullable=True)
    always_2fa = Column(Boolean, nullable=False, default=False)

    is_admin = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    last_login_at = Column(DateTime, nullable=True)

    backup_codes = relationship("BackupCode", back_populates="user",
                                cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user",
                            cascade="all, delete-orphan")
    grants = relationship("Grant", back_populates="user",
                          cascade="all, delete-orphan")

    @property
    def has_totp(self) -> bool:
        return bool(self.totp_secret and self.totp_confirmed_at)

    @property
    def display(self) -> str:
        return self.name or self.email or self.subject


class BackupCode(Base):
    __tablename__ = "backup_codes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code_hash = Column(String, nullable=False)
    used_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="backup_codes")


class Session(Base):
    """Stateful and revocable, which is the whole point: today not one of the
    twenty-two apps can revoke anything, because they all carry stateless JWTs
    (SPEC.md §1)."""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    token_hash = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    authed_at = Column(DateTime, nullable=False, default=utcnow)
    elevated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    absolute_expires_at = Column(DateTime, nullable=False)
    last_seen_at = Column(DateTime, nullable=False, default=utcnow)

    ip = Column(String, nullable=False, default="")
    user_agent = Column(String, nullable=False, default="")

    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String, nullable=True)

    user = relationship("User", back_populates="sessions")

    def is_live(self, at: datetime | None = None) -> bool:
        at = at or utcnow()
        return (self.revoked_at is None
                and aware(self.expires_at) > at
                and aware(self.absolute_expires_at) > at)


class App(Base):
    __tablename__ = "apps"

    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    host = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=False, default="")
    active = Column(Boolean, nullable=False, default=True)

    # 'any_authenticated' spares writing one grant row per user per app for
    # someone who uses everything. Admins bypass grants regardless.
    default_access = Column(String, nullable=False, default="grant_required")

    # Comma-separated vocabulary this app uses for `X-Borant-Hint`, purely so
    # the admin form can offer it instead of asking someone to remember it.
    # The gate never interprets these strings and never validates against them:
    # owning a domain vocabulary is exactly what SPEC.md §2 forbids.
    #
    # **Empty is a real answer, not a gap.** AutoCode and LSSR have a boolean
    # instead of roles, and PaperTrail's role is per-workspace — "read" on
    # which one? For those three the field is meaningless, so an empty list
    # makes it disappear from the form rather than inviting a typo.
    roles = Column(Text, nullable=False, default="")

    created_at = Column(DateTime, nullable=False, default=utcnow)

    def role_list(self) -> list[str]:
        return [r.strip() for r in (self.roles or "").split(",") if r.strip()]

    policies = relationship("Policy", back_populates="app",
                            cascade="all, delete-orphan")
    grants = relationship("Grant", back_populates="app",
                          cascade="all, delete-orphan")


class Policy(Base):
    """Which authentication level a path prefix of an app demands.

    Caddy decides public-vs-gated; this decides one-factor-vs-two. Two
    questions, two owners (SPEC.md §8)."""
    __tablename__ = "policies"
    __table_args__ = (UniqueConstraint("app_id", "path_prefix"),)

    id = Column(Integer, primary_key=True)
    app_id = Column(Integer, ForeignKey("apps.id"), nullable=False)
    path_prefix = Column(String, nullable=False, default="/")
    level = Column(String, nullable=False, default=ONE_FACTOR)
    max_age_minutes = Column(Integer, nullable=True)
    note = Column(String, nullable=False, default="")

    app = relationship("App", back_populates="policies")


class Grant(Base):
    __tablename__ = "grants"
    __table_args__ = (UniqueConstraint("user_id", "app_id"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    app_id = Column(Integer, ForeignKey("apps.id"), nullable=False)

    # Free string, handed to the app as X-Borant-Hint and used only when it
    # first provisions a local profile. After that the app owns its own roles.
    level_hint = Column(String, nullable=False, default="")

    created_at = Column(DateTime, nullable=False, default=utcnow)
    created_by = Column(String, nullable=False, default="")

    user = relationship("User", back_populates="grants")
    app = relationship("App", back_populates="grants")


class Token(Base):
    """Invites, password resets, email verification: one table, one `kind`."""
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)
    kind = Column(String, nullable=False)          # invite | reset | verify
    token_hash = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=False, default="")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    payload = Column(Text, nullable=False, default="{}")
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    created_by = Column(String, nullable=False, default="")

    def data(self) -> dict:
        try:
            return json.loads(self.payload or "{}")
        except ValueError:
            return {}

    def is_live(self) -> bool:
        return self.used_at is None and aware(self.expires_at) > utcnow()


class Audit(Base):
    __tablename__ = "audit"

    id = Column(Integer, primary_key=True)
    ts = Column(DateTime, nullable=False, default=utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event = Column(String, nullable=False)
    ip = Column(String, nullable=False, default="")
    user_agent = Column(String, nullable=False, default="")
    detail = Column(Text, nullable=False, default="{}")


class Setting(Base):
    """Key/value for what is configured from the interface instead of the
    environment — today the SMTP relay (SPEC.md §5). The SMTP password is
    stored Fernet-encrypted and is write-only in the form."""
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False, default="")


# ── Engine ────────────────────────────────────────────────────────────────────

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}",
                       connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _sqlite_pragmas(conn, _record):
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute("PRAGMA busy_timeout=5000")
    cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)
    _migrate()


# Colonne aggiunte dopo il primo deploy. SQLite non ha un ALTER idempotente, e
# `create_all` non tocca le tabelle che esistono già: senza questo, un database
# nato prima della colonna resta indietro in silenzio.
_MIGRATIONS = [
    "ALTER TABLE apps ADD COLUMN roles TEXT NOT NULL DEFAULT ''",
]


def _migrate() -> None:
    with engine.begin() as conn:
        for statement in _MIGRATIONS:
            try:
                conn.exec_driver_sql(statement)
            except Exception:
                pass          # colonna già presente: è il caso normale


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def audit(db, event_name: str, *, user=None, ip: str = "", ua: str = "",
          **detail) -> None:
    db.add(Audit(user_id=(user.id if user else None), event=event_name,
                 ip=ip or "", user_agent=(ua or "")[:400],
                 detail=json.dumps(detail, default=str)))
    db.commit()


def session_window(first_auth: datetime | None = None) -> tuple[datetime, datetime]:
    """(sliding expiry, absolute expiry). The slide is the main mitigation for
    losing a POST when a session dies mid-form (SPEC.md §8)."""
    now = utcnow()
    first = first_auth or now
    return now + timedelta(days=SESSION_DAYS), first + timedelta(days=SESSION_ABSOLUTE_DAYS)
