"""Research long-only NIFTY 200 trend/momentum rotation variants.

The latest 30% of dates are kept as a holdout.  A result is not a candidate
for paper trading unless that later period itself clears the documented
return/profit-factor criteria after costs.
"""

import argparse
from pathlib import Path

import pandas as pd

from backtest.momentum_rotation import MomentumRotationBacktest, MomentumRotationSettings
from config import INITIAL_CAPITAL
from data.downloader import download
from data.universe import NIFTY200
from strategy.swing_features import daily_indicators


VARIANTS = (
    # Short-term cross-sectional momentum.  These use a maximum of five equal
    # 20% entries, matching the default portfolio safety limits.
    MomentumRotationSettings("Weekly 20-day momentum, no stops", "RS20", "weekly", False, None, None),
    MomentumRotationSettings("Weekly 40-day momentum, no stops", "RS40", "weekly", False, None, None),
    MomentumRotationSettings("Weekly 60-day momentum, no stops", "RS60", "weekly", False, None, None),
    MomentumRotationSettings("Weekly 60-day momentum", "RS60", "weekly", True, 3.0, 4.0),
    MomentumRotationSettings("Weekly 120-day momentum", "RS120", "weekly", True, 3.0, 4.0),
    MomentumRotationSettings("Monthly 60-day momentum", "RS60", "monthly", True, 3.0, 4.0),
    MomentumRotationSettings("Monthly 120-day momentum", "RS120", "monthly", True, 3.0, 4.0),
    MomentumRotationSettings("Weekly 60-day, no short-term filter", "RS60", "weekly", False, 3.0, 4.0),
    MomentumRotationSettings("Monthly 120-day, no short-term filter", "RS120", "monthly", False, 3.0, 4.0),
    MomentumRotationSettings("Monthly 40-day momentum, no stops", "RS40", "monthly", False, None, None),
    MomentumRotationSettings("Monthly 60-day momentum, no stops", "RS60", "monthly", False, None, None),
    MomentumRotationSettings("Monthly 80-day momentum, no stops", "RS80", "monthly", False, None, None),
    # More concentrated variants retain the same fully-funded one-account
    # model; they are research comparisons, not a change to live defaults.
    MomentumRotationSettings("Weekly 60-day, three positions", "RS60", "weekly", False, 3.0, 4.0, 3, 1 / 3),
    MomentumRotationSettings("Monthly 60-day, three positions", "RS60", "monthly", False, 3.0, 4.0, 3, 1 / 3),
)


def _period_frames(frames, start=None, end=None):
    output = {}
    for symbol, frame in frames.items():
        subset = frame
        if start is not None:
            subset = subset[subset.index >= start]
        if end is not None:
            subset = subset[subset.index < end]
        # Features are calculated before the time split, using only preceding
        # closes.  The slice therefore needs enough *trading* sessions for a
        # meaningful rotation test, not another 120-session warm-up period.
        if len(subset) >= 40:
            output[symbol] = subset
    return output


def _metrics(settings, frames):
    backtest = MomentumRotationBacktest(settings)
    trades, equity = backtest.run(frames)
    winners = [trade.pnl for trade in trades if trade.pnl > 0]
    losers = [trade.pnl for trade in trades if trade.pnl <= 0]
    gross_profit = sum(winners)
    gross_loss = -sum(losers)
    final_equity = backtest.cash
    return {
        "Trades": len(trades),
        "WinRatePct": round(100 * len(winners) / len(trades), 2) if trades else 0.0,
        "NetPnL": round(final_equity - INITIAL_CAPITAL, 2),
        "ReturnPct": round(100 * (final_equity / INITIAL_CAPITAL - 1), 2),
        "ProfitFactor": round(gross_profit / gross_loss, 2) if gross_loss else 0.0,
        "FinalEquity": round(final_equity, 2),
        "MaxDrawdownPct": _max_drawdown(equity),
    }


def _max_drawdown(equity):
    if equity.empty:
        return 0.0
    curve = equity["Equity"]
    drawdowns = curve / curve.cummax() - 1
    return round(100 * float(drawdowns.min()), 2)


def _summary(settings, frames, split_date):
    full = _metrics(settings, frames)
    earlier = _metrics(settings, _period_frames(frames, end=split_date))
    later = _metrics(settings, _period_frames(frames, start=split_date))
    return {
        "Strategy": settings.name,
        **{f"Full{key}": value for key, value in full.items()},
        **{f"Earlier{key}": value for key, value in earlier.items()},
        **{f"Later{key}": value for key, value in later.items()},
        "PassesLater6PctGate": later["ReturnPct"] >= 6.0 and later["ProfitFactor"] >= 1.1,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate NIFTY 200 long-only momentum rotation.")
    parser.add_argument("--max-symbols", type=int, default=None, help="Use a small sample first.")
    parser.add_argument("--period", default="2y", help="Daily history period for missing cache files.")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Download the requested history instead of using the existing daily cache.",
    )
    args = parser.parse_args()

    symbols = NIFTY200[:args.max_symbols] if args.max_symbols else NIFTY200
    frames = {}
    for number, symbol in enumerate(symbols, start=1):
        try:
            print(f"[{number}/{len(symbols)}] {symbol}", flush=True)
            frames[symbol] = daily_indicators(
                download(symbol, period=args.period, interval="1d", use_cache=not args.refresh)
            )
        except Exception as error:
            print(f"Skipping {symbol}: {error}")
    if not frames:
        raise SystemExit("No daily candles were available.")

    all_dates = sorted({timestamp for frame in frames.values() for timestamp in frame.index})
    split_date = all_dates[int(len(all_dates) * 0.70)]
    print(f"Holdout begins on {split_date.date()} (latest 30% of available dates).", flush=True)

    summaries = []
    for settings in VARIANTS:
        print(f"Testing {settings.name}...", flush=True)
        summaries.append(_summary(settings, frames, split_date))

    report = pd.DataFrame(summaries).sort_values(
        ["PassesLater6PctGate", "LaterReturnPct", "LaterProfitFactor"],
        ascending=False,
    )
    Path("reports").mkdir(exist_ok=True)
    report.to_csv("reports/momentum_rotation_comparison.csv", index=False)
    print("\n" + report.to_string(index=False))
    print("Saved reports/momentum_rotation_comparison.csv")


if __name__ == "__main__":
    main()
