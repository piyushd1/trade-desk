"""
Crypto Utilities
Provides encryption and decryption helpers using Fernet
"""

from typing import Union
from cryptography.fernet import Fernet, InvalidToken
from app.config import settings


def _get_cipher() -> Fernet:
    """Create Fernet cipher using the configured encryption key"""
    key = settings.ENCRYPTION_KEY
    if not key:
        raise ValueError("ENCRYPTION_KEY is not configured in environment")
    return Fernet(key)


def encrypt(plain_text: Union[str, bytes]) -> str:
    """
    Encrypt a string using Fernet
    """
    cipher = _get_cipher()
    if isinstance(plain_text, str):
        plain_text = plain_text.encode("utf-8")
    token = cipher.encrypt(plain_text)
    return token.decode("utf-8")


def decrypt(token: Union[str, bytes]) -> str:
    """
    Decrypt a string using Fernet
    """
    cipher = _get_cipher()
    if isinstance(token, str):
        token = token.encode("utf-8")
    try:
        plain = cipher.decrypt(token)
        return plain.decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Invalid encryption token") from exc
