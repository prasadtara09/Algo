from data.loader import get_data

from indicators.indicator_engine import apply_indicators

from strategy.strategy_engine import StrategyEngine

from scanner.filters import basic_filter

from scanner.ranking import rank_signals


class Scanner:

    def __init__(self):

        self.engine = StrategyEngine()

    def scan(self, symbols):

        signals = []

        for symbol in symbols:

            try:

                df = get_data(symbol)

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