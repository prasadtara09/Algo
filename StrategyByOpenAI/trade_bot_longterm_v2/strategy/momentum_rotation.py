"""Shared selection rule for the validated long-only swing rotation model."""

from datetime import datetime, time
from typing import Mapping, Optional
from zoneinfo import ZoneInfo

import pandas as pd

from config import MAX_OPEN_POSITIONS, MAX_POSITION_VALUE_PCT


MODEL_NAME = "Weekly 20-day relative-strength rotation"


def rank_momentum_rows(rows, momentum_column="RS20", require_short_term_strength=False):
    """Return eligible symbols from strongest to weakest end-of-day momentum."""
    ranked = []
    for symbol, row in rows.items():
        momentum = row.get(momentum_column)
        if pd.isna(momentum) or momentum <= 0:
            continue
        if not (row["Close"] > row["SMA50"] > row["SMA200"]):
            continue
        if require_short_term_strength and row["RS20"] <= 0:
            continue
        ranked.append((float(momentum), symbol))
    ranked.sort(reverse=True)
    return [symbol for _, symbol in ranked]


def latest_completed_session(frames, now: Optional[datetime] = None):
    """Find the latest broadly available completed Indian-market daily bar.

    During market hours, Yahoo/FYERS may expose a partial candle for today.
    That candle is never used for a signal because the strategy only ranks
    completed sessions.
    """
    now = now or datetime.now(ZoneInfo("Asia/Kolkata"))
    dates = sorted({timestamp for frame in frames.values() for timestamp in frame.index})
    if not dates:
        raise ValueError("No daily data is available.")

    if dates[-1].date() == now.date() and now.time() < time(15, 45):
        dates.pop()
    minimum_coverage = max(50, len(frames) // 2)
    for timestamp in reversed(dates):
        coverage = sum(timestamp in frame.index for frame in frames.values())
        if coverage >= minimum_coverage:
            return timestamp
    raise ValueError("No completed session has sufficient NIFTY 200 coverage.")


def select_rotation_targets(
    frames: Mapping[str, pd.DataFrame],
    as_of=None,
    max_positions: int = MAX_OPEN_POSITIONS,
):
    """Select the validated model's target basket from completed daily bars."""
    if max_positions <= 0:
        raise ValueError("max_positions must be positive")
    as_of = as_of if as_of is not None else latest_completed_session(frames)
    rows = {
        symbol: frame.loc[as_of]
        for symbol, frame in frames.items()
        if as_of in frame.index
    }
    symbols = rank_momentum_rows(rows, momentum_column="RS20", require_short_term_strength=False)
    allocation_pct = 100 * min(MAX_POSITION_VALUE_PCT, 1 / max_positions)
    selected = []
    for rank, symbol in enumerate(symbols[:max_positions], start=1):
        row = rows[symbol]
        selected.append(
            {
                "Rank": rank,
                "Symbol": symbol,
                "AsOf": as_of,
                "Close": round(float(row["Close"]), 2),
                "RS20Pct": round(100 * float(row["RS20"]), 2),
                "SMA50": round(float(row["SMA50"]), 2),
                "SMA200": round(float(row["SMA200"]), 2),
                "MaxAllocationPct": round(allocation_pct, 2),
                "Model": MODEL_NAME,
            }
        )
    return as_of, selected
