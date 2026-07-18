"""FYERS API v3 Data WebSocket adapter for real-time market monitoring.

The adapter deliberately has no order-placement code.  Use it to monitor live
prices, and use :mod:`broker.fyers_client` separately for guarded REST calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Event, RLock
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Sequence

from broker.auth import access_token as configured_access_token
from config import FYERS_WS_LITE_MODE, FYERS_WS_MAX_SYMBOLS, FYERS_WS_RECONNECT_RETRY


FYERS_SYMBOL_UPDATE = "SymbolUpdate"


class FyersSubscriptionError(ValueError):
    """Raised when a requested stream subscription is invalid."""


@dataclass(frozen=True)
class MarketTick:
    """Normalized real-time market update from the FYERS DataSocket."""

    symbol: str
    ltp: Optional[float]
    timestamp: Optional[int]
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None
    raw: Optional[Mapping[str, Any]] = None


def to_fyers_symbol(symbol: str) -> str:
    """Convert Yahoo/NSE equity notation (``TCS.NS``) to FYERS notation."""
    value = str(symbol).strip().upper()
    if not value:
        raise FyersSubscriptionError("A WebSocket symbol cannot be blank.")
    if ":" in value:
        return value
    if value.endswith(".NS"):
        value = value[:-3]
    if value.endswith(".BO"):
        return f"BSE:{value[:-3]}-A"
    if value.endswith("-EQ"):
        value = value[:-3]
    return f"NSE:{value}-EQ"


def normalize_symbols(symbols: Iterable[str], max_symbols: int = FYERS_WS_MAX_SYMBOLS) -> list[str]:
    """Normalize, deduplicate, and cap a list of requested FYERS symbols."""
    normalized = []
    seen = set()
    for symbol in symbols:
        fyers_symbol = to_fyers_symbol(symbol)
        if fyers_symbol not in seen:
            seen.add(fyers_symbol)
            normalized.append(fyers_symbol)
    if not normalized:
        raise FyersSubscriptionError("Provide at least one symbol to subscribe to.")
    if len(normalized) > max_symbols:
        raise FyersSubscriptionError(
            f"Requested {len(normalized)} symbols, but FYERS_WS_MAX_SYMBOLS is {max_symbols}."
        )
    return normalized


def _number(payload: Mapping[str, Any], *keys: str) -> Optional[float]:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
    return None


def _timestamp(payload: Mapping[str, Any]) -> Optional[int]:
    for key in ("timestamp", "ts", "exchange_time"):
        value = payload.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
    return None


class FyersDataStream:
    """Thread-safe wrapper around FYERS API v3's ``FyersDataSocket``.

    ``start`` is non-blocking. Call ``stop`` from a signal handler or use the
    supplied runner script, which closes the connection cleanly on Ctrl+C.
    """

    def __init__(
        self,
        symbols: Sequence[str],
        *,
        token: Optional[str] = None,
        lite_mode: bool = FYERS_WS_LITE_MODE,
        max_symbols: int = FYERS_WS_MAX_SYMBOLS,
        reconnect_retry: int = FYERS_WS_RECONNECT_RETRY,
        on_tick: Optional[Callable[[MarketTick], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[Any], None]] = None,
        socket_factory: Optional[Callable[..., Any]] = None,
    ):
        self.symbols = normalize_symbols(symbols, max_symbols=max_symbols)
        self.token = token or configured_access_token()
        self.lite_mode = lite_mode
        self.reconnect_retry = reconnect_retry
        self.on_tick = on_tick
        self.on_status = on_status
        self.on_error = on_error
        self._socket_factory = socket_factory
        self._socket: Optional[Any] = None
        self._latest: Dict[str, MarketTick] = {}
        self._lock = RLock()
        self._connected = Event()

    def _emit_status(self, status: str) -> None:
        if self.on_status:
            self.on_status(status)

    def _handle_connect(self) -> None:
        if self._socket is None:
            return
        self._socket.subscribe(self.symbols, data_type=FYERS_SYMBOL_UPDATE)
        self._connected.set()
        self._emit_status(f"Subscribed to {len(self.symbols)} FYERS symbols.")

    def _handle_message(self, message: Any) -> None:
        if not isinstance(message, Mapping):
            return
        symbol = message.get("symbol")
        if not symbol:
            return
        tick = MarketTick(
            symbol=str(symbol),
            ltp=_number(message, "ltp", "lp", "last_traded_price"),
            timestamp=_timestamp(message),
            open=_number(message, "open_price", "open", "o"),
            high=_number(message, "high_price", "high", "h"),
            low=_number(message, "low_price", "low", "l"),
            close=_number(message, "prev_close_price", "close", "c"),
            volume=_number(message, "vol_traded_today", "volume", "v"),
            raw=dict(message),
        )
        with self._lock:
            self._latest[tick.symbol] = tick
        if self.on_tick:
            self.on_tick(tick)

    def _handle_error(self, error: Any) -> None:
        if self.on_error:
            self.on_error(error)
        else:
            self._emit_status(f"FYERS WebSocket error: {error}")

    def _handle_close(self, _message: Any) -> None:
        self._connected.clear()
        self._emit_status("FYERS DataSocket closed.")

    def _make_socket(self) -> Any:
        factory = self._socket_factory
        if factory is None:
            from fyers_apiv3.FyersWebsocket.data_ws import FyersDataSocket

            factory = FyersDataSocket
        return factory(
            access_token=self.token,
            write_to_file=False,
            log_path="logs",
            litemode=self.lite_mode,
            reconnect=True,
            on_message=self._handle_message,
            on_error=self._handle_error,
            on_connect=self._handle_connect,
            on_close=self._handle_close,
            reconnect_retry=self.reconnect_retry,
        )

    def start(self) -> "FyersDataStream":
        """Open the DataSocket and subscribe in ``SymbolUpdate`` mode."""
        if self._socket is None:
            self._socket = self._make_socket()
            self._socket.connect()
        return self

    def stop(self) -> None:
        """Close the WebSocket and stop receiving market data."""
        if self._socket is not None:
            self._socket.close_connection()
            self._socket = None
        self._connected.clear()

    def latest(self, symbol: str) -> Optional[MarketTick]:
        """Return the latest normalized tick for a FYERS or Yahoo-style symbol."""
        with self._lock:
            return self._latest.get(to_fyers_symbol(symbol))

    def latest_ticks(self) -> Dict[str, MarketTick]:
        """Return a snapshot of all received ticks without exposing mutable state."""
        with self._lock:
            return dict(self._latest)
