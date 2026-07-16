import pandas as pd
import numpy as np

def EMA(series, period):
    return series.ewm(span=period, adjust=False).mean()


def RSI(close, period=14):

    delta = close.diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()

    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def ATR(df, period=14):

    high = df["High"]

    low = df["Low"]

    close = df["Close"]

    tr1 = high - low

    tr2 = (high - close.shift()).abs()

    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    return tr.rolling(period).mean()


def VWAP(df):

    tp = (df["High"] + df["Low"] + df["Close"]) / 3

    return (tp * df["Volume"]).cumsum() / df["Volume"].cumsum()

def ADX(df, period=14):

    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

    dx = (
        abs(plus_di - minus_di)
        / (plus_di + minus_di)
    ) * 100

    return dx.rolling(period).mean()