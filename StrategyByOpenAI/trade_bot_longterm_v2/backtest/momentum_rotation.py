"""Long-only, portfolio-level momentum rotation research backtest.

This module is intentionally separate from the signal-entry swing engine.  It
tests a different hypothesis: own only the strongest NIFTY 200 stocks while
they remain in a long-term uptrend, then review the holdings at a fixed weekly
or monthly cadence.  Rankings use a completed daily bar and orders execute at
the following session's open, with slippage and brokerage applied.
"""

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from backtest.tradebook import Trade
from config import (
    BROKERAGE_PER_ORDER,
    INITIAL_CAPITAL,
    MAX_OPEN_POSITIONS,
    MAX_POSITION_VALUE_PCT,
    SLIPPAGE,
)
from strategy.momentum_rotation import rank_momentum_rows


@dataclass(frozen=True)
class MomentumRotationSettings:
    """Parameters for an end-of-day momentum ranking and next-open rotation."""

    name: str
    momentum_column: str = "RS60"
    rebalance: str = "weekly"  # weekly or monthly
    require_short_term_strength: bool = True
    initial_stop_atr: Optional[float] = 3.0
    trail_atr: Optional[float] = 4.0
    max_positions: int = MAX_OPEN_POSITIONS
    max_position_value_pct: float = MAX_POSITION_VALUE_PCT


