"""Small, guarded FYERS REST API facade.

Market data belongs on the Data WebSocket.  This client is intentionally used
only for account reads and explicitly authorised live order submission.
"""

from typing import Any, Mapping, Optional

from config import MODE
from broker.auth import access_token, client_id


class LiveTradingDisabledError(RuntimeError):
    """Raised when code attempts a broker order outside explicit LIVE mode."""


class FyersRestClient:
    """Lazy FYERS REST client so backtests do not require broker dependencies."""

    def __init__(self, client: Optional[Any] = None):
        self._client = client

    @property
    def client(self):
        if self._client is None:
            from fyers_apiv3 import fyersModel

            self._client = fyersModel.FyersModel(
                client_id=client_id(),
                token=access_token(),
                log_path="logs",
            )
        return self._client

    def profile(self) -> Mapping[str, Any]:
        return self.client.get_profile()

    def positions(self) -> Mapping[str, Any]:
        return self.client.positions()

    def orderbook(self) -> Mapping[str, Any]:
        return self.client.orderbook()

    def place_order(self, order: Mapping[str, Any]) -> Mapping[str, Any]:
        """Submit one order only when the user has explicitly enabled LIVE mode.

        This method is not called by the scanner or stream runner.  Keeping the
        guard here prevents a data-feed change from accidentally placing trades.
        """
        if MODE != "LIVE":
            raise LiveTradingDisabledError(
                "Broker orders are disabled. Set MODE=LIVE in .env only after paper-trading verification."
            )
        return self.client.place_order(dict(order))
