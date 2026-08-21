"""
First admin, and the apps of the perimeter.

Run once after the first start:

    docker exec -it borantid python seed.py --email spit@... --name Spit

The password is generated and printed, not chosen on the command line: a
password typed as an argument ends up in the shell history and in `ps`.

`--apps` also registers the eleven apps of the perimeter with a default
one-factor policy on `/` and a two-factor policy where SPEC.md §11 asks for
one. Registering an app here does *not* gate it: that needs a Caddy block, and
it is a separate, reversible decision per app.
"""
import argparse
import secrets
import sys

import auth
from models import App, Policy, SessionLocal, TWO_FACTOR, User, init_db, utcnow

# (slug, name, host, two-factor prefixes) — SPEC.md §11
PERIMETER = [
    ("roompulse",   "RoomPulse",   "roompulse.borant.eu",   []),
    ("lssr",        "LSSR",        "lssr.borant.eu",        []),
    ("papertrail",  "PaperTrail",  "papertrail.borant.eu",  ["/admin"]),
    ("autocode",    "AutoCode",    "autocode.borant.eu",    ["/admin", "/api/admin"]),
    ("argumap",     "ArguMap",     "argumap.borant.eu",     ["/admin"]),
    ("survey",      "Survey",      "survey.borant.eu",      ["/admin"]),
    ("contrarian",  "Contrarian",  "contrarian.borant.eu",  ["/admin"]),
    ("grantradar",  "Grant Radar", "grantradar.borant.eu",  []),
    ("onopedia",    "Onopedia",    "wiki.borant.eu",        []),
    ("topictracker", "TopicTracker", "topictracker.borant.eu", []),
    ("paper2md",    "paper2md",    "paper2md.borant.eu",    []),
]


def seed_apps(db) -> int:
    made = 0
    for slug, name, host, two_factor in PERIMETER:
        a = db.query(App).filter(App.host == host).first()
        if a is None:
            a = App(slug=slug, name=name, host=host)
            db.add(a)
            db.commit()
            db.add(Policy(app_id=a.id, path_prefix="/", note="default"))
            made += 1
        for prefix in two_factor:
            exists = (db.query(Policy)
                        .filter(Policy.app_id == a.id,
                                Policy.path_prefix == prefix).first())
            if exists is None:
                db.add(Policy(app_id=a.id, path_prefix=prefix,
                              level=TWO_FACTOR, note="SPEC §11"))
        db.commit()
    return made


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--email", required=True)
    p.add_argument("--name", default="")
    p.add_argument("--apps", action="store_true",
                   help="registra anche le undici app del perimetro")
    args = p.parse_args()

    init_db()
    db = SessionLocal()
    try:
        email = args.email.strip().lower()
        if db.query(User).filter(User.email == email).first():
            print(f"Esiste già un utente con {email}. Niente da fare.")
            return 1

        password = secrets.token_urlsafe(18)
        u = User(email=email, name=args.name or email.split("@")[0],
                 password_hash=auth.hash_password(password),
                 email_verified_at=utcnow(), is_admin=True, is_active=True)
        db.add(u)
        db.commit()

        made = seed_apps(db) if args.apps else 0

        print("\nAmministratore creato.")
        print(f"  email:    {email}")
        print(f"  password: {password}")
        print("\nCambiala dal profilo dopo il primo accesso, e attiva il")
        print("secondo fattore prima di mettere una policy two_factor su")
        print("qualcosa che usi.")
        if args.apps:
            print(f"\nApp registrate: {made} nuove su {len(PERIMETER)}.")
            print("Registrare non significa gatare: quello lo fa Caddy, "
                  "un'app alla volta.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
