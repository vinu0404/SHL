import re
from typing import List, Optional
from validators import url as validate_url_validator
from app.utils.logger import get_logger

logger = get_logger("validators")


def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL
    
    Args:
        url: URL string to validate
        
    Returns:
        bool: True if valid URL, False otherwise
    """
    try:
        return validate_url_validator(url) is True
    except Exception as e:
        logger.warning(f"URL validation error for {url}: {e}")
        return False


def validate_query_length(query: str, min_length: int = 10, max_length: int = 5000) -> tuple[bool, Optional[str]]:
    """
    Validate query length
    
    Args:
        query: Query string to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not query or not query.strip():
        return False, "Query cannot be empty"
    
    query_length = len(query.strip())
    
    if query_length < min_length:
        return False, f"Query is too short. Minimum {min_length} characters required."
    
    if query_length > max_length:
        return False, f"Query is too long. Maximum {max_length} characters allowed."
    
    return True, None


def extract_urls_from_text(text: str) -> List[str]:
    """
    Extract all URLs from a text string
    
    Args:
        text: Text containing potential URLs
        
    Returns:
        List[str]: List of extracted URLs
    """
    # Enhanced URL regex pattern
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    
    urls = re.findall(url_pattern, text)
    
    # Validate extracted URLs
    valid_urls = [url for url in urls if validate_url(url)]
    
    logger.debug(f"Extracted {len(valid_urls)} valid URLs from text")
    
    return valid_urls


def is_job_description(text: str) -> bool:
    """
    Heuristically determine if text is likely a job description
    
    Args:
        text: Text to analyze
        
    Returns:
        bool: True if likely a JD
    """
    # Keywords commonly found in job descriptions
    jd_keywords = [
        'responsibilities', 'requirements', 'qualifications', 'experience',
        'skills', 'job description', 'role', 'position', 'candidate',
        'duties', 'education', 'bachelor', 'master', 'years of experience',
        'team', 'company', 'hiring', 'seeking', 'looking for'
    ]
    
    text_lower = text.lower()
    
    # Count keyword matches
    matches = sum(1 for keyword in jd_keywords if keyword in text_lower)
    
    # If at least 3 keywords are found, likely a JD
    return matches >= 3


def validate_assessment_data(assessment: dict) -> tuple[bool, Optional[str]]:
    """
    Validate assessment data structure
    
    Args:
        assessment: Assessment dictionary
        
    Returns:
        tuple: (is_valid, error_message)
    """
    required_fields = ['name', 'url', 'test_type', 'description']
    
    for field in required_fields:
        if field not in assessment:
            return False, f"Missing required field: {field}"
        
        if not assessment[field]:
            return False, f"Empty value for required field: {field}"
    
    # Validate URL
    if not validate_url(assessment['url']):
        return False, f"Invalid URL: {assessment['url']}"
    
    # Validate test_type is a list
    if not isinstance(assessment['test_type'], list):
        return False, "test_type must be a list"
    
    return True, None


def sanitize_input(text: str) -> str:
    """
    Sanitize user input by removing potentially harmful content
    
    Args:
        text: Input text to sanitize
        
    Returns:
        str: Sanitized text
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove potential SQL injection patterns (basic)
    sql_patterns = [
        r'(\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b).*\b(TABLE|FROM|INTO)\b',
        r'--',
        r'/\*.*?\*/',
        r';.*$'
    ]
    
    for pattern in sql_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    return text.strip()