import base64
import hashlib
import secrets

from cryptography.fernet import Fernet
from django.conf import settings

SHIELD_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _as_fernet_key(raw_key: str | bytes) -> bytes:
    key_bytes = raw_key.encode("utf-8") if isinstance(raw_key, str) else raw_key
    try:
        Fernet(key_bytes)
        return key_bytes
    except Exception:
        digest = hashlib.sha256(key_bytes).digest()
        return base64.urlsafe_b64encode(digest)


def get_fernet() -> Fernet:
    return Fernet(_as_fernet_key(settings.ENCRYPTION_KEY))


def encrypt_value(value: str) -> str:
    return get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(token: str) -> str:
    return get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")


def _shield_block() -> str:
    return "".join(secrets.choice(SHIELD_ALPHABET) for _ in range(4))


def generate_shield_id() -> str:
    return f"SH-{_shield_block()}-{_shield_block()}"


def generate_certificate_id() -> str:
    suffix = "".join(secrets.choice(SHIELD_ALPHABET) for _ in range(8))
    return f"CERT-{suffix}"


def generate_passkey_challenge() -> str:
    return secrets.token_urlsafe(32)


def age_to_range(age: int) -> str:
    if age < 13:
        return "under-13"
    if age <= 17:
        return "13-17"
    return "18+"
