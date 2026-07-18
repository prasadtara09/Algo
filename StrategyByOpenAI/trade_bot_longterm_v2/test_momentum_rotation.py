import unittest

import pandas as pd

from backtest.momentum_rotation import MomentumRotationBacktest, MomentumRotationSettings
from strategy.momentum_rotation import rank_momentum_rows


def _frame(open_price, close_price, rs20):
    index = pd.DatetimeIndex([pd.Timestamp("2025-05-02"), pd.Timestamp("2025-05-05")])
    return pd.DataFrame(
        {
            "Open": [100.0, open_price],
            "High": [102.0, max(open_price, close_price) + 1],
            "Low": [99.0, min(open_price, close_price) - 1],
            "Close": [100.0, close_price],
            "ATR": [2.0, 2.0],
            "RS20": [rs20, rs20],
            "RS40": [rs20, rs20],
            "RS60": [rs20, rs20],
            "RS80": [rs20, rs20],
            "RS120": [rs20, rs20],
            "SMA50": [95.0, 95.0],
            "SMA200": [90.0, 90.0],
        },
        index=index,
    )


class MomentumRotationTests(unittest.TestCase):
    def test_ranking_requires_positive_momentum_and_long_trend(self):
        rows = {
            "WEAK.NS": pd.Series({"Close": 100, "SMA50": 95, "SMA200": 90, "RS20": -0.01}),
            "GOOD.NS": pd.Series({"Close": 100, "SMA50": 95, "SMA200": 90, "RS20": 0.12}),
            "BEST.NS": pd.Series({"Close": 100, "SMA50": 95, "SMA200": 90, "RS20": 0.20}),
            "BEAR.NS": pd.Series({"Close": 90, "SMA50": 95, "SMA200": 100, "RS20": 0.30}),
        }
        self.assertEqual(rank_momentum_rows(rows), ["BEST.NS", "GOOD.NS"])

    def test_friday_rank_is_filled_on_the_following_open_and_respects_position_cap(self):
        settings = MomentumRotationSettings(
            name="test",
            momentum_column="RS20",
            rebalance="weekly",
            require_short_term_strength=False,
            initial_stop_atr=None,
            trail_atr=None,
            max_positions=1,
            max_position_value_pct=1.0,
        )
        frames = {
            "LOWER.NS": _frame(110.0, 112.0, 0.10),
            "HIGHER.NS": _frame(120.0, 122.0, 0.20),
        }

        trades, _ = MomentumRotationBacktest(settings).run(frames)

        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].symbol, "HIGHER.NS")
        self.assertEqual(trades[0].entry_time, pd.Timestamp("2025-05-05"))
        self.assertAlmostEqual(trades[0].entry_price, 120.06, places=2)
        self.assertEqual(trades[0].exit_reason, "END_OF_DATA")


if __name__ == "__main__":
    unittest.main()