class MomentumRotationBacktest:
    """One-cash-account, long-only rotation simulator.

    It does not resize retained positions on every rebalance.  That avoids
    unnecessary turnover while always enforcing the position-count and entry
    exposure caps.  Stops are evaluated conservatively: gap stops use the
    session open and an intraday stop is checked before the trailing stop is
    raised using that day's high.
    """

    def __init__(self, settings: MomentumRotationSettings):
        self.settings = settings
        self.cash = INITIAL_CAPITAL
        self.positions = {}
        self.trades = []
        self.equity_rows = []

    def _equity(self, rows):
        marked_value = sum(
            (
                float(rows[symbol]["Close"])
                if symbol in rows
                else position["last_mark"]
            ) * position["quantity"]
            for symbol, position in self.positions.items()
        )
        return self.cash + marked_value

    def _close(self, position, price, timestamp, reason):
        exit_price = round(float(price) * (1 - SLIPPAGE), 2)
        proceeds = exit_price * position["quantity"]
        self.cash += proceeds - BROKERAGE_PER_ORDER
        pnl = (
            (exit_price - position["entry_price"]) * position["quantity"]
            - 2 * BROKERAGE_PER_ORDER
        )
        risk = position["entry_price"] - position["initial_stop"]
        self.trades.append(
            Trade(
                symbol=position["symbol"],
                side="BUY",
                quantity=position["quantity"],
                entry_time=position["entry_time"],
                exit_time=timestamp,
                entry_price=position["entry_price"],
                exit_price=exit_price,
                initial_stoploss=position["initial_stop"],
                stoploss=position["stop"],
                target=0.0,
                pnl=pnl,
                rr=round((exit_price - position["entry_price"]) / risk, 2) if risk else 0.0,
                exit_reason=reason,
                strategy=self.settings.name,
                atr=position["atr"],
                risk_reward=0.0,
            )
        )
        del self.positions[position["symbol"]]

    def _enter(self, symbol, candle, timestamp, allocation):
        entry_price = round(float(candle["Open"]) * (1 + SLIPPAGE), 2)
        quantity = min(
            int(allocation / entry_price),
            int((self.cash - BROKERAGE_PER_ORDER) / entry_price),
        )
        if quantity <= 0:
            return

        atr = float(candle["ATR"])
        initial_stop = (
            round(entry_price - atr * self.settings.initial_stop_atr, 2)
            if self.settings.initial_stop_atr is not None
            else 0.0
        )
        self.cash -= entry_price * quantity + BROKERAGE_PER_ORDER
        self.positions[symbol] = {
            "symbol": symbol,
            "entry_time": timestamp,
            "entry_price": entry_price,
            "quantity": quantity,
            "atr": atr,
            "initial_stop": initial_stop,
            "stop": initial_stop,
            "highest": entry_price,
            "last_mark": entry_price,
        }

    def _manage_position(self, position, candle, timestamp):
        if position["stop"] > 0 and float(candle["Open"]) <= position["stop"]:
            self._close(position, candle["Open"], timestamp, "STOPLOSS_GAP")
            return
        if position["stop"] > 0 and float(candle["Low"]) <= position["stop"]:
            self._close(position, position["stop"], timestamp, "STOPLOSS")
            return

        if self.settings.trail_atr is not None:
            position["highest"] = max(position["highest"], float(candle["High"]))
            trailing_stop = round(
                position["highest"] - position["atr"] * self.settings.trail_atr,
                2,
            )
            position["stop"] = max(position["stop"], trailing_stop)

    def _eligible_ranked_symbols(self, rows):
        return rank_momentum_rows(
            rows,
            momentum_column=self.settings.momentum_column,
            require_short_term_strength=self.settings.require_short_term_strength,
        )[: self.settings.max_positions]

    def _is_rebalance_date(self, current, following):
        if self.settings.rebalance == "weekly":
            return current.isocalendar()[:2] != following.isocalendar()[:2]
        if self.settings.rebalance == "monthly":
            return (current.year, current.month) != (following.year, following.month)
        raise ValueError(f"Unsupported rebalance cadence: {self.settings.rebalance}")

    def _rebalance(self, rows, target_symbols, timestamp):
        target_symbols = [symbol for symbol in target_symbols if symbol in rows]
        for symbol in list(self.positions):
            if symbol not in target_symbols and symbol in rows:
                self._close(self.positions[symbol], rows[symbol]["Open"], timestamp, "REBALANCE")

        portfolio_equity = self._equity(rows)
        allocation = min(
            portfolio_equity * self.settings.max_position_value_pct,
            portfolio_equity / self.settings.max_positions,
        )
        for symbol in target_symbols:
            if len(self.positions) >= self.settings.max_positions:
                break
            if symbol not in self.positions:
                self._enter(symbol, rows[symbol], timestamp, allocation)

    def run(self, frames):
        """Run the strategy against feature-complete daily frames."""
        frame_rows = {
            symbol: {timestamp: row for timestamp, row in frame.iterrows()}
            for symbol, frame in frames.items()
        }
        dates = sorted({timestamp for frame in frames.values() for timestamp in frame.index})
        scheduled_targets = {}

        for number, timestamp in enumerate(dates):
            rows = {
                symbol: row_map[timestamp]
                for symbol, row_map in frame_rows.items()
                if timestamp in row_map
            }

            if timestamp in scheduled_targets:
                self._rebalance(rows, scheduled_targets.pop(timestamp), timestamp)

            for symbol in list(self.positions):
                if symbol in rows:
                    self._manage_position(self.positions[symbol], rows[symbol], timestamp)

            # A stock can occasionally be absent from the union calendar (for
            # example, a symbol-specific data gap).  Carry its last close
            # forward for portfolio marking instead of treating its value as
            # zero, while never creating a trade on that missing session.
            for symbol, position in self.positions.items():
                if symbol in rows:
                    position["last_mark"] = float(rows[symbol]["Close"])

            if number < len(dates) - 1:
                next_timestamp = dates[number + 1]
                if self._is_rebalance_date(timestamp, next_timestamp):
                    scheduled_targets[next_timestamp] = self._eligible_ranked_symbols(rows)

            self.equity_rows.append(
                {
                    "Time": timestamp,
                    "Equity": self._equity(rows),
                    "OpenPositions": len(self.positions),
                }
            )

        for symbol in list(self.positions):
            frame = frames[symbol]
            last = frame.iloc[-1]
            self._close(self.positions[symbol], last["Close"], last.name, "END_OF_DATA")

        return self.trades, pd.DataFrame(self.equity_rows)
