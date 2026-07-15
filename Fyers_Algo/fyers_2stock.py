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
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCcVZ2ckFNZTNUVUtPRXEwcUluREV6Zm5lMlJMRmN2enNFWVhaZWxIUnpMX0I1NnJvemZzX2xSTFNfZW1hbzA4VGN1U1I4OEZwUEt2eUQ3TFhhaHE5Q3VxTmNBLW1nWjBMcmsxa2dNSHNLRTZ4cXRxUT0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJmMzE3NjkzMDk2Y2E5MTExYmFlNWE3YjFiNDg3OGI0NmI4NTNmOTAwMzVjYjNkZWRlZGM4YmNhOCIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFQwNjczOCIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzg0MTYxODAwLCJpYXQiOjE3ODQwODUxODQsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc4NDA4NTE4NCwic3ViIjoiYWNjZXNzX3Rva2VuIn0.Ch5tkOsXUzcR79EfUmD1XU7yxN1wcOB-Yl8URvm1oGY" # ⚠️ REMEMBER TO REGENERATE YOUR TOKEN
TICKERS = ["NSE:EASEMYTRIP-EQ", "NSE:IDEA-EQ"] 
QTY = 10
PAPER_TRADING = True  # SET TO FALSE ONLY WHEN READY FOR REAL MONEY

fyers = fyersModel.FyersModel(client_id=CLIENT_ID, token=ACCESS_TOKEN)
active_trades = {ticker: {"active": False, "side": None} for ticker in TICKERS}

def log_backtest_pnl(ticker, side, entry, exit_price, pnl_pct, pnl_abs, timeframe):
    """
    Logs the trade outcome to a CSV. 
    pnl_abs is the raw currency amount required by the Monte Carlo simulator.
    """
    file_exists = os.path.isfile('backtest_ledger.csv')
    with open('backtest_ledger.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            # Added PnL_Absolute column for the Quant Simulator
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
        
        while self.second_window and now - self.second_window[0] >= 1:
            self.second_window.popleft()
        while self.minute_window and now - self.minute_window[0] >= 60:
            self.minute_window.popleft()

        if self.daily_calls >= 100000:
            raise Exception("❌ CRITICAL: Daily API limit reached (100,000). Shutting down.")

        if len(self.minute_window) >= 195: 
            sleep_time = 60 - (now - self.minute_window[0])
            print(f"⏳ Minute limit nearing. Throttling API for {sleep_time:.2f}s...")
            time.sleep(max(0.1, sleep_time))
            now = time.time()

        if len(self.second_window) >= 9: 
            sleep_time = 1 - (now - self.second_window[0])
            time.sleep(max(0.1, sleep_time))
            now = time.time()

        self.second_window.append(now)
        self.minute_window.append(now)
        self.daily_calls += 1

limiter = FyersRateLimiter()

def api_call(func, *args, **kwargs):
    """Wrapper to route all Fyers calls through the rate limiter."""
    limiter.wait_if_needed()
    current_time = datetime.now().strftime("%H:%M:%S")
    symbol_log = f" for {kwargs['data']['symbol']}" if "data" in kwargs and "symbol" in kwargs["data"] else ""
        
    print(f"📡 [{current_time}] API Requesting: {func.__name__}{symbol_log}...")
    return func(*args, **kwargs)

# ==========================================
# 3. TRADING LOGIC
# ==========================================
def place_order(ticker, side):
    if PAPER_TRADING:
        print(f"⚠️ [PAPER TRADE] Simulating {side} order for {QTY} shares of {ticker}")
        return {"status": "success"}
    else:
        order_params = {
            "symbol": ticker, "qty": QTY, "type": 2, 
            "side": 1 if side == "LONG" else -1,
            "productType": "INTRADAY", "validity": "DAY"
        }
        return api_call(fyers.place_order, data=order_params)

def get_indicators(ticker):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    data = {
        "symbol": ticker,
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
    df['RSI'] = talib.RSI(df['close'], timeperiod=14)
    df['Upper'], df['Middle'], df['Lower'] = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2, nbdevdn=2)
    return df.iloc[-1]

# ==========================================
# 4. MAIN EVENT LOOP
# ==========================================
print(f"🚀 Bot Initialized. Paper Trading: {PAPER_TRADING}")

while True:
    now = datetime.now().time()
    
    if dt_time(9, 15) <= now <= dt_time(15, 30):
        try:
            for ticker in TICKERS:
                latest = get_indicators(ticker) 
                close, rsi, lower, upper, middle = latest['close'], latest['RSI'], latest['Lower'], latest['Upper'], latest['Middle']
                
                trade_state = active_trades[ticker]
                
                if not trade_state["active"]:
                    if rsi < 30 and close <= lower:
                        place_order(ticker, "LONG") 
                        active_trades[ticker] = {"active": True, "side": "LONG", "entry": close}
                    elif rsi > 70 and close >= upper:
                        place_order(ticker, "SHORT")
                        active_trades[ticker] = {"active": True, "side": "SHORT", "entry": close}
                else:
                    if (trade_state["side"] == "LONG" and close >= middle) or \
                       (trade_state["side"] == "SHORT" and close <= middle):
                        place_order(ticker, "SELL" if trade_state["side"] == "LONG" else "BUY")
                        
                        # --- MODIFIED P&L CALCULATION ---
                        entry_price = trade_state["entry"]
                        
                        # Points gained or lost per share
                        points_captured = (close - entry_price) if trade_state["side"] == "LONG" else (entry_price - close)
                        
                        # Percentage PnL
                        pnl_pct = (points_captured / entry_price) * 100
                        
                        # Absolute PnL (Points * Quantity) -> This is what the Quant Simulator needs!
                        pnl_absolute = points_captured * QTY
                        
                        # LOG THE TRADE TO CSV
                        log_backtest_pnl(ticker, trade_state["side"], entry_price, close, round(pnl_pct, 2), round(pnl_absolute, 2), "15m")
                        
                        print(f"✅ EXIT: {ticker} | PnL: {round(pnl_pct, 2)}% | Absolute ₹: {round(pnl_absolute, 2)}")
                        active_trades[ticker] = {"active": False, "side": None}
                
                print(f"⏳ Sleeping 30s before checking next ticker...")
                time.sleep(30)
                
        except Exception as e:
            print(f"❌ Error during execution: {e}")
            time.sleep(30) 
            
    else:
        print("Market closed. Bot sleeping for 5 minutes...")
        time.sleep(300)