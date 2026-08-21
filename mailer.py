"""
Outbound mail through somebody else's SMTP relay. No mail server here.

The contract that matters is in SPEC.md §15: **mail is a degradable
dependency**. Nothing in this module raises. Every caller gets (ok, error) and
is expected to show the link on screen when ok is False, so that a dead relay
or an expired app password costs a copy-paste instead of a locked-out admin.

Configured from /admin/config, not from the environment: the mailbox is not
known at deploy time (SPEC.md §5).
"""
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

import settings

TIMEOUT = 15


def _build(cfg: dict, to: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = formataddr((cfg["from_name"], cfg["from_email"]))
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    return msg


def send(db, to: str, subject: str, body: str) -> tuple[bool, str]:
    """(ok, error). Never raises — see the module docstring."""
    cfg = settings.smtp_config(db)

    if not cfg["enabled"]:
        return False, "SMTP non attivo: configuralo in /admin/config"
    if not cfg["host"] or not cfg["from_email"]:
        return False, "SMTP incompleto: mancano host o indirizzo mittente"
    if not to:
        return False, "Nessun destinatario"

    msg = _build(cfg, to, subject, body)

    try:
        if cfg["security"] == "ssl":
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=TIMEOUT,
                                  context=ctx) as s:
                if cfg["username"]:
                    s.login(cfg["username"], cfg["password"])
                s.send_message(msg)
        else:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=TIMEOUT) as s:
                s.ehlo()
                if cfg["security"] == "starttls":
                    s.starttls(context=ssl.create_default_context())
                    s.ehlo()
                if cfg["username"]:
                    s.login(cfg["username"], cfg["password"])
                s.send_message(msg)
        return True, ""

    except smtplib.SMTPAuthenticationError as e:
        # The single most likely failure, and worth naming precisely: Gmail
        # wants an app password (with 2FA on the account), and many Microsoft
        # 365 tenants disable SMTP AUTH outright (SPEC.md §15).
        return False, (f"Autenticazione SMTP rifiutata ({e.smtp_code}). "
                       "Con Gmail serve una app password; su Microsoft 365 "
                       "il tenant potrebbe avere SMTP AUTH disabilitato.")
    except (smtplib.SMTPException, ssl.SSLError, OSError) as e:
        return False, f"{type(e).__name__}: {e}"


# ── Messages ──────────────────────────────────────────────────────────────────

def send_invite(db, to: str, name: str, link: str) -> tuple[bool, str]:
    site = settings.get(db, "site_name")
    body = (
        f"Ciao{(' ' + name) if name else ''},\n\n"
        f"ti è stato creato un accesso a {site}, il punto di ingresso unico "
        "per gli strumenti su borant.eu.\n\n"
        f"Per attivarlo, apri questo link:\n{link}\n\n"
        "Potrai impostare una password oppure collegare il tuo ORCID.\n"
        "Il link scade fra 14 giorni e si usa una volta sola.\n"
    )
    return send(db, to, f"Il tuo accesso a {site}", body)


def send_reset(db, to: str, link: str) -> tuple[bool, str]:
    site = settings.get(db, "site_name")
    body = (
        "Hai chiesto di reimpostare la password.\n\n"
        f"{link}\n\n"
        "Il link scade fra un'ora e si usa una volta sola. Tutte le sessioni "
        "aperte verranno chiuse.\n\n"
        "Se non sei stato tu, ignora questa mail: senza il link non succede "
        "niente.\n"
    )
    return send(db, to, f"Reimposta la password — {site}", body)


def send_security_notice(db, to: str, what: str, detail: str) -> tuple[bool, str]:
    """New device, TOTP disabled, ORCID linked. Cheap, and the only alarm that
    would otherwise not exist at all (SPEC.md §15)."""
    site = settings.get(db, "site_name")
    body = (
        f"Movimento sul tuo account {site}: {what}\n\n"
        f"{detail}\n\n"
        "Se sei stato tu non devi fare niente. Se non sei stato tu, cambia la "
        "password e chiudi le sessioni aperte da /profile.\n"
    )
    return send(db, to, f"[{site}] {what}", body)
