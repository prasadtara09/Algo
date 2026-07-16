from dataclasses import dataclass
from datetime import datetime


@dataclass
class Trade:

    symbol: str
    side: str
    quantity: int

    entry_time: datetime
    exit_time: datetime

    entry_price: float
    exit_price: float

    initial_stoploss: float
    stoploss: float
    target: float

    pnl: float

    rr: float

    exit_reason: str

    strategy: str = ""

    atr: float = 0

    risk_reward: float = 0