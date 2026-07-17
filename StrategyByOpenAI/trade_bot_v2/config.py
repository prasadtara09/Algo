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
# Maximum simultaneous holdings; set this in .env (for example, 3).
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
# False lets the scanner download missing candles. Set true for offline runs.
SCANNER_CACHE_ONLY = os.getenv("SCANNER_CACHE_ONLY", "false").strip().lower() in {"1", "true", "yes"}
DATA_PROVIDER = os.getenv("DATA_PROVIDER", "AUTO").upper()

# Intraday session guardrails. Candle timestamps represent the start of a
# 15-minute bar, so the square-off is executed at the 15:15 bar open.
INTRADAY_ONLY = os.getenv("INTRADAY_ONLY", "true").strip().lower() in {"1", "true", "yes"}
# Selective profile: avoid the volatile open and late-session whipsaws.
INTRADAY_ENTRY_START = os.getenv("INTRADAY_ENTRY_START", "10:00")
INTRADAY_LAST_ENTRY = os.getenv("INTRADAY_LAST_ENTRY", "13:45")
INTRADAY_SQUARE_OFF = os.getenv("INTRADAY_SQUARE_OFF", "15:15")
MAX_TRADES_PER_SYMBOL_PER_DAY = int(os.getenv("MAX_TRADES_PER_SYMBOL_PER_DAY", "1"))

# Multi-timeframe trend-and-volume-breakout strategy settings.
EMA_FAST = int(os.getenv("EMA_FAST", "20"))
EMA_SLOW = int(os.getenv("EMA_SLOW", "50"))
HTF_EMA_FAST = int(os.getenv("HTF_EMA_FAST", "20"))
HTF_EMA_SLOW = int(os.getenv("HTF_EMA_SLOW", "50"))
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
RSI_MIN = float(os.getenv("RSI_MIN", "58"))
RSI_MAX = float(os.getenv("RSI_MAX", "68"))
SHORT_RSI_MIN = float(os.getenv("SHORT_RSI_MIN", "32"))
SHORT_RSI_MAX = float(os.getenv("SHORT_RSI_MAX", "42"))
ADX_PERIOD = int(os.getenv("ADX_PERIOD", "14"))
ADX_MIN = float(os.getenv("ADX_MIN", "25"))
ATR_PERIOD = int(os.getenv("ATR_PERIOD", "14"))
ATR_STOP = float(os.getenv("ATR_STOP", "1.5"))
ATR_TARGET = float(os.getenv("ATR_TARGET", "3.0"))
BREAKOUT_LOOKBACK = int(os.getenv("BREAKOUT_LOOKBACK", "20"))
VOLUME_LOOKBACK = int(os.getenv("VOLUME_LOOKBACK", "20"))
VOLUME_MULTIPLIER = float(os.getenv("VOLUME_MULTIPLIER", "1.75"))
MIN_SIGNAL_SCORE = int(os.getenv("MIN_SIGNAL_SCORE", "90"))
# A breakout must be meaningful but not already too extended, and the candle
# body must show conviction rather than an intrabar spike.
BREAKOUT_MIN_ATR = float(os.getenv("BREAKOUT_MIN_ATR", "0.10"))
BREAKOUT_MAX_ATR = float(os.getenv("BREAKOUT_MAX_ATR", "1.00"))
MIN_CANDLE_BODY_PCT = float(os.getenv("MIN_CANDLE_BODY_PCT", "0.60"))
# Enter only after price retests a confirmed breakout level, rather than on the
# initial breakout candle where false moves are most common.
RETEST_LOOKBACK = int(os.getenv("RETEST_LOOKBACK", "2"))
RETEST_TOLERANCE_ATR = float(os.getenv("RETEST_TOLERANCE_ATR", "0.15"))
RETEST_CLOSE_BUFFER_ATR = float(os.getenv("RETEST_CLOSE_BUFFER_ATR", "0.10"))

# Long-only swing trades are permitted only when the broad market is healthy.
# Optional research filter. It is disabled by default until it improves the
# full-universe out-of-sample result.
SWING_REQUIRE_MARKET_REGIME = os.getenv("SWING_REQUIRE_MARKET_REGIME", "false").strip().lower() in {"1", "true", "yes"}
SWING_MARKET_FAST_EMA = int(os.getenv("SWING_MARKET_FAST_EMA", "50"))
SWING_MARKET_SLOW_EMA = int(os.getenv("SWING_MARKET_SLOW_EMA", "200"))
SWING_REQUIRE_STOCK_LONG_TREND = os.getenv("SWING_REQUIRE_STOCK_LONG_TREND", "false").strip().lower() in {"1", "true", "yes"}
MIN_LOOKBACK = max(EMA_SLOW, BREAKOUT_LOOKBACK, VOLUME_LOOKBACK)

DATABASE = os.getenv("DATABASE", "database/trading.db")
LOGFILE = os.getenv("LOGFILE", "logs/tradebot.log")
