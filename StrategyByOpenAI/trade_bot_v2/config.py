"""Runtime configuration for the paper-trading and backtest components."""

import os

from dotenv import load_dotenv

load_dotenv()

# Broker credentials are read only by broker-specific code.
FYERS_CLIENT_ID = os.getenv("FYERS_CLIENT_ID")
FYERS_SECRET_KEY = os.getenv("FYERS_SECRET_KEY")
FYERS_REDIRECT_URI = os.getenv("FYERS_REDIRECT_URI")
FYERS_ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN")

# Execution and account settings. LIVE mode is deliberately not the default.
MODE = os.getenv("MODE", "PAPER").upper()
INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", "100000"))
CAPITAL = INITIAL_CAPITAL
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.005"))
MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "5"))
MAX_OPEN_TRADES = MAX_OPEN_POSITIONS
MAX_POSITION_VALUE_PCT = float(os.getenv("MAX_POSITION_VALUE_PCT", "0.20"))
MAX_DAILY_LOSS_PCT = float(os.getenv("MAX_DAILY_LOSS_PCT", "0.03"))
MAX_WEEKLY_LOSS_PCT = float(os.getenv("MAX_WEEKLY_LOSS_PCT", "0.06"))
BROKERAGE_PER_ORDER = float(os.getenv("BROKERAGE_PER_ORDER", "20"))
SLIPPAGE = float(os.getenv("SLIPPAGE", "0.0005"))

# Data and scanner settings.
TIMEFRAME = os.getenv("TIMEFRAME", "15m")
HIGHER_TIMEFRAME = os.getenv("HIGHER_TIMEFRAME", "60min")
UNIVERSE = os.getenv("UNIVERSE", "NIFTY200")
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "15"))
SCANNER_MAX_SIGNALS = int(os.getenv("SCANNER_MAX_SIGNALS", "20"))
SCANNER_CACHE_ONLY = os.getenv("SCANNER_CACHE_ONLY", "true").strip().lower() in {"1", "true", "yes"}

# Multi-timeframe trend-and-volume-breakout strategy settings.
EMA_FAST = int(os.getenv("EMA_FAST", "20"))
EMA_SLOW = int(os.getenv("EMA_SLOW", "50"))
HTF_EMA_FAST = int(os.getenv("HTF_EMA_FAST", "20"))
HTF_EMA_SLOW = int(os.getenv("HTF_EMA_SLOW", "50"))
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
RSI_MIN = float(os.getenv("RSI_MIN", "55"))
RSI_MAX = float(os.getenv("RSI_MAX", "75"))
ADX_PERIOD = int(os.getenv("ADX_PERIOD", "14"))
ADX_MIN = float(os.getenv("ADX_MIN", "20"))
ATR_PERIOD = int(os.getenv("ATR_PERIOD", "14"))
ATR_STOP = float(os.getenv("ATR_STOP", "1.5"))
ATR_TARGET = float(os.getenv("ATR_TARGET", "3.0"))
BREAKOUT_LOOKBACK = int(os.getenv("BREAKOUT_LOOKBACK", "20"))
VOLUME_LOOKBACK = int(os.getenv("VOLUME_LOOKBACK", "20"))
VOLUME_MULTIPLIER = float(os.getenv("VOLUME_MULTIPLIER", "1.5"))
MIN_SIGNAL_SCORE = int(os.getenv("MIN_SIGNAL_SCORE", "85"))
MIN_LOOKBACK = max(EMA_SLOW, BREAKOUT_LOOKBACK, VOLUME_LOOKBACK)

DATABASE = os.getenv("DATABASE", "database/trading.db")
LOGFILE = os.getenv("LOGFILE", "logs/tradebot.log")
