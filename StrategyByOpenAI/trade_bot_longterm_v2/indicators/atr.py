import pandas as pd


def atr(
    high,
    low,
    close,
    period=14
):

    prev_close = close.shift(1)

    tr = pd.concat(

        [

            high - low,

            (high - prev_close).abs(),

            (low - prev_close).abs()

        ],

        axis=1

    ).max(axis=1)

    atr = tr.ewm(

        alpha=1 / period,

        adjust=False

    ).mean()

    return atr