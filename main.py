"""
Borant ID — the gate.

Two surfaces:

  /verify   machine-facing, called by Caddy's forward_auth for every gated
            request in the perimeter. It is the only hot path in the app and
            the only one that must never be reachable from the public internet
            (SPEC.md §8: `respond /verify 404` in the id.borant.eu block).

  the rest  human-facing: login, second factor, profile, admin.

The apps never talk to this service. They read headers that Caddy attaches,
and they only believe those headers when AUTH_MODE=gateway and the request
came from the expected proxy — which is their side of the contract, not ours
(SPEC.md §10).
"""
import hashlib
import hmac
import json
import os
from datetime import timedelta
from urllib.parse import quote, urlparse

from fastapi import Cookie, Depends, FastAPI, Form, Request
from fastapi.responses import (
    HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DbSession

import auth
import locales
import mailer
import orcid
import settings
import totp as totplib
from crypto import decrypt_or_none, encrypt
from models import (
    ONE_FACTOR, TWO_FACTOR, AccessRequest, App, BackupCode, Grant, Policy,
    Session, Token, User, Audit, audit, aware, get_db, hash_token, init_db,
    new_token, utcnow,
)

BASE = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Borant ID", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=os.path.join(BASE, "static")),
          name="static")
templates = Jinja2Templates(directory=os.path.join(BASE, "templates"))

init_db()

INVITE_DAYS = 14
RESET_HOURS = 1


def _asset_version() -> str:
    """Impronta di CSS e logo, appesa come `?v=` ai loro URL.

    Serve perché la zona è dietro Cloudflare, che mette in cache gli statici per
    quattro ore: senza, un deploy corregge il foglio di stile all'origine e i
    visitatori continuano a vedere quello vecchio finché la cache non scade.
    Cambiando l'URL cambia la chiave di cache, quindi ogni deploy si porta
    dietro i propri asset senza purghe manuali dalla dashboard.
    """
    h = hashlib.sha256()
    for name in ("style.css", "borant-logo.png"):
        try:
            st = os.stat(os.path.join(BASE, "static", name))
            h.update(f"{name}:{st.st_mtime_ns}:{st.st_size}".encode())
        except OSError:
            h.update(name.encode())
    return h.hexdigest()[:10]


ASSET_V = _asset_version()


# ── Small helpers ─────────────────────────────────────────────────────────────

def client_ip(request: Request) -> str:
    """The caller's address, as well as we can know it.

    `CF-Connecting-IP` first, because the borant.eu zone is proxied by
    Cloudflare and without it every request looks like it comes from a
    Cloudflare edge node. That is not cosmetic: it breaks rate limiting in both
    directions — an attacker gets a fresh bucket per edge, and unrelated users
    behind one edge share a bucket and lock each other out — and it fills the
    audit log with addresses that identify nobody.

    Trusting that header is sound only as long as the origin is reachable
    exclusively through Cloudflare. Today it is not: ports 80/443 are open to
    the world at the Hetzner firewall, so somebody who learns the origin IP
    could forge it. The real fix is restricting those ports to Cloudflare's
    ranges; until then this is still strictly better than counting edges,
    because forging the header only lets an attacker evade their own limit —
    which rotating through edges already achieved.
    """
    for header in ("cf-connecting-ip", "x-forwarded-for"):
        value = request.headers.get(header, "")
        if value:
            return value.split(",")[0].strip()[:64]
    return (request.client.host if request.client else "")[:64]


def user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "")[:400]


def wants_json(request: Request) -> bool:
    """XHR or a page navigation? A 302 answered to a `fetch` becomes an HTML
    login page with status 200, and the caller's JSON.parse fails with an error
    that has nothing to do with the cause (SPEC.md §8).

    Checked in order of how much each signal actually knows. `Sec-Fetch-Mode`
    is decisive and every current browser sends it; `Accept` is a guess, and
    `*/*` — what curl and plenty of libraries send — is no evidence either way.
    That last case falls through to "page", because a redirect is something a
    browser recovers from on its own and a machine client can still read the
    Location header.
    """
    mode = request.headers.get("sec-fetch-mode", "").lower()
    if mode == "navigate":
        return False
    if mode in ("cors", "no-cors", "same-origin"):
        return True
    if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
        return True
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return False
    if "application/json" in accept:
        return True
    return False


def csrf_for(sess: Session | None) -> str:
    """Derived from the session's stored hash, which the browser never sees."""
    if sess is None:
        return ""
    key = os.environ["FERNET_KEY"].encode()
    return hmac.new(key, sess.token_hash.encode(), hashlib.sha256).hexdigest()[:32]


def csrf_ok(sess: Session | None, given: str) -> bool:
    expected = csrf_for(sess)
    return bool(expected) and hmac.compare_digest(expected, given or "")


def current(db: DbSession, token: str | None):
    """(session, user) or (None, None). Plain function, not a dependency: most
    pages here render both logged-in and logged-out."""
    got = auth.resolve(db, token)
    return got if got else (None, None)


