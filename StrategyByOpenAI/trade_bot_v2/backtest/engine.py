from execution.portfolio import Portfolio
from execution.risk_manager import RiskManager
from execution.trade_manager import TradeManager
from execution.account import Account
from config import MIN_LOOKBACK


class BacktestEngine:

    def __init__(self):

        self.account = Account()

        self.portfolio = Portfolio()

        self.risk = RiskManager()

        self.trade_manager = TradeManager(
            self.portfolio,
            self.risk,
            self.account
        )

        self.completed_trades = []

    

    def run(self, symbol, df, strategy_engine):

        self.completed_trades = []

        for i in range(MIN_LOOKBACK, len(df)):

            candle = df.iloc[i]

            if self.portfolio.has_position(symbol):

                position = self.portfolio.positions[symbol]

                trade = self.trade_manager.manage_trade(
                    position,
                    candle,
                )

                if trade:
                    self.completed_trades.append(trade)

            else:

                signal = strategy_engine.check_entry(
                    symbol,
                    df,
                    i,
                )

                if signal:
                    self.trade_manager.enter_trade(signal)

        return self.completed_trades