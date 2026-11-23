from cryptography.fernet import Fernet, InvalidToken

from ..config import settings
from .provider_errors import IntegrationFailed, IntegrationUnavailable


def encrypt_password(password: str) -> str:
    if not settings.credential_encryption_key:
        if settings.demo_mode:
            return "demo"
        raise IntegrationUnavailable("WordPress credential storage")
    fernet = Fernet(settings.credential_encryption_key.encode())
    return "fernet:" + fernet.encrypt(password.encode()).decode()


def decrypt_password(stored: str) -> str:
    if not settings.credential_encryption_key or not stored.startswith("fernet:"):
        raise IntegrationFailed("WordPress credentials. Reconnect the site")
    try:
        return (
            Fernet(settings.credential_encryption_key.encode())
            .decrypt(stored[7:].encode())
            .decode()
        )
    except InvalidToken as exc:
        raise IntegrationFailed("WordPress credentials") from exc
