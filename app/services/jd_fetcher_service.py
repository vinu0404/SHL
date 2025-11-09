import re
from typing import Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("jd_fetcher_service")


class JDFetcherService:
    """Service for fetching job descriptions from URLs"""
    
    def __init__(self):
        self.timeout = settings.SCRAPER_TIMEOUT
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def fetch_jd_from_url(self, url: str) -> Dict[str, Any]:
        """
        Fetch job description from URL
        
        Args:
            url: URL containing job description
            
        Returns:
            Dictionary with JD text and metadata
        """
        try:
            logger.info(f"Fetching JD from URL: {url}")
            
            # Fetch the page
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text content
            jd_text = self._extract_job_description(soup)
            
            if not jd_text:
                logger.warning(f"Could not extract JD text from URL: {url}")
                return {
                    "success": False,
                    "jd_text": None,
                    "error_message": "Failed to extract job description from page",
                    "metadata": {"url": url}
                }
            
            # Extract metadata
            metadata = self._extract_metadata(soup, url)
            
            logger.info(f"Successfully fetched JD ({len(jd_text)} characters)")
            
            return {
                "success": True,
                "jd_text": jd_text,
                "error_message": None,
                "metadata": metadata
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            return {
                "success": False,
                "jd_text": None,
                "error_message": f"Failed to fetch URL: {str(e)}",
                "metadata": {"url": url}
            }
        except Exception as e:
            logger.error(f"Error processing JD from URL {url}: {e}")
            return {
                "success": False,
                "jd_text": None,
                "error_message": f"Error processing page: {str(e)}",
                "metadata": {"url": url}
            }
    
    def _extract_job_description(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract job description text from HTML
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Extracted JD text or None
        """
        # Strategy 1: Look for common JD container classes/ids
        jd_containers = [
            soup.find('div', class_=re.compile(r'job.*description', re.I)),
            soup.find('div', id=re.compile(r'job.*description', re.I)),
            soup.find('section', class_=re.compile(r'job.*description', re.I)),
            soup.find('div', class_=re.compile(r'description', re.I)),
            soup.find('article'),
            soup.find('main'),
        ]
        
        for container in jd_containers:
            if container:
                text = self._clean_text(container.get_text())
                if len(text) > 200:  # Minimum length for a valid JD
                    return text
        
        # Strategy 2: Look for elements with keywords
        keywords = ['responsibilities', 'requirements', 'qualifications', 'job description']
        for keyword in keywords:
            elements = soup.find_all(string=re.compile(keyword, re.I))
            if elements:
                parent = elements[0].find_parent()
                if parent:
                    text = self._clean_text(parent.get_text())
                    if len(text) > 200:
                        return text
        
        # Strategy 3: Extract all paragraph text
        paragraphs = soup.find_all('p')
        if paragraphs:
            text = '\n'.join([p.get_text() for p in paragraphs])
            text = self._clean_text(text)
            if len(text) > 200:
                return text
        
        # Strategy 4: Get all body text as fallback
        body = soup.find('body')
        if body:
            # Remove script and style elements
            for script in body(['script', 'style', 'nav', 'header', 'footer']):
                script.decompose()
            
            text = self._clean_text(body.get_text())
            if len(text) > 200:
                return text
        
        return None
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extract metadata from page
        
        Args:
            soup: BeautifulSoup object
            url: Page URL
            
        Returns:
            Metadata dictionary
        """
        metadata = {"url": url}
        
        # Extract title
        title = soup.find('title')
        if title:
            metadata['title'] = title.get_text().strip()
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            metadata['meta_description'] = meta_desc['content'].strip()
        
        # Look for job title
        h1 = soup.find('h1')
        if h1:
            metadata['page_heading'] = h1.get_text().strip()
        
        return metadata
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters
        text = re.sub(r'[\r\n\t]+', '\n', text)
        
        # Remove multiple newlines
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
    
    def is_valid_jd_url(self, url: str) -> bool:
        """
        Check if URL is likely to contain a job description
        
        Args:
            url: URL to check
            
        Returns:
            True if likely a JD URL
        """
        # Common patterns in job posting URLs
        jd_patterns = [
            r'job',
            r'career',
            r'position',
            r'opening',
            r'hiring',
            r'apply',
            r'vacancy',
            r'recruit'
        ]
        
        url_lower = url.lower()
        
        return any(re.search(pattern, url_lower) for pattern in jd_patterns)


# Global JD fetcher service instance
jd_fetcher_service = JDFetcherService()


def get_jd_fetcher_service() -> JDFetcherService:
    """Get JD fetcher service instance"""
    return jd_fetcher_service