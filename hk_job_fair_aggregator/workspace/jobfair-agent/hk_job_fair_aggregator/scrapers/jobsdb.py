"""
Scraper for JobsDB Hong Kong job fairs.
"""

import re
import time
from datetime import datetime, timedelta
import pytz
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from hk_job_fair_aggregator.scrapers.base import BaseScraper
from hk_job_fair_aggregator.scrapers.scraper_types import ScraperType, UpdateFrequency
from hk_job_fair_aggregator.utils.normalizer import (
    normalize_date,
    normalize_datetime,
    normalize_venue_name,
    normalize_district,
    extract_contact_info,
    clean_html
)

class JobsDBScraper(BaseScraper):
    """
    Scraper for JobsDB Hong Kong job fairs.
    """
    
    def __init__(self):
        """Initialize the JobsDB scraper."""
        super().__init__(
            name="JobsDB Hong Kong",
            base_url="https://hk.jobsdb.com",
            source_id="jobsdb_hk",
            source_type="JOB_PORTAL",
            source_priority="PRIMARY",
            scraper_type=ScraperType.DYNAMIC,  # Uses Selenium for dynamic content
            update_frequency=UpdateFrequency.DAILY,
            language="BOTH",
            max_retries=3,
            retry_delay=5,
            use_proxy=False
        )
        
        # URLs for job fairs
        self.urls = {
            'recruitment_day': "https://hk.jobsdb.com/招聘日-recruitment-day-jobs",
            'job_fair': "https://hk.jobsdb.com/job-fair-jobs",
        }
    
    def scrape(self):
        """
        Scrape job fair information from JobsDB.
        
        Returns:
            list: List of job fair events
        """
        events = []
        
        try:
            # Scrape recruitment day page
            self.logger.info("Scraping JobsDB recruitment day page")
            events.extend(self.scrape_page(self.urls['recruitment_day'], 'recruitment_day'))
            
            # Scrape job fair page
            self.logger.info("Scraping JobsDB job fair page")
            events.extend(self.scrape_page(self.urls['job_fair'], 'job_fair'))
            
        except Exception as e:
            self.logger.error(f"Error in JobsDB scraper: {e}", exc_info=True)
        
        return events
    
    def scrape_page(self, url, event_type):
        """
        Scrape a JobsDB page for job fair listings.
        
        Args:
            url (str): URL to scrape
            event_type (str): Type of event ('recruitment_day' or 'job_fair')
            
        Returns:
            list: List of job fair events
        """
        events = []
        
        try:
            # Get the page using Selenium
            html = self.get_dynamic_page(url, wait_for_selector="article.job-card", wait_time=20)
            
            # Scroll down to load more content
            self.scroll_to_load_more()
            
            # Extract job cards
            job_cards = self.selenium_driver.find_elements(By.CSS_SELECTOR, "article.job-card")
            self.logger.info(f"Found {len(job_cards)} job cards")
            
            for card in job_cards:
                try:
                    event = self.parse_job_card(card, event_type)
                    if event:
                        events.append(event)
                except Exception as e:
                    self.logger.error(f"Error parsing job card: {e}", exc_info=True)
            
        except TimeoutException:
            self.logger.error(f"Timeout waiting for page to load: {url}")
        except Exception as e:
            self.logger.error(f"Error scraping page {url}: {e}", exc_info=True)
        
        return events
    
    def scroll_to_load_more(self, max_scrolls=10):
        """
        Scroll down to load more content.
        
        Args:
            max_scrolls (int): Maximum number of scrolls
        """
        if not self.selenium_driver:
            self.logger.error("Selenium driver not initialized")
            return
            
        for i in range(max_scrolls):
            # Scroll down
            self.selenium_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for content to load
            time.sleep(2)
            
            # Check if there's a "Load more" button and click it
            try:
                load_more = self.selenium_driver.find_element(By.XPATH, "//button[contains(text(), 'Load more') or contains(text(), '載入更多')]")
                load_more.click()
                time.sleep(2)
            except NoSuchElementException:
                pass
    
    def parse_job_card(self, card, event_type):
        """
        Parse a job card element.
        
        Args:
            card (WebElement): Job card element
            event_type (str): Type of event ('recruitment_day' or 'job_fair')
            
        Returns:
            dict: Job fair event data
        """
        event = {
            'event_type': event_type,
            'source_event_id': None,
            'is_physical': True,
            'is_virtual': False,
        }
        
        # Extract title
        try:
            title_elem = card.find_element(By.CSS_SELECTOR, "h1, h2, h3, .job-title")
            event['event_name'] = title_elem.text.strip()
            
            # Determine language and set appropriate name field
            if re.search(r'[\u4e00-\u9fff]', event['event_name']):
                event['event_name_zh'] = event['event_name']
                # Try to find English title
                try:
                    subtitle = card.find_element(By.CSS_SELECTOR, ".job-subtitle, .subtitle").text.strip()
                    if subtitle and not re.search(r'[\u4e00-\u9fff]', subtitle):
                        event['event_name_en'] = subtitle
                except NoSuchElementException:
                    pass
            else:
                event['event_name_en'] = event['event_name']
                # Try to find Chinese title
                try:
                    subtitle = card.find_element(By.CSS_SELECTOR, ".job-subtitle, .subtitle").text.strip()
                    if subtitle and re.search(r'[\u4e00-\u9fff]', subtitle):
                        event['event_name_zh'] = subtitle
                except NoSuchElementException:
                    pass
        except NoSuchElementException:
            # If no title found, skip this card
            return None
        
        # Extract company/organizer
        try:
            company_elem = card.find_element(By.CSS_SELECTOR, ".company-name, .employer-name")
            event['organizer_name'] = company_elem.text.strip()
        except NoSuchElementException:
            event['organizer_name'] = "JobsDB Recruitment Day"
        
        # Extract location
        try:
            location_elem = card.find_element(By.CSS_SELECTOR, ".job-location, .location-label")
            location = location_elem.text.strip()
            event['venue_name'] = normalize_venue_name(location)
            event['venue_address'] = location
            event['district'] = normalize_district(location)
        except NoSuchElementException:
            event['venue_name'] = "待定"  # To be determined
        
        # Extract date
        try:
            # Look for date in various formats
            date_elem = card.find_element(By.CSS_SELECTOR, ".job-date, .posted-date, .date-label")
            date_text = date_elem.text.strip()
            
            # Try to extract date from text
            date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})', date_text)
            if date_match:
                date_str = date_match.group(1)
                event['start_datetime'] = normalize_date(date_str)
            else:
                # Try to extract date from relative time (e.g., "3 days ago")
                days_ago_match = re.search(r'(\d+)\s+days?\s+ago', date_text)
                if days_ago_match:
                    days = int(days_ago_match.group(1))
                    today = datetime.now(pytz.timezone('Asia/Hong_Kong'))
                    event_date = today - timedelta(days=days)
                    event['start_datetime'] = event_date.strftime('%Y-%m-%d')
                else:
                    # If no date found, use today's date
                    event['start_datetime'] = datetime.now(pytz.timezone('Asia/Hong_Kong')).strftime('%Y-%m-%d')
        except NoSuchElementException:
            # If no date found, use today's date
            event['start_datetime'] = datetime.now(pytz.timezone('Asia/Hong_Kong')).strftime('%Y-%m-%d')
        
        # Extract link to details page
        try:
            link_elem = card.find_element(By.CSS_SELECTOR, "a.job-link, a.job-card-link")
            event['website_link'] = link_elem.get_attribute('href')
            
            # Extract source_event_id from URL
            url_match = re.search(r'/job/([^/]+)', event['website_link'])
            if url_match:
                event['source_event_id'] = url_match.group(1)
        except NoSuchElementException:
            pass
        
        # Extract description
        try:
            desc_elem = card.find_element(By.CSS_SELECTOR, ".job-description, .description")
            event['description'] = desc_elem.text.strip()
            
            # Determine language and set appropriate description field
            if re.search(r'[\u4e00-\u9fff]', event['description']):
                event['description_zh'] = event['description']
            else:
                event['description_en'] = event['description']
        except NoSuchElementException:
            event['description'] = ""
        
        # Set language based on content
        if 'event_name_zh' in event and 'event_name_en' in event:
            event['language'] = 'BOTH'
        elif 'event_name_zh' in event:
            event['language'] = 'ZH-HK'
        else:
            event['language'] = 'EN'
        
        # Set status
        event['status'] = 'UPCOMING'
        
        return event