def safe_rd(db: DbSession, rd: str) -> str:
    """A return URL is only honoured if its host is a registered app or this
    gate itself. Otherwise it is an open redirect with extra steps."""
    if not rd:
        return ""
    parsed = urlparse(rd)
    if not parsed.netloc:                        # relative path on the gate
        return rd if rd.startswith("/") else ""
    host = parsed.netloc.split(":")[0].lower()
    own = urlparse(settings.base_url(db)).netloc.split(":")[0].lower()
    if host == own:
        return rd
    if db.query(App).filter(App.host == host).first():
        return f"https://{host}{parsed.path or '/'}" + (
            f"?{parsed.query}" if parsed.query else "")
    return ""


def lang_of(request: Request) -> str:
    """Cookie, poi Accept-Language, poi italiano. La scelta esplicita vince
    sempre sull'intestazione del browser."""
    cookie = request.cookies.get(locales.COOKIE)
    if cookie:
        return locales.normalize(cookie)
    return locales.from_accept_language(request.headers.get("accept-language"))


def tr(request: Request) -> dict[str, str]:
    return locales.get_t(lang_of(request))


def render(request: Request, name: str, ctx: dict) -> HTMLResponse:
    ctx.setdefault("site_name", "Borant ID")
    ctx.setdefault("asset_v", ASSET_V)
    return templates.TemplateResponse(request, name, ctx)


def page(request: Request, db: DbSession, name: str, sess, user,
         **ctx) -> HTMLResponse:
    lang = lang_of(request)
    return render(request, name, {
        "user": user, "sess": sess, "csrf": csrf_for(sess),
        "site_name": settings.get(db, "site_name"),
        "orcid_ready": orcid.configured(),
        "t": locales.get_t(lang),
        "lang": lang,
        "reg_open": settings.get_bool(db, "registration_open"),
        "languages": locales.LANGUAGE_NAMES,
        "supported": locales.SUPPORTED,
        **ctx,
    })


def require_user(db: DbSession, token: str | None):
    sess, user = current(db, token)
    if user is None:
        return None, None, RedirectResponse("/login", status_code=303)
    return sess, user, None


def require_admin(db: DbSession, token: str | None):
    sess, user, redirect = require_user(db, token)
    if redirect:
        return None, None, redirect
    if not user.is_admin:
        return None, None, RedirectResponse("/", status_code=303)
    return sess, user, None


# ── /verify — the contract with Caddy ─────────────────────────────────────────

VERIFY_HEADERS = ("X-Borant-Sub", "X-Borant-Email", "X-Borant-Name",
                  "X-Borant-Level", "X-Borant-Hint", "X-Borant-Expires")


@app.get("/verify")
def verify(request: Request,
           borant_session: str | None = Cookie(default=None),
           db: DbSession = Depends(get_db)):
    host = request.headers.get("x-forwarded-host", "")
    uri = request.headers.get("x-forwarded-uri", "/")
    ip = client_ip(request)

    d = auth.decide(db, host, uri, borant_session, ip=ip)
    login_base = settings.base_url(db)
    target = f"https://{host}{uri}" if host else ""

    if d.outcome == "ok":
        r = Response(status_code=200)
        r.headers["X-Borant-Sub"] = d.user.subject
        r.headers["X-Borant-Email"] = d.user.email or ""
        r.headers["X-Borant-Name"] = d.user.name or ""
        r.headers["X-Borant-Level"] = d.level
        r.headers["X-Borant-Hint"] = d.hint or ""
        r.headers["X-Borant-Expires"] = aware(d.session.expires_at).isoformat()
        return r

    if d.outcome == "unknown":
        # Fail closed, and leave a trace: a host behind the gate with no row in
        # `apps` is a configuration mistake that would otherwise be silent.
        audit(db, "verify.unknown_host", user=d.user, ip=ip, host=host)
        return PlainTextResponse("Host non registrato in Borant ID",
                                 status_code=403)

    if d.outcome == "forbidden":
        if wants_json(request):
            return JSONResponse({"error": "forbidden"}, status_code=403)
        where = f"{login_base}/forbidden?app={quote(host)}"
        return RedirectResponse(where, status_code=302)

    where = "/2fa" if d.outcome == "stepup" else "/login"
    if wants_json(request):
        return JSONResponse(
            {"error": "unauthenticated" if where == "/login" else "step_up_required",
             "login": f"{login_base}{where}"},
            status_code=401)
    url = f"{login_base}{where}?rd={quote(target, safe='')}" if target else \
          f"{login_base}{where}"
    return RedirectResponse(url, status_code=302)


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/lang/{code}")
def set_lang(code: str, request: Request):
    """Sceglie la lingua e torna da dove si veniva. Il `rd` implicito è il
    Referer, che qui è innocuo perché serve solo a non perdere la pagina: se
    punta fuori dal gate lo si butta."""
    chosen = locales.normalize(code)
    back = request.headers.get("referer", "") or "/"
    if "://" in back:
        host = urlparse(back).netloc.split(":")[0].lower()
        if host != (request.url.hostname or "").lower():
            back = "/"
    r = RedirectResponse(back, status_code=303)
    r.set_cookie(locales.COOKIE, chosen, max_age=365 * 24 * 3600,
                 httponly=False, secure=auth.COOKIE_SECURE, samesite="lax",
                 path="/")
    return r


