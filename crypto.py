"""
Symmetric encryption for the two secrets that have to be stored recoverable:
enrolled TOTP secrets and the SMTP relay password.

Fernet with a server-side key from FERNET_KEY (generate once with
`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`).
Same pattern as survey/crypto.py, deliberately — this is not the place to
invent something.

Passwords are NOT handled here: those are bcrypt-hashed and never recovered.
"""
import os

from cryptography.fernet import Fernet, InvalidToken

_fernet = Fernet(os.environ["FERNET_KEY"].encode())


def encrypt(plain: str) -> str:
    return _fernet.encrypt(plain.encode()).decode()


def decrypt(encrypted: str) -> str:
    return _fernet.decrypt(encrypted.encode()).decode()


def decrypt_or_none(encrypted: str | None) -> str | None:
    """For call sites where a rotated or corrupt key must degrade instead of
    crashing the request — a TOTP that cannot be decrypted means "no TOTP",
    not "500"."""
    if not encrypted:
        return None
    try:
        return decrypt(encrypted)
    except (InvalidToken, ValueError):
        return None
