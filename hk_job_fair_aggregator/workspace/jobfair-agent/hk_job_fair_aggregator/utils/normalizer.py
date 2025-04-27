"""
Data normalization utilities for the HK Job Fair Aggregator.
Handles date/time formats, venue names, and deduplication.
"""

import re
import uuid
import hashlib
import pytz
from datetime import datetime, timedelta
from dateutil import parser
from opencc import OpenCC

# Initialize OpenCC converter for Simplified to Traditional Chinese
s2t_converter = OpenCC('s2t')

# Hong Kong timezone
HK_TIMEZONE = pytz.timezone('Asia/Hong_Kong')

def normalize_date(date_str, source=None):
    """
    Normalize date strings to ISO format (YYYY-MM-DD).
    
    Args:
        date_str (str): Date string in various formats
        source (str, optional): Source name for source-specific parsing
        
    Returns:
        str: Normalized date in ISO format
    """
    if not date_str:
        return None
    
    # Remove extra whitespace
    date_str = re.sub(r'\s+', ' ', date_str.strip())
    
    # Source-specific parsing
    if source == 'labour_dept':
        # Handle Labour Department date format (e.g., "2023年12月25日")
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # Try to parse with dateutil
    try:
        parsed_date = parser.parse(date_str, fuzzy=True)
        return parsed_date.strftime('%Y-%m-%d')
    except (ValueError, parser.ParserError):
        return None

def normalize_datetime(datetime_str, date_str=None, time_str=None, source=None):
    """
    Normalize datetime strings to ISO format with timezone (YYYY-MM-DDTHH:MM:SS+08:00).
    
    Args:
        datetime_str (str, optional): Combined datetime string
        date_str (str, optional): Date string if separate from time
        time_str (str, optional): Time string if separate from date
        source (str, optional): Source name for source-specific parsing
        
    Returns:
        str: Normalized datetime in ISO format with timezone
    """
    if not any([datetime_str, (date_str and time_str)]):
        return None
    
    # If date and time are provided separately, combine them
    if date_str and time_str:
        datetime_str = f"{date_str} {time_str}"
    
    # Remove extra whitespace
    datetime_str = re.sub(r'\s+', ' ', datetime_str.strip())
    
    # Source-specific parsing
    if source == 'labour_dept':
        # Handle Labour Department datetime format (e.g., "2023年12月25日 上午10:00 - 下午5:00")
        date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', datetime_str)
        time_match = re.search(r'(上午|下午)(\d{1,2}):(\d{2})', datetime_str)
        
        if date_match and time_match:
            year, month, day = date_match.groups()
            am_pm, hour, minute = time_match.groups()
            
            hour = int(hour)
            if am_pm == '下午' and hour < 12:
                hour += 12
            
            dt = datetime(int(year), int(month), int(day), hour, int(minute))
            return dt.astimezone(HK_TIMEZONE).isoformat()
    
    # Try to parse with dateutil
    try:
        parsed_dt = parser.parse(datetime_str, fuzzy=True)
        
        # If no timezone info, assume Hong Kong time
        if parsed_dt.tzinfo is None:
            parsed_dt = HK_TIMEZONE.localize(parsed_dt)
            
        return parsed_dt.isoformat()
    except (ValueError, parser.ParserError):
        return None

def normalize_venue_name(venue_name):
    """
    Normalize venue names for consistency.
    
    Args:
        venue_name (str): Raw venue name
        
    Returns:
        str: Normalized venue name
    """
    if not venue_name:
        return None
    
    # Remove extra whitespace
    venue_name = re.sub(r'\s+', ' ', venue_name.strip())
    
    # Common venue name mappings
    venue_mappings = {
        r'香港會議展覽中心': '香港會議展覽中心',
        r'Hong Kong Convention and Exhibition Centre': '香港會議展覽中心',
        r'HKCEC': '香港會議展覽中心',
        r'九龍灣國際展貿中心': '九龍灣國際展貿中心',
        r'Kowloonbay International Trade & Exhibition Centre': '九龍灣國際展貿中心',
        r'KITEC': '九龍灣國際展貿中心',
    }
    
    # Apply mappings
    for pattern, replacement in venue_mappings.items():
        if re.search(pattern, venue_name, re.IGNORECASE):
            return replacement
    
    return venue_name

