import unittest
from datetime import datetime

import pandas as pd

from backtest.engine import BacktestEngine
from config import MIN_LOOKBACK
from execution.risk_manager import RiskManager
from strategy.signal import Signal


class OneSignalStrategy:
    def __init__(self):
        self.calls = 0

    def check_entry(self, symbol, df, index):
        self.calls += 1
        if self.calls != 1:
            return None
        return Signal(
            symbol=symbol,
            timestamp=df.index[index],
            side="BUY",
            score=100,
            entry=float(df.iloc[index]["Close"]),
            stoploss=98.0,
            target=104.0,
            strategy="test",
            atr=2.0,
        )


class BacktestSafetyTests(unittest.TestCase):
    def test_position_size_is_capped_by_exposure(self):
        risk = RiskManager()
        # Risk sizing would request 250 shares, but 20% of 100,000 at 100 is 200.
        self.assertEqual(risk.calculate_position_size(100, 98, 100_000), 200)

    def test_signal_is_filled_on_next_open_not_signal_close(self):
        index = pd.date_range("2025-01-01 09:15", periods=MIN_LOOKBACK + 2, freq="15min")
        df = pd.DataFrame(
            {
                "Open": [100.0] * (MIN_LOOKBACK + 1) + [110.0],
                "High": [101.0] * (MIN_LOOKBACK + 1) + [115.0],
                "Low": [99.0] * (MIN_LOOKBACK + 1) + [109.0],
                "Close": [100.0] * (MIN_LOOKBACK + 2),
            },
            index=index,
        )

        trades = BacktestEngine().run("TEST.NS", df, OneSignalStrategy())

        self.assertEqual(len(trades), 1)
        # Entry price includes the configured slippage, but is based on 110 open.
        self.assertAlmostEqual(trades[0].entry_price, 110.05, places=2)
        # The same candle touches the tightened trailing stop before the
        # target; the engine deliberately takes that conservative outcome.
        self.assertEqual(trades[0].exit_reason, "TRAILING_STOP")


if __name__ == "__main__":
    unittest.main()
