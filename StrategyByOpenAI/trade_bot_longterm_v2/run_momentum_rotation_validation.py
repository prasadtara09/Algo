"""Rolling validation for the predeclared momentum-rotation variants.

It uses consecutive, non-overlapping calendar windows after enough NIFTY 200
members have a completed SMA200.  Each window starts with a fresh portfolio,
so its result does not inherit a previous window's gains or losses.
"""

from pathlib import Path

import pandas as pd

from data.downloader import download
from data.universe import NIFTY200
from run_momentum_rotation_research import VARIANTS, _metrics, _period_frames
from strategy.swing_features import daily_indicators


def _active_dates(frames):
    dates = sorted({timestamp for frame in frames.values() for timestamp in frame.index})
    # Avoid treating the indicator warm-up as a market regime.  A large
    # majority of the NIFTY 200 must have a real 200-day average before the
    # first validation window starts.
    for timestamp in dates:
        available = sum(
            timestamp in frame.index and pd.notna(frame.loc[timestamp, "SMA200"])
            for frame in frames.values()
        )
        if available >= 100:
            return [date for date in dates if date >= timestamp]
    raise RuntimeError("Insufficient completed SMA200 history for rolling validation.")


def _windows(dates):
    third = len(dates) // 3
    return (
        ("Fold1", dates[0], dates[third]),
        ("Fold2", dates[third], dates[2 * third]),
        ("Fold3", dates[2 * third], None),
    )


def main():
    frames = {}
    for number, symbol in enumerate(NIFTY200, start=1):
        try:
            print(f"[{number}/{len(NIFTY200)}] {symbol}", flush=True)
            frames[symbol] = daily_indicators(download(symbol, period="2y", interval="1d"))
        except Exception as error:
            print(f"Skipping {symbol}: {error}")
    if not frames:
        raise SystemExit("No daily candles were available.")

    dates = _active_dates(frames)
    windows = _windows(dates)
    print(
        "Validation windows: "
        + "; ".join(
            f"{name} {start.date()} to {(end.date() if end is not None else dates[-1].date())}"
            for name, start, end in windows
        ),
        flush=True,
    )

    rows = []
    for settings in VARIANTS:
        print(f"Testing {settings.name}...", flush=True)
        result = {"Strategy": settings.name}
        for name, start, end in windows:
            metrics = _metrics(settings, _period_frames(frames, start=start, end=end))
            result.update({f"{name}{key}": value for key, value in metrics.items()})
        result["PassesTwoLaterFolds6PctGate"] = (
            result["Fold2ReturnPct"] >= 6.0
            and result["Fold2ProfitFactor"] >= 1.1
            and result["Fold3ReturnPct"] >= 6.0
            and result["Fold3ProfitFactor"] >= 1.1
        )
        rows.append(result)

    report = pd.DataFrame(rows).sort_values(
        ["PassesTwoLaterFolds6PctGate", "Fold3ReturnPct", "Fold2ReturnPct"],
        ascending=False,
    )
    Path("reports").mkdir(exist_ok=True)
    report.to_csv("reports/momentum_rotation_rolling_validation.csv", index=False)
    display_columns = [
        "Strategy",
        "Fold1ReturnPct", "Fold1ProfitFactor",
        "Fold2ReturnPct", "Fold2ProfitFactor",
        "Fold3ReturnPct", "Fold3ProfitFactor",
        "Fold3MaxDrawdownPct",
        "PassesTwoLaterFolds6PctGate",
    ]
    print("\n" + report[display_columns].to_string(index=False))
    print("Saved reports/momentum_rotation_rolling_validation.csv")


if __name__ == "__main__":
    main()
