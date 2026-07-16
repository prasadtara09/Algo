"""NIFTY universe management.

The official NIFTY 200 constituent list changes over time.  Run
``python update_universe.py`` before a full scan to refresh the local list.
Until then, the bundled liquid watchlist keeps development and offline tests
usable without pretending that it is the full index.
"""

from io import StringIO
from pathlib import Path

import pandas as pd
import requests


NIFTY200_CONSTITUENTS_URL = "https://www.niftyindices.com/IndexConstituent/ind_nifty200list.csv"
UNIVERSE_FILE = Path(__file__).with_name("nifty200_symbols.csv")

# Offline fallback only. It is intentionally named separately from NIFTY200.
DEFAULT_WATCHLIST = [
    "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "INFY.NS",
    "TCS.NS", "LT.NS", "AXISBANK.NS", "BHARTIARTL.NS", "ITC.NS",
    "KOTAKBANK.NS", "MARUTI.NS", "SUNPHARMA.NS", "HCLTECH.NS",
    "ULTRACEMCO.NS", "TITAN.NS", "NTPC.NS", "POWERGRID.NS",
    "ASIANPAINT.NS", "BAJFINANCE.NS",
]


def _to_yahoo_symbol(symbol):
    symbol = str(symbol).strip().upper()
    return symbol if symbol.endswith(".NS") else f"{symbol}.NS"


def load_nifty200_symbols(path=UNIVERSE_FILE):
    """Load the last refreshed official NIFTY 200 list, if present."""
    path = Path(path)
    if not path.exists():
        return []

    frame = pd.read_csv(path)
    if "Symbol" not in frame.columns:
        raise ValueError(f"{path} must contain a Symbol column")
    return [_to_yahoo_symbol(symbol) for symbol in frame["Symbol"].dropna().unique()]


def refresh_nifty200_symbols(path=UNIVERSE_FILE, timeout=30, session=requests):
    """Download and validate the official NIFTY 200 constituent CSV."""
    response = session.get(
        NIFTY200_CONSTITUENTS_URL,
        timeout=timeout,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-200",
        },
    )
    response.raise_for_status()
    frame = pd.read_csv(StringIO(response.text))
    symbol_column = next((column for column in frame.columns if column.strip().lower() == "symbol"), None)
    if symbol_column is None:
        raise ValueError("Official constituent file did not include a Symbol column")

    symbols = sorted({str(symbol).strip().upper() for symbol in frame[symbol_column].dropna() if str(symbol).strip()})
    if len(symbols) < 180 or len(symbols) > 220:
        raise ValueError(f"Expected approximately 200 constituents, received {len(symbols)}")

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"Symbol": symbols}).to_csv(destination, index=False)
    return [_to_yahoo_symbol(symbol) for symbol in symbols]


NIFTY200 = load_nifty200_symbols()
UNIVERSE = NIFTY200 if NIFTY200 else DEFAULT_WATCHLIST
