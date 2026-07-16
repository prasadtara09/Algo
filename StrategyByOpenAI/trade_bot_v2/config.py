from dotenv import load_dotenv
import os

load_dotenv()

# ------------------------
# Broker
# ------------------------

FYERS_CLIENT_ID = os.getenv("FYERS_CLIENT_ID")

FYERS_SECRET_KEY = os.getenv("FYERS_SECRET_KEY")

FYERS_REDIRECT_URI = os.getenv("FYERS_REDIRECT_URI")

FYERS_ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN")

# ------------------------
# Trading
# ------------------------

MODE = os.getenv("MODE", "PAPER")

CAPITAL = float(os.getenv("CAPITAL", "100000"))

RISK_PER_TRADE = float(
    os.getenv("RISK_PER_TRADE", "0.01")
)

MAX_OPEN_POSITIONS = int(
    os.getenv("MAX_OPEN_POSITIONS", "5")
)

TIMEFRAME = "15"

# ------------------------
# Strategy
# ------------------------

EMA_FAST = 20

EMA_SLOW = 50

RSI_PERIOD = 14

ADX_PERIOD = 14

ATR_PERIOD = 14

VWAP = True

ATR_STOP = 1.5

ATR_TARGET = 3

MIN_LOOKBACK = 50

# ------------------------
# Scanner
# ------------------------

UNIVERSE = "NIFTY200"

SCAN_INTERVAL = 15

# ------------------------
# Database
# ------------------------

DATABASE = "database/trading.db"

LOGFILE = "logs/tradebot.log"

# ------------------------
# Signal Settings
# ------------------------

MIN_SIGNAL_SCORE = 90

ATR_STOP = 1.5

ATR_TARGET = 3.0

# -----------------------
# Capital
# -----------------------

CAPITAL = 100000

RISK_PER_TRADE = 0.01

MAX_OPEN_POSITIONS = 5

# =========================
# Account Settings
# =========================

INITIAL_CAPITAL = 100000

RISK_PER_TRADE = 0.01      # 1%

MAX_OPEN_TRADES = 5

BROKERAGE_PER_ORDER = 20

SLIPPAGE = 0.0005
