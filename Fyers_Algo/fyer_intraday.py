import pandas as pd
import talib
import time
import csv
import os
from collections import deque
from datetime import datetime, timedelta, time as dt_time
from fyers_apiv3 import fyersModel

# ==========================================
# 1. CONFIGURATION
# ==========================================
CLIENT_ID = "91I39L89HO-100"
ACCESS_TOKEN = "YOUR_MASKED_TOKEN_HERE" # ⚠️ REMEMBER TO REGENERATE YOUR TOKEN
TICKER = "NSE:EASEMYTRIP-EQ"
QTY = 10
PAPER_TRADING = True  # SET TO FALSE ONLY WHEN READY FOR REAL MONEY
POLLING_INTERVAL = 30 # Seconds between strategy checks

fyers = fyersModel.FyersModel(client_id=CLIENT_ID, token=ACCESS_TOKEN)

def log_backtest_pnl(ticker, side, entry, exit_price, pnl_pct, pnl_abs, timeframe):
    """Logs the trade outcome to a CSV for the Monte Carlo Simulator."""
    file_exists = os.path.isfile('backtest_ledger.csv')
    with open('backtest_ledger.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'Ticker', 'Timeframe', 'Side', 'Entry', 'Exit', 'PnL_Percent', 'PnL_Absolute'])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ticker, timeframe, side, entry, exit_price, pnl_pct, pnl_abs])

# ==========================================
# 2. RATE LIMITER INFRASTRUCTURE
# ==========================================
class FyersRateLimiter:
    """Rolling-window throttle to respect 10/s, 200/m, and 100k/d limits."""
    def __init__(self):
        self.second_window = deque()
        self.minute_window = deque()
        self.daily_calls = 0

    def wait_if_needed(self):
        now = time.time()
        
        # Clean up old timestamps from the windows
        while self.second_window and now - self.second_window[0] >= 1:
            self.second_window.popleft()
        while self.minute_window and now - self.minute_window[0] >= 60:
            self.minute_window.popleft()

        # 3. Daily Limit Check (100,000)
        if self.daily_calls >= 100000:
            raise Exception("❌ CRITICAL: Daily API limit reached (100,000). Shutting down.")

        # 2. Per Minute Limit Check (200)
        if len(self.minute_window) >= 195: # Buffer of 5 for safety
            sleep_time = 60 - (now - self.minute_window[0])
            print(f"⏳ Minute limit nearing. Throttling API for {sleep_time:.2f}s...")
            time.sleep(max(0.1, sleep_time))
            now = time.time()

        # 1. Per Second Limit Check (10)
        if len(self.second_window) >= 9: # Buffer of 1 for safety
            sleep_time = 1 - (now - self.second_window[0])
            time.sleep(max(0.1, sleep_time))
            now = time.time()

        # Record the successful call
        self.second_window.append(now)
        self.minute_window.append(now)
        self.daily_calls += 1

limiter = FyersRateLimiter()

def api_call(func, *args, **kwargs):
    """Wrapper to route all Fyers calls through the rate limiter and log the request."""
    limiter.wait_if_needed()
    
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"📡 [{current_time}] API Requesting: {func.__name__}...")
    
    return func(*args, **kwargs)

# ==========================================
# 3. TRADING LOGIC
# ==========================================
def place_order(side):
    if PAPER_TRADING:
        print(f"⚠️ [PAPER TRADE] Simulating {side} order for {QTY} shares of {TICKER}")
        return {"status": "success"}
    else:
        order_params = {
            "symbol": TICKER, "qty": QTY, "type": 2, 
            "side": 1 if side == "LONG" else -1,
            "productType": "INTRADAY", "validity": "DAY"
        }
        return api_call(fyers.place_order, data=order_params)

def get_indicators():
    # Dynamically calculate the last 60 days to ensure data is always current
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    data = {
        "symbol": TICKER, 
        "resolution": "15", 
        "date_format": "1", 
        "range_from": start_date.strftime("%Y-%m-%d"), 
        "range_to": end_date.strftime("%Y-%m-%d"), 
        "cont_flag": "1"
    }
    
    response = api_call(fyers.history, data=data)
    
    if "candles" not in response:
        raise ValueError(f"Unexpected API response: {response}")
        
    df = pd.DataFrame(response['candles'], columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
    
    # Calculate indicators
    df['RSI'] = talib.RSI(df['close'], timeperiod=14)
    df['Upper'], df['Middle'], df['Lower'] = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2, nbdevdn=2)
    return df.iloc[-1]

# ==========================================
# 4. MAIN EVENT LOOP
# ==========================================
print(f"🚀 Bot Initialized. Paper Trading: {PAPER_TRADING}")
trade_active = False
trade_side = None
trade_entry_price = 0.0  # Added to track entry for PnL calculation

while True:
    now = datetime.now().time()
    
    if dt_time(9, 15) <= now <= dt_time(15, 30):
        try:
            latest = get_indicators()
            close, rsi, lower, upper, middle = latest['close'], latest['RSI'], latest['Lower'], latest['Upper'], latest['Middle']
            
            if not trade_active:
                if rsi < 30 and close <= lower:
                    place_order("LONG")
                    trade_active, trade_side = True, "LONG"
                    trade_entry_price = close
                elif rsi > 70 and close >= upper:
                    place_order("SHORT")
                    trade_active, trade_side = True, "SHORT"
                    trade_entry_price = close
            else:
                if (trade_side == "LONG" and close >= middle) or (trade_side == "SHORT" and close <= middle):
                    place_order("SELL" if trade_side == "LONG" else "BUY")
                    
                    # --- P&L CALCULATION ---
                    points_captured = (close - trade_entry_price) if trade_side == "LONG" else (trade_entry_price - close)
                    pnl_pct = (points_captured / trade_entry_price) * 100
                    pnl_absolute = points_captured * QTY
                    
                    # LOG THE TRADE TO CSV
                    log_backtest_pnl(TICKER, trade_side, trade_entry_price, close, round(pnl_pct, 2), round(pnl_absolute, 2), "15m")
                    print(f"✅ EXIT: {TICKER} | PnL: {round(pnl_pct, 2)}% | Absolute ₹: {round(pnl_absolute, 2)}")
                    
                    # Reset variables for the next trade
                    trade_active = False
                    trade_side = None
                    trade_entry_price = 0.0
                    
        except Exception as e:
            print(f"❌ Error during execution: {e}")
            
        time.sleep(POLLING_INTERVAL) 
    else:
        print("Market closed. Bot sleeping for 5 minutes...")
        time.sleep(300)