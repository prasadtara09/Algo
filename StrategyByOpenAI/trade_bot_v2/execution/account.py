from config import INITIAL_CAPITAL


class Account:

    def __init__(self):

        self.initial_capital = INITIAL_CAPITAL

        self.cash = INITIAL_CAPITAL

        self.realized_pnl = 0.0

        self.unrealized_pnl = 0.0

    @property
    def equity(self):

        return (
            self.cash
            + self.unrealized_pnl
        )

    def book_profit(self, pnl):

        self.cash += pnl

        self.realized_pnl += pnl

    def reset_unrealized(self):

        self.unrealized_pnl = 0

    def add_unrealized(self, pnl):

        self.unrealized_pnl += pnl