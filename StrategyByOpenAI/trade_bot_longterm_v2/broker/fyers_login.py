"""Helpers for the FYERS browser-login and access-token exchange flow.

The functions in this module intentionally never log the access token or app
secret.  They are kept separate from the command-line runner so the parsing
and response checks can be tested without contacting FYERS.
"""

from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import parse_qs, urlparse


class FyersLoginError(RuntimeError):
    """Raised when FYERS login cannot safely produce an access token."""


def extract_auth_code(redirect_url_or_code: str) -> str:
    """Extract FYERS's one-time authorization code from a redirect URL.

    FYERS normally names the query parameter ``auth_code``.  ``code`` is also
    accepted to make the helper resilient to SDK/API naming changes.  A raw
    code is accepted as a convenience for users who copy only that value.
    """
    value = (redirect_url_or_code or "").strip()
    if not value:
        raise FyersLoginError("No redirect URL or authorization code was provided.")

    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        query = parse_qs(parsed.query)
        for field in ("auth_code", "code"):
            code = (query.get(field) or [""])[0].strip()
            if code:
                return code
        raise FyersLoginError(
            "The redirected URL does not contain auth_code. Complete FYERS login, then copy the full URL from the browser address bar."
        )

    # A raw value must not look like a URL or contain whitespace.  This keeps
    # a copied error page from being sent to FYERS as if it were a code.
    if "://" not in value and not any(character.isspace() for character in value):
        return value
    raise FyersLoginError("Enter the full redirected URL, or only the one-time authorization code.")


def access_token_from_response(response: Mapping[str, Any]) -> str:
    """Return a token only from a successful-looking FYERS token response."""
    token = response.get("access_token")
    if isinstance(token, str) and token.strip():
        return token.strip()

    message = response.get("message") or response.get("error") or response.get("s") or "unknown error"
    raise FyersLoginError(f"FYERS did not return an access token ({message}).")