# ── Home ──────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home(request: Request, borant_session: str | None = Cookie(default=None),
         db: DbSession = Depends(get_db)):
    sess, user = current(db, borant_session)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    apps = db.query(App).filter(App.active.is_(True)).order_by(App.name).all()
    mine = [a for a in apps if auth.may_enter(db, user, a)[0]]
    others = [a for a in apps if a not in mine]
    pending = {r.app_id for r in db.query(AccessRequest).filter(
        AccessRequest.user_id == user.id,
        AccessRequest.status == "pending").all()}
    return page(request, db, "home.html", sess, user, apps=mine,
                others=others, pending=pending,
                verified=bool(user.email_verified_at))


# ── Login ─────────────────────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request, rd: str = "", retry: int = 0,
               borant_session: str | None = Cookie(default=None),
               db: DbSession = Depends(get_db)):
    sess, user = current(db, borant_session)
    rd = safe_rd(db, rd)
    if user is not None and retry < 1:
        return RedirectResponse(rd or "/", status_code=303)
    # Loop breaker: a second arrival with a live session means the cookie is
    # not sticking (wrong domain, blocked cookies, clock skew). Say so instead
    # of bouncing forever (SPEC.md §8).
    return page(request, db, "login.html", None, None, rd=rd,
                cookie_trouble=(user is not None and retry >= 1), error="")


@app.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, email: str = Form(""),
                 password: str = Form(""), rd: str = Form(""),
                 db: DbSession = Depends(get_db)):
    ip = client_ip(request)
    rd = safe_rd(db, rd)
    email = email.strip().lower()
    t = tr(request)

    if not auth.login_limiter.hit(f"ip:{ip}") or \
       not auth.login_limiter.hit(f"acct:{email}"):
        audit(db, "login.rate_limited", ip=ip, email=email)
        return page(request, db, "login.html", None, None, rd=rd,
                    error=t["login_rate"])

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active or \
       not auth.verify_password(password, user.password_hash):
        audit(db, "login.failed", user=user, ip=ip, ua=user_agent(request),
              email=email)
        return page(request, db, "login.html", None, None, rd=rd,
                    error=t["login_err"])

    auth.login_limiter.reset(f"acct:{email}")
    token = auth.create_session(db, user, ip=ip, ua=user_agent(request))
    audit(db, "login.ok", user=user, ip=ip, ua=user_agent(request))

    # A user who asked for it always does the second step, whatever the target
    # app requires.
    dest = "/2fa" if (user.always_2fa and user.has_totp) else (rd or "/")
    if dest == "/2fa" and rd:
        dest = f"/2fa?rd={quote(rd, safe='')}"

    r = RedirectResponse(dest, status_code=303)
    auth.set_cookie(r, token)
    return r


@app.get("/logout", response_class=HTMLResponse)
def logout_confirm(request: Request,
                   borant_session: str | None = Cookie(default=None),
                   db: DbSession = Depends(get_db)):
    """Le app del perimetro mandano qui il browser quando qualcuno esce (§10
    regola 5), e un redirect è per forza una GET: senza questa rotta l'utente
    riceve un «Method Not Allowed» invece di uscire.

    Ma la GET **non revoca**, e la ragione è precisa: `SameSite=Lax` spedisce
    il cookie sulle navigazioni GET di primo livello, quindi un `<img
    src="https://id.borant.eu/logout">` su un sito qualunque butterebbe fuori
    chiunque lo guardasse. Qui si chiede; a revocare resta la form in POST.

    Chi arriva senza sessione è già fuori: lo si manda al login invece di
    mostrargli un bottone che non fa niente."""
    sess, user = current(db, borant_session)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    return page(request, db, "logout.html", sess, user)


@app.post("/logout")
def logout(request: Request, borant_session: str | None = Cookie(default=None),
           db: DbSession = Depends(get_db)):
    sess, user = current(db, borant_session)
    if sess is not None:
        auth.revoke(db, sess, "logout")
        audit(db, "logout", user=user, ip=client_ip(request))
    r = RedirectResponse("/login", status_code=303)
    auth.clear_cookie(r)
    return r


@app.post("/logout/all")
def logout_all(request: Request, csrf: str = Form(""),
               borant_session: str | None = Cookie(default=None),
               db: DbSession = Depends(get_db)):
    sess, user = current(db, borant_session)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if not csrf_ok(sess, csrf):
        return RedirectResponse("/profile", status_code=303)
    n = auth.revoke_all(db, user, "logout_all")
    audit(db, "logout.all", user=user, ip=client_ip(request), count=n)
    r = RedirectResponse("/login", status_code=303)
    auth.clear_cookie(r)
    return r


# ── Second factor ─────────────────────────────────────────────────────────────

@app.get("/2fa", response_class=HTMLResponse)
def twofa_form(request: Request, rd: str = "",
               borant_session: str | None = Cookie(default=None),
               db: DbSession = Depends(get_db)):
    sess, user = current(db, borant_session)
    if user is None:
        return RedirectResponse(f"/login?rd={quote(safe_rd(db, rd), safe='')}",
                                status_code=303)
    rd = safe_rd(db, rd)

    if not user.has_totp:
        # Not a dead end: enrol here, inside a session that is already
        # authenticated (SPEC.md §6).
        secret = totplib.generate_secret()
        uri = totplib.provisioning_uri(secret, user.email or user.subject)
        return page(request, db, "twofa_enroll.html", sess, user, rd=rd,
                    secret=secret, otpauth=uri,
                    qr=totplib.qr_data_uri(uri),
                    stash=encrypt(json.dumps({"secret": secret})), error="")

    return page(request, db, "twofa.html", sess, user, rd=rd, error="")


