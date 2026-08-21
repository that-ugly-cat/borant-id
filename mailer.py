"""
Outbound mail through somebody else's SMTP relay. No mail server here.

The contract that matters is in SPEC.md §15: **mail is a degradable
dependency**. Nothing in this module raises. Every caller gets (ok, error) and
is expected to show the link on screen when ok is False, so that a dead relay
or an expired app password costs a copy-paste instead of a locked-out admin.

Configured from /admin/config, not from the environment: the mailbox is not
known at deploy time (SPEC.md §5).

**Every message here is in English, and every message lives here.** The
interface speaks four languages; the mail speaks one. The reason is that at the
moment we write to somebody we usually do not know their language: an invitation
goes out before that person has ever touched the interface, and it is the first
thing they see of the system. English is the language this perimeter shares.

Keeping the copy in one file is what makes "all mail is in English" a claim you
can check by reading a single module instead of grepping three.
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
        # The single most likely failure, and worth naming precisely: Infomaniak
        # wants the mailbox password (2FA does not apply to SMTP), Gmail wants an
        # app password, and many Microsoft 365 tenants disable SMTP AUTH
        # outright (SPEC.md §15). The error text stays in Italian: it is read by
        # the administrator in the admin panel, not by a recipient.
        return False, (f"Autenticazione SMTP rifiutata ({e.smtp_code}). "
                       "Su Infomaniak serve la password della casella; con "
                       "Gmail una app password; su Microsoft 365 il tenant "
                       "potrebbe avere SMTP AUTH disabilitato.")
    except (smtplib.SMTPException, ssl.SSLError, OSError) as e:
        return False, f"{type(e).__name__}: {e}"


# ── Messages ──────────────────────────────────────────────────────────────────
#
# All of them in English. See the module docstring for why.

def send_invite(db, to: str, name: str, link: str) -> tuple[bool, str]:
    site = settings.get(db, "site_name")
    body = (
        f"Hello{(' ' + name) if name else ''},\n\n"
        f"An account has been created for you on {site}, the single sign-on "
        "for the research tools at borant.eu.\n\n"
        f"To activate it, open this link:\n{link}\n\n"
        "You will be able to set a password or link your ORCID.\n"
        "The link expires in 14 days and can be used once.\n"
    )
    return send(db, to, f"Your {site} account", body)


def send_confirm(db, to: str, link: str) -> tuple[bool, str]:
    site = settings.get(db, "site_name")
    body = (
        "Please confirm your email address by opening this link:\n\n"
        f"{link}\n\n"
        "You need a confirmed address before you can request access to any "
        "tool. The link expires in 7 days.\n"
    )
    return send(db, to, f"Confirm your address — {site}", body)


def send_reset(db, to: str, link: str) -> tuple[bool, str]:
    site = settings.get(db, "site_name")
    body = (
        "You asked to reset your password.\n\n"
        f"{link}\n\n"
        "The link expires in one hour and can be used once. All open sessions "
        "will be closed.\n\n"
        "If this was not you, ignore this message: nothing happens without the "
        "link.\n"
    )
    return send(db, to, f"Reset your password — {site}", body)


def send_security_notice(db, to: str, what: str, detail: str) -> tuple[bool, str]:
    """New device, TOTP disabled, ORCID linked. Cheap, and the only alarm that
    would otherwise not exist at all (SPEC.md §15)."""
    site = settings.get(db, "site_name")
    body = (
        f"Something changed on your {site} account: {what}\n\n"
        f"{detail}\n\n"
        "If this was you, there is nothing to do. If it was not, change your "
        "password and close the open sessions from /profile.\n"
    )
    return send(db, to, f"[{site}] {what}", body)


def send_access_granted(db, to: str, app_name: str, host: str) -> tuple[bool, str]:
    site = settings.get(db, "site_name")
    body = (
        f"Your request for access to {app_name} has been approved.\n\n"
        f"https://{host}/\n\n"
        f"Sign in through {site} as usual.\n"
    )
    return send(db, to, f"Access granted: {app_name}", body)


def send_access_denied(db, to: str, app_name: str) -> tuple[bool, str]:
    body = (
        f"Your request for access to {app_name} was not approved.\n\n"
        "If you think this is a mistake, reply to the administrator who "
        "handles that tool.\n"
    )
    return send(db, to, f"Access not granted: {app_name}", body)


def send_access_request(db, to: str, who: str, who_email: str, app_name: str,
                        host: str, message: str, base_url: str
                        ) -> tuple[bool, str]:
    """To an administrator, not to a user — but still English, because the rule
    is one language for outbound mail, not one language per audience."""
    body = (
        f"{who} <{who_email}> is requesting access to {app_name} ({host}).\n\n"
        f"{message or '(no message)'}\n\n"
        f"Decide at {base_url}/admin/users\n"
    )
    return send(db, to, f"Access request: {app_name}", body)


def send_test(db, to: str) -> tuple[bool, str]:
    site = settings.get(db, "site_name")
    return send(db, to, f"Test message — {site}",
                "If you are reading this, the SMTP relay works.\n")
