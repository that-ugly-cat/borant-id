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
from datetime import timedelta

from fastapi import APIRouter, Cookie, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session as DbSession

import auth
import mailer
import settings
from models import (
    ONE_FACTOR, TWO_FACTOR, App, Audit, Grant, Policy, Session, Token, User,
    audit, get_db, new_token, utcnow,
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
    return _page(request, db, "admin_users.html", sess, me, rows=rows,
                 pending=[t for t in pending if t.is_live()], apps=apps,
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
    return _page(request, db, "admin_config.html", sess, me, cfg=cfg,
                 has_password=bool(settings.get(db, "smtp_password_enc")),
                 site_name=settings.get(db, "site_name"),
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
