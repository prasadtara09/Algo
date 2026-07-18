"""Rate-conscious Yahoo chart downloader for reproducible long-horizon research.

The normal downloader remains the application's short-horizon data source.
This module writes a separate cache so a long validation run cannot overwrite
the scanner's current daily candles.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import sleep

import pandas as pd
import requests


LONG_HISTORY_CACHE = Path("cache/history_6y")
LONG_HISTORY_CACHE.mkdir(parents=True, exist_ok=True)


class YahooHistoryError(RuntimeError):
    pass


class YahooHistoryClient:
    def __init__(self, pause_seconds=0.35):
        self.pause_seconds = pause_seconds
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
        })
        # Yahoo returns an A3 cookie from this endpoint.  The chart endpoint
        # accepts that normal session cookie without a user credential.
        self.session.get("https://fc.yahoo.com/", timeout=20)
        self.session.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=20)

    def fetch_daily(self, symbol, days=2192):
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            "period1": int(start.timestamp()),
            "period2": int(end.timestamp()),
            "interval": "1d",
            "events": "history",
            "includeAdjustedClose": "true",
        }
        last_error = None
        for attempt in range(4):
            try:
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code == 429:
                    last_error = YahooHistoryError("Yahoo rate-limited the request")
                    sleep(2 * (attempt + 1))
                    continue
                response.raise_for_status()
                payload = response.json()
                result = payload.get("chart", {}).get("result", [None])[0]
                if result is None:
                    message = payload.get("chart", {}).get("error", {}) or "No result returned"
                    raise YahooHistoryError(str(message))
                frame = self._to_frame(result)
                if frame.empty:
                    raise YahooHistoryError("Yahoo returned no completed daily candles")
                sleep(self.pause_seconds)
                return frame
            except (requests.RequestException, ValueError, YahooHistoryError) as error:
                last_error = error
                sleep(2 * (attempt + 1))
        raise YahooHistoryError(f"{symbol}: {last_error}")

    @staticmethod
    def _to_frame(result):
        timestamps = result.get("timestamp") or []
        quote = (result.get("indicators", {}).get("quote") or [{}])[0]
        adjusted = (result.get("indicators", {}).get("adjclose") or [{}])[0].get("adjclose")
        if not timestamps or not quote:
            return pd.DataFrame()
        frame = pd.DataFrame({
            "Open": quote.get("open"),
            "High": quote.get("high"),
            "Low": quote.get("low"),
            "Close": quote.get("close"),
            "Volume": quote.get("volume"),
        })
        frame.index = (
            pd.to_datetime(timestamps, unit="s", utc=True)
            .tz_convert("Asia/Kolkata")
            .normalize()
            .tz_localize(None)
        )
        adjusted_close = pd.Series(adjusted, index=frame.index) if adjusted else None
        frame = frame.apply(pd.to_numeric, errors="coerce").dropna()
        if adjusted_close is not None:
            adjusted_close = adjusted_close.reindex(frame.index)
            factor = (adjusted_close / frame["Close"]).replace([float("inf"), -float("inf")], pd.NA).fillna(1.0)
            for column in ("Open", "High", "Low", "Close"):
                frame[column] = frame[column] * factor
        return frame[~frame.index.duplicated(keep="last")].sort_index()


def _cache_path(symbol):
    return LONG_HISTORY_CACHE / f"{symbol.replace('.NS', '')}_1d_6y.parquet"


def load_or_fetch_daily(client, symbol, refresh=False):
    path = _cache_path(symbol)
    if path.exists() and not refresh:
        return pd.read_parquet(path)
    frame = client.fetch_daily(symbol)
    frame.to_parquet(path)
    return frame
