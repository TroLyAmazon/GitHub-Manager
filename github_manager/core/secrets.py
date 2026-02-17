"""
Secure token storage via Windows Credential Manager using keyring.
Tokens are NEVER stored in JSON; only secretKey (reference) and metadata.
"""
import keyring
import secrets as std_secrets

SERVICE_NAME = "GitHubManager"


def _make_secret_key() -> str:
    return std_secrets.token_urlsafe(32)


def store_token(secret_key: str, token: str) -> None:
    """Store PAT in Credential Manager under secret_key."""
    keyring.set_password(SERVICE_NAME, secret_key, token)


def get_token(secret_key: str) -> str | None:
    """Retrieve PAT from Credential Manager. Returns None if not found."""
    return keyring.get_password(SERVICE_NAME, secret_key)


def delete_token(secret_key: str) -> None:
    """Remove token from Credential Manager."""
    try:
        keyring.delete_password(SERVICE_NAME, secret_key)
    except keyring.errors.PasswordDeleteError:
        pass


def create_and_store_token(token: str) -> str:
    """Store token and return new secret_key for accounts.json."""
    secret_key = _make_secret_key()
    store_token(secret_key, token)
    return secret_key