def normalize_district(address):
    """
    Extract and normalize district from address.
    
    Args:
        address (str): Full address
        
    Returns:
        str: Normalized district name
    """
    if not address:
        return None
    
    # Common districts in Hong Kong
    districts = [
        '中西區', '灣仔', '東區', '南區',  # Hong Kong Island
        '油尖旺', '深水埗', '九龍城', '黃大仙', '觀塘',  # Kowloon
        '葵青', '荃灣', '屯門', '元朗', '北區', '大埔', '沙田', '西貢', '離島'  # New Territories
    ]
    
    # Check if any district is in the address
    for district in districts:
        if district in address:
            return district
    
    # English district names
    english_districts = {
        'Central': '中西區',
        'Western': '中西區',
        'Wan Chai': '灣仔',
        'Eastern': '東區',
        'Southern': '南區',
        'Yau Tsim Mong': '油尖旺',
        'Sham Shui Po': '深水埗',
        'Kowloon City': '九龍城',
        'Wong Tai Sin': '黃大仙',
        'Kwun Tong': '觀塘',
        'Kwai Tsing': '葵青',
        'Tsuen Wan': '荃灣',
        'Tuen Mun': '屯門',
        'Yuen Long': '元朗',
        'North': '北區',
        'Tai Po': '大埔',
        'Sha Tin': '沙田',
        'Sai Kung': '西貢',
        'Islands': '離島'
    }
    
    # Check English district names
    for eng, chi in english_districts.items():
        if eng in address:
            return chi
    
    return None

def normalize_language(text):
    """
    Detect and normalize language of text.
    
    Args:
        text (str): Input text
        
    Returns:
        str: Language code ('ZH-HK', 'EN', or 'BOTH')
    """
    if not text:
        return None
    
    # Count Chinese characters
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    
    # Count English characters
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    
    # Determine language based on character counts
    if chinese_chars > 0 and english_chars == 0:
        return 'ZH-HK'
    elif chinese_chars == 0 and english_chars > 0:
        return 'EN'
    elif chinese_chars > 0 and english_chars > 0:
        return 'BOTH'
    else:
        return None

def simplified_to_traditional(text):
    """
    Convert Simplified Chinese to Traditional Chinese.
    
    Args:
        text (str): Text in Simplified Chinese
        
    Returns:
        str: Text in Traditional Chinese
    """
    if not text:
        return None
    
    return s2t_converter.convert(text)

def extract_contact_info(text):
    """
    Extract contact information from text.
    
    Args:
        text (str): Input text
        
    Returns:
        dict: Dictionary with email and phone keys
    """
    if not text:
        return {'email': None, 'phone': None}
    
    # Extract email
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    email = email_match.group(0) if email_match else None
    
    # Extract Hong Kong phone number
    phone_match = re.search(r'(?:\+852\s?)?(?:\d{4}\s?\d{4}|\d{8})', text)
    phone = phone_match.group(0) if phone_match else None
    
    return {'email': email, 'phone': phone}

def clean_html(html_text):
    """
    Clean HTML text by removing tags and normalizing whitespace.
    
    Args:
        html_text (str): HTML text
        
    Returns:
        str: Cleaned text
    """
    if not html_text:
        return None
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def generate_event_id(event_data):
    """
    Generate a unique ID for an event based on its key attributes.
    
    Args:
        event_data (dict): Event data
        
    Returns:
        str: UUID for the event
    """
    # Create a composite key from event attributes
    key_parts = [
        event_data.get('event_name', ''),
        event_data.get('start_datetime', ''),
        event_data.get('venue_name', ''),
        event_data.get('organizer_name', '')
    ]
    
    # Join parts and create a hash
    key = '|'.join([str(part).lower() for part in key_parts if part])
    hash_obj = hashlib.md5(key.encode())
    
    # Create a UUID based on the hash
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, hash_obj.hexdigest()))

def is_duplicate_event(event, existing_events, threshold=0.85):
    """
    Check if an event is a duplicate of any existing event.
    
    Args:
        event (dict): Event data
        existing_events (list): List of existing events
        threshold (float): Similarity threshold (0.0 to 1.0)
        
    Returns:
        tuple: (is_duplicate, matching_event)
    """
    # Generate event ID
    event_id = generate_event_id(event)
    
    # Check for exact ID match
    for existing in existing_events:
        existing_id = generate_event_id(existing)
        if event_id == existing_id:
            return True, existing
    
    # Check for fuzzy matches
    event_name = event.get('event_name', '').lower()
    event_date = event.get('start_datetime', '')[:10]  # YYYY-MM-DD
    event_venue = event.get('venue_name', '').lower()
    
    for existing in existing_events:
        existing_name = existing.get('event_name', '').lower()
        existing_date = existing.get('start_datetime', '')[:10]
        existing_venue = existing.get('venue_name', '').lower()
        
        # Skip if dates are more than 1 day apart
        if event_date and existing_date:
            try:
                event_date_obj = datetime.fromisoformat(event_date)
                existing_date_obj = datetime.fromisoformat(existing_date)
                date_diff = abs((event_date_obj - existing_date_obj).days)
                if date_diff > 1:
                    continue
            except ValueError:
                pass
        
        # Check name similarity
        if event_name and existing_name:
            # Simple similarity check (can be improved with more sophisticated algorithms)
            shorter = min(len(event_name), len(existing_name))
            similarity = sum(c1 == c2 for c1, c2 in zip(event_name[:shorter], existing_name[:shorter])) / shorter
            
            # If name and venue are similar, consider it a duplicate
            if similarity >= threshold and event_venue == existing_venue:
                return True, existing
    
    return False, None
