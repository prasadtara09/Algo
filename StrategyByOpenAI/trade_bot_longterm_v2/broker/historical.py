"""Read-only FYERS historical-candle client.

This module never creates, modifies, or places an order. It only converts the
History API response into a DataFrame that the scanner/backtester can cache.
"""

from datetime import date, timedelta

import pandas as pd

from config import FYERS_ACCESS_TOKEN, FYERS_CLIENT_ID


class FyersDataError(RuntimeError):
    pass


def fyers_equity_symbol(symbol):
    """Convert RELIANCE.NS (or RELIANCE) to the FYERS NSE equity format."""
    ticker = symbol.upper().replace(".NS", "")
    return f"NSE:{ticker}-EQ"


def fetch_candles(symbol, resolution="15", days=60, client_id=None, access_token=None):
    """Fetch completed OHLCV candles through FYERS API v3 History API."""
    client_id = client_id or FYERS_CLIENT_ID
    access_token = access_token or FYERS_ACCESS_TOKEN
    if not client_id or not access_token:
        raise FyersDataError("FYERS_CLIENT_ID and FYERS_ACCESS_TOKEN are required for FYERS data")

    try:
        from fyers_apiv3 import fyersModel
    except ImportError as error:
        raise FyersDataError("Install fyers-apiv3 to use the FYERS data provider") from error

    end = date.today()
    request = {
        "symbol": fyers_equity_symbol(symbol),
        "resolution": str(resolution),
        "date_format": "1",
        "range_from": (end - timedelta(days=days)).isoformat(),
        "range_to": end.isoformat(),
        "cont_flag": "1",
    }
    client = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="")
    response = client.history(data=request)
    if response.get("s") != "ok" or not response.get("candles"):
        raise FyersDataError(response.get("message", "FYERS did not return historical candles"))

    frame = pd.DataFrame(response["candles"], columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"])
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], unit="s", utc=True).dt.tz_convert("Asia/Kolkata")
    frame = frame.set_index("Timestamp")
    return frame.apply(pd.to_numeric, errors="coerce").dropna()