@app.post("/2fa", response_class=HTMLResponse)
def twofa_submit(request: Request, code: str = Form(""), rd: str = Form(""),
                 csrf: str = Form(""), stash: str = Form(""),
                 borant_session: str | None = Cookie(default=None),
                 db: DbSession = Depends(get_db)):
    sess, user = current(db, borant_session)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    rd = safe_rd(db, rd)
    ip = client_ip(request)
    t = tr(request)

    if not csrf_ok(sess, csrf):
        return RedirectResponse("/2fa", status_code=303)
    if not auth.totp_limiter.hit(f"totp:{user.id}"):
        audit(db, "2fa.rate_limited", user=user, ip=ip)
        return page(request, db, "twofa.html", sess, user, rd=rd,
                    error=t["twofa_rate"])

    # Enrolment in progress: the secret is not stored until a code proves the
    # authenticator actually has it.
    if stash:
        raw = decrypt_or_none(stash)
        secret = (json.loads(raw).get("secret") if raw else None)
        if secret and totplib.verify(secret, code):
            from crypto import encrypt as enc
            user.totp_secret = enc(secret)
            user.totp_confirmed_at = utcnow()
            db.commit()
            plain = _issue_backup_codes(db, user)
            auth.elevate(db, sess)
            audit(db, "2fa.enrolled", user=user, ip=ip)
            auth.invalidate_user(user.id)
            # I codici si mostrano subito, non si rimanda alla destinazione:
            # generarli e reindirizzare lascia l'utente con dieci codici che
            # esistono, che non ha mai visto, e che quindi non può usare.
            return page(request, db, "backup_codes.html", sess, user,
                        codes=plain, cont=rd or "/profile")
        uri = totplib.provisioning_uri(secret or "", user.email or user.subject)
        return page(request, db, "twofa_enroll.html", sess, user, rd=rd,
                    secret=secret or "", otpauth=uri,
                    qr=totplib.qr_data_uri(uri), stash=stash,
                    error=t["twofa_err_retry"])

    secret = decrypt_or_none(user.totp_secret)
    if secret and totplib.verify(secret, code):
        auth.elevate(db, sess)
        audit(db, "2fa.ok", user=user, ip=ip)
        return RedirectResponse(rd or "/", status_code=303)

    if auth.consume_backup_code(db, user, code):
        auth.elevate(db, sess)
        audit(db, "2fa.backup_code", user=user, ip=ip)
        return RedirectResponse(rd or "/", status_code=303)

    audit(db, "2fa.failed", user=user, ip=ip)
    return page(request, db, "twofa.html", sess, user, rd=rd,
                error=t["twofa_err"])


def _issue_backup_codes(db: DbSession, user: User) -> list[str]:
    db.query(BackupCode).filter(BackupCode.user_id == user.id).delete()
    plain, hashes = totplib.generate_backup_codes()
    for h in hashes:
        db.add(BackupCode(user_id=user.id, code_hash=h))
    db.commit()
    return plain


# ── ORCID ─────────────────────────────────────────────────────────────────────

def _redirect_uri(db: DbSession) -> str:
    return settings.base_url(db) + "/orcid/callback"


@app.get("/login/orcid")
def orcid_login(request: Request, rd: str = "",
                db: DbSession = Depends(get_db)):
    if not orcid.configured():
        return RedirectResponse("/login", status_code=303)
    state, cookie = orcid.make_state("login", safe_rd(db, rd))
    r = RedirectResponse(orcid.authorize_url(state, _redirect_uri(db)),
                         status_code=302)
    r.set_cookie(orcid.STATE_COOKIE, cookie, max_age=orcid.STATE_TTL,
                 httponly=True, secure=auth.COOKIE_SECURE, samesite="lax",
                 path="/")
    return r


@app.get("/link/orcid")
def orcid_link(request: Request,
               borant_session: str | None = Cookie(default=None),
               db: DbSession = Depends(get_db)):
    sess, user, redirect = require_user(db, borant_session)
    if redirect:
        return redirect
    if not orcid.configured():
        return RedirectResponse("/profile", status_code=303)
    state, cookie = orcid.make_state("link", "/profile")
    r = RedirectResponse(orcid.authorize_url(state, _redirect_uri(db)),
                         status_code=302)
    r.set_cookie(orcid.STATE_COOKIE, cookie, max_age=orcid.STATE_TTL,
                 httponly=True, secure=auth.COOKIE_SECURE, samesite="lax",
                 path="/")
    return r


