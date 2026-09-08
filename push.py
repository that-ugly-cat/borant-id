"""Telling an app, in advance, who is allowed in.

Without this, a profile in RoomPulse or ArguMap is born the first time its owner
opens the app. That is fine for four presenters and wrong for a class: until
somebody has clicked, they do not exist over there, so they cannot be put in a
workspace, assigned to a group, or prepared for in any way. The evening before
the lecture there is nobody to prepare.

So after a grant is written here, the gate tells the app: *these people may
come*. The app creates the rows and the roster is ready hours early.

Three things keep this small, and all three come from the same place — the far
end already works without us:

  - **The lazy path stays.** A push that fails costs the advance notice, never
    the person: whoever was missed is still provisioned at first access, the way
    everyone was before this file existed. That is why there is no queue here,
    no outbox and no retry. The repair for "the app was down" is a button that
    pushes the whole roster again, and it is idempotent because the far end
    keys on `subject`.
  - **Create-only, at the far end.** The endpoint may create profiles that do
    not exist. It may not update one, change a role, or deactivate anything.
    The gate does not become a service that can write into other people's
    databases (SPEC.md §2); it becomes one that can say a name in advance.
  - **No linking by email.** If a local profile already holds that address
    without a `borant_sub`, the far end reports a conflict and touches nothing.
    §10 rule 2 refuses that guess at runtime because one typo would merge two
    accounts, and the reason does not improve for happening at office hours.
    Those few come back in the result and get `map_borant.py` by hand.

Everything here is synchronous on purpose: it runs either in a threadpool (so
the single worker keeps answering `/verify` — §12) or as a background task
after the response has gone out.
"""
import logging

import httpx

import crypto
from models import App, Grant, User

log = logging.getLogger("borantid.push")

# Long enough for an app that clones a welcome map per person (ArguMap does),
# short enough that a container which is up but wedged does not hold an admin
# page open. Past this the roster is simply late, not lost.
TIMEOUT = 30.0

# One POST carries the whole class. Beyond this it is split, so that a roster of
# thousands cannot become one request that either all works or all fails.
CHUNK = 250


def roster(db, app: App, only_user_ids: list[int] | None = None) -> list[dict]:
    """Who this app should know about: subject, address, name, role hint.

    Normally that is its grant rows. An app left open to everyone
    (`any_authenticated`) has no grant rows by definition, and for it the
    honest answer is every active account — otherwise «resync» on an open app
    would push nobody and look broken. Those go across with an empty hint,
    which lets the app apply its own default role.
    """
    rows: dict[str, dict] = {}

    if app.default_access == "any_authenticated":
        query = db.query(User).filter(User.is_active.is_(True))
        if only_user_ids is not None:
            query = query.filter(User.id.in_(only_user_ids))
        for u in query.all():
            rows[u.subject] = {"subject": u.subject, "email": u.email or "",
                               "name": u.name or "", "hint": ""}

    query = (db.query(User, Grant)
             .join(Grant, Grant.user_id == User.id)
             .filter(Grant.app_id == app.id, User.is_active.is_(True)))
    if only_user_ids is not None:
        query = query.filter(User.id.in_(only_user_ids))
    for u, g in query.all():
        # An explicit grant wins over the blanket one: it carries a hint.
        rows[u.subject] = {"subject": u.subject, "email": u.email or "",
                           "name": u.name or "", "hint": g.level_hint or ""}

    return list(rows.values())


def send(app: App, entries: list[dict]) -> dict:
    """POST the roster and return what the far end says it did.

    Never raises: a push is an optimisation over a path that already works, so
    a failure is a line in the result and in the audit, not a 500 on a page
    where an admin has just created a hundred accounts.
    """
    result = {"ok": False, "created": 0, "already": 0, "conflict": 0,
              "conflicts": [], "sent": len(entries), "error": ""}
    if not app.provisions:
        result["error"] = "not_configured"
        return result
    if not entries:
        result["ok"] = True
        return result

    try:
        secret = crypto.decrypt(app.provision_secret)
    except Exception:
        # A rotated or corrupt FERNET_KEY must not look like a network problem:
        # it is a configuration fault and it says so.
        log.error("push %s: provision_secret non decifrabile, controlla FERNET_KEY", app.slug)
        result["error"] = "bad_secret"
        return result

    headers = {"Authorization": f"Bearer {secret}"}
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            for start in range(0, len(entries), CHUNK):
                chunk = entries[start:start + CHUNK]
                response = client.post(app.provision_url, headers=headers,
                                       json={"users": chunk})
                if response.status_code != 200:
                    result["error"] = f"http_{response.status_code}"
                    log.error("push %s: %s ha risposto %s — %s", app.slug,
                              app.provision_url, response.status_code,
                              response.text[:200])
                    return result
                body = response.json()
                result["created"] += int(body.get("created", 0))
                result["already"] += int(body.get("already", 0))
                result["conflict"] += int(body.get("conflict", 0))
                result["conflicts"].extend(body.get("conflicts", [])[:50])
    except (httpx.HTTPError, ValueError) as exc:
        result["error"] = type(exc).__name__
        log.error("push %s verso %s: %s", app.slug, app.provision_url, exc)
        return result

    result["ok"] = True
    log.info("push %s: creati %d, già presenti %d, conflitti %d",
             app.slug, result["created"], result["already"], result["conflict"])
    return result


def push_users(db, app_ids, user_ids: list[int] | None = None) -> dict[str, dict]:
    """Push to several apps at once. Returns {app name: result}.

    Apps that have not opted in are skipped silently: an empty `provision_url`
    is an answer, not an omission.
    """
    out = {}
    for app_id in app_ids:
        app = db.query(App).filter(App.id == int(app_id)).first()
        if app is None or not app.active or not app.provisions:
            continue
        out[app.name] = send(app, roster(db, app, user_ids))
    return out


def push_later(app_id: int, user_id: int) -> None:
    """One person, one app, after the response has already gone out.

    For the single grant given from /admin/users there is nowhere to show a
    number: the route redirects. So the outcome goes to the audit log instead
    of the screen, because a push that fails silently and leaves no trace would
    be worse than not pushing at all.

    Opens its own session on purpose — the request's is closed by the time a
    background task runs.
    """
    from models import SessionLocal, audit

    db = SessionLocal()
    try:
        app = db.query(App).filter(App.id == int(app_id)).first()
        if app is None or not app.active or not app.provisions:
            return
        result = send(app, roster(db, app, [int(user_id)]))
        audit(db, "grant.pushed", slug=app.slug,
              **{k: result[k] for k in ("ok", "created", "already", "conflict", "error")})
    except Exception as exc:                       # noqa: BLE001
        # A background task that raises dies in the server log and takes the
        # trace with it. The grant itself is already committed and the lazy
        # path still works, so this is a note, never a failure.
        log.error("push differito su app %s per l'utente %s: %s", app_id, user_id, exc)
    finally:
        db.close()


def audit_detail(results: dict[str, dict]) -> dict:
    """The compact shape that goes into the audit log: names and numbers, no
    addresses. The conflicts are already visible to the admin who caused them,
    and the log is kept for years."""
    return {name: {k: r[k] for k in ("ok", "created", "already", "conflict", "error")}
            for name, r in results.items()}
