import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime, timedelta
from config import LOG_CONFIG

def setup_logging():
    """Set up logging configuration"""
    handler = RotatingFileHandler(
        LOG_CONFIG['log_file'],
        maxBytes=LOG_CONFIG['max_bytes'],
        backupCount=LOG_CONFIG['backup_count']
    )
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    # Also log to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def round_to_minute(dt):
    """Round datetime to the nearest minute"""
    return dt.replace(second=0, microsecond=0)

def get_current_time():
    """Get current time in HH:MM:SS format"""
    return datetime.now().strftime("%H:%M:%S")

def calculate_next_run_time(current_time, market_start_time):
    """Calculate the next run time based on current time and market start time"""
    if current_time.time() < market_start_time:
        next_run = current_time.replace(
            hour=int(market_start_time[:2]),
            minute=int(market_start_time[3:5]),
            second=int(market_start_time[6:8]),
            microsecond=0
        )
    else:
        next_run = current_time + timedelta(minutes=1)
        next_run = next_run.replace(second=2, microsecond=0)
    
    return next_run 
