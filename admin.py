"""
Admin: users, apps, policies, grants, sessions, audit, SMTP config.

This is where the two questions of SPEC.md §8 that belong to the gate get
answered by hand: *who may enter which app* (grants) and *what level a path
demands* (policies). The third question — what a user may do once inside — is
not here and never will be: that is the app's, and PaperTrail's workspace model
already says it better than any claim could.

Every write invalidates the caches in auth.py. Forgetting that is how a revoked
grant keeps working for thirty seconds.
"""
import json
import secrets
from datetime import timedelta
from urllib.parse import quote

from fastapi import APIRouter, Cookie, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session as DbSession

import auth
import mailer
import settings
from models import (
    ONE_FACTOR, TWO_FACTOR, AccessRequest, App, Audit, Grant, Policy,
    Session, Token, User, audit, get_db, new_token, utcnow,
)

router = APIRouter(prefix="/admin")

INVITE_DAYS = 14


def _guard(db, token):
    """(sess, user, redirect). Import-time cycle avoided by importing main
    lazily — admin is included by main, not the other way round."""
    from main import require_admin
    return require_admin(db, token)


def _page(request, db, name, sess, user, **ctx):
    from main import page
    return page(request, db, name, sess, user, **ctx)


def _ip(request):
    from main import client_ip
    return client_ip(request)


def _csrf_ok(sess, given):
    from main import csrf_ok
    return csrf_ok(sess, given)


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
def admin_home():
    return RedirectResponse("/admin/users", status_code=303)


