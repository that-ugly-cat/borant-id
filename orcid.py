"""
ORCID as a way in — the authorization code flow, by hand.

Why by hand: the whole point of not writing an OIDC *provider* (SPEC.md §2)
also argues against pulling a full OIDC *client* stack in for one upstream.
ORCID's token endpoint returns the ORCID iD and the name as plain fields
alongside the id_token, over TLS, straight to us — so there is no JWT to
validate and no JWKS to cache. Sixty lines and one dependency we already have.

Three rules from SPEC.md §9, all defensive, all enforced by the caller in
main.py rather than here:

  1. The identifier is the ORCID iD, never the email. ORCID only releases an
     email if the person made it public, and most do not.
  2. Linking happens only from an already-authenticated session. Never
     auto-link on matching email: that hands the account to whoever registers
     an ORCID with somebody else's address.
  3. /login/orcid does not create users. No account with that iD means "ask
     for an invite", not "welcome".

State travels in a short-lived Fernet-encrypted cookie: integrity for free,
no server-side store, and it expires by itself.
"""
import json
import os
import secrets
import time

import httpx

from crypto import decrypt_or_none, encrypt

CLIENT_ID = os.environ.get("ORCID_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ORCID_CLIENT_SECRET", "")
SANDBOX = os.environ.get("ORCID_SANDBOX", "0") in ("1", "true", "yes")

_BASE = "https://sandbox.orcid.org" if SANDBOX else "https://orcid.org"
AUTHORIZE_URL = f"{_BASE}/oauth/authorize"
TOKEN_URL = f"{_BASE}/oauth/token"

STATE_COOKIE = "borant_orcid_state"
STATE_TTL = 600  # seconds


def configured() -> bool:
    return bool(CLIENT_ID and CLIENT_SECRET)


def profile_url(orcid_id: str) -> str:
    return f"{_BASE}/{orcid_id}"


# ── State ─────────────────────────────────────────────────────────────────────

def make_state(mode: str, rd: str = "") -> tuple[str, str]:
    """(state to send to ORCID, cookie value to set). `mode` is 'login' or
    'link' — a link callback must never be able to masquerade as a login."""
    state = secrets.token_urlsafe(24)
    blob = encrypt(json.dumps({
        "s": state, "mode": mode, "rd": rd, "exp": int(time.time()) + STATE_TTL,
    }))
    return state, blob


def read_state(cookie_value: str | None, state_param: str) -> dict | None:
    """The decoded state, or None if it is missing, stale, or does not match
    what came back from ORCID."""
    raw = decrypt_or_none(cookie_value)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    if data.get("exp", 0) < time.time():
        return None
    if not state_param or not secrets.compare_digest(data.get("s", ""),
                                                     state_param):
        return None
    return data


# ── Flow ──────────────────────────────────────────────────────────────────────

def authorize_url(state: str, redirect_uri: str) -> str:
    from urllib.parse import urlencode
    return AUTHORIZE_URL + "?" + urlencode({
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid",
        "redirect_uri": redirect_uri,
        "state": state,
    })


def exchange(code: str, redirect_uri: str) -> tuple[dict | None, str]:
    """({orcid, name, ...}, error). Never raises."""
    if not configured():
        return None, "ORCID non configurato (ORCID_CLIENT_ID / ORCID_CLIENT_SECRET)"
    try:
        r = httpx.post(
            TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
            timeout=15,
        )
    except httpx.HTTPError as e:
        return None, f"ORCID irraggiungibile: {type(e).__name__}"

    if r.status_code != 200:
        return None, f"ORCID ha rifiutato lo scambio ({r.status_code})"

    try:
        data = r.json()
    except ValueError:
        return None, "Risposta ORCID illeggibile"

    orcid_id = (data.get("orcid") or "").strip()
    if not orcid_id:
        return None, "ORCID non ha restituito un iD"

    return {"orcid": orcid_id, "name": (data.get("name") or "").strip()}, ""
