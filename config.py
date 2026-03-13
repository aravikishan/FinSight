"""Application configuration for FinSight."""

import os

# Server
HOST = "0.0.0.0"
PORT = int(os.environ.get("FINSIGHT_PORT", 8001))
DEBUG = os.environ.get("FINSIGHT_DEBUG", "false").lower() == "true"

# Database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "instance", "finsight.db")
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL", f"sqlite:///{DATABASE_PATH}"
)

# Market simulation
DEFAULT_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM",
    "V", "JNJ", "WMT", "PG", "MA", "UNH", "HD", "DIS", "BAC",
    "XOM", "KO", "PFE", "NFLX", "INTC",
]

SIMULATION_DAYS = 252  # One trading year
INITIAL_PORTFOLIO_CASH = 100_000.00

# Technical indicator defaults
SMA_PERIODS = [20, 50, 200]
EMA_PERIODS = [12, 26]
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2

# Sentiment
SENTIMENT_DECAY = 0.95
SENTIMENT_CATEGORIES = ["bullish", "bearish", "neutral"]

# Testing
TESTING = False
