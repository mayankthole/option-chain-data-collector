import asyncio
from Dhan_Tradehull import Tradehull
import pandas as pd
import time
from datetime import datetime, timedelta
import os
import ssl
import certifi
import traceback
from dotenv import load_dotenv
import signal
import sys
from config import (
    ALL_SYMBOLS, MARKET_START_TIME,
    MARKET_END_TIME, COLLECTION_INTERVAL,
    START_TIME_OFFSET
)
from utils import (
    setup_logging,
    round_to_minute, get_current_time,
    calculate_next_run_time
)
from database import (
    create_tables, insert_option_chain_data
)

# Load environment variables
load_dotenv()

# Configure SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl._create_default_https_context = lambda: ssl_context

# Initialize Tradehull client with environment variables
client_code = os.getenv('DHAN_CLIENT_CODE')
token_id = os.getenv('DHAN_TOKEN_ID')
tsl = Tradehull(client_code, token_id)

def save_option_chain_data(df, expiry_date, fetch_time, symbol):
    """Save option chain data to PostgreSQL database organized by expiry date"""
    try:
        # Add required columns if they don't exist
        df['Symbol'] = symbol
        df['expiry_date'] = expiry_date
        df['fetch_time'] = fetch_time
        
        # Ensure timestamp is rounded to minute
        current_time = datetime.now()
        df['timestamp'] = round_to_minute(current_time).strftime('%H:%M:00')
        
        # Define the exact column order we want
        column_order = [
            'Symbol', 'expiry_date', 'fetch_time', 'Spot Price', 'ATM Strike',
            'CE OI', 'CE Chg in OI', 'CE Volume', 'CE IV', 'CE LTP',
            'CE Bid Qty', 'CE Bid', 'CE Ask', 'CE Ask Qty',
            'CE Delta', 'CE Theta', 'CE Gamma', 'CE Vega',
            'Strike Price',
            'PE Bid Qty', 'PE Bid', 'PE Ask', 'PE Ask Qty',
            'PE LTP', 'PE IV', 'PE Volume', 'PE Chg in OI', 'PE OI',
            'PE Delta', 'PE Theta', 'PE Gamma', 'PE Vega',
            'timestamp'
        ]
        
        # Reorder columns and ensure all required columns exist
        for col in column_order:
            if col not in df.columns:
                df[col] = None  # Fill missing columns with None
        
        # Reorder columns to match the required order
        df = df[column_order]
        
        # Insert data into PostgreSQL
        records_inserted = insert_option_chain_data(symbol, expiry_date, df)
        
        print(f"Successfully inserted {records_inserted} records to PostgreSQL for {symbol}_{expiry_date}")
        print(f"Number of strikes saved: {len(df)}")
        
    except Exception as e:
        print(f"Error saving data to PostgreSQL: {str(e)}")
        print("Full error details:", e.__class__.__name__)
        print("Traceback:", traceback.format_exc())

def get_initial_data(symbol):
    """Get LTP only"""
    try:
        # Get LTP
        start_time = time.time()
        ltp = tsl.get_ltp_data(names=symbol)
        end_time = time.time()
        # print(f"LTP API call took: {end_time - start_time:.3f} seconds")
        time.sleep(0)  # No delay after LTP
        
        spot_price = None
        if ltp and isinstance(ltp, dict):
            spot_price = ltp.get(symbol)
            msg = f"Current {symbol} spot price: {spot_price}"
            logger.info(msg)
            # print(msg)
        
        if spot_price is None:
            msg = f"Warning: Could not fetch {symbol} spot price"
            logger.warning(msg)
            # print(msg)
            return None
            
        return spot_price
            
    except Exception as e:
        msg = f"{symbol} - Error getting LTP: {str(e)}"
        logger.error(msg)
        # print(msg)
        return None

