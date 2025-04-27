"""
Enhanced base scraper class for the HK Job Fair Aggregator.
Provides common functionality for all scrapers with support for:
- Different scraper types (static HTML, dynamic content with Selenium, API-based)
- Configurable update frequencies
- Anti-scraping measures (IP rotation, user-agent rotation, CAPTCHA handling)
- Proper error handling and logging
- Data validation and normalization
"""

import os
import json
import time
import logging
import random
import requests
from datetime import datetime, timedelta
import pytz
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Union, Tuple
from selenium import webdriver
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log

from hk_job_fair_aggregator.utils.logging import setup_logger
from hk_job_fair_aggregator.utils.normalizer import (
    normalize_date, 
    normalize_datetime, 
    normalize_venue_name,
    normalize_district,
    normalize_language,
    simplified_to_traditional,
    extract_contact_info,
    clean_html,
    generate_event_id,
    is_duplicate_event
)
from hk_job_fair_aggregator.utils.anti_scrape import (
    get_headers,
    get_proxy,
    add_random_delay,
    setup_selenium_driver,
    handle_captcha,
    is_rate_limited,
    handle_rate_limit
)
from hk_job_fair_aggregator.scrapers.scraper_types import ScraperType, UpdateFrequency
from hk_job_fair_aggregator.models.job_fair import JobFairEvent

