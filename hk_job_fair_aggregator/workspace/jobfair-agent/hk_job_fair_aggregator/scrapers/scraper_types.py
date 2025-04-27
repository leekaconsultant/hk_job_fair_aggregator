"""
Enum definitions for scraper types and configurations.
"""

from enum import Enum, auto

class ScraperType(Enum):
    """
    Types of scrapers based on the technology used.
    """
    STATIC = auto()  # Static HTML content using requests and BeautifulSoup
    DYNAMIC = auto()  # Dynamic content requiring Selenium
    API = auto()      # API-based scraper

class UpdateFrequency(Enum):
    """
    Update frequency for scrapers.
    """
    HOURLY = auto()
    DAILY = auto()
    WEEKLY = auto()
    MONTHLY = auto()
    CUSTOM = auto()  # Custom cron schedule