def fetch_symbol_data(symbol):
    """Fetch and save option chain data for a given symbol"""
    try:
        symbol_config = ALL_SYMBOLS[symbol]
        msg = f"Starting data fetch for {symbol}"
        logger.info(msg)
        # print(msg)
        
        # Get LTP only once
        spot_price = get_initial_data(symbol)
        if spot_price is None:
            return

        # Process each expiry
        for expiry_index in range(symbol_config['num_expiries']):
            try:
                # Add delay between expiries (except for first expiry)
                if expiry_index > 0:
                    time.sleep(0)  # No delay between expiries
                    
                # Get ATM strike for this expiry
                try:
                    start_time = time.time()
                    ce_name, pe_name, atm_strike = tsl.ATM_Strike_Selection(
                        Underlying=symbol,
                        Expiry=expiry_index
                    )
                    end_time = time.time()
                    # print(f"ATM API call took: {end_time - start_time:.3f} seconds")
                    time.sleep(0)  # No delay after ATM
                    
                    msg = f"\n{symbol} - ATM Strike for expiry {expiry_index}: {atm_strike}"
                    logger.info(msg)
                    # print(msg)
                except Exception as e:
                    msg = f"{symbol} - ATM_Strike_Selection failed for expiry {expiry_index}: {str(e)}"
                    logger.warning(msg)
                    # print(msg)
                    # Calculate ATM strike based on symbol type
                    if symbol in ["NIFTY", "BANKNIFTY"]:
                        strike_gap = ALL_SYMBOLS[symbol]['strike_gap']
                        atm_strike = round(spot_price / strike_gap) * strike_gap
                    else:
                        strike_gap = ALL_SYMBOLS[symbol]['strike_gap']
                        atm_strike = round(spot_price / strike_gap) * strike_gap
                    msg = f"{symbol} - Using fallback ATM Strike: {atm_strike}"
                    logger.info(msg)
                    # print(msg)
                
                msg = f"\n{symbol} - Processing expiry index: {expiry_index}"
                logger.info(msg)
                # print(msg)
                msg = f"{symbol} - Using spot price: {spot_price}, ATM Strike: {atm_strike}"
                logger.info(msg)
                # print(msg)
                
                # Get option chain data
                start_time = time.time()
                option_chain = tsl.get_option_chain(
                    Underlying=symbol,
                    exchange=symbol_config['exchange'],
                    expiry=expiry_index,
                    num_strikes=symbol_config['num_strikes']
                )
                end_time = time.time()
                # print(f"Option Chain API call took: {end_time - start_time:.3f} seconds")
                time.sleep(0)  # No delay after option chain
                
                if option_chain is not None and isinstance(option_chain, tuple) and len(option_chain) > 1:
                    metadata, df = option_chain
                    
                    # Add spot price and ATM strike
                    df.insert(0, 'Spot Price', spot_price)
                    df.insert(1, 'ATM Strike', atm_strike)
                    
                    # Add timestamp
                    current_time = datetime.now()
                    df['timestamp'] = round_to_minute(current_time).strftime('%H:%M:00')
                    
                    # Extract expiry date from option names
                    expiry_date = None
                    try:
                        parts = ce_name.split()
                        if len(parts) >= 4:
                            expiry_date = ' '.join(parts[1:3])
                    except Exception as e:
                        msg = f"{symbol} - Error parsing expiry date: {e}"
                        logger.error(msg)
                        # print(msg)
                        expiry_date = f"Expiry_{expiry_index}"
                    
                    # Save to PostgreSQL
                    save_option_chain_data(
                        df, 
                        expiry_date, 
                        current_time.strftime('%Y-%m-%d %H:%M:%S'),
                        symbol
                    )
                    msg = f"{symbol} - Data saved for expiry: {expiry_date}"
                    logger.info(msg)
                    # print(msg)
                    msg = f"{symbol} - Number of strikes saved: {len(df)}"
                    logger.info(msg)
                    # print(msg)
                else:
                    msg = f"{symbol} - Failed to fetch option chain data for expiry index {expiry_index}"
                    logger.error(msg)
                    # print(msg)
                    
            except Exception as e:
                msg = f"{symbol} - Error processing expiry index {expiry_index}: {str(e)}"
                logger.error(msg)
                # print(msg)
                logger.error(f"{symbol} - Full error details:", exc_info=True)
                
    except Exception as e:
        msg = f"{symbol} - Error occurred: {str(e)}"
        logger.error(msg)
        # print(msg)
        logger.error(f"{symbol} - Full error details:", exc_info=True)

def signal_handler(signum, frame):
    print("Received signal to stop. Cleaning up...")
    sys.exit(0)

