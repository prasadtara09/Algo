import pandas as pd
import numpy as np


def adx(
    high,
    low,
    close,
    period=14
):

    up_move = high.diff()

    down_move = -low.diff()

    plus_dm = np.where(
        (up_move > down_move) & (up_move > 0),
        up_move,
        0
    )

    minus_dm = np.where(
        (down_move > up_move) & (down_move > 0),
        down_move,
        0
    )

    tr = pd.concat(

        [

            high - low,

            (high - close.shift()).abs(),

            (low - close.shift()).abs()

        ],

        axis=1

    ).max(axis=1)

    atr = tr.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    plus_di = 100 * (
        pd.Series(plus_dm, index=high.index)
        .ewm(alpha=1 / period, adjust=False)
        .mean()
        / atr
    )

    minus_di = 100 * (
        pd.Series(minus_dm, index=high.index)
        .ewm(alpha=1 / period, adjust=False)
        .mean()
        / atr
    )

    dx = (
        (plus_di - minus_di).abs()
        /
        (plus_di + minus_di)
    ) * 100

    return dx.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()