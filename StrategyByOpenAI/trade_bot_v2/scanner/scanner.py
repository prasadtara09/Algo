from config import SCANNER_CACHE_ONLY, TIMEFRAME
from data.cache import load_cache
from data.loader import get_data

from indicators.indicator_engine import apply_indicators

from strategy.strategy_engine import StrategyEngine

from scanner.filters import basic_filter

from scanner.ranking import rank_signals


class Scanner:

    def __init__(self):

        self.engine = StrategyEngine()
        self.last_scan_stats = {"requested": 0, "scanned": 0, "missing_data": 0, "errors": 0}

    def _load_data(self, symbol):
        if SCANNER_CACHE_ONLY:
            return load_cache(symbol, TIMEFRAME)
        return get_data(symbol, interval=TIMEFRAME)

    def scan(self, symbols):
        """Return historical signals; useful for research, not live scanning."""

        signals = []

        for symbol in symbols:

            try:

                df = self._load_data(symbol)

                if df is None:
                    continue

                df = apply_indicators(df)

                if not basic_filter(df):

                    continue

                stock_signals = self.engine.scan(

                    symbol,

                    df

                )

                signals.extend(stock_signals)

            except Exception as e:

                print(symbol, e)

        return rank_signals(signals)

    def scan_latest(self, symbols, limit=None):
        """Return at most one actionable signal per symbol from its last bar."""
        signals = []
        self.last_scan_stats = {"requested": len(symbols), "scanned": 0, "missing_data": 0, "errors": 0}

        for symbol in symbols:
            try:
                data = self._load_data(symbol)
                if data is None:
                    self.last_scan_stats["missing_data"] += 1
                    continue

                df = apply_indicators(data)
                if df.empty or not basic_filter(df):
                    continue

                self.last_scan_stats["scanned"] += 1

                signal = self.engine.check_entry(symbol, df.copy(), len(df) - 1)
                if signal:
                    signals.append(signal)
            except Exception as error:
                self.last_scan_stats["errors"] += 1
                print(f"{symbol}: {error}")

        ranked = rank_signals(signals)
        return ranked if limit is None else ranked[:limit]
