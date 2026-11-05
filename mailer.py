"""
Outbound mail through somebody else's SMTP relay. No mail server here.

The contract that matters is in SPEC.md §15: **mail is a degradable
dependency**. Nothing in this module raises. Every caller gets (ok, error) and
is expected to show the link on screen when ok is False, so that a dead relay
or an expired app password costs a copy-paste instead of a locked-out admin.

Configured from /admin/config, not from the environment: the mailbox is not
known at deploy time (SPEC.md §5).

**Every message here is in English, and every *default* message lives here.**
The interface speaks four languages; the mail speaks one. The reason is that at
the moment we write to somebody we usually do not know their language: an
invitation goes out before that person has ever touched the interface, and it is
the first thing they see of the system. English is the language this perimeter
shares.

Keeping the copy in one file is what makes "all mail is in English" a claim you
can check by reading a single module instead of grepping three.

The word *default* earns its place, and it was not there before the batch form
grew a custom invitation text. **One message can be rewritten from outside this
module** — the invitation, from the batch form in `/admin/users` — and what an
administrator types is in whatever language that cohort reads. The claim that
survives is narrower and still checkable by reading one file: every message the
system composes *by itself* is here, in English, and the single exception is a
text a human wrote on purpose for one batch. `INVITE_BODY` below is what keeps
that exception from turning into a second copy of the invitation.
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
    """(ok, error). Never raises — see the module docstring.

    `error` is a **code** for the failures this module can name — `smtp_off`,
    `smtp_incomplete`, `no_recipient`, `auth_refused <smtp code>` — and raw
    library text for the ones it cannot. `locales.mail_error` turns the first
    kind into a sentence in the reader's language and leaves the second alone,
    because `ConnectError: [Errno 111]` is nobody's language and translating it
    would only make it harder to search for.
    """
    cfg = settings.smtp_config(db)

    if not cfg["enabled"]:
        return False, "smtp_off"
    if not cfg["host"] or not cfg["from_email"]:
        return False, "smtp_incomplete"
    if not to:
        return False, "no_recipient"

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
        # The single most likely failure, and worth naming precisely:
        # Infomaniak wants the mailbox password (2FA does not apply to SMTP),
        # Gmail wants an app password, and many Microsoft 365 tenants disable
        # SMTP AUTH outright (SPEC.md §15). The sentence lives in the locales
        # now — the admin panel speaks four languages — and the numeric code
        # rides along as the detail, since a number is the same everywhere.
        return False, f"auth_refused {e.smtp_code}"
    except (smtplib.SMTPException, ssl.SSLError, OSError) as e:
        return False, f"{type(e).__name__}: {e}"


# ── Messages ──────────────────────────────────────────────────────────────────
#
# All of them in English. See the module docstring for why.

# The invitation is the one message an administrator can rewrite, from the
# batch form. Three decisions keep that from eroding the claim in the module
# docstring:
#
#   - **The default is a template carrying the same placeholders a custom text
#     gets** — `{nome}`, `{email}`, `{link}`, `{site}`, the vocabulary the
#     broadcast message in /admin/config already uses. The box in the panel is
#     pre-filled with *this very string*, so "custom" starts as a copy of what
#     we would have sent anyway, and both texts then travel the same
#     substitution. Were the default an f-string and the pre-fill a second
#     literal in a template, the two would say different things within a year.
#
#   - **Substitution is `str.replace`, never `str.format`.** A stray brace in
#     something a human typed — `{{nome}`, a smiley, a Jinja leftover — makes
#     `format()` raise, and this module promises never to raise.
#
#   - **An unknown placeholder stays visible.** `{nmoe}` arrives in the mail as
#     `{nmoe}`, which is ugly and gets noticed and fixed. Silently blanking it
#     would send thirty people a greeting with a hole in it.
#
# One consequence worth naming: the greeting is now `Hello {nome},` with
# `{nome}` falling back to the local part of the address, so an invitation for
# an address with no name says "Hello luca," where it used to say "Hello,".
# That is the price of having one text instead of two, and it reads better.
INVITE_BODY = (
    "Hello {nome},\n\n"
    "An account has been created for you on {site}, the single sign-on "
    "for the research tools at borant.eu.\n\n"
    "To activate it, open this link:\n{link}\n\n"
    "You will be able to set a password or link your ORCID.\n"
    "The link expires in 14 days and can be used once.\n"
)


def render_invite(body: str, *, name: str, email: str, link: str,
                  site: str) -> str:
    """The invitation template with one person's details in it."""
    who = (name or "").strip() or ((email or "").split("@")[0])
    return (body.replace("{nome}", who)
                .replace("{email}", email or "")
                .replace("{link}", link or "")
                .replace("{site}", site or ""))


def send_invite(db, to: str, name: str, link: str,
                body: str | None = None) -> tuple[bool, str]:
    """`body` overrides `INVITE_BODY`; the subject stays ours either way.

    The caller is responsible for having checked that a custom body contains
    `{link}` — an invitation without one is a dead end that looks like it was
    delivered. This function does not second-guess it, because by the time we
    are here the batch is already running and refusing the thirtieth message
    after sending twenty-nine is worse than either outcome.
    """
    site = settings.get(db, "site_name")
    text = render_invite(body or INVITE_BODY, name=name, email=to, link=link,
                         site=site)
    return send(db, to, f"Your {site} account", text)


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
