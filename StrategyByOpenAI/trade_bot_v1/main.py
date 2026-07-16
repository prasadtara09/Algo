from data import get_intraday
from strategy import prepare_dataframe, debug_strategy
from backtester import backtest
from report import generate_report


SYMBOL = "TCS.NS"

print("Downloading Data...")

df = get_intraday(SYMBOL)

print("Calculating Indicators...")

df = prepare_dataframe(df)
print(df[["RSI", "ADX", "ATR"]].describe())

debug_strategy(df)

print("Running Backtest...")

trades = backtest(df, SYMBOL)

generate_report(trades)