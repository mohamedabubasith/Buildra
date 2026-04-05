import base64
import os
from cryptography.fernet import Fernet
from ..config import settings


def _get_fernet() -> Fernet:
    key = settings.encryption_key
    if not key:
        # Dev fallback: generate a stable key from a fixed seed
        key = base64.urlsafe_b64encode(b"buildra-dev-key-" + b"0" * 16)
    # Fernet keys must be 32 url-safe base64-encoded bytes
    if isinstance(key, str):
        key = key.encode()
    try:
        return Fernet(key)
    except Exception:
        # If key is not valid Fernet format, derive one
        import hashlib
        derived = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
        return Fernet(derived)


def encrypt(plaintext: str) -> str:
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()
