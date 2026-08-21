"""
Configuration that lives in the database instead of the environment.

Today that means the SMTP relay, which Spit sets from /admin/config after the
gate is already running — the mailbox is not known at deploy time and does not
belong in a compose file that gets committed.

Everything security-critical stays in the environment (JWT/FERNET keys, the
ORCID client secret): those are needed before the first request and must not be
editable from a web form.
"""
import json

from models import Setting
from crypto import decrypt_or_none, encrypt

SMTP_DEFAULTS = {
    "smtp_enabled": "0",
    "smtp_host": "",
    "smtp_port": "587",
    "smtp_security": "starttls",     # starttls | ssl | none
    "smtp_username": "",
    "smtp_password_enc": "",         # Fernet, write-only in the form
    "smtp_from_email": "",
    "smtp_from_name": "Borant ID",
}

DEFAULTS = {
    **SMTP_DEFAULTS,
    "site_name": "Borant ID",
    "public_base_url": "https://id.borant.eu",

    # Registrazione aperta. Spenta di default: accenderla è una decisione, non
    # uno stato di fatto. Aprirla NON apre nessuna app — un account nuovo nasce
    # con zero grant e non raggiunge niente — ma riempie la tabella utenti di
    # chiunque passi, quindi va accesa sapendo perché (SPEC.md §18).
    #
    # Governa anche ORCID: con le registrazioni aperte, «entra con ORCID» crea
    # l'account se non esiste. Tenere le due porte con regole diverse
    # significherebbe spiegare a qualcuno perché una funziona e l'altra no.
    "registration_open": "0",

    # Domini ammessi alla registrazione, separati da virgola. Vuoto = tutti.
    # È un filtro grossolano, non un controllo d'identità: serve a tenere fuori
    # il rumore, non gli attaccanti.
    "registration_domains": "",
}


def get(db, key: str, default: str | None = None) -> str:
    row = db.get(Setting, key)
    if row is not None:
        return row.value
    return DEFAULTS.get(key, "" if default is None else default)


def get_bool(db, key: str) -> bool:
    return get(db, key).strip() in ("1", "true", "yes", "on")


def get_int(db, key: str, default: int = 0) -> int:
    try:
        return int(get(db, key))
    except (TypeError, ValueError):
        return default


def put(db, key: str, value: str) -> None:
    row = db.get(Setting, key)
    if row is None:
        db.add(Setting(key=key, value=value))
    else:
        row.value = value


def put_many(db, values: dict) -> None:
    for k, v in values.items():
        put(db, k, v)
    db.commit()


def smtp_config(db) -> dict:
    """Everything the mailer needs, password already decrypted."""
    return {
        "enabled": get_bool(db, "smtp_enabled"),
        "host": get(db, "smtp_host").strip(),
        "port": get_int(db, "smtp_port", 587),
        "security": get(db, "smtp_security").strip() or "starttls",
        "username": get(db, "smtp_username").strip(),
        "password": decrypt_or_none(get(db, "smtp_password_enc")) or "",
        "from_email": get(db, "smtp_from_email").strip(),
        "from_name": get(db, "smtp_from_name").strip() or "Borant ID",
    }


def set_smtp_password(db, plain: str) -> None:
    """Empty string means "leave it alone" — the form never round-trips the
    password back to the browser, so a blank field is not an instruction to
    clear it. Use clear_smtp_password() for that."""
    if not plain:
        return
    put(db, "smtp_password_enc", encrypt(plain))
    db.commit()


def clear_smtp_password(db) -> None:
    put(db, "smtp_password_enc", "")
    db.commit()


def base_url(db) -> str:
    return get(db, "public_base_url").rstrip("/")


def as_json(db) -> str:
    """For the audit log: config as stored, with the secret redacted."""
    rows = {r.key: r.value for r in db.query(Setting).all()}
    if rows.get("smtp_password_enc"):
        rows["smtp_password_enc"] = "<set>"
    return json.dumps(rows)
