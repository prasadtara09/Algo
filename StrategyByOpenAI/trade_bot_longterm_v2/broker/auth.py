"""Credential helpers shared by the FYERS REST and WebSocket adapters."""

from config import FYERS_ACCESS_TOKEN, FYERS_CLIENT_ID


class FyersCredentialsError(RuntimeError):
    """Raised when the FYERS credentials required for a broker call are absent."""


def access_token() -> str:
    """Return the raw FYERS JWT required by the API v3 sockets.

    Older FYERS examples sometimes store a token as ``client_id:jwt``.  The
    API v3 DataSocket expects the JWT itself, so accept either representation
    without ever logging the token.
    """
    token = (FYERS_ACCESS_TOKEN or "").strip()
    if ":" in token:
        _, candidate = token.split(":", 1)
        if candidate.count(".") == 2:
            token = candidate
    if not token or token.count(".") != 2:
        raise FyersCredentialsError(
            "FYERS_ACCESS_TOKEN is missing or malformed. Set a current FYERS API v3 access token in .env."
        )
    return token


def client_id() -> str:
    """Return the FYERS app client ID required by REST API calls."""
    value = (FYERS_CLIENT_ID or "").strip()
    if not value:
        raise FyersCredentialsError("FYERS_CLIENT_ID is missing. Set it in .env before using the FYERS REST API.")
    return value
