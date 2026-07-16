import pandas as pd
from indicators import EMA, RSI, ATR, VWAP, ADX

# -----------------------------
# Prepare Indicators
# -----------------------------

def prepare_dataframe(df):

    df = df.copy()

    df["EMA20"] = EMA(df["Close"], 20)
    df["EMA50"] = EMA(df["Close"], 50)

    df["RSI"] = RSI(df["Close"], 14)

    df["ATR"] = ATR(df, 14)

    df["ADX"] = ADX(df, 14)

    df["VWAP"] = VWAP(df)

    df["VOL_MA"] = df["Volume"].rolling(20).mean()

    df.dropna(inplace=True)

    return df


# -----------------------------
# Buy Signal
# -----------------------------

def buy_signal(df, i):

    row = df.iloc[i]

    # Trend
    ema = row["EMA20"] > row["EMA50"]

    # Price above EMA
    price = row["Close"] > row["EMA20"]

    # Above VWAP
    vwap = row["Close"] > row["VWAP"]

    # RSI
    rsi = row["RSI"] > 50

    # ADX
    adx = row["ADX"] > 20

    # Volume
    volume = row["Volume"] > row["VOL_MA"]

    return (
        ema
        and price
        and vwap
        and rsi
        and adx
        and volume
    )

def debug_strategy(df):

    stats = {
        "EMA": 0,
        "PRICE": 0,
        "VWAP": 0,
        "RSI": 0,
        "ADX": 0,
        "VOL": 0,
        "ALL": 0
    }

    for i in range(50, len(df)):

        row = df.iloc[i]

        ema = row["EMA20"] > row["EMA50"]
        price = row["Close"] > row["EMA20"]
        vwap = row["Close"] > row["VWAP"]
        rsi = row["RSI"] > 50
        adx = row["ADX"] > 20
        vol = row["Volume"] > row["VOL_MA"]

        if ema:
            stats["EMA"] += 1

        if price:
            stats["PRICE"] += 1

        if vwap:
            stats["VWAP"] += 1

        if rsi:
            stats["RSI"] += 1

        if adx:
            stats["ADX"] += 1

        if vol:
            stats["VOL"] += 1

        if ema and price and vwap and rsi and adx and vol:
            stats["ALL"] += 1

    print(stats)