class BaseScraper(ABC):
    """
    Enhanced base class for all scrapers.
    
    Attributes:
        name (str): Name of the scraper
        base_url (str): Base URL for the source
        source_id (str): Unique identifier for the source
        source_type (str): Type of source (GOVERNMENT, JOB_PORTAL, etc.)
        source_priority (str): Priority level (PRIMARY, SECONDARY)
        scraper_type (ScraperType): Type of scraper (STATIC, DYNAMIC, API)
        update_frequency (UpdateFrequency): How often to update (DAILY, WEEKLY, etc.)
        custom_schedule (str): Custom cron schedule (if update_frequency is CUSTOM)
        language (str): Primary language of the source (ZH-HK, EN, BOTH)
        logger (logging.Logger): Logger instance
        data_dir (str): Directory for storing data
        max_retries (int): Maximum number of retries for requests
        retry_delay (int): Delay between retries in seconds
        use_proxy (bool): Whether to use proxies
        selenium_driver (webdriver.Chrome): Selenium WebDriver instance (for DYNAMIC scrapers)
    """
    
    def __init__(
        self, 
        name: str,
        base_url: str,
        source_id: str,
        source_type: str,
        source_priority: str,
        scraper_type: ScraperType = ScraperType.STATIC,
        update_frequency: UpdateFrequency = UpdateFrequency.DAILY,
        custom_schedule: Optional[str] = None,
        language: str = "ZH-HK",
        max_retries: int = 3,
        retry_delay: int = 5,
        use_proxy: bool = False
    ):
        """
        Initialize the enhanced base scraper.
        
        Args:
            name (str): Name of the scraper
            base_url (str): Base URL for the source
            source_id (str): Unique identifier for the source
            source_type (str): Type of source (GOVERNMENT, JOB_PORTAL, etc.)
            source_priority (str): Priority level (PRIMARY, SECONDARY)
            scraper_type (ScraperType): Type of scraper (STATIC, DYNAMIC, API)
            update_frequency (UpdateFrequency): How often to update (DAILY, WEEKLY, etc.)
            custom_schedule (str, optional): Custom cron schedule (if update_frequency is CUSTOM)
            language (str): Primary language of the source (ZH-HK, EN, BOTH)
            max_retries (int): Maximum number of retries for requests
            retry_delay (int): Delay between retries in seconds
            use_proxy (bool): Whether to use proxies
        """
        self.name = name
        self.base_url = base_url
        self.source_id = source_id
        self.source_type = source_type
        self.source_priority = source_priority
        self.scraper_type = scraper_type
        self.update_frequency = update_frequency
        self.custom_schedule = custom_schedule
        self.language = language
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.use_proxy = use_proxy
        
        # Set up logger
        self.logger = setup_logger(f"scraper.{name.lower().replace(' ', '_')}")
        
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize Selenium driver for DYNAMIC scrapers
        self.selenium_driver = None
        if self.scraper_type == ScraperType.DYNAMIC:
            self.init_selenium_driver()
    
    def init_selenium_driver(self) -> None:
        """
        Initialize Selenium WebDriver for DYNAMIC scrapers.
        """
        if self.scraper_type != ScraperType.DYNAMIC:
            return
            
        try:
            proxy = get_proxy() if self.use_proxy else None
            proxy_str = proxy['https'] if proxy and 'https' in proxy else None
            
            self.selenium_driver = setup_selenium_driver(
                headless=True,
                proxy=proxy_str
            )
            self.logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing Selenium WebDriver: {e}", exc_info=True)
            raise
    
    def close_selenium_driver(self) -> None:
        """
        Close Selenium WebDriver if it exists.
        """
        if self.selenium_driver:
            try:
                self.selenium_driver.quit()
                self.logger.info("Selenium WebDriver closed")
            except Exception as e:
                self.logger.error(f"Error closing Selenium WebDriver: {e}", exc_info=True)
            finally:
                self.selenium_driver = None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.HTTPError)),
        before_sleep=before_sleep_log(logging.getLogger("tenacity"), logging.WARNING)
    )
    def get_page(self, url: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Get a page from the source with retry logic and anti-scraping measures.
        
        Args:
            url (str): URL to fetch
            params (dict, optional): Query parameters
            
        Returns:
            requests.Response: Response object
        """
        self.logger.info(f"Fetching page: {url}")
        
        # Get headers with random user agent
        headers = get_headers()
        
        # Get proxy if enabled
        proxies = get_proxy() if self.use_proxy else None
        
        # Add random delay to avoid rate limiting
        add_random_delay()
        
        # Make the request
        response = requests.get(
            url, 
            headers=headers, 
            params=params, 
            proxies=proxies,
            timeout=30
        )
        
        # Check for rate limiting
        if is_rate_limited(response):
            wait_time = handle_rate_limit(response)
            self.logger.warning(f"Rate limited. Waiting for {wait_time} seconds before retrying.")
            time.sleep(wait_time)
            return self.get_page(url, params)
        
        # Raise for HTTP errors
        response.raise_for_status()
        
        return response
    
    def get_dynamic_page(self, url: str, wait_for_selector: Optional[str] = None, wait_time: int = 10) -> str:
        """
        Get a dynamic page using Selenium.
        
        Args:
            url (str): URL to fetch
            wait_for_selector (str, optional): CSS selector to wait for
            wait_time (int): Time to wait for the selector in seconds
            
        Returns:
            str: Page HTML content
        """
        if self.scraper_type != ScraperType.DYNAMIC:
            raise ValueError("This method is only available for DYNAMIC scrapers")
            
        if not self.selenium_driver:
            self.init_selenium_driver()
            
        self.logger.info(f"Fetching dynamic page: {url}")
        
        try:
            # Navigate to the URL
            self.selenium_driver.get(url)
            
            # Wait for specific element if selector provided
            if wait_for_selector:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                WebDriverWait(self.selenium_driver, wait_time).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                )
            else:
                # Otherwise, just wait a fixed amount of time
                time.sleep(wait_time)
            
            # Check for CAPTCHA
            captcha_handled = handle_captcha(self.selenium_driver, "img[alt*='captcha'], .captcha, #captcha")
            if not captcha_handled:
                self.logger.warning("CAPTCHA detected but not handled. Results may be incomplete.")
            
            # Get the page source
            return self.selenium_driver.page_source
            
        except Exception as e:
            self.logger.error(f"Error fetching dynamic page {url}: {e}", exc_info=True)
            raise
    
    def get_api_data(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Get data from an API endpoint.
        
        Args:
            url (str): API URL to fetch
            params (dict, optional): Query parameters
            headers (dict, optional): Custom headers
            
        Returns:
            dict: JSON response data
        """
        if self.scraper_type != ScraperType.API:
            raise ValueError("This method is only available for API scrapers")
            
        self.logger.info(f"Fetching API data: {url}")
        
        # Get default headers with random user agent
        default_headers = get_headers()
        
        # Add custom headers
        if headers:
            default_headers.update(headers)
        
        # Add JSON content type if not specified
        if 'Content-Type' not in default_headers:
            default_headers['Content-Type'] = 'application/json'
            
        # Get proxy if enabled
        proxies = get_proxy() if self.use_proxy else None
        
        # Add random delay to avoid rate limiting
        add_random_delay()
        
        # Make the request
        response = requests.get(
            url, 
            headers=default_headers, 
            params=params, 
            proxies=proxies,
            timeout=30
        )
        
        # Check for rate limiting
        if is_rate_limited(response):
            wait_time = handle_rate_limit(response)
            self.logger.warning(f"Rate limited. Waiting for {wait_time} seconds before retrying.")
            time.sleep(wait_time)
            return self.get_api_data(url, params, headers)
        
        # Raise for HTTP errors
        response.raise_for_status()
        
        # Parse JSON response
        return response.json()
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML content.
        
        Args:
            html (str): HTML content
            
        Returns:
            BeautifulSoup: BeautifulSoup object
        """
        return BeautifulSoup(html, 'lxml')
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """
        Save data to a JSON file.
        
        Args:
            data (list): List of event data dictionaries
            filename (str, optional): Custom filename
            
        Returns:
            str: Path to the saved file
        """
        if not filename:
            today = datetime.now(pytz.timezone('Asia/Hong_Kong')).strftime('%Y-%m-%d')
            filename = f"{self.name.lower().replace(' ', '_')}_{today}.json"
        
        file_path = os.path.join(self.data_dir, filename)
        
        # Add source metadata to each event
        for event in data:
            event['source_id'] = self.source_id
            event['source_name'] = self.name
            event['source_type'] = self.source_type
            event['source_priority'] = self.source_priority
            event['scraped_at'] = datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Saved {len(data)} events to {file_path}")
        return file_path
    
    def load_existing_data(self) -> List[Dict[str, Any]]:
        """
        Load existing data for deduplication.
        
        Returns:
            list: List of existing events
        """
        existing_events = []
        
        # Get all JSON files for this source
        for filename in os.listdir(self.data_dir):
            if filename.startswith(self.name.lower().replace(' ', '_')) and filename.endswith('.json'):
                file_path = os.path.join(self.data_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        events = json.load(f)
                        existing_events.extend(events)
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    self.logger.error(f"Error loading {file_path}: {e}")
        
        return existing_events
    
    def deduplicate_events(self, new_events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Deduplicate events against existing data.
        
        Args:
            new_events (list): List of new events
            
        Returns:
            tuple: (deduplicated_events, duplicate_count)
        """
        existing_events = self.load_existing_data()
        deduplicated_events = []
        duplicate_count = 0
        
        for event in new_events:
            is_duplicate, matching_event = is_duplicate_event(event, existing_events)
            if not is_duplicate:
                deduplicated_events.append(event)
            else:
                duplicate_count += 1
                self.logger.debug(f"Duplicate event found: {event.get('event_name')}")
        
        self.logger.info(f"Deduplicated {duplicate_count} events")
        return deduplicated_events, duplicate_count
    
    def validate_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize event data using Pydantic model.
        
        Args:
            event_data (dict): Raw event data
            
        Returns:
            dict: Validated and normalized event data
        """
        try:
            # Create Pydantic model instance
            event_model = JobFairEvent(**event_data)
            
            # Convert back to dict
            validated_data = event_model.dict(exclude_none=True)
            
            return validated_data
        except Exception as e:
            self.logger.error(f"Error validating event data: {e}")
            
            # Try to fix common issues
            if 'event_name' not in event_data or not event_data['event_name']:
                event_data['event_name'] = f"Unknown Event ({self.name})"
                
            if 'start_datetime' not in event_data or not event_data['start_datetime']:
                event_data['start_datetime'] = datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
                
            if 'venue_name' not in event_data or not event_data['venue_name']:
                event_data['venue_name'] = "To be announced"
                
            if 'organizer_name' not in event_data or not event_data['organizer_name']:
                event_data['organizer_name'] = self.name
            
            # Try validation again with fixed data
            try:
                event_model = JobFairEvent(**event_data)
                return event_model.dict(exclude_none=True)
            except Exception as e2:
                self.logger.error(f"Error validating event data after fixes: {e2}")
                return event_data  # Return original data if validation still fails
    
    def should_update(self) -> bool:
        """
        Check if the scraper should update based on the update frequency.
        
        Returns:
            bool: True if the scraper should update, False otherwise
        """
        # Get the latest file for this source
        latest_file = None
        latest_time = None
        
        for filename in os.listdir(self.data_dir):
            if filename.startswith(self.name.lower().replace(' ', '_')) and filename.endswith('.json'):
                file_path = os.path.join(self.data_dir, filename)
                file_time = os.path.getmtime(file_path)
                
                if latest_time is None or file_time > latest_time:
                    latest_time = file_time
                    latest_file = file_path
        
        # If no file exists, we should update
        if latest_file is None:
            return True
        
        # Get the last update time
        last_update = datetime.fromtimestamp(latest_time, pytz.timezone('Asia/Hong_Kong'))
        now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
        
        # Check based on update frequency
        if self.update_frequency == UpdateFrequency.HOURLY:
            return (now - last_update) > timedelta(hours=1)
        elif self.update_frequency == UpdateFrequency.DAILY:
            return (now - last_update) > timedelta(days=1)
        elif self.update_frequency == UpdateFrequency.WEEKLY:
            return (now - last_update) > timedelta(weeks=1)
        elif self.update_frequency == UpdateFrequency.MONTHLY:
            return (now - last_update) > timedelta(days=30)
        elif self.update_frequency == UpdateFrequency.CUSTOM:
            # For custom schedules, we would need to implement cron parsing
            # This is a simplified version that always returns True
            self.logger.warning("Custom schedule checking not implemented, defaulting to update")
            return True
        
        # Default to update
        return True
    
    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape the source for job fair information.
        
        Returns:
            list: List of event data dictionaries
        """
        pass
    
    def run(self) -> Optional[str]:
        """
        Run the scraper and save the results.
        
        Returns:
            str: Path to the saved file, or None if no update was needed or an error occurred
        """
        self.logger.info(f"Starting {self.name} scraper")
        
        # Check if we should update
        if not self.should_update():
            self.logger.info(f"No update needed based on frequency {self.update_frequency}")
            return None
        
        try:
            # Initialize Selenium driver if needed
            if self.scraper_type == ScraperType.DYNAMIC and not self.selenium_driver:
                self.init_selenium_driver()
            
            # Scrape events
            events = self.scrape()
            self.logger.info(f"Scraped {len(events)} events")
            
            # Validate events
            validated_events = []
            for event in events:
                try:
                    validated_event = self.validate_event(event)
                    validated_events.append(validated_event)
                except Exception as e:
                    self.logger.error(f"Error validating event: {e}")
            
            self.logger.info(f"Validated {len(validated_events)} events")
            
            # Deduplicate events
            deduplicated_events, duplicate_count = self.deduplicate_events(validated_events)
            
            # Save to JSON
            if deduplicated_events:
                file_path = self.save_to_json(deduplicated_events)
                self.logger.info(f"Saved {len(deduplicated_events)} new events to {file_path}")
                return file_path
            else:
                self.logger.info("No new events to save")
                return None
        
        except Exception as e:
            self.logger.error(f"Error running {self.name} scraper: {e}", exc_info=True)
            return None
        
        finally:
            # Close Selenium driver if it exists
            if self.scraper_type == ScraperType.DYNAMIC:
                self.close_selenium_driver()
