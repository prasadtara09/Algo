import pandas as pd

from backtest.performance import Performance


class Metrics:

    @staticmethod
    def summary(
        trades,
        initial_capital,
    ):

        if len(trades) == 0:

            return {}

        df = pd.DataFrame([
            {
                "PnL": t.pnl
            }
            for t in trades
        ])

        wins = len(df[df.PnL > 0])

        losses = len(df[df.PnL <= 0])

        equity = Performance.equity_curve(
            trades,
            initial_capital,
        )

        return {

            "Trades": len(df),

            "Wins": wins,

            "Losses": losses,

            "WinRate": round(
                wins * 100 / len(df),
                2,
            ),

            "NetPnL": round(
                df.PnL.sum(),
                2,
            ),

            "AverageTrade": round(
                df.PnL.mean(),
                2,
            ),

            "ProfitFactor":
                Performance.profit_factor(
                    trades
                ),

            "Expectancy":
                Performance.expectancy(
                    trades
                ),

            "MaxDrawdown":
                Performance.max_drawdown(
                    equity
                ),

            "FinalEquity":
                round(
                    equity.iloc[-1]["Equity"],
                    2,
                )
        }