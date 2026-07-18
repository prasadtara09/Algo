import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Exponential Moving Average

    Parameters
    ----------
    series : pd.Series
    period : int

    Returns
    -------
    pd.Series
    """

    return series.ewm(
        span=period,
        adjust=False
    ).mean()