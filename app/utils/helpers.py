import re
from typing import List, Dict, Any, Optional
from app.utils.logger import get_logger

logger = get_logger("helpers")


def clean_text(text: str) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
    
    return text.strip()


def calculate_duration_category(duration: Optional[int]) -> str:
    """
    Categorize assessment duration
    
    Args:
        duration: Duration in minutes
        
    Returns:
        str: Duration category
    """
    if duration is None:
        return "Unknown"
    
    if duration <= 15:
        return "Short"
    elif duration <= 45:
        return "Medium"
    elif duration <= 90:
        return "Long"
    else:
        return "Very Long"


def parse_test_types(test_type_codes: List[str]) -> List[str]:
    """
    Convert test type codes to full names
    
    Args:
        test_type_codes: List of test type codes
        
    Returns:
        List[str]: Full test type names
    """
    test_type_mapping = {
        'A': 'Ability & Aptitude',
        'B': 'Biodata & Situational Judgement',
        'C': 'Competencies',
        'D': 'Development & 360',
        'E': 'Assessment Exercises',
        'K': 'Knowledge & Skills',
        'P': 'Personality & Behavior',
        'S': 'Simulations'
    }
    
    full_names = []
    for code in test_type_codes:
        if code in test_type_mapping:
            full_names.append(test_type_mapping[code])
        else:
            full_names.append(code)
    
    return full_names


def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract technical skills from text
    
    Args:
        text: Text to analyze
        
    Returns:
        List[str]: Extracted skills
    """
    # Common technical skills and tools
    common_skills = [
        'python', 'java', 'javascript', 'sql', 'c++', 'c#', 'ruby', 'php',
        'react', 'angular', 'vue', 'node', 'django', 'flask', 'spring',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins',
        'git', 'agile', 'scrum', 'ci/cd', 'devops',
        'machine learning', 'data science', 'ai', 'deep learning',
        'excel', 'tableau', 'power bi', 'sap', 'salesforce'
    ]
    
    text_lower = text.lower()
    found_skills = []
    
    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill.title())
    
    return list(set(found_skills))


def extract_duration_from_text(text: str) -> Optional[int]:
    """
    Extract duration requirement from text
    
    Args:
        text: Text containing duration information
        
    Returns:
        Optional[int]: Duration in minutes
    """
    # Patterns for duration extraction
    patterns = [
        r'(\d+)\s*(?:minutes?|mins?)',
        r'(\d+)\s*(?:hours?|hrs?)',
        r'about\s+(\d+)\s*(?:minutes?|mins?)',
        r'(?:at most|maximum|max)\s+(\d+)\s*(?:minutes?|mins?)',
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            value = int(match.group(1))
            
            # Convert hours to minutes if needed
            if 'hour' in match.group(0) or 'hr' in match.group(0):
                value *= 60
            
            return value
    
    return None


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List[List]: Chunked list
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def merge_dicts_by_key(dicts: List[Dict], key: str) -> Dict:
    """
    Merge list of dictionaries by a specific key
    
    Args:
        dicts: List of dictionaries
        key: Key to use for merging
        
    Returns:
        Dict: Merged dictionary
    """
    merged = {}
    
    for d in dicts:
        if key in d:
            merged[d[key]] = d
    
    return merged


def calculate_similarity_score(text1: str, text2: str) -> float:
    """
    Calculate simple similarity score between two texts
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        float: Similarity score (0-1)
    """
    # Simple word overlap similarity
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_job_level_from_text(text: str) -> List[str]:
    """
    Extract job level requirements from text
    
    Args:
        text: Text to analyze
        
    Returns:
        List[str]: Extracted job levels
    """
    job_level_patterns = {
        'Graduate': r'\b(?:graduate|entry|fresher|junior)\b',
        'Mid-Professional': r'\b(?:mid|intermediate|experienced)\b',
        'Professional Individual Contributor': r'\b(?:senior|lead|expert|professional)\b',
        'Manager': r'\b(?:manager|management|supervisor)\b',
        'Executive': r'\b(?:executive|director|vp|vice president|c-level)\b'
    }
    
    text_lower = text.lower()
    found_levels = []
    
    for level, pattern in job_level_patterns.items():
        if re.search(pattern, text_lower):
            found_levels.append(level)
    
    return found_levels


def normalize_url(url: str) -> str:
    """
    Normalize URL for comparison
    
    Args:
        url: URL to normalize
        
    Returns:
        str: Normalized URL
    """
    # Remove trailing slashes
    url = url.rstrip('/')
    
    # Ensure https
    if url.startswith('http://'):
        url = url.replace('http://', 'https://', 1)
    
    return url