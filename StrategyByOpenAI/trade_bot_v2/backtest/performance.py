import pandas as pd


class Performance:

    @staticmethod
    def equity_curve(trades, initial_capital):

        equity = initial_capital

        rows = []

        for trade in trades:

            equity += trade.pnl

            rows.append({

                "Time": trade.exit_time,

                "Equity": equity,

                "PnL": trade.pnl,

            })

        return pd.DataFrame(rows)

    @staticmethod
    def max_drawdown(equity_df):

        if equity_df.empty:
            return 0

        peak = equity_df["Equity"].cummax()

        drawdown = equity_df["Equity"] - peak

        return round(drawdown.min(), 2)

    @staticmethod
    def profit_factor(trades):

        gross_profit = sum(
            t.pnl
            for t in trades
            if t.pnl > 0
        )

        gross_loss = abs(sum(
            t.pnl
            for t in trades
            if t.pnl < 0
        ))

        if gross_loss == 0:
            return 999

        return round(
            gross_profit / gross_loss,
            2,
        )

    @staticmethod
    def expectancy(trades):

        if len(trades) == 0:
            return 0

        wins = [
            t.pnl
            for t in trades
            if t.pnl > 0
        ]

        losses = [
            abs(t.pnl)
            for t in trades
            if t.pnl < 0
        ]

        if len(losses) == 0:
            return 0

        win_rate = len(wins) / len(trades)

        loss_rate = len(losses) / len(trades)

        avg_win = sum(wins) / len(wins) if wins else 0

        avg_loss = sum(losses) / len(losses)

        expectancy = (
            (win_rate * avg_win)
            -
            (loss_rate * avg_loss)
        )

        return round(expectancy, 2)