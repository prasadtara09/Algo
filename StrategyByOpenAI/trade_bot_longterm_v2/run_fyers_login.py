"""Generate and safely store a FYERS API v3 access token.

Run this locally, complete the FYERS browser login, then paste the redirected
URL when asked. The token is stored in .env or its configured AWS secret, and
is never printed.
"""

from __future__ import annotations

import argparse
import os
import sys
import webbrowser
from pathlib import Path

from dotenv import load_dotenv

from broker.fyers_login import FyersLoginError, access_token_from_response, extract_auth_code


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


def _required_setting(credentials: dict[str, str], name: str) -> str:
    value = credentials[name]
    if value:
        return value
    raise FyersLoginError(f"{name} is missing. Add it to .env before running this command.")


def _session(client_id: str, secret_key: str, redirect_uri: str):
    try:
        from fyers_apiv3 import fyersModel
    except ImportError as error:
        raise FyersLoginError("Missing fyers-apiv3. Install requirements.txt in the active virtual environment.") from error

    return fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        response_type="code",
        grant_type="authorization_code",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and store a FYERS API v3 access token in .env.")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE, help="Credentials file to read and update.")
    parser.add_argument("--no-browser", action="store_true", help="Print the FYERS login URL without opening it.")
    args = parser.parse_args()

    env_file = args.env_file.expanduser().resolve()
    if not env_file.exists():
        print(f"Credentials file not found: {env_file}", file=sys.stderr)
        print("Create it with FYERS_SECRET_ID or the individual FYERS credentials first.", file=sys.stderr)
        return 2

    load_dotenv(env_file, override=True)
    os.environ["FYERS_ENV_FILE"] = str(env_file)
    try:
        # Import after loading --env-file so this existing config module reads
        # the selected .env before it resolves FYERS_SECRET_ID.
        from config import fyers_credentials, save_fyers_access_token

        credentials = fyers_credentials()
        client_id = _required_setting(credentials, "FYERS_CLIENT_ID")
        secret_key = _required_setting(credentials, "FYERS_SECRET_KEY")
        redirect_uri = _required_setting(credentials, "FYERS_REDIRECT_URI")
        session = _session(client_id, secret_key, redirect_uri)
        login_url = session.generate_authcode()

        print("Opening FYERS login in your browser. Log in and approve the app.")
        print("After FYERS redirects you, copy the complete URL from the browser address bar and paste it here.")
        if args.no_browser:
            print(f"\nFYERS login URL:\n{login_url}\n")
        else:
            webbrowser.open(login_url, new=1)

        redirect_value = input("Redirected URL (or authorization code): ").strip()
        auth_code = extract_auth_code(redirect_value)
        session.set_token(auth_code)
        token = access_token_from_response(session.generate_token())
        saved_to = save_fyers_access_token(token, env_file)
    except (RuntimeError, KeyboardInterrupt) as error:
        print(f"\nAccess token was not saved: {error}", file=sys.stderr)
        return 1
    except Exception as error:  # FYERS SDK/network errors should not expose secrets.
        print(f"\nFYERS token exchange failed: {error.__class__.__name__}: {error}", file=sys.stderr)
        return 1

    print(f"Access token saved to {saved_to}. It was not printed to the terminal.")
    print("You can now run: python3 run_fyers_stream.py --nifty200")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
