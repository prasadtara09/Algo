import vectorbt as vbt
import yfinance as yf
import pandas as pd
import os

print("Fetching 15m historical data...")
# Yahoo Finance supports up to 60 days of 15-minute intraday data
# Translating your Fyers tickers to Yahoo Finance tickers
tickers = ["EASEMYTRIP.NS", "IDEA.NS"]
price_data = yf.download(tickers, period="60d", interval="15m")['Close']

print("Calculating Indicators (RSI & Bollinger Bands)...")
# Using VectorBT's TA-Lib integration, matching your exact parameters
rsi = vbt.talib("RSI").run(price_data, timeperiod=14).real
bbands = vbt.talib("BBANDS").run(price_data, timeperiod=20, nbdevup=2, nbdevdn=2)

lower_band = bbands.lowerband
middle_band = bbands.middleband
upper_band = bbands.upperband

# ==========================================
# 🛠️ FIX 1: ALIGN DATAFRAME COLUMNS
# Prevents ValueError when comparing DataFrames
# ==========================================
rsi.columns = price_data.columns
lower_band.columns = price_data.columns
middle_band.columns = price_data.columns
upper_band.columns = price_data.columns

print("Applying Trading Logic...")
# --- LONG LOGIC ---
# Entry: RSI < 30 AND Close <= Lower BB
long_entries = (rsi < 30) & (price_data <= lower_band)
# Exit: Close >= Middle BB
long_exits = (price_data >= middle_band)

# --- SHORT LOGIC ---
# Entry: RSI > 70 AND Close >= Upper BB
short_entries = (rsi > 70) & (price_data >= upper_band)
# Exit: Close <= Middle BB
short_exits = (price_data <= middle_band)

print("Executing Vectorized Backtest...")
# Run the simulation for both tickers simultaneously
portfolio = vbt.Portfolio.from_signals(
    price_data,
    entries=long_entries,
    exits=long_exits,
    short_entries=short_entries,
    short_exits=short_exits,
    init_cash=10000,
    fees=0.0005, # Simulating basic slippage/brokerage
    freq='15min' # 🛠️ FIX 2: Updated frequency for newer pandas versions
)

# Output summary to terminal
print("\n--- Strategy Performance (60 Days, 15m Timeframe) ---")
print(portfolio.stats())

# Extract raw trade ledger and format it for the Monte Carlo Simulator
trade_history = portfolio.trades.records_readable

# Rename columns to match your preferred format and the Simulator's requirements
trade_history = trade_history.rename(columns={
    'Exit Timestamp': 'Timestamp',
    'Column': 'Ticker',
    'Direction': 'Side',
    'Entry Price': 'Entry',
    'Exit Price': 'Exit',
    'Return': 'PnL_Percent',
    'PnL': 'PnL_Absolute'  # Maps VectorBT's raw currency return to the simulator's required column
})

csv_filename = "fyers_strategy_backtest.csv"
trade_history.to_csv(csv_filename, index=False)

print(f"\n✅ Success! Historical backtest complete.")
print(f"File exported to: {os.path.abspath(csv_filename)}")