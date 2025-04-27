"""
Anti-scraping utilities for the HK Job Fair Aggregator.
Provides functions for rotating user agents, proxies, and handling CAPTCHAs.
"""

import random
import time
import logging
from typing import List, Dict, Optional, Tuple, Union
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Setup logger
logger = logging.getLogger(__name__)

# List of common user agents
USER_AGENTS = [
    # Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux i686; rv:89.0) Gecko/20100101 Firefox/89.0",
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
    # Mobile
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
]

# Default headers
DEFAULT_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-HK,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

def get_random_user_agent() -> str:
    """
    Get a random user agent from the list.
    
    Returns:
        str: Random user agent string
    """
    return random.choice(USER_AGENTS)

def get_headers(custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Get headers with a random user agent.
    
    Args:
        custom_headers (dict, optional): Custom headers to add
        
    Returns:
        dict: Headers with random user agent
    """
    headers = DEFAULT_HEADERS.copy()
    headers['User-Agent'] = get_random_user_agent()
    
    if custom_headers:
        headers.update(custom_headers)
        
    return headers

def get_proxy() -> Optional[Dict[str, str]]:
    """
    Get a proxy for requests.
    This is a placeholder function. In a production environment,
    you would implement a proxy rotation service or use a proxy provider API.
    
    Returns:
        dict or None: Proxy configuration for requests
    """
    # Placeholder for proxy implementation
    # In a real implementation, you would:
    # 1. Maintain a list of proxies
    # 2. Rotate through them
    # 3. Check their health
    # 4. Handle authentication if needed
    
    # Example proxy format for requests:
    # proxies = {
    #     'http': 'http://user:pass@10.10.1.10:3128',
    #     'https': 'http://user:pass@10.10.1.10:1080',
    # }
    
    logger.info("Proxy functionality is a placeholder. No actual proxy used.")
    return None

def add_random_delay(min_delay: float = 1.0, max_delay: float = 5.0) -> None:
    """
    Add a random delay between requests to avoid rate limiting.
    
    Args:
        min_delay (float): Minimum delay in seconds
        max_delay (float): Maximum delay in seconds
    """
    delay = random.uniform(min_delay, max_delay)
    logger.debug(f"Adding random delay of {delay:.2f} seconds")
    time.sleep(delay)

def setup_selenium_driver(headless: bool = True, proxy: Optional[str] = None) -> webdriver.Chrome:
    """
    Set up a Selenium WebDriver with anti-detection measures.
    
    Args:
        headless (bool): Whether to run in headless mode
        proxy (str, optional): Proxy server to use
        
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver
    """
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless")
    
    # Add common options to avoid detection
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Set random user agent
    chrome_options.add_argument(f"user-agent={get_random_user_agent()}")
    
    # Add proxy if provided
    if proxy:
        chrome_options.add_argument(f"--proxy-server={proxy}")
    
    # Set up the service
    service = Service(ChromeDriverManager().install())
    
    # Create the driver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Execute CDP commands to avoid detection
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
    })
    
    return driver

def handle_captcha(driver: webdriver.Chrome, captcha_selector: str) -> bool:
    """
    Handle CAPTCHA detection. This is a placeholder function.
    In a production environment, you would implement a CAPTCHA solving service.
    
    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance
        captcha_selector (str): CSS selector for the CAPTCHA element
        
    Returns:
        bool: True if CAPTCHA was handled successfully, False otherwise
    """
    # Check if CAPTCHA is present
    try:
        captcha_element = driver.find_element(By.CSS_SELECTOR, captcha_selector)
        if captcha_element.is_displayed():
            logger.warning("CAPTCHA detected. This is a placeholder function.")
            logger.warning("In a production environment, implement a CAPTCHA solving service.")
            
            # Placeholder for CAPTCHA solving
            # In a real implementation, you would:
            # 1. Take a screenshot of the CAPTCHA
            # 2. Send it to a CAPTCHA solving service
            # 3. Input the solution
            # 4. Submit the form
            
            return False
    except NoSuchElementException:
        # No CAPTCHA found
        return True
    
    return False

def is_rate_limited(response: requests.Response) -> bool:
    """
    Check if a response indicates rate limiting.
    
    Args:
        response (requests.Response): Response object
        
    Returns:
        bool: True if rate limited, False otherwise
    """
    # Check status code (common rate limit status codes)
    if response.status_code in (429, 403):
        return True
    
    # Check for rate limit headers
    rate_limit_headers = [
        'X-RateLimit-Remaining',
        'RateLimit-Remaining',
        'X-Rate-Limit-Remaining'
    ]
    
    for header in rate_limit_headers:
        if header in response.headers and int(response.headers[header]) == 0:
            return True
    
    # Check content for rate limit messages
    if response.headers.get('Content-Type', '').startswith('text/html'):
        soup = BeautifulSoup(response.text, 'lxml')
        rate_limit_phrases = [
            'rate limit',
            'too many requests',
            'access denied',
            'blocked',
            'captcha'
        ]
        
        page_text = soup.get_text().lower()
        if any(phrase in page_text for phrase in rate_limit_phrases):
            return True
    
    return False

def handle_rate_limit(response: requests.Response, retry_after: int = 60) -> int:
    """
    Handle rate limiting by determining how long to wait.
    
    Args:
        response (requests.Response): Response object
        retry_after (int): Default retry delay in seconds
        
    Returns:
        int: Number of seconds to wait before retrying
    """
    # Check for Retry-After header
    if 'Retry-After' in response.headers:
        try:
            return int(response.headers['Retry-After'])
        except (ValueError, TypeError):
            pass
    
    # Check for rate limit reset headers
    rate_limit_reset_headers = [
        'X-RateLimit-Reset',
        'RateLimit-Reset',
        'X-Rate-Limit-Reset'
    ]
    
    for header in rate_limit_reset_headers:
        if header in response.headers:
            try:
                reset_time = int(response.headers[header])
                current_time = int(time.time())
                wait_time = max(0, reset_time - current_time)
                return wait_time
            except (ValueError, TypeError):
                pass
    
    # Default retry delay
    return retry_after