def main():
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Set up logging first
    global logger
    logger = setup_logging()
    logger.info("Starting option chain data collection...")
    
    # Create database tables and schemas
    try:
        create_tables()
        logger.info("Database tables and schemas created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        sys.exit(1)
    
    # Convert market times to datetime.time objects
    market_start = datetime.strptime(MARKET_START_TIME, "%H:%M:%S").time()
    market_end = datetime.strptime(MARKET_END_TIME, "%H:%M:%S").time()
    
    # Wait until the next minute's specified second before starting
    current_time = datetime.now()
    next_minute = (current_time + timedelta(minutes=1)).replace(second=START_TIME_OFFSET, microsecond=0)
    initial_wait = (next_minute - current_time).total_seconds()
    if initial_wait > 0:
        logger.info(f"Waiting {initial_wait:.2f} seconds until first data collection at {next_minute.strftime('%H:%M:%S')}")
        time.sleep(initial_wait)
    
    while True:
        try:
            current_time = datetime.now()
            current_time_str = current_time.strftime("%H:%M:%S")
            
            # Check if it's weekend
            if current_time.weekday() >= 5:  # 5 is Saturday, 6 is Sunday
                logger.info(f"Market closed: Weekend - {current_time_str}")
                next_day = current_time + timedelta(days=1)
                next_day = next_day.replace(
                    hour=int(MARKET_START_TIME[:2]),
                    minute=int(MARKET_START_TIME[3:5]),
                    second=int(MARKET_START_TIME[6:8]),
                    microsecond=0
                )
                sleep_seconds = (next_day - current_time).total_seconds()
                logger.info(f"Sleeping until next trading day: {next_day.strftime('%Y-%m-%d %H:%M:%S')}")
                time.sleep(sleep_seconds)
                continue
            
            # If before market open, sleep until market open
            if current_time.time() < market_start:
                next_run = current_time.replace(
                    hour=int(MARKET_START_TIME[:2]),
                    minute=int(MARKET_START_TIME[3:5]),
                    second=int(MARKET_START_TIME[6:8]),
                    microsecond=0
                )
                sleep_seconds = (next_run - current_time).total_seconds()
                logger.info(f"Market not open yet. Sleeping until market open: {next_run.strftime('%H:%M:%S')}")
                time.sleep(sleep_seconds)
                continue
            
            # If after market close, sleep until next trading day
            if current_time.time() > market_end:
                next_day = current_time + timedelta(days=1)
                next_day = next_day.replace(
                    hour=int(MARKET_START_TIME[:2]),
                    minute=int(MARKET_START_TIME[3:5]),
                    second=int(MARKET_START_TIME[6:8]),
                    microsecond=0
                )
                sleep_seconds = (next_day - current_time).total_seconds()
                logger.info(f"Market closed for today. Sleeping until next trading day: {next_day.strftime('%Y-%m-%d %H:%M:%S')}")
                time.sleep(sleep_seconds)
                continue
            
            # Market is open, proceed with data collection
            logger.info(f"Starting new cycle at: {current_time_str}")
            
            # Process symbols sequentially
            symbols = list(ALL_SYMBOLS.keys())
            for symbol in symbols:
                msg = f"Processing symbol: {symbol}"
                logger.info(msg)
                # print(msg)
                fetch_symbol_data(symbol)
                time.sleep(0)  # No delay between symbols
            
            # Calculate time taken for this cycle
            cycle_end_time = datetime.now()
            time_taken = (cycle_end_time - current_time).total_seconds()
            logger.info(f"Cycle completed in {time_taken:.2f} seconds")
            
            # Calculate next run time using COLLECTION_INTERVAL from config
            next_minute = (cycle_end_time + timedelta(seconds=COLLECTION_INTERVAL))
            next_run = next_minute.replace(second=START_TIME_OFFSET, microsecond=0)
            wait_time = (next_run - cycle_end_time).total_seconds()
            
            if wait_time > 0:
                logger.info(f"Waiting {wait_time:.2f} seconds until next cycle at {next_run.strftime('%H:%M:%S')}")
                time.sleep(wait_time)
            
        except KeyboardInterrupt:
            logger.info("Stopping data collection...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            logger.error("Full error details:", exc_info=True)
            # Sleep for 1 minute before retrying
            time.sleep(60)

if __name__ == "__main__":
    main()
