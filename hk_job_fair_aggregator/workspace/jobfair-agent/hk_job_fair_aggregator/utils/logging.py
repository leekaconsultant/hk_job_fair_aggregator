"""
Logging utility for the HK Job Fair Aggregator.
Provides a consistent logging interface and retry decorator.
"""

import logging
import os
import sys
import time
from datetime import datetime
from functools import wraps
from logging.handlers import RotatingFileHandler
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configure logging
def setup_logger(name, log_level=logging.INFO):
    """
    Set up a logger with file and console handlers.
    
    Args:
        name (str): Logger name
        log_level (int): Logging level
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Prevent adding handlers multiple times
    if not logger.handlers:
        # Create a file handler
        log_file = os.path.join(logs_dir, f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setLevel(log_level)
        
        # Create a console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Create a formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add the handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# Create a retry decorator for web requests
def with_retry(max_attempts=3, min_wait=1, max_wait=10):
    """
    Decorator to retry functions with exponential backoff.
    
    Args:
        max_attempts (int): Maximum number of retry attempts
        min_wait (int): Minimum wait time in seconds
        max_wait (int): Maximum wait time in seconds
        
    Returns:
        function: Decorated function with retry logic
    """
    def decorator(func):
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type((
                ConnectionError, 
                TimeoutError, 
                Exception
            )),
            reraise=True
        )
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Main logger for the application
main_logger = setup_logger('hk_job_fair_aggregator')
