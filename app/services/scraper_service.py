import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import re
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("scraper_service")


class ScraperService:
    """Service for scraping SHL assessment catalog"""
    
    def __init__(self):
        self.base_url = "https://www.shl.com"
        self.catalog_url = settings.SHL_CATALOG_URL
        self.delay = settings.SCRAPER_DELAY
        self.timeout = settings.SCRAPER_TIMEOUT
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.test_type_mapping = {
            'A': 'Ability & Aptitude',
            'B': 'Biodata & Situational Judgement',
            'C': 'Competencies',
            'D': 'Development & 360',
            'E': 'Assessment Exercises',
            'K': 'Knowledge & Skills',
            'P': 'Personality & Behavior',
            'S': 'Simulations'
        }
    
    def get_catalog_page(self, start: int = 0) -> Optional[BeautifulSoup]:
        """Fetch a single catalog page"""
        try:
            url = f"{self.catalog_url}?start={start}&type=1"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching catalog page (start={start}): {e}")
            return None
    
    def get_total_pages(self, soup: BeautifulSoup) -> int:
        """Extract total number of pages from pagination"""
        try:
            pagination = soup.find('ul', class_='pagination')
            if pagination:
                page_items = pagination.find_all('li', class_='pagination__item')
                page_numbers = []
                for item in page_items:
                    link = item.find('a', class_='pagination__link')
                    if link and link.text.strip().isdigit():
                        page_numbers.append(int(link.text.strip()))
                    span = item.find('span', class_='pagination__link')
                    if span and span.text.strip().isdigit():
                        page_numbers.append(int(span.text.strip()))
                
                return max(page_numbers) if page_numbers else 1
        except Exception as e:
            logger.error(f"Error extracting total pages: {e}")
        return 1
    
    def extract_tests_from_page(self, soup: BeautifulSoup) -> list:
        """Extract test information from a catalog page"""
        tests = []
        try:
            table = soup.find('table')
            if not table:
                return tests
            
            rows = table.find_all('tr', attrs={'data-entity-id': True})
            
            for row in rows:
                try:
                    # Extract test name and URL
                    title_cell = row.find('td', class_='custom__table-heading__title')
                    if not title_cell:
                        continue
                    
                    link = title_cell.find('a')
                    if not link:
                        continue
                    
                    test_name = link.text.strip()
                    test_url = self.base_url + link['href']
                    
                    # Extract remote testing support
                    remote_cells = row.find_all('td', class_='custom__table-heading__general')
                    remote_support = "No"
                    adaptive_support = "No"
                    
                    if len(remote_cells) >= 2:
                        if remote_cells[0].find('span', class_='catalogue__circle -yes'):
                            remote_support = "Yes"
                        if remote_cells[1].find('span', class_='catalogue__circle -yes'):
                            adaptive_support = "Yes"
                    
                    # Extract test types
                    test_type_cell = row.find('td', class_='product-catalogue__keys')
                    test_types = []
                    if test_type_cell:
                        type_spans = test_type_cell.find_all('span', class_='product-catalogue__key')
                        for span in type_spans:
                            type_letter = span.text.strip()
                            if type_letter in self.test_type_mapping:
                                test_types.append(self.test_type_mapping[type_letter])
                    
                    tests.append({
                        'name': test_name,
                        'url': test_url,
                        'remote_support': remote_support,
                        'adaptive_support': adaptive_support,
                        'test_type': test_types
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing test row: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error extracting tests from page: {e}")
        
        return tests
    
    def get_test_details(self, test_url: str) -> Dict[str, Any]:
        """Fetch detailed information from individual test page"""
        try:
            response = requests.get(test_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            details = {
                'description': '',
                'job_levels': '',
                'languages': '',
                'duration': None,
                'test_type': []
            }
            
            # Extract description
            desc_section = soup.find('h4', string='Description')
            if desc_section:
                desc_p = desc_section.find_next('p')
                if desc_p:
                    details['description'] = desc_p.text.strip()
            
            # Extract job levels
            job_section = soup.find('h4', string='Job levels')
            if job_section:
                job_p = job_section.find_next('p')
                if job_p:
                    details['job_levels'] = job_p.text.strip()
            
            # Extract languages
            lang_section = soup.find('h4', string='Languages')
            if lang_section:
                lang_p = lang_section.find_next('p')
                if lang_p:
                    details['languages'] = lang_p.text.strip()
            
            # Extract assessment length and duration - FIXED VERSION
            length_section = soup.find('h4', string='Assessment length')
            if length_section:
                # Try to find the parent div and then search within it
                parent_div = length_section.find_parent('div', class_='product-catalogue-training-calendar__row')
                if parent_div:
                    length_p = parent_div.find('p')
                else:
                    # Fallback to the original method
                    length_p = length_section.find_next('p')
                
                if length_p:
                    duration_text = length_p.text.strip()
                    # Look for patterns like "= 10" or "10 minutes" or "10min"
                    # First try: "= XX" pattern
                    match = re.search(r'=\s*(\d+)', duration_text)
                    if not match:
                        # Second try: "XX minutes" or "XX mins" pattern
                        match = re.search(r'(\d+)\s*(?:minutes?|mins?)', duration_text, re.IGNORECASE)
                    if not match:
                        # Third try: just any number in the text
                        match = re.search(r'(\d+)', duration_text)
                    
                    if match:
                        details['duration'] = int(match.group(1))
            
            # Extract test type from detail page
            test_type_text = soup.find('p', class_='product-catalogue__small-text')
            if test_type_text and 'Test Type:' in test_type_text.text:
                type_spans = test_type_text.find_all('span', class_='product-catalogue__key')
                test_types = []
                for span in type_spans:
                    type_letter = span.text.strip()
                    if type_letter in self.test_type_mapping:
                        test_types.append(self.test_type_mapping[type_letter])
                if test_types:
                    details['test_type'] = test_types
            
            return details
            
        except Exception as e:
            logger.error(f"Error fetching test details from {test_url}: {e}")
            return {}
    
    async def scrape_all_tests(self) -> Dict[str, Dict[str, Any]]:
        """Scrape all tests from the catalog with pagination"""
        all_tests = {}
        
        logger.info("Fetching first page to determine total pages...")
        first_page_soup = self.get_catalog_page(0)
        
        if not first_page_soup:
            logger.error("Failed to fetch first page")
            return all_tests
        
        total_pages = self.get_total_pages(first_page_soup)
        logger.info(f"Total pages to scrape: {total_pages}")
        
        # Process first page
        logger.info(f"Processing page 1/{total_pages}...")
        tests_page_1 = self.extract_tests_from_page(first_page_soup)
        logger.info(f"Found {len(tests_page_1)} tests on page 1")
        
        for test in tests_page_1:
            all_tests[test['url']] = test
        
        await asyncio.sleep(self.delay)
        
        # Process remaining pages
        items_per_page = 12
        for page_num in range(2, total_pages + 1):
            start_index = (page_num - 1) * items_per_page
            logger.info(f"Processing page {page_num}/{total_pages} (start={start_index})...")
            
            page_soup = self.get_catalog_page(start_index)
            if not page_soup:
                logger.warning(f"Failed to fetch page {page_num}")
                continue
            
            tests = self.extract_tests_from_page(page_soup)
            logger.info(f"Found {len(tests)} tests on page {page_num}")
            
            for test in tests:
                all_tests[test['url']] = test
            
            await asyncio.sleep(self.delay)
        
        logger.info(f"Total tests collected: {len(all_tests)}")
        logger.info("Fetching detailed information for each test...")
        
        # Fetch detailed information for each test
        for idx, (url, test_data) in enumerate(all_tests.items(), 1):
            logger.info(f"Fetching details {idx}/{len(all_tests)}: {test_data['name']}")
            details = self.get_test_details(url)
            
            if details:
                test_data.update(details)
            
            await asyncio.sleep(self.delay)
        
        return all_tests
    
    def save_to_json(self, data: Dict[str, Any], filename: str = None):
        """Save scraped data to JSON file"""
        filename = filename or settings.ASSESSMENTS_JSON_PATH
        
        try:
            output_path = Path(filename)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            raise
    
    def load_from_json(self, filename: str = None) -> Dict[str, Any]:
        """Load assessments from JSON file"""
        filename = filename or settings.ASSESSMENTS_JSON_PATH
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {len(data)} assessments from {filename}")
            return data
        except FileNotFoundError:
            logger.warning(f"Assessment file not found: {filename}")
            return {}
        except Exception as e:
            logger.error(f"Error loading from JSON: {e}")
            return {}


# Global scraper service instance
scraper_service = ScraperService()


def get_scraper_service() -> ScraperService:
    """Get scraper service instance"""
    return scraper_service