@router.get("/users", response_class=HTMLResponse)
def users(request: Request, borant_session: str | None = Cookie(default=None),
          db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    rows = db.query(User).order_by(User.created_at.desc()).all()
    pending = (db.query(Token)
                 .filter(Token.kind == "invite", Token.used_at.is_(None))
                 .order_by(Token.created_at.desc()).all())
    apps = db.query(App).order_by(App.name).all()
    requests_pending = (db.query(AccessRequest)
                          .filter(AccessRequest.status == "pending")
                          .order_by(AccessRequest.created_at).all())
    return _page(request, db, "admin_users.html", sess, me, rows=rows,
                 pending=[t for t in pending if t.is_live()], apps=apps,
                 requests=requests_pending,
                 invite_link=request.query_params.get("link", ""),
                 mail_error=request.query_params.get("mailerr", ""))


@router.post("/users/invite", response_class=HTMLResponse)
async def invite(request: Request, email: str = Form(""), name: str = Form(""),
                 orcid_hint: str = Form(""), is_admin: str = Form(""),
                 csrf: str = Form(""),
                 borant_session: str | None = Cookie(default=None),
                 db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    if not _csrf_ok(sess, csrf):
        return RedirectResponse("/admin/users", status_code=303)

    email = email.strip().lower()
    if not email or "@" not in email:
        return RedirectResponse("/admin/users", status_code=303)

    # The app checkboxes are dynamic (one per row in `apps`), so they are read
    # from the raw form rather than declared as parameters.
    form = await request.form()
    grants = {}
    for key in form.keys():
        if key.startswith("app_"):
            app_id = key[len("app_"):]
            grants[app_id] = (form.get(f"hint_{app_id}") or "").strip()

    plain, digest = new_token()
    db.add(Token(kind="invite", token_hash=digest, email=email,
                 payload=json.dumps({"name": name.strip(),
                                     "orcid": orcid_hint.strip(),
                                     "is_admin": bool(is_admin),
                                     "grants": grants}),
                 expires_at=utcnow() + timedelta(days=INVITE_DAYS),
                 created_by=me.display))
    db.commit()

    link = f"{settings.base_url(db)}/invite/{plain}"
    ok, err = mailer.send_invite(db, email, name.strip(), link)
    audit(db, "invite.created", user=me, ip=_ip(request), email=email,
          mail_ok=ok, error=err)

    # Mail is a degradable dependency: when the relay is not there, hand the
    # link over on screen rather than leaving a dead invite in the table.
    from urllib.parse import quote
    if ok:
        return RedirectResponse("/admin/users", status_code=303)
    return RedirectResponse(
        f"/admin/users?link={quote(link, safe='')}&mailerr={quote(err[:200], safe='')}",
        status_code=303)


@router.post("/users/{uid}/toggle-active")
def toggle_active(uid: int, request: Request, csrf: str = Form(""),
                  borant_session: str | None = Cookie(default=None),
                  db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    u = db.get(User, uid)
    if u is not None and _csrf_ok(sess, csrf) and u.id != me.id:
        u.is_active = not u.is_active
        db.commit()
        if not u.is_active:
            auth.revoke_all(db, u, "deactivated")
        auth.invalidate_user(u.id)
        audit(db, "user.toggled", user=me, ip=_ip(request), target=u.email,
              active=u.is_active)
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/users/{uid}/toggle-admin")
def toggle_admin(uid: int, request: Request, csrf: str = Form(""),
                 borant_session: str | None = Cookie(default=None),
                 db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    u = db.get(User, uid)
    if u is not None and _csrf_ok(sess, csrf) and u.id != me.id:
        u.is_admin = not u.is_admin
        db.commit()
        auth.invalidate_registry()
        audit(db, "user.admin_toggled", user=me, ip=_ip(request),
              target=u.email, admin=u.is_admin)
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/users/{uid}/reset-2fa")
def reset_2fa(uid: int, request: Request, csrf: str = Form(""),
              borant_session: str | None = Cookie(default=None),
              db: DbSession = Depends(get_db)):
    """The break-glass for a lost authenticator. Logged loudly, and the owner
    is told by mail — an admin silently clearing someone's second factor is
    exactly the move an attacker would want."""
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    u = db.get(User, uid)
    if u is not None and _csrf_ok(sess, csrf):
        from models import BackupCode
        u.totp_secret = None
        u.totp_confirmed_at = None
        u.always_2fa = False
        db.query(BackupCode).filter(BackupCode.user_id == u.id).delete()
        db.commit()
        auth.invalidate_user(u.id)
        audit(db, "user.2fa_reset_by_admin", user=me, ip=_ip(request),
              target=u.email)
        if u.email:
            mailer.send_security_notice(
                db, u.email, "Secondo fattore azzerato da un amministratore",
                f"È stato azzerato da {me.display}. Riattivalo dal profilo.")
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/users/{uid}/grant")
def set_grant(uid: int, request: Request, app_id: int = Form(0),
              level_hint: str = Form(""), remove: str = Form(""),
              csrf: str = Form(""),
              borant_session: str | None = Cookie(default=None),
              db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    if not _csrf_ok(sess, csrf):
        return RedirectResponse("/admin/users", status_code=303)
    u, a = db.get(User, uid), db.get(App, app_id)
    if u is None or a is None:
        return RedirectResponse("/admin/users", status_code=303)

    g = (db.query(Grant).filter(Grant.user_id == u.id,
                                Grant.app_id == a.id).first())
    if remove:
        if g is not None:
            db.delete(g)
        action = "revoked"
    elif g is None:
        db.add(Grant(user_id=u.id, app_id=a.id, level_hint=level_hint.strip(),
                     created_by=me.display))
        action = "granted"
    else:
        g.level_hint = level_hint.strip()
        action = "updated"
    db.commit()
    auth.invalidate_registry()
    audit(db, f"grant.{action}", user=me, ip=_ip(request), target=u.email,
          app=a.slug, hint=level_hint)
    return RedirectResponse(f"/admin/users#u{uid}", status_code=303)


# ── Apps and policies ─────────────────────────────────────────────────────────

@router.get("/apps", response_class=HTMLResponse)
def apps(request: Request, borant_session: str | None = Cookie(default=None),
         db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    rows = db.query(App).order_by(App.name).all()
    return _page(request, db, "admin_apps.html", sess, me, rows=rows,
                 levels=(ONE_FACTOR, TWO_FACTOR))


@router.post("/apps", response_class=HTMLResponse)
def app_create(request: Request, slug: str = Form(""), name: str = Form(""),
               host: str = Form(""), description: str = Form(""),
               default_access: str = Form("grant_required"),
               roles: str = Form(""), csrf: str = Form(""),
               borant_session: str | None = Cookie(default=None),
               db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    if not _csrf_ok(sess, csrf):
        return RedirectResponse("/admin/apps", status_code=303)
    slug, host = slug.strip().lower(), host.strip().lower()
    if slug and host and not db.query(App).filter(App.host == host).first():
        a = App(slug=slug, name=name.strip() or slug, host=host,
                description=description.strip(),
                roles=", ".join(r.strip() for r in roles.split(",") if r.strip()),
                default_access=(default_access if default_access in
                                ("grant_required", "any_authenticated")
                                else "grant_required"))
        db.add(a)
        db.commit()
        db.add(Policy(app_id=a.id, path_prefix="/", level=ONE_FACTOR,
                      note="default"))
        db.commit()
        auth.invalidate_registry()
        audit(db, "app.created", user=me, ip=_ip(request), slug=slug, host=host)
    return RedirectResponse("/admin/apps", status_code=303)


@router.post("/apps/{aid}/toggle")
def app_toggle(aid: int, request: Request, csrf: str = Form(""),
               borant_session: str | None = Cookie(default=None),
               db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    a = db.get(App, aid)
    if a is not None and _csrf_ok(sess, csrf):
        a.active = not a.active
        db.commit()
        auth.invalidate_registry()
        audit(db, "app.toggled", user=me, ip=_ip(request), slug=a.slug,
              active=a.active)
    return RedirectResponse("/admin/apps", status_code=303)


@router.post("/apps/{aid}/roles")
def app_roles(aid: int, request: Request, roles: str = Form(""),
              csrf: str = Form(""),
              borant_session: str | None = Cookie(default=None),
              db: DbSession = Depends(get_db)):
    """Il vocabolario che questa app usa per X-Borant-Hint.

    Serve solo a riempire il menu nella form dei grant: il gate non lo
    interpreta e non lo impone. Lasciarlo **vuoto è una risposta**, non una
    dimenticanza — per le app che hanno un booleano invece dei ruoli il campo
    sparisce del tutto."""
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    a = db.get(App, aid)
    if a is not None and _csrf_ok(sess, csrf):
        cleaned = ", ".join(r.strip() for r in roles.split(",") if r.strip())
        a.roles = cleaned
        db.commit()
        auth.invalidate_registry()
        audit(db, "app.roles_set", user=me, ip=_ip(request), slug=a.slug,
              roles=cleaned)
    return RedirectResponse(f"/admin/apps#a{aid}", status_code=303)


@router.post("/apps/{aid}/access")
def app_access(aid: int, request: Request, default_access: str = Form(""),
               csrf: str = Form(""),
               borant_session: str | None = Cookie(default=None),
               db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    a = db.get(App, aid)
    if a is not None and _csrf_ok(sess, csrf) and default_access in (
            "grant_required", "any_authenticated"):
        a.default_access = default_access
        db.commit()
        auth.invalidate_registry()
        audit(db, "app.access_changed", user=me, ip=_ip(request), slug=a.slug,
              mode=default_access)
    return RedirectResponse("/admin/apps", status_code=303)


@router.post("/apps/{aid}/policy")
def policy_upsert(aid: int, request: Request, path_prefix: str = Form("/"),
                  level: str = Form(ONE_FACTOR), max_age: str = Form(""),
                  note: str = Form(""), remove: str = Form(""),
                  policy_id: int = Form(0), csrf: str = Form(""),
                  borant_session: str | None = Cookie(default=None),
                  db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    a = db.get(App, aid)
    if a is None or not _csrf_ok(sess, csrf):
        return RedirectResponse("/admin/apps", status_code=303)

    if remove and policy_id:
        p = db.get(Policy, policy_id)
        if p is not None and p.app_id == a.id and p.path_prefix != "/":
            db.delete(p)
            db.commit()
            auth.invalidate_registry()
            audit(db, "policy.removed", user=me, ip=_ip(request), slug=a.slug,
                  prefix=p.path_prefix)
        return RedirectResponse(f"/admin/apps#a{aid}", status_code=303)

    prefix = auth.normalize_path(path_prefix or "/")
    lvl = level if level in (ONE_FACTOR, TWO_FACTOR) else ONE_FACTOR
    try:
        age = int(max_age) if max_age.strip() else None
    except ValueError:
        age = None

    p = (db.query(Policy).filter(Policy.app_id == a.id,
                                 Policy.path_prefix == prefix).first())
    if p is None:
        db.add(Policy(app_id=a.id, path_prefix=prefix, level=lvl,
                      max_age_minutes=age, note=note.strip()))
    else:
        p.level, p.max_age_minutes, p.note = lvl, age, note.strip()
    db.commit()
    auth.invalidate_registry()
    audit(db, "policy.set", user=me, ip=_ip(request), slug=a.slug,
          prefix=prefix, level=lvl, max_age=age)
    return RedirectResponse(f"/admin/apps#a{aid}", status_code=303)


# ── Sessions and audit ────────────────────────────────────────────────────────

@router.get("/sessions", response_class=HTMLResponse)
def sessions(request: Request,
             borant_session: str | None = Cookie(default=None),
             db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    rows = [s for s in db.query(Session).order_by(Session.authed_at.desc())
            .limit(300).all() if s.is_live()]
    return _page(request, db, "admin_sessions.html", sess, me, rows=rows)


@router.post("/sessions/{sid}/revoke")
def session_revoke(sid: int, request: Request, csrf: str = Form(""),
                   borant_session: str | None = Cookie(default=None),
                   db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    target = db.get(Session, sid)
    if target is not None and _csrf_ok(sess, csrf):
        auth.revoke(db, target, "revoked_by_admin")
        audit(db, "session.revoked_by_admin", user=me, ip=_ip(request),
              target=target.user.email if target.user else "", sid=sid)
    return RedirectResponse("/admin/sessions", status_code=303)


@router.get("/audit", response_class=HTMLResponse)
def audit_log(request: Request, q: str = "",
              borant_session: str | None = Cookie(default=None),
              db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    query = db.query(Audit).order_by(Audit.ts.desc())
    if q.strip():
        query = query.filter(Audit.event.like(f"%{q.strip()}%"))
    rows = query.limit(400).all()
    users = {u.id: u for u in db.query(User).all()}
    return _page(request, db, "admin_audit.html", sess, me, rows=rows,
                 users=users, q=q)


# ── SMTP configuration ────────────────────────────────────────────────────────

@router.get("/config", response_class=HTMLResponse)
def config(request: Request, borant_session: str | None = Cookie(default=None),
           db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    cfg = settings.smtp_config(db)
    cfg.pop("password", None)
    everyone = (db.query(User)
                  .filter(User.is_active.is_(True), User.email.isnot(None))
                  .order_by(User.email).all())
    return _page(request, db, "admin_config.html", sess, me, cfg=cfg,
                 has_password=bool(settings.get(db, "smtp_password_enc")),
                 site_name=settings.get(db, "site_name"),
                 registration_domains=settings.get(db, "registration_domains"),
                 apps=db.query(App).order_by(App.name).all(),
                 all_users=everyone, n_users=len(everyone),
                 base=settings.base_url(db),
                 msg=request.query_params.get("msg", ""),
                 error=request.query_params.get("err", ""))


@router.post("/config")
def config_save(request: Request, smtp_enabled: str = Form(""),
                smtp_host: str = Form(""), smtp_port: str = Form("587"),
                smtp_security: str = Form("starttls"),
                smtp_username: str = Form(""), smtp_password: str = Form(""),
                clear_password: str = Form(""),
                smtp_from_email: str = Form(""),
                smtp_from_name: str = Form("Borant ID"),
                site_name: str = Form("Borant ID"),
                public_base_url: str = Form(""),
                registration_open: str = Form(""),
                registration_domains: str = Form(""),
                csrf: str = Form(""),
                borant_session: str | None = Cookie(default=None),
                db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    if not _csrf_ok(sess, csrf):
        return RedirectResponse("/admin/config", status_code=303)

    settings.put_many(db, {
        "smtp_enabled": "1" if smtp_enabled else "0",
        "smtp_host": smtp_host.strip(),
        "smtp_port": smtp_port.strip() or "587",
        "smtp_security": (smtp_security if smtp_security in
                          ("starttls", "ssl", "none") else "starttls"),
        "smtp_username": smtp_username.strip(),
        "smtp_from_email": smtp_from_email.strip(),
        "smtp_from_name": smtp_from_name.strip() or "Borant ID",
        "site_name": site_name.strip() or "Borant ID",
        "public_base_url": (public_base_url.strip().rstrip("/") or
                            settings.base_url(db)),
        "registration_open": "1" if registration_open else "0",
        "registration_domains": ", ".join(
            d.strip().lstrip("@") for d in registration_domains.split(",")
            if d.strip()),
    })
    if clear_password:
        settings.clear_smtp_password(db)
    else:
        # Blank means "leave it": the form never round-trips the password back
        # to the browser, so an empty field is not an instruction to erase it.
        settings.set_smtp_password(db, smtp_password)

    audit(db, "config.saved", user=me, ip=_ip(request))
    return RedirectResponse("/admin/config?msg=Configurazione+salvata",
                            status_code=303)


@router.post("/config/test")
def config_test(request: Request, to: str = Form(""), csrf: str = Form(""),
                borant_session: str | None = Cookie(default=None),
                db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    if not _csrf_ok(sess, csrf):
        return RedirectResponse("/admin/config", status_code=303)
    from urllib.parse import quote
    target = to.strip() or (me.email or "")
    ok, err = mailer.send(db, target, "Prova di invio — Borant ID",
                          "Se leggi questo, il relay SMTP funziona.\n")
    audit(db, "config.smtp_test", user=me, ip=_ip(request), to=target,
          ok=ok, error=err)
    if ok:
        return RedirectResponse(
            f"/admin/config?msg={quote('Mail di prova inviata a ' + target)}",
            status_code=303)
    return RedirectResponse(f"/admin/config?err={quote(err[:300])}",
                            status_code=303)


# ── Richieste di accesso ──────────────────────────────────────────────────────
#
# La seconda metà della registrazione aperta. Il ruolo si sceglie **qui**, al
# momento di approvare, non quando la richiesta viene fatta: è l'unico momento
# in cui si sa cosa concedere, ed è la difesa contro il concedere per inerzia
# un ruolo che spende (SPEC.md §18).

@router.post("/requests/{rid}/approve")
def request_approve(rid: int, request: Request, level_hint: str = Form(""),
                    csrf: str = Form(""),
                    borant_session: str | None = Cookie(default=None),
                    db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    req = db.get(AccessRequest, rid)
    if req is None or not _csrf_ok(sess, csrf) or req.status != "pending":
        return RedirectResponse("/admin/users", status_code=303)

    if not db.query(Grant).filter(Grant.user_id == req.user_id,
                                  Grant.app_id == req.app_id).first():
        db.add(Grant(user_id=req.user_id, app_id=req.app_id,
                     level_hint=level_hint.strip(), created_by=me.display))
    req.status = "approved"
    req.decided_at = utcnow()
    req.decided_by = me.display
    db.commit()
    auth.invalidate_registry()
    audit(db, "access.approved", user=me, ip=_ip(request),
          target=req.user.email if req.user else "", app=req.app.slug,
          hint=level_hint)
    if req.user and req.user.email:
        mailer.send(db, req.user.email,
                    f"Accesso concesso: {req.app.name}",
                    f"Puoi ora entrare in {req.app.name} "
                    f"(https://{req.app.host}/).\n")
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/requests/{rid}/deny")
def request_deny(rid: int, request: Request, csrf: str = Form(""),
                 borant_session: str | None = Cookie(default=None),
                 db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    req = db.get(AccessRequest, rid)
    if req is None or not _csrf_ok(sess, csrf) or req.status != "pending":
        return RedirectResponse("/admin/users", status_code=303)
    req.status = "denied"
    req.decided_at = utcnow()
    req.decided_by = me.display
    db.commit()
    audit(db, "access.denied", user=me, ip=_ip(request),
          target=req.user.email if req.user else "", app=req.app.slug)
    return RedirectResponse("/admin/users", status_code=303)


# ── Creazione in blocco ───────────────────────────────────────────────────────

def _parse_people(raw: str) -> list[tuple[str, str]]:
    """Una persona per riga: `email` oppure `email, Nome Cognome`.

    Tollera il punto e virgola e il tab perché è così che escono gli elenchi
    incollati da un foglio, e chiedere a qualcuno di ripulire trenta righe a
    mano è il modo migliore di far usare un'altra strada."""
    people, seen = [], set()
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for sep in (";", "\t"):
            line = line.replace(sep, ",")
        parts = [p.strip() for p in line.split(",")]
        email = parts[0].lower()
        if "@" not in email or email in seen:
            continue
        seen.add(email)
        people.append((email, " ".join(parts[1:]).strip()))
    return people


@router.post("/users/batch", response_class=HTMLResponse)
async def users_batch(request: Request, people: str = Form(""),
                      mode: str = Form("invite"), csrf: str = Form(""),
                      borant_session: str | None = Cookie(default=None),
                      db: DbSession = Depends(get_db)):
    """Trenta studenti in un colpo solo, con i grant già assegnati.

    Due modi. `invite` manda un link e lascia scegliere la password a loro:
    più sicuro, e verifica l'indirizzo per costruzione. `create` crea l'account
    con una password generata, che compare **una volta sola** in una tabella da
    copiare — serve per l'aula dove la posta istituzionale non arriva o non si
    può aspettare.
    """
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    if not _csrf_ok(sess, csrf):
        return RedirectResponse("/admin/users", status_code=303)

    form = await request.form()
    grants = {}
    for key in form.keys():
        if key.startswith("app_"):
            app_id = key[len("app_"):]
            grants[app_id] = (form.get(f"hint_{app_id}") or "").strip()

    rows = []
    for email, name in _parse_people(people):
        existing = db.query(User).filter(User.email == email).first()
        if existing is not None:
            # Non si tocca chi c'è già: si aggiungono solo i grant mancanti,
            # perché un batch rilanciato per sbaglio non deve azzerare nulla.
            for app_id, hint in grants.items():
                if not db.query(Grant).filter(
                        Grant.user_id == existing.id,
                        Grant.app_id == int(app_id)).first():
                    db.add(Grant(user_id=existing.id, app_id=int(app_id),
                                 level_hint=hint, created_by=me.display))
            db.commit()
            rows.append({"email": email, "esito": "già presente, grant aggiornati",
                         "extra": ""})
            continue

        if mode == "create":
            password = secrets.token_urlsafe(12)
            # Verificata per asserzione dell'admin: nessuna mail parte in
            # questa modalità, quindi senza questo l'utente resterebbe in un
            # vicolo cieco — non può chiedere altre app e non ha un link da
            # cliccare. Nel modo `invite` la verifica arriva dall'accettazione.
            u = User(email=email, name=name or email.split("@")[0],
                     password_hash=auth.hash_password(password),
                     email_verified_at=utcnow(), is_active=True)
            db.add(u)
            db.commit()
            for app_id, hint in grants.items():
                db.add(Grant(user_id=u.id, app_id=int(app_id),
                             level_hint=hint, created_by=me.display))
            db.commit()
            rows.append({"email": email, "esito": "account creato",
                         "extra": password})
        else:
            plain, digest = new_token()
            db.add(Token(kind="invite", token_hash=digest, email=email,
                         payload=json.dumps({"name": name, "grants": grants}),
                         expires_at=utcnow() + timedelta(days=INVITE_DAYS),
                         created_by=me.display))
            db.commit()
            link = f"{settings.base_url(db)}/invite/{plain}"
            ok, err = mailer.send_invite(db, email, name, link)
            rows.append({"email": email,
                         "esito": "invito inviato" if ok else f"mail non partita: {err[:60]}",
                         "extra": "" if ok else link})

    auth.invalidate_registry()
    audit(db, "users.batch", user=me, ip=_ip(request), mode=mode,
          count=len(rows), apps=list(grants))
    return _page(request, db, "admin_batch.html", sess, me, rows=rows,
                 mode=mode)


# ── Cancellazione utente ──────────────────────────────────────────────────────
#
# Esiste perché con le classi arriveranno richieste di cancellazione dati, e
# fino a oggi non c'era una strada: il pannello offre «disattiva», e un
# `DELETE` diretto sbatte contro la chiave esterna di `audit`.
#
# Tre cose che questa funzione fa e che non sono ovvie:
#
#   1. **Le righe di audit sopravvivono, slegate.** Un log che sparisce quando
#      sparisce l'utente non è un log. Restano con `user_id = NULL`, e le
#      occorrenze dell'indirizzo nel dettaglio vengono sostituite, altrimenti
#      la cancellazione sarebbe finta.
#
#   2. **Non cancella niente nelle app.** Il profilo locale in LSSR, ArguMap o
#      PaperTrail resta dov'è, con il suo `borant_sub` ormai orfano. Per una
#      cancellazione vera bisogna passare da ognuna. La pagina di conferma
#      elenca quali, perché scoprirlo dopo significa credere di aver cancellato
#      qualcuno e non averlo fatto.
#
#   3. **Chiede di riscrivere l'indirizzo.** In un elenco di trenta studenti un
#      bottone rosso accanto al nome sbagliato è un incidente che aspetta.

def _delete_blockers(db, me, u):
    """Perché questo utente non si può cancellare, se non si può."""
    if u is None:
        return "Utente inesistente."
    if u.id == me.id:
        return "Non puoi cancellare il tuo stesso account."
    if u.is_admin:
        others = (db.query(User)
                    .filter(User.is_admin.is_(True), User.is_active.is_(True),
                            User.id != u.id).count())
        if others == 0:
            return ("È l'ultimo amministratore attivo. Nominane un altro "
                    "prima, o resti fuori tu.")
    return ""


@router.get("/users/{uid}/delete", response_class=HTMLResponse)
def delete_confirm(uid: int, request: Request,
                   borant_session: str | None = Cookie(default=None),
                   db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    u = db.get(User, uid)
    blocker = _delete_blockers(db, me, u)
    if u is None:
        return RedirectResponse("/admin/users", status_code=303)

    apps_with_grant = [db.get(App, g.app_id) for g in u.grants]
    live_sessions = sum(1 for s in u.sessions if s.is_live())
    audit_rows = db.query(Audit).filter(Audit.user_id == u.id).count()
    return _page(request, db, "admin_user_delete.html", sess, me, target=u,
                 apps_with_grant=[a for a in apps_with_grant if a],
                 live_sessions=live_sessions, audit_rows=audit_rows,
                 blocker=blocker,
                 error=request.query_params.get("err", ""))


@router.post("/users/{uid}/delete")
def delete_user(uid: int, request: Request, confirm_email: str = Form(""),
                csrf: str = Form(""),
                borant_session: str | None = Cookie(default=None),
                db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    u = db.get(User, uid)
    if u is None or not _csrf_ok(sess, csrf):
        return RedirectResponse("/admin/users", status_code=303)

    blocker = _delete_blockers(db, me, u)
    if blocker:
        return RedirectResponse(f"/admin/users/{uid}/delete?err="
                                f"{quote(blocker)}", status_code=303)

    typed = (confirm_email or "").strip().lower()
    if not u.email or typed != u.email.lower():
        return RedirectResponse(
            f"/admin/users/{uid}/delete?err="
            f"{quote('Riscrivi esattamente l indirizzo per confermare.')}",
            status_code=303)

    subject, email, name = u.subject, u.email, u.name
    apps_touched = [db.get(App, g.app_id).slug for g in u.grants
                    if db.get(App, g.app_id)]

    # 1. le sessioni muoiono subito, prima di toccare qualsiasi altra cosa
    auth.revoke_all(db, u, "account_deleted")

    # 2. il log resta, slegato e ripulito dall'indirizzo.
    #
    # Lo slegamento tocca solo le righe di questo utente, ma la ripulitura deve
    # passare su **tutte**: un `invite.created` è registrato sotto l'admin che
    # l'ha mandato e contiene l'indirizzo dell'invitato. Cancellare solo le
    # proprie righe lascerebbe l'email in giro sotto il nome di qualcun altro,
    # che è una cancellazione finta.
    own = db.query(Audit).filter(Audit.user_id == u.id).all()
    for row in own:
        row.user_id = None
    scrubbed = 0
    for row in db.query(Audit).all():
        detail = row.detail or ""
        original = detail
        if email:
            detail = detail.replace(email, "(indirizzo rimosso)")
        if name and len(name) > 3:      # un nome di due lettere colpirebbe di tutto
            detail = detail.replace(name, "(nome rimosso)")
        if detail != original:
            row.detail = detail
            scrubbed += 1
    db.commit()

    # 3. ciò che non ha cascade dichiarata. Gli inviti pendenti hanno
    # `user_id` nullo — l'utente non esisteva ancora quando sono stati creati —
    # quindi vanno presi per indirizzo, o restano lì buoni da usare.
    db.query(AccessRequest).filter(AccessRequest.user_id == u.id).delete()
    db.query(Token).filter(Token.user_id == u.id).delete()
    if email:
        db.query(Token).filter(Token.email == email).delete()
    db.commit()

    # 4. l'utente, e con lui grants, sessioni e codici di backup
    db.delete(u)
    db.commit()
    auth.invalidate_registry()

    # L'evento si registra con il `subject`, non con l'email: tenerla qui
    # significherebbe cancellare l'indirizzo da ogni riga tranne quella che
    # dice che è stato cancellato.
    audit(db, "user.deleted", user=me, ip=_ip(request), subject=subject,
          audit_rows_kept=len(own), audit_rows_scrubbed=scrubbed,
          apps=apps_touched)
    return RedirectResponse("/admin/users?deleted=1", status_code=303)


# ── Messaggi agli utenti ──────────────────────────────────────────────────────
#
# Tre scelte che valgono più del codice:
#
#   1. **Una mail per persona, mai in copia nascosta.** Un BCC a trenta
#      studenti sembra efficiente ed è il modo di scoprire che qualcuno ha
#      risposto a tutti. E non risparmia quota: Infomaniak conta i destinatari
#      uno per uno comunque. Individuale vuol dire anche che la tabella dei
#      risultati dice *chi* è fallito, non *che qualcosa* è fallito.
#
#   2. **Solo a utenti registrati.** Nessun campo per indirizzi liberi: quello
#      farebbe di questo pannello un piccolo strumento di spam, con la
#      reputazione di un dominio vero attaccata sopra.
#
#   3. **Si passa da una conferma**, come per la cancellazione (§19). Spedire è
#      irreversibile e tocca altre persone: vedere quanti sono prima di premere
#      non è cerimonia.

def _recipients(db, target: str):
    """(lista di utenti, descrizione leggibile). Solo attivi e con un'email:
    un utente entrato solo con ORCID può non averla."""
    base = (db.query(User)
              .filter(User.is_active.is_(True), User.email.isnot(None))
              .order_by(User.email))
    if target == "tutti":
        return base.all(), "tutti gli utenti attivi"
    if target.startswith("app:"):
        try:
            app_id = int(target[4:])
        except ValueError:
            return [], "selezione non valida"
        a = db.get(App, app_id)
        if a is None:
            return [], "app inesistente"
        ids = {g.user_id for g in
               db.query(Grant).filter(Grant.app_id == app_id).all()}
        return [u for u in base.all() if u.id in ids], f"chi ha un grant su {a.name}"
    if target.startswith("user:"):
        try:
            u = db.get(User, int(target[5:]))
        except ValueError:
            return [], "selezione non valida"
        return ([u] if u and u.is_active and u.email else []), "un utente solo"
    return [], "selezione non valida"


@router.post("/message/preview", response_class=HTMLResponse)
def message_preview(request: Request, target: str = Form("tutti"),
                    subject: str = Form(""), body: str = Form(""),
                    csrf: str = Form(""),
                    borant_session: str | None = Cookie(default=None),
                    db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    if not _csrf_ok(sess, csrf):
        return RedirectResponse("/admin/config", status_code=303)

    people,descrizione = _recipients(db, target)
    problem = ""
    if not subject.strip() or not body.strip():
        problem = "Servono un oggetto e un testo."
    elif not people:
        problem = "Nessun destinatario con questa selezione."
    elif not settings.get_bool(db, "smtp_enabled"):
        problem = "SMTP non è attivo: la mail non partirebbe."

    return _page(request, db, "admin_message.html", sess, me, sent=False,
                 people=people, target=target, description=descrizione,
                 subject=subject, body=body, problem=problem, rows=[])


@router.post("/message/send", response_class=HTMLResponse)
def message_send(request: Request, target: str = Form("tutti"),
                 subject: str = Form(""), body: str = Form(""),
                 csrf: str = Form(""),
                 borant_session: str | None = Cookie(default=None),
                 db: DbSession = Depends(get_db)):
    sess, me, redirect = _guard(db, borant_session)
    if redirect:
        return redirect
    if not _csrf_ok(sess, csrf):
        return RedirectResponse("/admin/config", status_code=303)

    people, descrizione = _recipients(db, target)
    if not subject.strip() or not body.strip() or not people:
        return RedirectResponse("/admin/config", status_code=303)

    rows, ok_count = [], 0
    for u in people:
        text = (body.replace("{nome}", u.name or u.email.split("@")[0])
                    .replace("{email}", u.email))
        ok, err = mailer.send(db, u.email, subject.strip(), text + "\n")
        rows.append({"email": u.email, "ok": ok, "error": err[:80]})
        if ok:
            ok_count += 1

    # Il corpo non finisce nel log: può essere lungo e può contenere di tutto.
    # Restano oggetto, quanti e a chi, che è ciò che serve per ricostruire.
    audit(db, "message.sent", user=me, ip=_ip(request), subject=subject.strip(),
          target=descrizione, inviati=ok_count, falliti=len(rows) - ok_count)
    return _page(request, db, "admin_message.html", sess, me, sent=True,
                 people=people, target=target, description=descrizione,
                 subject=subject, body=body, problem="", rows=rows)
