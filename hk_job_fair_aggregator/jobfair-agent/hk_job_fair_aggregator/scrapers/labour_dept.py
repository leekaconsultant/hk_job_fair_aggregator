"""
Scraper for the Hong Kong Labour Department job fairs.
"""

import re
from datetime import datetime
import pytz
from bs4 import BeautifulSoup

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base import BaseScraper
from utils.normalizer import (
    normalize_date,
    normalize_datetime,
    normalize_venue_name,
    normalize_district,
    extract_contact_info,
    clean_html
)

class LabourDeptScraper(BaseScraper):
    """
    Scraper for the Hong Kong Labour Department job fairs.
    """
    
    def __init__(self):
        """Initialize the Labour Department scraper."""
        super().__init__(
            name="Hong Kong Labour Department",
            base_url="https://www2.jobs.gov.hk",
            source_id="labour_dept_hk",
            source_type="GOVERNMENT",
            source_priority="PRIMARY",
            check_frequency="DAILY",
            language="ZH-HK"
        )
        
        # URLs for different types of job fairs
        self.urls = {
            'main': "https://www2.jobs.gov.hk/0/tc/information/Epem/Vacancy/",
            'full_time': "https://www2.jobs.gov.hk/0/tc/information/Epem/Vacancy/",
            'part_time': "https://www2.jobs.gov.hk/0/tc/information/Epem/Vacancy/",
            'recruitment_day': "https://www2.jobs.gov.hk/0/tc/information/jobseekers/jobfair/",
        }
    
    def scrape(self):
        """
        Scrape job fair information from the Labour Department website.
        
        Returns:
            list: List of job fair events
        """
        events = []
        
        # Scrape main job fair page
        self.logger.info("Scraping Labour Department main job fair page")
        events.extend(self.scrape_main_page())
        
        # Scrape recruitment day page
        self.logger.info("Scraping Labour Department recruitment day page")
        events.extend(self.scrape_recruitment_day_page())
        
        return events
    
    def scrape_main_page(self):
        """
        Scrape the main job fair page.
        
        Returns:
            list: List of job fair events
        """
        events = []
        
        try:
            # Get the main page
            response = self.get_page(self.urls['main'])
            soup = self.parse_html(response.text)
            
            # Find job fair listings
            job_fair_sections = soup.find_all('div', class_='job-fair-item')
            
            if not job_fair_sections:
                # Try alternative selectors if the expected ones aren't found
                job_fair_sections = soup.find_all('div', class_='content-box')
            
            for section in job_fair_sections:
                try:
                    event = self.parse_job_fair_section(section)
                    if event:
                        events.append(event)
                except Exception as e:
                    self.logger.error(f"Error parsing job fair section: {e}", exc_info=True)
            
            # If no events found using the expected structure, try to extract from the page text
            if not events:
                self.logger.warning("No job fair sections found with expected structure, trying text extraction")
                events.extend(self.extract_events_from_text(soup.get_text()))
            
        except Exception as e:
            self.logger.error(f"Error scraping main page: {e}", exc_info=True)
        
        return events
    
    def scrape_recruitment_day_page(self):
        """
        Scrape the recruitment day page.
        
        Returns:
            list: List of job fair events
        """
        events = []
        
        try:
            # Get the recruitment day page
            response = self.get_page(self.urls['recruitment_day'])
            soup = self.parse_html(response.text)
            
            # Find recruitment day listings
            recruitment_day_sections = soup.find_all('div', class_='recruitment-day-item')
            
            if not recruitment_day_sections:
                # Try alternative selectors if the expected ones aren't found
                recruitment_day_sections = soup.find_all('div', class_='content-box')
            
            for section in recruitment_day_sections:
                try:
                    event = self.parse_recruitment_day_section(section)
                    if event:
                        events.append(event)
                except Exception as e:
                    self.logger.error(f"Error parsing recruitment day section: {e}", exc_info=True)
            
            # If no events found using the expected structure, try to extract from the page text
            if not events:
                self.logger.warning("No recruitment day sections found with expected structure, trying text extraction")
                events.extend(self.extract_events_from_text(soup.get_text()))
            
        except Exception as e:
            self.logger.error(f"Error scraping recruitment day page: {e}", exc_info=True)
        
        return events
    
    def parse_job_fair_section(self, section):
        """
        Parse a job fair section from the main page.
        
        Args:
            section (BeautifulSoup): BeautifulSoup object for the section
            
        Returns:
            dict: Job fair event data
        """
        event = {
            'event_type': 'job_fair',
            'source_event_id': None,
            'is_physical': True,
            'is_virtual': False,
        }
        
        # Extract title
        title_elem = section.find('h3') or section.find('h2') or section.find('strong')
        if title_elem:
            event['event_name'] = title_elem.get_text().strip()
            event['event_name_zh'] = event['event_name']
        
        # Extract date and time
        date_elem = section.find('span', class_='date') or section.find(text=re.compile(r'\d{4}年\d{1,2}月\d{1,2}日'))
        if date_elem:
            date_text = date_elem.get_text().strip() if hasattr(date_elem, 'get_text') else date_elem.strip()
            event['start_datetime'] = normalize_datetime(date_text, source='labour_dept')
            
            # Try to extract end time if available
            time_range_match = re.search(r'(\d{1,2}:\d{2})\s*[至-]\s*(\d{1,2}:\d{2})', date_text)
            if time_range_match:
                start_time, end_time = time_range_match.groups()
                event['end_datetime'] = normalize_datetime(f"{date_text.split()[0]} {end_time}", source='labour_dept')
        
        # Extract venue
        venue_elem = section.find('span', class_='venue') or section.find(text=re.compile(r'地點|地址|場地'))
        if venue_elem:
            venue_text = venue_elem.get_text().strip() if hasattr(venue_elem, 'get_text') else venue_elem.strip()
            venue_match = re.search(r'[：:]\s*(.+)', venue_text)
            if venue_match:
                venue = venue_match.group(1).strip()
                event['venue_name'] = normalize_venue_name(venue)
                event['venue_address'] = venue
                event['district'] = normalize_district(venue)
        
        # Extract organizer
        organizer_elem = section.find('span', class_='organizer') or section.find(text=re.compile(r'主辦機構|舉辦機構'))
        if organizer_elem:
            organizer_text = organizer_elem.get_text().strip() if hasattr(organizer_elem, 'get_text') else organizer_elem.strip()
            organizer_match = re.search(r'[：:]\s*(.+)', organizer_text)
            if organizer_match:
                event['organizer_name'] = organizer_match.group(1).strip()
        else:
            event['organizer_name'] = "香港勞工處"  # Default organizer
        
        # Extract description
        desc_elem = section.find('div', class_='description') or section.find('p')
        if desc_elem:
            event['description'] = clean_html(str(desc_elem))
            event['description_zh'] = event['description']
        
        # Extract link to details page
        link_elem = section.find('a', href=True)
        if link_elem:
            event['website_link'] = self.base_url + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
        
        # Extract contact information
        contact_elem = section.find(text=re.compile(r'聯絡|查詢|電話|電郵'))
        if contact_elem:
            contact_text = contact_elem.strip() if isinstance(contact_elem, str) else contact_elem.get_text().strip()
            contact_info = extract_contact_info(contact_text)
            event['contact_email'] = contact_info['email']
            event['contact_phone'] = contact_info['phone']
        
        # Set default values for required fields if not found
        if 'event_name' not in event:
            return None
        
        if 'start_datetime' not in event:
            # Try to find date in the text
            text = section.get_text()
            date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
            if date_match:
                year, month, day = date_match.groups()
                event['start_datetime'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        if 'venue_name' not in event:
            event['venue_name'] = "待定"  # To be determined
        
        # Set language
        event['language'] = 'ZH-HK'
        
        # Set status
        event['status'] = 'UPCOMING'
        
        return event
    
    def parse_recruitment_day_section(self, section):
        """
        Parse a recruitment day section.
        
        Args:
            section (BeautifulSoup): BeautifulSoup object for the section
            
        Returns:
            dict: Recruitment day event data
        """
        # Recruitment day parsing is similar to job fair parsing
        event = self.parse_job_fair_section(section)
        
        if event:
            event['event_type'] = 'recruitment_day'
        
        return event
    
    def extract_events_from_text(self, text):
        """
        Extract events from page text when structured parsing fails.
        
        Args:
            text (str): Page text
            
        Returns:
            list: List of events
        """
        events = []
        
        # Look for date patterns
        date_matches = re.finditer(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
        
        for date_match in date_matches:
            try:
                # Extract date
                year, month, day = date_match.groups()
                date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                
                # Find surrounding text (50 chars before and 200 chars after the date)
                start_pos = max(0, date_match.start() - 50)
                end_pos = min(len(text), date_match.end() + 200)
                context = text[start_pos:end_pos]
                
                # Extract event name (look for title-like text before the date)
                name_match = re.search(r'([^。！？\n]{5,30})[^\n]*' + re.escape(date_match.group(0)), context)
                event_name = name_match.group(1).strip() if name_match else f"勞工處招聘活動 ({date_str})"
                
                # Extract venue
                venue_match = re.search(r'地[點址場].*?[：:]\s*([^。！？\n]{3,50})', context)
                venue = venue_match.group(1).strip() if venue_match else "待定"
                
                # Extract time
                time_match = re.search(r'(\d{1,2}:\d{2})\s*[至-]\s*(\d{1,2}:\d{2})', context)
                start_time = time_match.group(1) if time_match else "09:00"
                end_time = time_match.group(2) if time_match else "17:00"
                
                # Create event
                event = {
                    'event_name': event_name,
                    'event_name_zh': event_name,
                    'start_datetime': f"{date_str}T{start_time}:00+08:00",
                    'end_datetime': f"{date_str}T{end_time}:00+08:00",
                    'venue_name': normalize_venue_name(venue),
                    'venue_address': venue,
                    'district': normalize_district(venue),
                    'organizer_name': "香港勞工處",
                    'description': context,
                    'description_zh': context,
                    'event_type': 'job_fair',
                    'is_physical': True,
                    'is_virtual': False,
                    'language': 'ZH-HK',
                    'status': 'UPCOMING'
                }
                
                events.append(event)
            
            except Exception as e:
                self.logger.error(f"Error extracting event from text: {e}", exc_info=True)
        
        return events
