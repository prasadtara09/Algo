import vectorbt as vbt
import yfinance as yf
import os

# 1. Download Data (Example: Reliance Industries)
print("Fetching market data...")
price_data = yf.download("IDEA.NS", start="2025-01-01", end="2026-07-01")['Close']

# 2. Define Indicators
fast_ma = vbt.MA.run(price_data, window=10)
slow_ma = vbt.MA.run(price_data, window=50)

# 3. Generate Signals (Fast crosses above Slow = Buy, below = Sell)
entries = fast_ma.ma_crossed_above(slow_ma)
exits = fast_ma.ma_crossed_below(slow_ma)

# 4. Run the Backtest Engine
print("Executing backtest...")
portfolio = vbt.Portfolio.from_signals(price_data, entries, exits, init_cash=10000)

# 5. Output the Results to Terminal
print("\n--- Strategy Performance ---")
print(portfolio.stats())

# 6. Extract raw trade ledger
trade_history = portfolio.trades.records_readable

# 7. Export the data to CSV for the Monte Carlo Simulator
csv_filename = "idea_backtest_trades.csv"
trade_history.to_csv(csv_filename, index=False)

print(f"\n✅ Success! Trade history exported to: {os.path.abspath(csv_filename)}")