"""
Pydantic models for job fair events.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
import pytz

class JobFairEvent(BaseModel):
    """
    Pydantic model for job fair events.
    """
    # Required fields
    event_name: str = Field(..., description="Name of the event")
    start_datetime: str = Field(..., description="Start date and time in ISO format")
    venue_name: str = Field(..., description="Name of the venue")
    organizer_name: str = Field(..., description="Name of the organizer")
    event_type: str = Field(..., description="Type of event (job_fair, recruitment_day, etc.)")
    source_id: str = Field(..., description="ID of the source")
    source_name: str = Field(..., description="Name of the source")
    
    # Optional fields
    event_name_en: Optional[str] = Field(None, description="English name of the event")
    event_name_zh: Optional[str] = Field(None, description="Chinese name of the event")
    end_datetime: Optional[str] = Field(None, description="End date and time in ISO format")
    venue_address: Optional[str] = Field(None, description="Address of the venue")
    district: Optional[str] = Field(None, description="District of the venue")
    description: Optional[str] = Field(None, description="Description of the event")
    description_en: Optional[str] = Field(None, description="English description of the event")
    description_zh: Optional[str] = Field(None, description="Chinese description of the event")
    website_link: Optional[str] = Field(None, description="Link to the event website")
    registration_link: Optional[str] = Field(None, description="Link to register for the event")
    contact_email: Optional[str] = Field(None, description="Contact email for the event")
    contact_phone: Optional[str] = Field(None, description="Contact phone for the event")
    is_physical: bool = Field(True, description="Whether the event is physical")
    is_virtual: bool = Field(False, description="Whether the event is virtual")
    virtual_link: Optional[str] = Field(None, description="Link to the virtual event")
    language: str = Field("ZH-HK", description="Language of the event (ZH-HK, EN, BOTH)")
    status: str = Field("UPCOMING", description="Status of the event (UPCOMING, ONGOING, PAST, CANCELLED)")
    source_event_id: Optional[str] = Field(None, description="ID of the event from the source")
    source_type: str = Field("JOB_PORTAL", description="Type of source (GOVERNMENT, JOB_PORTAL, etc.)")
    source_priority: str = Field("PRIMARY", description="Priority of the source (PRIMARY, SECONDARY)")
    scraped_at: Optional[str] = Field(None, description="Timestamp when the event was scraped")
    
    # Additional fields for internal use
    _id: Optional[str] = Field(None, description="Internal ID for the event")
    _raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw data from the source")
    
    @validator('start_datetime', 'end_datetime', pre=True)
    def validate_datetime(cls, v):
        """Validate and normalize datetime strings."""
        if not v:
            return v
            
        try:
            # If it's already in ISO format, return as is
            if 'T' in v and '+' in v:
                return v
                
            # Try to parse the datetime
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            
            # If no timezone, assume Hong Kong time
            if dt.tzinfo is None:
                dt = pytz.timezone('Asia/Hong_Kong').localize(dt)
                
            return dt.isoformat()
        except (ValueError, TypeError):
            # If it's just a date, append time and timezone
            if len(v) == 10 and '-' in v:
                return f"{v}T00:00:00+08:00"
            return v
    
    @validator('event_name', 'venue_name', 'organizer_name', pre=True)
    def validate_required_text(cls, v):
        """Ensure required text fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @validator('event_name_en', 'event_name_zh', 'venue_address', 'description', 
               'description_en', 'description_zh', pre=True)
    def validate_optional_text(cls, v):
        """Clean optional text fields."""
        if not v:
            return None
        return v.strip()
    
    @validator('website_link', 'registration_link', 'virtual_link', pre=True)
    def validate_urls(cls, v):
        """Validate URLs."""
        if not v:
            return None
            
        v = v.strip()
        if not (v.startswith('http://') or v.startswith('https://')):
            v = 'https://' + v
            
        return v
    
    @validator('language', pre=True)
    def validate_language(cls, v):
        """Validate language code."""
        valid_languages = ['ZH-HK', 'EN', 'BOTH']
        if v and v.upper() in valid_languages:
            return v.upper()
        return 'ZH-HK'  # Default to Chinese
    
    @validator('status', pre=True)
    def validate_status(cls, v):
        """Validate event status."""
        valid_statuses = ['UPCOMING', 'ONGOING', 'PAST', 'CANCELLED']
        if v and v.upper() in valid_statuses:
            return v.upper()
        return 'UPCOMING'  # Default to upcoming
    
    class Config:
        """Pydantic model configuration."""
        extra = 'ignore'  # Ignore extra fields
