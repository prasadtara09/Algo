from config import (
    INITIAL_CAPITAL,
    RISK_PER_TRADE,
    MAX_OPEN_POSITIONS,
)


class RiskManager:

    def __init__(self):

        self.capital = INITIAL_CAPITAL
        self.risk_per_trade = RISK_PER_TRADE
        self.max_positions = MAX_OPEN_POSITIONS

    def calculate_position_size(
        self,
        entry,
        stoploss,
    ):

        risk_per_share = abs(entry - stoploss)

        if risk_per_share == 0:
            return 0

        risk_amount = (
            self.capital *
            self.risk_per_trade
        )

        qty = int(
            risk_amount /
            risk_per_share
        )

        return max(qty, 0)

    def can_take_trade(
        self,
        portfolio,
    ):

        return (
            len(portfolio.positions)
            < self.max_positions
        )