import pandas as pd
import yfinance as yf
import talib # Requires: pip install TA-Lib
from datetime import time

# ==========================================
# 1. CONFIGURATION
# ==========================================
TICKER = "EASEMYTRIP.NS"          
BACKTEST_PERIOD = "30d"    
INTERVAL = "15m"           

INITIAL_CAPITAL = 5000.0   
LEVERAGE = 10              
SLIPPAGE = 0.002           # Added: 0.2% Slippage

def calculate_fyers_charges(buy_price, sell_price, qty):
    # (Same as before)
    buy_value, sell_value = buy_price * qty, sell_price * qty
    total_brokerage = min(20.0, buy_value * 0.0003) + min(20.0, sell_value * 0.0003)
    return round(total_brokerage + (sell_value * 0.00025) + ( (buy_value + sell_value) * 0.0000354) + (buy_value * 0.00003), 2)

print(f"📥 Downloading data for {TICKER}...")
df = yf.download(TICKER, period=BACKTEST_PERIOD, interval=INTERVAL)
if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

# Indicators: RSI and Bollinger Bands
df['RSI'] = talib.RSI(df['Close'], timeperiod=14)
df['Upper'], df['Middle'], df['Lower'] = talib.BBANDS(df['Close'], timeperiod=20, nbdevup=2, nbdevdn=2)

df.index = pd.to_datetime(df.index).tz_convert('Asia/Kolkata')
df['Date'], df['Time'] = df.index.date, df.index.time

current_capital = INITIAL_CAPITAL
print(f"🚀 MEAN REVERSION BACKTEST FOR {TICKER}")

for date, day_data in df.groupby('Date'):
    trade_active, trade_side, entry_price = False, None, 0.0
    
    for idx, row in day_data.iterrows():
        close, rsi, lower, upper = float(row['Close']), float(row['RSI']), float(row['Lower']), float(row['Upper'])
        
        if not trade_active:
            if rsi < 30 and close <= lower: # Oversold: Buy
                trade_active, trade_side = True, "LONG"
                entry_price = close * (1 + SLIPPAGE) # Added 0.2% slippage penalty on buy
                trade_qty = int((current_capital * LEVERAGE) // entry_price)
            elif rsi > 70 and close >= upper: # Overbought: Short
                trade_active, trade_side = True, "SHORT"
                entry_price = close * (1 - SLIPPAGE) # Added 0.2% slippage penalty on short sell
                trade_qty = int((current_capital * LEVERAGE) // entry_price)
        else:
            # Exit Logic: Revert to Mean (Touch the Middle Band)
            if (trade_side == "LONG" and close >= row['Middle']) or (trade_side == "SHORT" and close <= row['Middle']):
                exit_price = close * (1 - SLIPPAGE) if trade_side == "LONG" else close * (1 + SLIPPAGE) # Added slippage to exit
                gross_pnl = (exit_price - entry_price) * trade_qty if trade_side == "LONG" else (entry_price - exit_price) * trade_qty
                fees = calculate_fyers_charges(entry_price, exit_price, trade_qty)
                current_capital += (gross_pnl - fees)
                print(f"Date: {date} | {trade_side:5s} | Net: ₹{(gross_pnl-fees):>7.2f} | Bal: ₹{current_capital:,.2f}")
                trade_active = False