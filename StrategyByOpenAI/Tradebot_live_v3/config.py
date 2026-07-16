from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("FYERS_CLIENT_ID")
SECRET_KEY = os.getenv("FYERS_SECRET_KEY")
REDIRECT_URI = os.getenv("FYERS_REDIRECT_URI")
ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN")

MODE = os.getenv("MODE", "PAPER")

TIMEFRAME = "15"

RISK_PER_TRADE = 0.01

CAPITAL = 100000

MAX_POSITIONS = 5

STOP_LOSS_ATR = 1.5

TARGET_ATR = 3

SCAN_INTERVAL = 15