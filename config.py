from typing import Dict, List

# Market hours configuration
MARKET_START_TIME = "09:15:01" # correct it later
MARKET_END_TIME = "15:30:00"
COLLECTION_INTERVAL = 60  # select the number of seconds 1 min so 60 seconds
START_TIME_OFFSET = 1 # Number of seconds after each minute to start data collection

#we can fetch option chain data in 3 seconds via APIs because it takes time to reflect the oi data

# Index options configuration
INDEX_OPTIONS = {
    "NIFTY": {
        "exchange": "INDEX",
        "num_expiries": 2,
        "num_strikes": 25,  # Number of strikes above and below ATM
        "strike_gap": 50,  # Gap between strikes
    },
    # "BANKNIFTY": {
    #     "exchange": "INDEX",
    #     "num_expiries": 1,
    #     "num_strikes": 20,  # Number of strikes above and below ATM
    #     "strike_gap": 100,  # Gap between strikes
    # },
    "SENSEX": {
        "exchange": "INDEX",
        "num_expiries": 1,
        "num_strikes": 20,  # Number of strikes above and below ATM
        "strike_gap": 100,  # Gap between strikes
    },

}

# Stock options configuration
STOCK_OPTIONS = {
    "RELIANCE": {
        "exchange": "NSE",
        "num_expiries": 1,
        "num_strikes": 20,  # Number of strikes above and below ATM
        "strike_gap": 10,  # Gap between strikes
    },
    # "KOTAKBANK": {
    #     "exchange": "NSE",
    #     "num_expiries": 1,
    #     "num_strikes": 20,  # Number of strikes above and below ATM
    #     "strike_gap": 20,  # Gap between strikes
    # },
    #     "INFY": {
    #     "exchange": "NSE",
    #     "num_expiries": 50,
    #     "num_strikes": 5,  # Number of strikes above and below ATM
    #     "strike_gap": 20,  # Gap between strikes
    # },
    #     "SBIN": {
    #     "exchange": "NSE",
    #     "num_expiries": 1,
    #     "num_strikes": 5,  # Number of strikes above and below ATM
    #     "strike_gap": 10,  # Gap between strikes
    # },
    #     "HDFCBANK": {
    #     "exchange": "NSE",
    #     "num_expiries": 1,
    #     "num_strikes": 5,  # Number of strikes above and below ATM
    #     "strike_gap": 20,  # Gap between strikes
    # },
    #     "TATAMOTORS": {
    #     "exchange": "NSE",
    #     "num_expiries": 1,
    #     "num_strikes": 5,  # Number of strikes above and below ATM
    #     "strike_gap": 10,  # Gap between strikes
    # },
    #     "CANBK": {
    #     "exchange": "NSE",
    #     "num_expiries": 1,
    #     "num_strikes": 10,  # Number of strikes above and below ATM
    #     "strike_gap": 1,  # Gap between strikes
    # },
    #     "COALINDIA": {
    #     "exchange": "NSE",
    #     "num_expiries": 1,
    #     "num_strikes": 5,  # Number of strikes above and below ATM
    #     "strike_gap": 5,  # Gap between strikes
    # },



    # Add more stocks here as needed
}

# Combine all symbols
ALL_SYMBOLS = {**INDEX_OPTIONS, **STOCK_OPTIONS}





# Logging configuration
LOG_CONFIG = {
    "log_file": "option_chain.log",
    "max_bytes": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5
}

