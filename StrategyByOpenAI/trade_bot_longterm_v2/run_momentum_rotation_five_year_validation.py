"""Five-year validation of the fixed weekly 20-day momentum rotation model."""

import argparse
from pathlib import Path

import pandas as pd

from backtest.momentum_rotation import MomentumRotationBacktest, MomentumRotationSettings
from data.universe import NIFTY200
from data.yahoo_history import YahooHistoryClient, YahooHistoryError, load_or_fetch_daily
from run_momentum_rotation_research import _metrics, _period_frames
from strategy.swing_features import daily_indicators


FIXED_STRATEGY = MomentumRotationSettings(
    "Weekly 20-day momentum, no stops",
    momentum_column="RS20",
    rebalance="weekly",
    require_short_term_strength=False,
    initial_stop_atr=None,
    trail_atr=None,
)


def _five_year_windows(end_date):
    start = end_date - pd.DateOffset(years=5)
    boundaries = [start + pd.DateOffset(years=number) for number in range(6)]
    return [
        (f"Year{number + 1}", boundaries[number], boundaries[number + 1])
        for number in range(5)
    ]


def main():
    parser = argparse.ArgumentParser(description="Validate the fixed rotation strategy over five years.")
    parser.add_argument("--max-symbols", type=int, default=None, help="Download a small smoke-test subset.")
    parser.add_argument("--refresh", action="store_true", help="Re-download any cached six-year daily history.")
    args = parser.parse_args()

    symbols = NIFTY200[:args.max_symbols] if args.max_symbols else NIFTY200
    client = YahooHistoryClient()
    frames = {}
    failures = []
    for number, symbol in enumerate(symbols, start=1):
        try:
            raw = load_or_fetch_daily(client, symbol, refresh=args.refresh)
            frames[symbol] = daily_indicators(raw)
            print(f"[{number}/{len(symbols)}] {symbol}: {len(raw)} daily candles", flush=True)
        except YahooHistoryError as error:
            failures.append((symbol, str(error)))
            print(f"[{number}/{len(symbols)}] Skipping {symbol}: {error}", flush=True)
    if not frames:
        raise SystemExit("No six-year daily candles were available.")

    last_date = max(frame.index.max() for frame in frames.values())
    start_date = last_date - pd.DateOffset(years=5)
    test_frames = _period_frames(frames, start=start_date)
    full_backtest = MomentumRotationBacktest(FIXED_STRATEGY)
    trades, _ = full_backtest.run(test_frames)
    full = _metrics(FIXED_STRATEGY, test_frames)
    result = {"Strategy": FIXED_STRATEGY.name, "TestStart": start_date.date(), "TestEnd": last_date.date(), **full}

    for name, start, end in _five_year_windows(last_date):
        metrics = _metrics(FIXED_STRATEGY, _period_frames(frames, start=start, end=end))
        result.update({f"{name}{key}": value for key, value in metrics.items()})

    report = pd.DataFrame([result])
    Path("reports").mkdir(exist_ok=True)
    report.to_csv("reports/momentum_rotation_five_year_validation.csv", index=False)
    # Match the supplied FYERS-style export format exactly so it can be
    # compared with a paper-trading export in a spreadsheet.
    trade_export = pd.DataFrame(
        [
            {
                "symbol": trade.symbol,
                "entry_price": round(trade.entry_price, 2),
                "exit_price": round(trade.exit_price, 2),
                "pnl": round(trade.pnl, 2),
            }
            for trade in trades
        ],
        columns=["symbol", "entry_price", "exit_price", "pnl"],
    )
    trade_export.to_csv(
        "reports/weekly_20day_momentum_no_stops_five_year_trades.csv",
        index=False,
        encoding="utf-8-sig",
    )
    print("\n" + report.to_string(index=False))
    if failures:
        pd.DataFrame(failures, columns=["Symbol", "Error"]).to_csv(
            "reports/momentum_rotation_five_year_download_failures.csv", index=False
        )
        print(f"Saved {len(failures)} download failures for retry.")
    print("Saved reports/momentum_rotation_five_year_validation.csv")
    print("Saved reports/weekly_20day_momentum_no_stops_five_year_trades.csv")


if __name__ == "__main__":
    main()
