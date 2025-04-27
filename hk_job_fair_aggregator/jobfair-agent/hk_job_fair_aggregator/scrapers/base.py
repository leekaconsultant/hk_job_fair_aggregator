"""
Base scraper class for the HK Job Fair Aggregator.
Provides common functionality for all scrapers.
"""

import os
import json
import requests
from datetime import datetime
import pytz
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import setup_logger, with_retry
from utils.normalizer import (
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

class BaseScraper(ABC):
    """
    Base class for all scrapers.
    
    Attributes:
        name (str): Name of the scraper
        base_url (str): Base URL for the source
        source_id (str): Unique identifier for the source
        source_type (str): Type of source (GOVERNMENT, JOB_PORTAL, etc.)
        source_priority (str): Priority level (PRIMARY, SECONDARY)
        check_frequency (str): How often to check (DAILY, WEEKLY)
        language (str): Primary language of the source (ZH-HK, EN, BOTH)
        logger (logging.Logger): Logger instance
    """
    
    def __init__(self, name, base_url, source_id, source_type, source_priority, check_frequency, language):
        """
        Initialize the base scraper.
        
        Args:
            name (str): Name of the scraper
            base_url (str): Base URL for the source
            source_id (str): Unique identifier for the source
            source_type (str): Type of source (GOVERNMENT, JOB_PORTAL, etc.)
            source_priority (str): Priority level (PRIMARY, SECONDARY)
            check_frequency (str): How often to check (DAILY, WEEKLY)
            language (str): Primary language of the source (ZH-HK, EN, BOTH)
        """
        self.name = name
        self.base_url = base_url
        self.source_id = source_id
        self.source_type = source_type
        self.source_priority = source_priority
        self.check_frequency = check_frequency
        self.language = language
        self.logger = setup_logger(f"scraper.{name.lower().replace(' ', '_')}")
        
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # User agent for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'zh-HK,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }
    
    @with_retry(max_attempts=3, min_wait=2, max_wait=10)
    def get_page(self, url, params=None):
        """
        Get a page from the source.
        
        Args:
            url (str): URL to fetch
            params (dict, optional): Query parameters
            
        Returns:
            requests.Response: Response object
        """
        self.logger.info(f"Fetching page: {url}")
        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        response.raise_for_status()
        return response
    
    def parse_html(self, html):
        """
        Parse HTML content.
        
        Args:
            html (str): HTML content
            
        Returns:
            BeautifulSoup: BeautifulSoup object
        """
        return BeautifulSoup(html, 'lxml')
    
    def save_to_json(self, data, filename=None):
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
    
    def load_existing_data(self):
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
    
    def deduplicate_events(self, new_events):
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
    
    @abstractmethod
    def scrape(self):
        """
        Scrape the source for job fair information.
        
        Returns:
            list: List of event data dictionaries
        """
        pass
    
    def run(self):
        """
        Run the scraper and save the results.
        
        Returns:
            str: Path to the saved file
        """
        self.logger.info(f"Starting {self.name} scraper")
        
        try:
            # Scrape events
            events = self.scrape()
            self.logger.info(f"Scraped {len(events)} events")
            
            # Deduplicate events
            deduplicated_events, duplicate_count = self.deduplicate_events(events)
            
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
