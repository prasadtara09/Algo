"""Common daily features for fair long-only swing-strategy comparisons."""

from indicators.adx import adx
from indicators.atr import atr
from indicators.ema import ema
from indicators.rsi import rsi


def daily_indicators(df):
    data = df.copy()
    data["EMA20"] = ema(data["Close"], 20)
    data["EMA50"] = ema(data["Close"], 50)
    data["EMA200"] = ema(data["Close"], 200)
    data["SMA20"] = data["Close"].rolling(20).mean()
    data["SMA50"] = data["Close"].rolling(50).mean()
    data["SMA200"] = data["Close"].rolling(200).mean()
    data["ATR"] = atr(data["High"], data["Low"], data["Close"], 14)
    data["RSI"] = rsi(data["Close"], 14)
    data["RSI2"] = rsi(data["Close"], 2)
    data["ADX"] = adx(data["High"], data["Low"], data["Close"], 14)
    data["VOL_MA"] = data["Volume"].rolling(20).mean()
    data["RS20"] = data["Close"].pct_change(20)
    data["RS40"] = data["Close"].pct_change(40)
    data["RS60"] = data["Close"].pct_change(60)
    data["RS80"] = data["Close"].pct_change(80)
    # Longer momentum is used by the portfolio rotation research.  It is
    # deliberately calculated from closing prices only, so a ranking decided
    # at the end of a session can be traded no earlier than the next session.
    data["RS120"] = data["Close"].pct_change(120)
    data["BB_MID"] = data["Close"].rolling(20).mean()
    bb_std = data["Close"].rolling(20).std()
    data["BB_UPPER"] = data["BB_MID"] + 2 * bb_std
    data["BB_LOWER"] = data["BB_MID"] - 2 * bb_std
    data["HH20"] = data["High"].rolling(20).max().shift(1)
    data["HH55"] = data["High"].rolling(55).max().shift(1)
    required = [
        "EMA20", "EMA50", "ATR", "RSI", "RSI2", "ADX", "VOL_MA",
        "RS20", "RS40", "RS60", "RS80", "RS120", "BB_MID", "BB_UPPER", "BB_LOWER", "HH20", "HH55",
    ]
    return data.dropna(subset=required)
