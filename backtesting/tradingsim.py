import pandas as pd
import yfinance as yf
import talib # Requires: pip install TA-Lib
from datetime import time

# ==========================================
# 1. CONFIGURATION
# ==========================================
TICKERS = ["EASEMYTRIP.NS", "IDEA.NS", "RELIANCE.NS", "TATAMOTORS.NS", "INFY.NS", "HDFCBANK.NS", "TCS.NS", "SBIN.NS", "ICICIBANK.NS", "AXISBANK.NS", "BAJFINANCE.NS", "KOTAKBANK.NS", "ASHOKLEY.NS"] 
BACKTEST_PERIOD = "30d"    
INTERVAL = "15m"           

STARTING_CAPITAL = 5000.0   
LEVERAGE = 10              
SLIPPAGE = 0.002           # 0.2% slippage applied to every entry and exit

def calculate_fyers_charges(buy_price, sell_price, qty):
    buy_value, sell_value = buy_price * qty, sell_price * qty
    total_brokerage = min(20.0, buy_value * 0.0003) + min(20.0, sell_value * 0.0003)
    return round(total_brokerage + (sell_value * 0.00025) + ( (buy_value + sell_value) * 0.0000354) + (buy_value * 0.00003), 2)

# ==========================================
# 2. BACKTESTING LOOP
# ==========================================
for ticker in TICKERS:
    print(f"\n{'='*60}")
    print(f"📥 Downloading 15m data for {ticker}...")
    
    df = yf.download(ticker, period=BACKTEST_PERIOD, interval=INTERVAL, progress=False)
    
    if isinstance(df.columns, pd.MultiIndex): 
        df.columns = df.columns.get_level_values(0)
        
    if df.empty:
        print(f"⚠️ No data found for {ticker}. Skipping to next stock.")
        continue

    # Indicators: RSI and Bollinger Bands
    df['RSI'] = talib.RSI(df['Close'], timeperiod=14)
    df['Upper'], df['Middle'], df['Lower'] = talib.BBANDS(df['Close'], timeperiod=20, nbdevup=2, nbdevdn=2)

    df.index = pd.to_datetime(df.index).tz_convert('Asia/Kolkata')
    df['Date'], df['Time'] = df.index.date, df.index.time

    current_capital = STARTING_CAPITAL
    total_trades = 0
    winning_trades = 0
    
    print(f"🚀 MEAN REVERSION BACKTEST FOR {ticker} (WITH {SLIPPAGE*100}% SLIPPAGE)")
    print("-" * 60)

    for date, day_data in df.groupby('Date'):
        trade_active, trade_side, entry_price = False, None, 0.0
        trade_qty = 0
        
        for idx, row in day_data.iterrows():
            if pd.isna(row['Close']) or pd.isna(row['RSI']) or pd.isna(row['Lower']):
                continue
                
            close, rsi, lower, upper = float(row['Close']), float(row['RSI']), float(row['Lower']), float(row['Upper'])
            
            if not trade_active:
                if rsi < 30 and close <= lower: 
                    # Oversold: Buy
                    trade_active, trade_side = True, "LONG"
                    entry_price = close * (1 + SLIPPAGE)
                    trade_qty = int((current_capital * LEVERAGE) // entry_price)
                    
                elif rsi > 70 and close >= upper: 
                    # Overbought: Short
                    trade_active, trade_side = True, "SHORT"
                    entry_price = close * (1 - SLIPPAGE)
                    trade_qty = int((current_capital * LEVERAGE) // entry_price)
            else:
                # Exit Logic
                if trade_side == "LONG" and close >= row['Middle']:
                    exit_price = close * (1 - SLIPPAGE)
                    gross_pnl = (exit_price - entry_price) * trade_qty
                    fees = calculate_fyers_charges(buy_price=entry_price, sell_price=exit_price, qty=trade_qty)
                    
                    net_pnl = gross_pnl - fees
                    current_capital += net_pnl
                    total_trades += 1
                    if net_pnl > 0: winning_trades += 1
                        
                    print(f"Date: {date} | {trade_side:5s} | Net: ₹{net_pnl:>7.2f} | Bal: ₹{current_capital:,.2f}")
                    trade_active = False
                    
                elif trade_side == "SHORT" and close <= row['Middle']:
                    exit_price = close * (1 + SLIPPAGE)
                    gross_pnl = (entry_price - exit_price) * trade_qty
                    fees = calculate_fyers_charges(buy_price=exit_price, sell_price=entry_price, qty=trade_qty)
                    
                    net_pnl = gross_pnl - fees
                    current_capital += net_pnl
                    total_trades += 1
                    if net_pnl > 0: winning_trades += 1
                        
                    print(f"Date: {date} | {trade_side:5s} | Net: ₹{net_pnl:>7.2f} | Bal: ₹{current_capital:,.2f}")
                    trade_active = False

    # Print Summary for the stock
    print("-" * 60)
    print(f"📊 SUMMARY FOR {ticker}")
    print(f"Total Trades : {total_trades}")
    if total_trades > 0:
        win_rate = (winning_trades / total_trades) * 100
        print(f"Win Rate     : {win_rate:.1f}%")
    print(f"Start Capital: ₹{STARTING_CAPITAL:,.2f}")
    print(f"Final Capital: ₹{current_capital:,.2f}")
    print(f"Net Profit   : ₹{(current_capital - STARTING_CAPITAL):,.2f}")
    print(f"{'='*60}\n")