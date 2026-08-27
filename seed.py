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

`--descriptions` additionally rewrites the description of apps that are already
registered. It is the one thing in here that overwrites a choice somebody made
by hand, so it is a flag of its own and it prints every line it changes. The
descriptions are in English on purpose: the home page renders them in all four
languages out of a single column, and the wording is the one on borant.eu/tools
so that the two surfaces say the same thing.
"""
import argparse
import secrets
import sys

import auth
from models import App, Policy, SessionLocal, TWO_FACTOR, User, init_db, utcnow

# (slug, name, host, prefissi two-factor, ruoli, descrizione) — SPEC.md §11 e §17
#
# I ruoli riempiono soltanto il menu del campo «ruolo suggerito» in /admin. Il
# gate non li interpreta: il vocabolario di dominio è dell'app (SPEC.md §2).
#
# **Vuoto è una risposta.** Le tre app di categoria B lasciate vuote hanno un
# motivo diverso ciascuna, ed è scritto accanto. Le app di categoria A non
# leggono nessun header, quindi per loro l'hint non esiste proprio.
PERIMETER = [
    # categoria B — provisioning
    # Tutti e tre onorati dal 24/8/2026: prima il codice ne accettava solo
    # `free`, cioe' il pannello offriva un menu di cui il codice guardava un
    # terzo. `full` e `admin` usano la chiave Anthropic centrale.
    ("roompulse",   "RoomPulse",   "roompulse.borant.eu",   [],
     "free, full, admin", "Live polling for talks and lectures"),
    # `admin` dal 24/8/2026: e' un booleano, ma un booleano che il codice legge
    # dall'hint vale un vocabolario di una parola. Apre la gestione utenti, non
    # le funzioni del prodotto — quelle le ha chiunque abbia un grant.
    ("lssr",        "LSSR",        "lssr.borant.eu",        [],
     "admin", "Living systematic scoping review platform"),
    # `admin` dal 24/8/2026. Resta vero che il ruolo **di dominio** e' per
    # workspace e un hint globale non saprebbe rispondere a «read su quale»:
    # questo `admin` e' l'altro flag, quello che apre /admin/users.
    # Niente `2F` su /admin (deciso il 21/8/2026): quel pannello crea utenti e
    # workspace, non apre dati che il resto dell'app non apra già. Se torna
    # qui, un riseeding la rimette.
    ("papertrail",  "PaperTrail",  "papertrail.borant.eu",  [],
     "admin", "Research project tracker, idea to publication"),
    # `/` e non `/admin`, dal 24/8/2026, per la stessa ragione di Survey e con
    # una prova in più: il secondo fattore di AutoCode è **cablato davvero** —
    # `POST /api/auth/login` dà solo un pending token da dieci minuti finché
    # non si passa il TOTP. In `gateway` il login locale si spegne e quel
    # fattore se ne andrebbe con lui, quindi qui il gate non lo aggiunge, lo
    # eredita. E va su `/` perché le chiavi Anthropic per-utente si impostano
    # da `/profile`: un livello si mette su una classe di segreti, non su un URL.
    # `admin` dal 24/8/2026: apre /api/admin/*, cioe' la gestione utenti e il
    # reset del secondo fattore.
    # Attenzione all'omonimo: in AutoCode «roles» sono i ruoli dei parlanti
    # nelle trascrizioni, non i permessi.
    ("autocode",    "AutoCode",    "autocode.borant.eu",    ["/"],
     "admin", "AI-assisted qualitative coding platform"),
    # Riempito il 24/8/2026, quando ArguMap ha imparato a leggere l'hint. RBAC
    # vero, tabelle roles/permissions: questa lista e' una **fotografia** e va
    # rifatta se si crea un ruolo nuovo — e' il prezzo di non far chiamare le
    # app dal gate, che sarebbe l'unica alternativa sempre esatta.
    # `basic` e' l'unico che non ha il permesso `pipeline`, cioe' l'unico che
    # non spende: gli altri quattro sono onorati ma scrivono un warning.
    ("argumap",     "ArguMap",     "argumap.borant.eu",     ["/admin"],
     "basic, standard, full, teacher, admin", "Argument mapping platform"),

    # categoria A — solo la porta, nessun provisioning, nessun hint
    # `/` e non `/admin`: Survey impone il TOTP da sé su qualunque pagina da
    # autenticato, quindi una policy sul solo pannello avrebbe reso il passaggio
    # al gate un indebolimento. Gli export sotto /admin/surveys/{slug}/export.*
    # sono i dati dei rispondenti, e lo è anche il cruscotto che li elenca.
    ("survey",      "Survey",      "survey.borant.eu",      ["/"], "",
     "Structured survey platform"),
    ("contrarian",  "Contrarian",  "contrarian.borant.eu",  [], "",
     "Claim verification against the literature"),
                                 # Niente `2F` (deciso il 21/8/2026). Le
                                 # credenziali istituzionali si impostano da
                                 # `/me`, che e' a un fattore: metterlo solo su
                                 # `/admin` avrebbe protetto la porta di
                                 # servizio lasciando aperta quella principale.
    ("grantradar",  "Grant Radar", "grantradar.borant.eu",  [], "",
     "Funding opportunity radar"),
    ("onopedia",    "Onopedia",    "wiki.borant.eu",        [], "",
     "Served research wiki"),
    # `admin` dal 24/8/2026: apre /admin/users. Un non-admin crea run
    # tranquillamente, quindi qui il flag non e' la differenza fra usare e non.
    ("topictracker", "TopicTracker", "topictracker.borant.eu", [], "admin",
     "PubMed literature analysis platform"),
    ("paper2md",    "paper2md",    "paper2md.borant.eu",    [], "",
     "PDF-to-clean-text extraction service"),
    # Ruoli **vuoti**, e non per pigrizia: in TheList il ruolo e' per-board
    # (owner della propria lista, editor su invito) e vive nella tabella
    # `memberships`. Il gate non ha niente da suggerire, e infatti l'app non
    # legge nessun header di hint: il grant apre la porta, il ruolo lo decide
    # chi possiede la lista.
    ("thelist",     "TheList",     "thelist.borant.eu",     [], "",
     "Shared list of macro-tasks"),
]


def seed_apps(db, refresh_descriptions: bool = False) -> int:
    """Registra le app mancanti. `refresh_descriptions` riscrive anche quelle
    che ci sono già — è l'unica cosa qui dentro che sovrascrive una scelta fatta
    a mano, quindi sta dietro a un flag e stampa riga per riga cosa cambia."""
    made = 0
    for slug, name, host, two_factor, roles, description in PERIMETER:
        a = db.query(App).filter(App.host == host).first()
        if a is None:
            # L'host è la chiave di ricerca, lo slug è UNIQUE: se una riga con
            # questo slug esiste già sotto un altro host, l'INSERT esplode in
            # IntegrityError **a metà ciclo**, lasciando il registro riallineato
            # per le app viste prima e non per quelle dopo. Succede appena un
            # host cambia qui o viene corretto a mano da /admin/apps. Quale
            # delle due versioni abbia ragione non lo può decidere un seed.
            clash = db.query(App).filter(App.slug == slug).first()
            if clash is not None:
                print(f"  ! {slug}: registrato su {clash.host}, questa lista "
                      f"dice {host}. Salto: decidi da /admin/apps.")
                continue
            a = App(slug=slug, name=name, host=host, roles=roles,
                    description=description)
            db.add(a)
            db.commit()
            db.add(Policy(app_id=a.id, path_prefix="/", note="default"))
            made += 1
        else:
            if roles and not a.roles:
                # riallineo solo se qui non è mai stato scritto niente: quello
                # che è stato messo a mano da /admin vince sempre su questa
                # lista
                a.roles = roles
            # La descrizione la legge chi arriva sulla home, in quattro lingue,
            # e `apps` non ne ha una per lingua: sta in inglese come le vetrine
            # pubbliche, e come `borant.eu/tools`, da cui viene il testo.
            if description and (refresh_descriptions or not a.description):
                if a.description != description:
                    # ASCII di proposito: questo gira anche da una console
                    # Windows in cp1252, dove una freccia tipografica non
                    # stampa un carattere strano, alza UnicodeEncodeError e
                    # ferma il riallineamento a metà.
                    print(f'  {slug}: "{a.description}" -> "{description}"')
                    a.description = description
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
    p.add_argument("--email", default="",
                   help="crea un amministratore con questa email")
    p.add_argument("--name", default="")
    p.add_argument("--apps", action="store_true",
                   help="registra o riallinea le undici app del perimetro")
    p.add_argument("--descriptions", action="store_true",
                   help="riscrive anche le descrizioni gia' presenti con "
                        "quelle canoniche in inglese (implica --apps)")
    args = p.parse_args()

    if args.descriptions:
        args.apps = True
    if not args.email and not args.apps:
        p.error("serve almeno --email oppure --apps")

    init_db()
    db = SessionLocal()
    try:
        # --apps da solo riallinea il registro senza toccare gli utenti.
        # Prima --email era obbligatoria e un riallineamento distratto creava
        # un amministratore vero in produzione: successo il 21/8/2026.
        if not args.email:
            made = seed_apps(db, refresh_descriptions=args.descriptions)
            print(f"App registrate: {made} nuove su {len(PERIMETER)}.")
            print("Nessun utente creato.")
            return 0

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

        made = (seed_apps(db, refresh_descriptions=args.descriptions)
                if args.apps else 0)

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