@app.get("/orcid/callback", response_class=HTMLResponse)
def orcid_callback(request: Request, code: str = "", state: str = "",
                   borant_orcid_state: str | None = Cookie(default=None),
                   borant_session: str | None = Cookie(default=None),
                   db: DbSession = Depends(get_db)):
    ip = client_ip(request)
    t = tr(request)
    st = orcid.read_state(borant_orcid_state, state)
    if st is None or not code:
        return page(request, db, "message.html", None, None,
                    title=t["orcid_fail_title"], body=t["orcid_fail_body"],
                    back="/login")

    data, err = orcid.exchange(code, _redirect_uri(db))
    if data is None:
        audit(db, "orcid.exchange_failed", ip=ip, error=err)
        return page(request, db, "message.html", None, None,
                    title=t["orcid_fail_title"], body=err, back="/login")

    orcid_id = data["orcid"]
    sess, user = current(db, borant_session)

    if st["mode"] == "link":
        if user is None:
            return RedirectResponse("/login", status_code=303)
        taken = db.query(User).filter(User.orcid == orcid_id,
                                      User.id != user.id).first()
        if taken is not None:
            return page(request, db, "message.html", sess, user,
                        title=t["orcid_taken_title"],
                        body=t["orcid_taken_body"], back="/profile")
        user.orcid = orcid_id
        user.orcid_linked_at = utcnow()
        if not user.name and data.get("name"):
            user.name = data["name"]
        db.commit()
        audit(db, "orcid.linked", user=user, ip=ip, orcid=orcid_id)
        if user.email:
            mailer.send_security_notice(
                db, user.email, "ORCID linked",
                f"The ORCID iD {orcid_id} is now linked to your account.")
        return RedirectResponse("/profile", status_code=303)

    # mode == login. Crea l'account solo se le registrazioni sono aperte, e
    # allora comunque **senza grant**: la regola difensiva del §9 non era
    # «ORCID non crea utenti» ma «l'accesso non si concede da sé», e quella
    # resta intatta. Tenere le due porte con regole diverse significherebbe
    # dover spiegare perché la password apre un account e ORCID no.
    found = db.query(User).filter(User.orcid == orcid_id).first()
    if found is None and registration_open(db):
        found = User(orcid=orcid_id, orcid_linked_at=utcnow(),
                     name=data.get("name", "") or orcid_id, is_active=True)
        db.add(found)
        db.commit()
        audit(db, "register.orcid", user=found, ip=ip, orcid=orcid_id)
    if found is None or not found.is_active:
        audit(db, "orcid.login_unknown", ip=ip, orcid=orcid_id)
        return page(request, db, "message.html", None, None,
                    title=t["orcid_unknown_title"],
                    body=f"{orcid_id} — {t['orcid_unknown_body']}",
                    back="/login")

    token = auth.create_session(db, found, ip=ip, ua=user_agent(request))
    audit(db, "login.orcid", user=found, ip=ip, orcid=orcid_id)
    dest = st.get("rd") or "/"
    if found.always_2fa and found.has_totp:
        dest = f"/2fa?rd={quote(dest, safe='')}"
    r = RedirectResponse(dest, status_code=303)
    auth.set_cookie(r, token)
    r.delete_cookie(orcid.STATE_COOKIE, path="/")
    return r


# ── Forbidden ─────────────────────────────────────────────────────────────────

@app.get("/forbidden", response_class=HTMLResponse)
def forbidden(request: Request, app_host: str = "",
              borant_session: str | None = Cookie(default=None),
              db: DbSession = Depends(get_db)):
    host = request.query_params.get("app", app_host)
    sess, user = current(db, borant_session)
    target = db.query(App).filter(App.host == host).first()
    return page(request, db, "forbidden.html", sess, user,
                host=host, target=target)


@app.post("/forbidden")
def forbidden_ask(request: Request, host: str = Form(""), csrf: str = Form(""),
                  borant_session: str | None = Cookie(default=None),
                  db: DbSession = Depends(get_db)):
    sess, user = current(db, borant_session)
    t = tr(request)
    if user is None or not csrf_ok(sess, csrf):
        return RedirectResponse("/login", status_code=303)
    audit(db, "access.requested", user=user, ip=client_ip(request), host=host)
    admins = db.query(User).filter(User.is_admin.is_(True),
                                   User.is_active.is_(True)).all()
    for a in admins:
        if a.email:
            mailer.send_access_request(db, a.email, user.display, user.email,
                                       host, host, "",
                                       settings.base_url(db))
    return page(request, db, "message.html", sess, user,
                title=t["forbidden_sent_title"],
                body=t["forbidden_sent_body"], back="/")


# ── Invites ───────────────────────────────────────────────────────────────────

@app.get("/invite/{raw}", response_class=HTMLResponse)
def invite_form(raw: str, request: Request, db: DbSession = Depends(get_db)):
    t = tr(request)
    tok = db.query(Token).filter(Token.token_hash == hash_token(raw),
                                 Token.kind == "invite").first()
    if tok is None or not tok.is_live():
        return page(request, db, "message.html", None, None,
                    title=t["invite_bad_title"], body=t["invite_bad_body"],
                    back="/login")
    return page(request, db, "invite.html", None, None, raw=raw, tok=tok,
                data=tok.data(), error="")


