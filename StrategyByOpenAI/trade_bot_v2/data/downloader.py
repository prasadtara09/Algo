import pandas as pd
import yfinance as yf

from core.logger import logger
from data.cache import load_cache, save_cache


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