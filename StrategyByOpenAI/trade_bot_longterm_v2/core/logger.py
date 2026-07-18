import logging
import os

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("TradeBot")

logger.setLevel(logging.INFO)

formatter = logging.Formatter(

    "%(asctime)s | %(levelname)s | %(message)s"

)

file_handler = logging.FileHandler(

    "logs/tradebot.log"

)

file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()

console_handler.setFormatter(formatter)

logger.addHandler(file_handler)

logger.addHandler(console_handler)