@app.post("/invite/{raw}", response_class=HTMLResponse)
def invite_accept(raw: str, request: Request, name: str = Form(""),
                  password: str = Form(""), password2: str = Form(""),
                  db: DbSession = Depends(get_db)):
    t = tr(request)
    tok = db.query(Token).filter(Token.token_hash == hash_token(raw),
                                 Token.kind == "invite").first()
    if tok is None or not tok.is_live():
        return page(request, db, "message.html", None, None,
                    title=t["invite_bad_title"], body=t["invite_bad_body"],
                    back="/login")

    data = tok.data()
    if len(password) < 10 or password != password2:
        return page(request, db, "invite.html", None, None, raw=raw, tok=tok,
                    data=data, error=t["invite_err"])

    user = db.query(User).filter(User.email == tok.email).first()
    if user is None:
        user = User(email=tok.email, name=name.strip() or data.get("name", ""))
        db.add(user)
    user.name = name.strip() or user.name or data.get("name", "")
    user.password_hash = auth.hash_password(password)
    user.email_verified_at = utcnow()      # accepting the invite verifies it
    user.is_active = True
    if data.get("is_admin"):
        user.is_admin = True
    db.commit()

    for app_id, hint in (data.get("grants") or {}).items():
        if not db.query(Grant).filter(Grant.user_id == user.id,
                                      Grant.app_id == int(app_id)).first():
            db.add(Grant(user_id=user.id, app_id=int(app_id),
                         level_hint=hint or "", created_by="invite"))
    tok.used_at = utcnow()
    db.commit()
    auth.invalidate_registry()

    ip = client_ip(request)
    audit(db, "invite.accepted", user=user, ip=ip)
    token = auth.create_session(db, user, ip=ip, ua=user_agent(request))
    r = RedirectResponse("/profile", status_code=303)
    auth.set_cookie(r, token)
    return r


# ── Password reset ────────────────────────────────────────────────────────────

@app.get("/reset", response_class=HTMLResponse)
def reset_request_form(request: Request, db: DbSession = Depends(get_db)):
    return page(request, db, "reset_request.html", None, None, sent=False,
                error="")


@app.post("/reset", response_class=HTMLResponse)
def reset_request(request: Request, email: str = Form(""),
                  db: DbSession = Depends(get_db)):
    email = email.strip().lower()
    ip = client_ip(request)
    user = db.query(User).filter(User.email == email,
                                 User.is_active.is_(True)).first()
    if user is not None:
        plain, digest = new_token()
        db.add(Token(kind="reset", token_hash=digest, email=email,
                     user_id=user.id,
                     expires_at=utcnow() + timedelta(hours=RESET_HOURS)))
        db.commit()
        link = f"{settings.base_url(db)}/reset/{plain}"
        ok, err = mailer.send_reset(db, email, link)
        audit(db, "reset.requested", user=user, ip=ip, mail_ok=ok, error=err)
    # Same answer either way: whether an address has an account here is not
    # something a form should tell you.
    return page(request, db, "reset_request.html", None, None, sent=True,
                error="")


@app.get("/reset/{raw}", response_class=HTMLResponse)
def reset_form(raw: str, request: Request, db: DbSession = Depends(get_db)):
    t = tr(request)
    tok = db.query(Token).filter(Token.token_hash == hash_token(raw),
                                 Token.kind == "reset").first()
    if tok is None or not tok.is_live():
        return page(request, db, "message.html", None, None,
                    title=t["reset_expired_title"],
                    body=t["reset_expired_body"], back="/reset")
    return page(request, db, "reset.html", None, None, raw=raw, error="")


@app.post("/reset/{raw}", response_class=HTMLResponse)
def reset_submit(raw: str, request: Request, password: str = Form(""),
                 password2: str = Form(""), db: DbSession = Depends(get_db)):
    t = tr(request)
    tok = db.query(Token).filter(Token.token_hash == hash_token(raw),
                                 Token.kind == "reset").first()
    if tok is None or not tok.is_live():
        return page(request, db, "message.html", None, None,
                    title=t["reset_expired_title"],
                    body=t["reset_expired_body"], back="/reset")
    if len(password) < 10 or password != password2:
        return page(request, db, "reset.html", None, None, raw=raw,
                    error=t["reset_err"])
    user = db.get(User, tok.user_id)
    user.password_hash = auth.hash_password(password)
    tok.used_at = utcnow()
    db.commit()
    n = auth.revoke_all(db, user, "password_reset")
    audit(db, "reset.done", user=user, ip=client_ip(request), sessions=n)
    if user.email:
        closed = ("There were no other open sessions." if n == 0 else
                   "One open session was closed." if n == 1 else
                   f"{n} open sessions were closed.")
        mailer.send_security_notice(db, user.email, "Password changed", closed)
    return page(request, db, "message.html", None, None,
                title=t["reset_done_title"], body=t["reset_done_body"],
                back="/login")


# ── Profile ───────────────────────────────────────────────────────────────────

@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request, codes: int = 0,
            borant_session: str | None = Cookie(default=None),
            db: DbSession = Depends(get_db)):
    sess, user, redirect = require_user(db, borant_session)
    if redirect:
        return redirect
    live = [s for s in sorted(user.sessions, key=lambda s: s.authed_at,
                              reverse=True) if s.is_live()]
    unused = db.query(BackupCode).filter(BackupCode.user_id == user.id,
                                         BackupCode.used_at.is_(None)).count()
    err = request.query_params.get("err", "")
    t = tr(request)
    return page(request, db, "profile.html", sess, user, live=live,
                unused_codes=unused,
                orcid_url=orcid.profile_url(user.orcid) if user.orcid else "",
                error={"pw": t["profile_pw_err"],
                       "short": t["profile_pw_short"]}.get(err, ""),
                msg=(t["profile_2fa_msg"] if codes else ""))


