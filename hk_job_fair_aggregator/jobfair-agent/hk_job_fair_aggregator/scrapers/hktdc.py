"""
Scraper for Hong Kong Trade Development Council (HKTDC) job fairs.
"""

import re
from datetime import datetime
import pytz
import json
from bs4 import BeautifulSoup

from .base import BaseScraper
from ..utils.normalizer import (
    normalize_date,
    normalize_datetime,
    normalize_venue_name,
    normalize_district,
    extract_contact_info,
    clean_html
)

class HKTDCScraper(BaseScraper):
    """
    Scraper for Hong Kong Trade Development Council (HKTDC) job fairs.
    """
    
    def __init__(self):
        """Initialize the HKTDC scraper."""
        super().__init__(
            name="Hong Kong Trade Development Council",
            base_url="https://www.hktdc.com",
            source_id="hktdc",
            source_type="STATUTORY_BODY",
            source_priority="PRIMARY",
            check_frequency="DAILY",
            language="BOTH"
        )
        
        # URLs for job fairs
        self.urls = {
            'education_expo': "https://www.hktdc.com/event/hkeducationexpo/tc",
            'events_calendar': "https://www.hktdc.com/event/schedule/tc",
            'career_expo': "https://www.hktdc.com/event/hkcareerexpo/tc",
        }
    
    def scrape(self):
        """
        Scrape job fair information from HKTDC.
        
        Returns:
            list: List of job fair events
        """
        events = []
        
        # Scrape education expo page
        self.logger.info("Scraping HKTDC Education & Careers Expo page")
        events.extend(self.scrape_education_expo())
        
        # Scrape career expo page
        self.logger.info("Scraping HKTDC Career Expo page")
        events.extend(self.scrape_career_expo())
        
        # Scrape events calendar for additional job fairs
        self.logger.info("Scraping HKTDC Events Calendar for job fairs")
        events.extend(self.scrape_events_calendar())
        
        return events
    
    def scrape_education_expo(self):
        """
        Scrape the Education & Careers Expo page.
        
        Returns:
            list: List of job fair events
        """
        events = []
        
        try:
            # Get the education expo page
            response = self.get_page(self.urls['education_expo'])
            soup = self.parse_html(response.text)
            
            # Extract main expo information
            event = self.extract_expo_info(soup, 'education_expo')
            if event:
                events.append(event)
            
            # Extract sub-events if available
            sub_events = self.extract_sub_events(soup, 'education_expo')
            events.extend(sub_events)
            
        except Exception as e:
            self.logger.error(f"Error scraping education expo page: {e}", exc_info=True)
        
        return events
    
    def scrape_career_expo(self):
        """
        Scrape the Career Expo page.
        
        Returns:
            list: List of job fair events
        """
        events = []
        
        try:
            # Get the career expo page
            response = self.get_page(self.urls['career_expo'])
            soup = self.parse_html(response.text)
            
            # Extract main expo information
            event = self.extract_expo_info(soup, 'career_expo')
            if event:
                events.append(event)
            
            # Extract sub-events if available
            sub_events = self.extract_sub_events(soup, 'career_expo')
            events.extend(sub_events)
            
        except Exception as e:
            self.logger.error(f"Error scraping career expo page: {e}", exc_info=True)
        
        return events
    
    def scrape_events_calendar(self):
        """
        Scrape the Events Calendar for job fairs.
        
        Returns:
            list: List of job fair events
        """
        events = []
        
        try:
            # Get the events calendar page
            response = self.get_page(self.urls['events_calendar'])
            soup = self.parse_html(response.text)
            
            # Look for event listings
            event_listings = soup.find_all('div', class_='event-item') or soup.find_all('div', class_='event-card')
            
            for listing in event_listings:
                try:
                    # Check if it's a job fair or career-related event
                    title = listing.find('h3') or listing.find('h2') or listing.find('div', class_='title')
                    if not title:
                        continue
                    
                    title_text = title.get_text().strip()
                    
                    # Skip if not related to careers or job fairs
                    if not any(keyword in title_text.lower() for keyword in ['career', 'job', 'employment', '就業', '招聘', '職業']):
                        continue
                    
                    # Extract event information
                    event = self.extract_event_from_listing(listing)
                    if event:
                        events.append(event)
                
                except Exception as e:
                    self.logger.error(f"Error extracting event from listing: {e}", exc_info=True)
            
        except Exception as e:
            self.logger.error(f"Error scraping events calendar: {e}", exc_info=True)
        
        return events
    
    def extract_expo_info(self, soup, expo_type):
        """
        Extract information about the main expo.
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object for the page
            expo_type (str): Type of expo ('education_expo' or 'career_expo')
            
        Returns:
            dict: Expo event data
        """
        event = {
            'event_type': expo_type,
            'source_event_id': expo_type,
            'is_physical': True,
            'is_virtual': False,
            'organizer_name': "Hong Kong Trade Development Council",
        }
        
        # Extract title
        title_elem = soup.find('h1') or soup.find('h2', class_='event-title')
        if title_elem:
            title_text = title_elem.get_text().strip()
            event['event_name'] = title_text
            
            # Determine language and set appropriate name field
            if re.search(r'[\u4e00-\u9fff]', title_text):
                event['event_name_zh'] = title_text
                
                # Look for English title
                english_title = soup.find('span', class_='en-title') or soup.find('div', class_='en-title')
                if english_title:
                    event['event_name_en'] = english_title.get_text().strip()
            else:
                event['event_name_en'] = title_text
                
                # Look for Chinese title
                chinese_title = soup.find('span', class_='zh-title') or soup.find('div', class_='zh-title')
                if chinese_title:
                    event['event_name_zh'] = chinese_title.get_text().strip()
        
        # Extract date
        date_elem = soup.find('div', class_='event-date') or soup.find('span', class_='date')
        if date_elem:
            date_text = date_elem.get_text().strip()
            
            # Extract start and end dates
            date_range_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s*[-至]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', date_text)
            if date_range_match:
                start_date, end_date = date_range_match.groups()
                event['start_datetime'] = normalize_date(start_date)
                event['end_datetime'] = normalize_date(end_date)
            else:
                # Try to find single date
                date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', date_text)
                if date_match:
                    event['start_datetime'] = normalize_date(date_match.group(1))
        
        # If no date found, look for date in text
        if 'start_datetime' not in event:
            text = soup.get_text()
            
            # Look for date patterns
            date_range_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s*[-至]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text)
            if date_range_match:
                start_date, end_date = date_range_match.groups()
                event['start_datetime'] = normalize_date(start_date)
                event['end_datetime'] = normalize_date(end_date)
            else:
                # Try Chinese date format
                cn_date_range_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日\s*[-至]\s*(\d{1,2})月(\d{1,2})日', text)
                if cn_date_range_match:
                    year, start_month, start_day, end_month, end_day = cn_date_range_match.groups()
                    event['start_datetime'] = f"{year}-{start_month.zfill(2)}-{start_day.zfill(2)}"
                    event['end_datetime'] = f"{year}-{end_month.zfill(2)}-{end_day.zfill(2)}"
        
        # Extract venue
        venue_elem = soup.find('div', class_='event-venue') or soup.find('span', class_='venue')
        if venue_elem:
            venue_text = venue_elem.get_text().strip()
            event['venue_name'] = normalize_venue_name(venue_text)
            event['venue_address'] = venue_text
            event['district'] = normalize_district(venue_text)
        
        # If no venue found, look for venue in text
        if 'venue_name' not in event:
            text = soup.get_text()
            venue_match = re.search(r'地[點址場].*?[：:]\s*([^。！？\n]{3,50})', text)
            if venue_match:
                venue = venue_match.group(1).strip()
                event['venue_name'] = normalize_venue_name(venue)
                event['venue_address'] = venue
                event['district'] = normalize_district(venue)
            else:
                # Default to HKCEC for HKTDC events
                event['venue_name'] = "香港會議展覽中心"
                event['venue_address'] = "香港灣仔博覽道1號"
                event['district'] = "灣仔"
        
        # Extract description
        desc_elem = soup.find('div', class_='event-description') or soup.find('div', class_='description')
        if desc_elem:
            event['description'] = clean_html(str(desc_elem))
            
            # Determine language and set appropriate description field
            if re.search(r'[\u4e00-\u9fff]', event['description']):
                event['description_zh'] = event['description']
            else:
                event['description_en'] = event['description']
        
        # Extract website link
        event['website_link'] = self.urls[expo_type]
        
        # Set language based on content
        if 'event_name_zh' in event and 'event_name_en' in event:
            event['language'] = 'BOTH'
        elif 'event_name_zh' in event:
            event['language'] = 'ZH-HK'
        else:
            event['language'] = 'EN'
        
        # Set status
        event['status'] = 'UPCOMING'
        
        # Set default values for required fields if not found
        if 'event_name' not in event:
            if expo_type == 'education_expo':
                event['event_name'] = "HKTDC Education & Careers Expo"
                event['event_name_en'] = "HKTDC Education & Careers Expo"
                event['event_name_zh'] = "香港貿發局教育及職業博覽"
            else:
                event['event_name'] = "HKTDC Career Expo"
                event['event_name_en'] = "HKTDC Career Expo"
                event['event_name_zh'] = "香港貿發局職業博覽"
        
        if 'start_datetime' not in event:
            # Use next January as default for education expo (typically held in January)
            now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
            next_year = now.year + 1 if now.month > 1 else now.year
            event['start_datetime'] = f"{next_year}-01-15"
        
        return event
    
    def extract_sub_events(self, soup, expo_type):
        """
        Extract sub-events from the expo page.
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object for the page
            expo_type (str): Type of expo ('education_expo' or 'career_expo')
            
        Returns:
            list: List of sub-event data
        """
        sub_events = []
        
        # Look for event schedule or program
        schedule_section = soup.find('div', class_='event-schedule') or soup.find('div', class_='program')
        if not schedule_section:
            return sub_events
        
        # Look for event items
        event_items = schedule_section.find_all('div', class_='event-item') or schedule_section.find_all('tr')
        
        for item in event_items:
            try:
                # Extract date
                date_elem = item.find('div', class_='date') or item.find('td', class_='date')
                if not date_elem:
                    continue
                
                date_text = date_elem.get_text().strip()
                date = normalize_date(date_text)
                
                # Extract time
                time_elem = item.find('div', class_='time') or item.find('td', class_='time')
                time_text = time_elem.get_text().strip() if time_elem else ""
                
                # Extract title
                title_elem = item.find('div', class_='title') or item.find('td', class_='title')
                if not title_elem:
                    continue
                
                title_text = title_elem.get_text().strip()
                
                # Extract venue
                venue_elem = item.find('div', class_='venue') or item.find('td', class_='venue')
                venue_text = venue_elem.get_text().strip() if venue_elem else ""
                
                # Create sub-event
                sub_event = {
                    'event_name': title_text,
                    'start_datetime': normalize_datetime(None, date, time_text),
                    'venue_name': normalize_venue_name(venue_text) if venue_text else "香港會議展覽中心",
                    'venue_address': venue_text if venue_text else "香港灣仔博覽道1號",
                    'district': normalize_district(venue_text) if venue_text else "灣仔",
                    'organizer_name': "Hong Kong Trade Development Council",
                    'event_type': f"{expo_type}_sub_event",
                    'source_event_id': f"{expo_type}_{len(sub_events)}",
                    'is_physical': True,
                    'is_virtual': False,
                    'website_link': self.urls[expo_type],
                    'status': 'UPCOMING'
                }
                
                # Determine language and set appropriate name field
                if re.search(r'[\u4e00-\u9fff]', title_text):
                    sub_event['event_name_zh'] = title_text
                    sub_event['language'] = 'ZH-HK'
                else:
                    sub_event['event_name_en'] = title_text
                    sub_event['language'] = 'EN'
                
                sub_events.append(sub_event)
            
            except Exception as e:
                self.logger.error(f"Error extracting sub-event: {e}", exc_info=True)
        
        return sub_events
    
    def extract_event_from_listing(self, listing):
        """
        Extract event information from a listing in the events calendar.
        
        Args:
            listing (BeautifulSoup): BeautifulSoup object for the listing
            
        Returns:
            dict: Event data
        """
        event = {
            'event_type': 'career_event',
            'is_physical': True,
            'is_virtual': False,
            'organizer_name': "Hong Kong Trade Development Council",
        }
        
        # Extract title
        title_elem = listing.find('h3') or listing.find('h2') or listing.find('div', class_='title')
        if title_elem:
            title_text = title_elem.get_text().strip()
            event['event_name'] = title_text
            
            # Determine language and set appropriate name field
            if re.search(r'[\u4e00-\u9fff]', title_text):
                event['event_name_zh'] = title_text
                event['language'] = 'ZH-HK'
            else:
                event['event_name_en'] = title_text
                event['language'] = 'EN'
        
        # Extract date
        date_elem = listing.find('div', class_='date') or listing.find('span', class_='date')
        if date_elem:
            date_text = date_elem.get_text().strip()
            
            # Extract start and end dates
            date_range_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s*[-至]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', date_text)
            if date_range_match:
                start_date, end_date = date_range_match.groups()
                event['start_datetime'] = normalize_date(start_date)
                event['end_datetime'] = normalize_date(end_date)
            else:
                # Try to find single date
                date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', date_text)
                if date_match:
                    event['start_datetime'] = normalize_date(date_match.group(1))
        
        # Extract venue
        venue_elem = listing.find('div', class_='venue') or listing.find('span', class_='venue')
        if venue_elem:
            venue_text = venue_elem.get_text().strip()
            event['venue_name'] = normalize_venue_name(venue_text)
            event['venue_address'] = venue_text
            event['district'] = normalize_district(venue_text)
        
        # Extract link
        link_elem = listing.find('a', href=True)
        if link_elem:
            event['website_link'] = self.base_url + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
            
            # Extract source_event_id from URL
            url_match = re.search(r'/event/([^/]+)', event['website_link'])
            if url_match:
                event['source_event_id'] = url_match.group(1)
        
        # Set status
        event['status'] = 'UPCOMING'
        
        # Set default values for required fields if not found
        if 'event_name' not in event:
            return None
        
        if 'venue_name' not in event:
            # Default to HKCEC for HKTDC events
            event['venue_name'] = "香港會議展覽中心"
            event['venue_address'] = "香港灣仔博覽道1號"
            event['district'] = "灣仔"
        
        return event
