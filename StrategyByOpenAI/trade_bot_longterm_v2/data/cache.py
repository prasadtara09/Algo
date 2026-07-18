from pathlib import Path
import pandas as pd

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


def cache_file(symbol: str, interval: str) -> Path:
    filename = f"{symbol.replace('.NS','')}_{interval}.parquet"
    return CACHE_DIR / filename


def save_cache(df: pd.DataFrame, symbol: str, interval: str):

    path = cache_file(symbol, interval)

    df.to_parquet(path)


def load_cache(symbol: str, interval: str):

    path = cache_file(symbol, interval)

    if path.exists():

        return pd.read_parquet(path)

    return None