@app.post("/profile/password", response_class=HTMLResponse)
def profile_password(request: Request, current_pw: str = Form(""),
                     password: str = Form(""), password2: str = Form(""),
                     csrf: str = Form(""),
                     borant_session: str | None = Cookie(default=None),
                     db: DbSession = Depends(get_db)):
    sess, user, redirect = require_user(db, borant_session)
    if redirect:
        return redirect
    if not csrf_ok(sess, csrf):
        return RedirectResponse("/profile", status_code=303)
    if user.password_hash and not auth.verify_password(current_pw,
                                                       user.password_hash):
        return RedirectResponse("/profile?err=pw", status_code=303)
    if len(password) < 10 or password != password2:
        return RedirectResponse("/profile?err=short", status_code=303)
    user.password_hash = auth.hash_password(password)
    db.commit()
    auth.revoke_all(db, user, "password_change", keep=sess)
    audit(db, "password.changed", user=user, ip=client_ip(request))
    return RedirectResponse("/profile", status_code=303)


@app.post("/profile/totp/disable")
def profile_totp_disable(request: Request, csrf: str = Form(""),
                         borant_session: str | None = Cookie(default=None),
                         db: DbSession = Depends(get_db)):
    sess, user, redirect = require_user(db, borant_session)
    if redirect:
        return redirect
    if not csrf_ok(sess, csrf):
        return RedirectResponse("/profile", status_code=303)
    user.totp_secret = None
    user.totp_confirmed_at = None
    user.always_2fa = False
    db.query(BackupCode).filter(BackupCode.user_id == user.id).delete()
    db.commit()
    auth.invalidate_user(user.id)
    audit(db, "2fa.disabled", user=user, ip=client_ip(request))
    if user.email:
        mailer.send_security_notice(
            db, user.email, "Two-factor authentication turned off",
            "If this was not you, turn it back on immediately.")
    return RedirectResponse("/profile", status_code=303)


@app.post("/profile/always-2fa")
def profile_always_2fa(request: Request, csrf: str = Form(""),
                       value: str = Form("0"),
                       borant_session: str | None = Cookie(default=None),
                       db: DbSession = Depends(get_db)):
    sess, user, redirect = require_user(db, borant_session)
    if redirect:
        return redirect
    if csrf_ok(sess, csrf) and user.has_totp:
        user.always_2fa = value in ("1", "on", "true")
        db.commit()
        auth.invalidate_user(user.id)
    return RedirectResponse("/profile", status_code=303)


@app.post("/profile/backup-codes", response_class=HTMLResponse)
def profile_backup_codes(request: Request, csrf: str = Form(""),
                         borant_session: str | None = Cookie(default=None),
                         db: DbSession = Depends(get_db)):
    sess, user, redirect = require_user(db, borant_session)
    if redirect:
        return redirect
    if not csrf_ok(sess, csrf) or not user.has_totp:
        return RedirectResponse("/profile", status_code=303)
    plain = _issue_backup_codes(db, user)
    audit(db, "2fa.backup_codes_issued", user=user, ip=client_ip(request))
    return page(request, db, "backup_codes.html", sess, user, codes=plain)


@app.post("/profile/sessions/{sid}/revoke")
def profile_revoke(sid: int, request: Request, csrf: str = Form(""),
                   borant_session: str | None = Cookie(default=None),
                   db: DbSession = Depends(get_db)):
    sess, user, redirect = require_user(db, borant_session)
    if redirect:
        return redirect
    if not csrf_ok(sess, csrf):
        return RedirectResponse("/profile", status_code=303)
    target = db.get(Session, sid)
    if target is not None and target.user_id == user.id:
        auth.revoke(db, target, "revoked_by_user")
        audit(db, "session.revoked", user=user, ip=client_ip(request), sid=sid)
        if target.id == sess.id:
            r = RedirectResponse("/login", status_code=303)
            auth.clear_cookie(r)
            return r
    return RedirectResponse("/profile", status_code=303)


# ── Registrazione aperta ──────────────────────────────────────────────────────
#
# Aprire le registrazioni **non apre nessuna app**: un account nuovo nasce con
# zero grant, e `grant_required` è il default. Chi si registra ottiene il
# diritto di *chiedere*, non di entrare. È questa proprietà che rende la cosa
# sicura, non un controllo all'ingresso (SPEC.md §18).
#
# La conferma dell'email non serve a proteggere l'account — non c'è niente da
# proteggere — ma a evitare che si possa chiedere accesso da un indirizzo che
# non è tuo. Per questo blocca /request-access e nient'altro.

def registration_open(db: DbSession) -> bool:
    return settings.get_bool(db, "registration_open")


