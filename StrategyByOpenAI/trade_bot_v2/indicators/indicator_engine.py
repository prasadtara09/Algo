from indicators.ema import ema
from indicators.rsi import rsi
from indicators.atr import atr
from indicators.adx import adx
from indicators.vwap import vwap
from indicators.supertrend import supertrend

from config import (
    EMA_FAST,
    EMA_SLOW,
    RSI_PERIOD,
    ATR_PERIOD,
    ADX_PERIOD,
)


def apply_indicators(df):

    df = df.copy()

    df["EMA20"] = ema(df["Close"], EMA_FAST)

    df["EMA50"] = ema(df["Close"], EMA_SLOW)

    df["RSI"] = rsi(df["Close"], RSI_PERIOD)

    df["ATR"] = atr(
        df["High"],
        df["Low"],
        df["Close"],
        ATR_PERIOD,
    )

    df["ADX"] = adx(
        df["High"],
        df["Low"],
        df["Close"],
        ADX_PERIOD,
    )

    df["VWAP"] = vwap(df)

    df["SUPERTREND"] = supertrend(df)

    df["VOL_MA"] = df["Volume"].rolling(20).mean()

    df["HH5"] = (
        df["High"]
        .rolling(5)
        .max()
        .shift(1)
    )

    df["LL5"] = (
        df["Low"]
        .rolling(5)
        .min()
        .shift(1)
    )

    return df.dropna()