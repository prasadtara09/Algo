import pandas as pd
import yfinance as yf

from broker.historical import FyersDataError, fetch_candles
from config import DATA_PROVIDER, FYERS_ACCESS_TOKEN, FYERS_CLIENT_ID
from core.logger import logger
from data.cache import load_cache, save_cache


def _fyers_resolution(interval):
    return "D" if interval.lower() in {"1d", "d"} else interval.replace("min", "").replace("m", "")


def _period_days(period):
    """Convert common period strings to an approximate FYERS date range."""
    unit = period[-1:].lower()
    try:
        value = int(period[:-1])
    except ValueError:
        return 60
    return value * {"d": 1, "mo": 30, "y": 365}.get(unit, 1)


def download(
    symbol: str,
    period: str = "60d",
    interval: str = "15m",
    use_cache: bool = True,
):

    # Load from cache if available
    if use_cache:
        cached = load_cache(symbol, interval)
        if cached is not None:
            logger.info(f"Loaded {symbol} from cache")
            return cached

    logger.info(f"Downloading {symbol}...")

    use_fyers = DATA_PROVIDER == "FYERS" or (DATA_PROVIDER == "AUTO" and FYERS_CLIENT_ID and FYERS_ACCESS_TOKEN)
    if use_fyers:
        try:
            df = fetch_candles(
                symbol,
                resolution=_fyers_resolution(interval),
                days=_period_days(period),
            )
            save_cache(df, symbol, interval)
            logger.info(f"Downloaded {len(df)} candles from FYERS")
            return df
        except FyersDataError as error:
            if DATA_PROVIDER == "FYERS":
                raise
            logger.warning(f"FYERS data unavailable for {symbol}; using Yahoo fallback: {error}")

    df = yf.download(
        symbol,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
    )

    if df.empty:
        raise ValueError(f"No data found for {symbol}")

    # Flatten MultiIndex columns (Yahoo Finance)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna()

    save_cache(df, symbol, interval)

    logger.info(f"Downloaded {len(df)} candles")

    return df