def domain_allowed(db: DbSession, email: str) -> bool:
    raw = settings.get(db, "registration_domains").strip()
    if not raw:
        return True
    domain = email.rsplit("@", 1)[-1].lower()
    allowed = [d.strip().lower().lstrip("@") for d in raw.split(",") if d.strip()]
    return any(domain == a or domain.endswith("." + a) for a in allowed)


@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request, db: DbSession = Depends(get_db)):
    t = tr(request)
    if not registration_open(db):
        return page(request, db, "message.html", None, None,
                    title=t["reg_closed_title"], body=t["reg_closed_body"],
                    back="/login")
    return page(request, db, "register.html", None, None, error="",
                domains=settings.get(db, "registration_domains"))


@app.post("/register", response_class=HTMLResponse)
def register_submit(request: Request, name: str = Form(""),
                    email: str = Form(""), password: str = Form(""),
                    password2: str = Form(""),
                    db: DbSession = Depends(get_db)):
    t = tr(request)
    ip = client_ip(request)
    if not registration_open(db):
        return RedirectResponse("/login", status_code=303)

    def again(msg: str):
        return page(request, db, "register.html", None, None, error=msg,
                    domains=settings.get(db, "registration_domains"))

    if not auth.register_limiter.hit(f"ip:{ip}"):
        audit(db, "register.rate_limited", ip=ip)
        return again(t["login_rate"])

    email = email.strip().lower()
    if not email or "@" not in email:
        return again(t["reg_bad_email"])
    if not domain_allowed(db, email):
        return again(t["reg_bad_domain"])
    if len(password) < 10 or password != password2:
        return again(t["invite_err"])
    if db.query(User).filter(User.email == email).first():
        # Si dice, perché il contrario sarebbe peggio: senza questo l'utente
        # crea un secondo account convinto di non averne uno.
        return again(t["reg_taken"])

    user = User(email=email, name=name.strip() or email.split("@")[0],
                password_hash=auth.hash_password(password), is_active=True)
    db.add(user)
    db.commit()

    plain, digest = new_token()
    db.add(Token(kind="verify", token_hash=digest, email=email,
                 user_id=user.id, expires_at=utcnow() + timedelta(days=7)))
    db.commit()
    link = f"{settings.base_url(db)}/confirm/{plain}"
    ok, err = mailer.send_confirm(db, email, link)
    audit(db, "register.ok", user=user, ip=ip, ua=user_agent(request),
          mail_ok=ok, error=err)

    token = auth.create_session(db, user, ip=ip, ua=user_agent(request))
    r = RedirectResponse("/", status_code=303)
    auth.set_cookie(r, token)
    return r


@app.get("/confirm/{raw}", response_class=HTMLResponse)
def confirm_email(raw: str, request: Request,
                  borant_session: str | None = Cookie(default=None),
                  db: DbSession = Depends(get_db)):
    t = tr(request)
    tok = db.query(Token).filter(Token.token_hash == hash_token(raw),
                                 Token.kind == "verify").first()
    if tok is None or not tok.is_live():
        return page(request, db, "message.html", None, None,
                    title=t["reset_expired_title"],
                    body=t["reset_expired_body"], back="/")
    user = db.get(User, tok.user_id)
    if user is not None:
        user.email_verified_at = utcnow()
    tok.used_at = utcnow()
    db.commit()
    audit(db, "email.verified", user=user, ip=client_ip(request))
    sess, me = current(db, borant_session)
    return page(request, db, "message.html", sess, me,
                title=t["reg_confirmed_title"], body=t["reg_confirmed_body"],
                back="/")


@app.post("/request-access", response_class=HTMLResponse)
def request_access(request: Request, app_id: int = Form(0),
                   message: str = Form(""), csrf: str = Form(""),
                   borant_session: str | None = Cookie(default=None),
                   db: DbSession = Depends(get_db)):
    t = tr(request)
    sess, user, redirect = require_user(db, borant_session)
    if redirect:
        return redirect
    if not csrf_ok(sess, csrf):
        return RedirectResponse("/", status_code=303)
    if not user.email_verified_at:
        return page(request, db, "message.html", sess, user,
                    title=t["req_unverified_title"],
                    body=t["req_unverified_body"], back="/")

    target = db.get(App, app_id)
    if target is None or not target.active:
        return RedirectResponse("/", status_code=303)

    existing = (db.query(AccessRequest)
                  .filter(AccessRequest.user_id == user.id,
                          AccessRequest.app_id == target.id,
                          AccessRequest.status == "pending").first())
    if existing is None:
        db.add(AccessRequest(user_id=user.id, app_id=target.id,
                             message=message.strip()[:500]))
        db.commit()
        audit(db, "access.requested", user=user, ip=client_ip(request),
              app=target.slug)
        for a in db.query(User).filter(User.is_admin.is_(True),
                                       User.is_active.is_(True)).all():
            if a.email:
                mailer.send_access_request(
                    db, a.email, user.display, user.email, target.name,
                    target.host, message.strip()[:500],
                    settings.base_url(db))
    return page(request, db, "message.html", sess, user,
                title=t["req_sent_title"], body=t["req_sent_body"], back="/")


# ── Admin ─────────────────────────────────────────────────────────────────────

import admin  # noqa: E402  (imports `page`/`require_admin` from here)

app.include_router(admin.router)
