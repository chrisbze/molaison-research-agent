import requests
import time
import logging
from typing import List, Dict, Any, Optional, Generator
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from fake_useragent import UserAgent
from urllib.parse import urljoin, urlparse
import re

from config.scraper_config import ScrapingTarget, ProductSchema


class MolaisonCrawler:
    """Advanced web scraping framework for product catalogs"""
    
    def __init__(self, target_config: ScrapingTarget, use_selenium: bool = False):
        self.config = target_config
        self.use_selenium = use_selenium
        self.session = requests.Session()
        self.driver = None
        self.ua = UserAgent()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Setup session headers
        self._setup_session()
        
    def _setup_session(self):
        """Configure requests session with headers and user agent rotation"""
        self.session.headers.update(self.config.headers)
        
    def _setup_selenium(self):
        """Initialize Selenium WebDriver with stealth options"""
        if self.driver:
            return
            
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Use headless mode for production
        options.add_argument('--headless')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def _clean_selenium(self):
        """Clean up Selenium driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def _get_page_content(self, url: str) -> BeautifulSoup:
        """Fetch page content using requests or Selenium"""
        try:
            if self.use_selenium:
                if not self.driver:
                    self._setup_selenium()
                
                self.driver.get(url)
                time.sleep(self.config.delay)
                content = self.driver.page_source
                return BeautifulSoup(content, 'lxml')
            else:
                # Rotate user agent occasionally
                if hasattr(self, '_request_count'):
                    self._request_count += 1
                    if self._request_count % 10 == 0:
                        self.session.headers['User-Agent'] = self.ua.random
                else:
                    self._request_count = 1
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                time.sleep(self.config.delay)
                
                return BeautifulSoup(response.content, 'lxml')
                
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            raise
    
    def _extract_text_safely(self, element, selector: str) -> Optional[str]:
        """Safely extract text from element using CSS selector"""
        if not element:
            return None
            
        try:
            found = element.select_one(selector)
            if found:
                text = found.get_text(strip=True)
                return text if text else None
        except Exception as e:
            self.logger.debug(f"Error extracting text with selector '{selector}': {e}")
        
        return None
    
    def _extract_attribute_safely(self, element, selector: str, attribute: str = 'href') -> Optional[str]:
        """Safely extract attribute from element"""
        if not element:
            return None
            
        try:
            found = element.select_one(selector)
            if found and found.has_attr(attribute):
                return found[attribute]
        except Exception as e:
            self.logger.debug(f"Error extracting attribute '{attribute}' with selector '{selector}': {e}")
        
        return None
    
    def _normalize_price(self, price_text: str) -> Optional[str]:
        """Normalize price text by extracting numeric values"""
        if not price_text:
            return None
            
        # Extract price using regex (handles $, €, £, etc.)
        price_match = re.search(r'[\$€£¥]?\s*(\d+(?:\.\d{2})?)', price_text)
        if price_match:
            return price_match.group(1)
        
        # Fallback: extract any decimal number
        decimal_match = re.search(r'(\d+\.\d{2})', price_text)
        if decimal_match:
            return decimal_match.group(1)
        
        # Fallback: extract any number
        number_match = re.search(r'(\d+)', price_text)
        if number_match:
            return number_match.group(1)
        
        return price_text.strip()
    
    def _extract_pricing_from_text(self, text: str) -> Dict[str, str]:
        """Extract pricing information from text using regex patterns"""
        if not text:
            return {}
        
        pricing = {}
        
        # Extract Core Plan Price
        core_match = re.search(r'Core Plan Price\s*\$?(\d+\.?\d*)', text, re.IGNORECASE)
        if core_match:
            pricing['Core Price'] = core_match.group(1)
        
        # Extract Premier Plan Price  
        premier_match = re.search(r'Premier Plan Price\s*\$?(\d+\.?\d*)', text, re.IGNORECASE)
        if premier_match:
            pricing['Premier Price'] = premier_match.group(1)
        
        # Extract Suggested Retail Price
        retail_match = re.search(r'Suggested Retail Price\s*\$?(\d+\.?\d*)', text, re.IGNORECASE)
        if retail_match:
            pricing['Suggested Retail'] = retail_match.group(1)
        
        # Extract bulk pricing if available
        bulk_10_match = re.search(r'10\+[^\d]*\$?(\d+\.?\d*)', text, re.IGNORECASE)
        if bulk_10_match:
            pricing['Bulk 10+'] = bulk_10_match.group(1)
        
        bulk_50_match = re.search(r'50\+[^\d]*\$?(\d+\.?\d*)', text, re.IGNORECASE)
        if bulk_50_match:
            pricing['Bulk 50+'] = bulk_50_match.group(1)
        
        bulk_100_match = re.search(r'100\+[^\d]*\$?(\d+\.?\d*)', text, re.IGNORECASE)
        if bulk_100_match:
            pricing['Bulk 100+'] = bulk_100_match.group(1)
        
        return pricing

    def _fetch_detailed_product_data(self, product_url: str) -> Dict[str, Any]:
        """Fetch detailed product data from individual product page"""
        try:
            # Get product page content
            soup = self._get_page_content(product_url)
            
            # Extract pricing from meta description
            meta_desc = soup.select_one('meta[name="description"]')
            pricing_data = {}
            
            if meta_desc and meta_desc.get('content'):
                pricing_data.update(self._extract_pricing_from_text(meta_desc.get('content')))
            
            # Also check og:description
            og_desc = soup.select_one('meta[property="og:description"]')
            if og_desc and og_desc.get('content'):
                pricing_data.update(self._extract_pricing_from_text(og_desc.get('content')))
            
            # Extract category from breadcrumbs
            category = None
            breadcrumb_links = soup.select('.kadence-breadcrumbs a')
            if len(breadcrumb_links) >= 2:  # Skip Home, get category
                category = breadcrumb_links[-1].get_text(strip=True)
            
            # Extract SKU from product ID if available
            sku = None
            product_div = soup.select_one('[id^="product-"]')
            if product_div:
                sku_match = re.search(r'product-(\d+)', product_div.get('id', ''))
                if sku_match:
                    sku = f"YPB-{sku_match.group(1)}"
            
            # Extract variant/strength from product title
            title_element = soup.select_one('h1.product_title, .product_title')
            variant = None
            if title_element:
                title = title_element.get_text(strip=True)
                # Extract dosage information like (10mg), (5mg), etc.
                variant_match = re.search(r'\(([0-9]+(?:\.[0-9]+)?(?:mg|mcg|iu|ml))\)', title)
                if variant_match:
                    variant = variant_match.group(1)
            
            return {
                'category': category,
                'sku': sku,
                'variant': variant,
                **pricing_data
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching detailed data from {product_url}: {str(e)}")
            return {}

    def _extract_product_data(self, product_element) -> Dict[str, Any]:
        """Extract all product data from a product container element"""
        selectors = self.config.selectors
        
        # Extract basic product information
        product_name = self._extract_text_safely(product_element, selectors.get("product_name", ""))
        
        # Extract product URL first
        product_link = self._extract_attribute_safely(product_element, selectors.get("product_link", "a"))
        product_url = None
        if product_link:
            product_url = urljoin(self.config.base_url, product_link)
        
        # Initialize with basic data
        product_data = {
            "Product Name": product_name,
            "Category": None,
            "SKU": None,
            "Variant/Strength": None,
            "Units/Size": None,
            "Core Price": None,
            "Premier Price": None,
            "Suggested Retail": None,
            "Bulk 10+": None,
            "Bulk 50+": None,
            "Bulk 100+": None,
            "Product URL": product_url
        }
        
        # Fetch detailed data from product page if URL is available
        if product_url:
            detailed_data = self._fetch_detailed_product_data(product_url)
            
            # Update with detailed data
            if detailed_data.get('category'):
                product_data["Category"] = detailed_data['category']
            if detailed_data.get('sku'):
                product_data["SKU"] = detailed_data['sku']
            if detailed_data.get('variant'):
                product_data["Variant/Strength"] = detailed_data['variant']
            
            # Update pricing information
            for price_field in ['Core Price', 'Premier Price', 'Suggested Retail', 'Bulk 10+', 'Bulk 50+', 'Bulk 100+']:
                if detailed_data.get(price_field):
                    product_data[price_field] = detailed_data[price_field]
        
        return product_data
    
    def _get_all_catalog_pages(self) -> Generator[str, None, None]:
        """Generator that yields all catalog page URLs"""
        base_catalog_url = urljoin(self.config.base_url, self.config.catalog_path)
        yield base_catalog_url
        
        if not self.config.pagination:
            return
        
        current_page = 1
        max_pages = self.config.pagination.get("max_pages", 50)
        
        while current_page < max_pages:
            try:
                # Get current page content
                soup = self._get_page_content(base_catalog_url)
                
                # Look for next page link
                next_selector = self.config.pagination.get("selector", ".next")
                next_link_element = soup.select_one(next_selector)
                
                if not next_link_element:
                    self.logger.info("No more pages found")
                    break
                
                # Handle different pagination types
                if self.config.pagination.get("type") == "click" and self.use_selenium:
                    # Click-based pagination (requires Selenium)
                    try:
                        if not self.driver:
                            self._setup_selenium()
                        
                        next_button = self.driver.find_element(By.CSS_SELECTOR, next_selector)
                        if next_button.is_enabled():
                            next_button.click()
                            time.sleep(self.config.delay)
                            current_page += 1
                            yield self.driver.current_url
                        else:
                            break
                    except (NoSuchElementException, TimeoutException):
                        break
                        
                else:
                    # URL-based pagination
                    next_url = next_link_element.get('href')
                    if next_url:
                        base_catalog_url = urljoin(self.config.base_url, next_url)
                        current_page += 1
                        yield base_catalog_url
                    else:
                        break
                        
            except Exception as e:
                self.logger.error(f"Error during pagination: {str(e)}")
                break
    
    def scrape_catalog(self) -> List[Dict[str, Any]]:
        """Main method to scrape the entire product catalog"""
        all_products = []
        
        try:
            for page_url in self._get_all_catalog_pages():
                self.logger.info(f"Scraping page: {page_url}")
                
                try:
                    soup = self._get_page_content(page_url)
                    
                    # Find all product containers
                    product_containers = soup.select(self.config.selectors.get("product_container", ".product"))
                    
                    if not product_containers:
                        self.logger.warning(f"No products found on page: {page_url}")
                        continue
                    
                    # Extract data from each product
                    for container in product_containers:
                        try:
                            product_data = self._extract_product_data(container)
                            
                            # Validate that we have at least a product name or SKU
                            if product_data.get("Product Name") or product_data.get("SKU"):
                                all_products.append(product_data)
                            else:
                                self.logger.debug("Skipping product with no name or SKU")
                                
                        except Exception as e:
                            self.logger.error(f"Error extracting product data: {str(e)}")
                            continue
                    
                    self.logger.info(f"Extracted {len(product_containers)} products from {page_url}")
                    
                except Exception as e:
                    self.logger.error(f"Error scraping page {page_url}: {str(e)}")
                    continue
        
        finally:
            # Clean up Selenium driver if used
            self._clean_selenium()
        
        self.logger.info(f"Total products extracted: {len(all_products)}")
        return all_products
    
    def validate_extraction(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate extracted data and return quality metrics"""
        if not products:
            return {"success": False, "error": "No products extracted"}
        
        total_products = len(products)
        field_stats = {}
        
        # Analyze field completion rates
        for product in products:
            for field, value in product.items():
                if field not in field_stats:
                    field_stats[field] = {"filled": 0, "empty": 0}
                
                if value and str(value).strip():
                    field_stats[field]["filled"] += 1
                else:
                    field_stats[field]["empty"] += 1
        
        # Calculate completion percentages
        field_completion = {}
        for field, stats in field_stats.items():
            completion_rate = (stats["filled"] / total_products) * 100
            field_completion[field] = round(completion_rate, 2)
        
        return {
            "success": True,
            "total_products": total_products,
            "field_completion_rates": field_completion,
            "critical_fields_missing": [
                field for field, rate in field_completion.items() 
                if rate < 50 and field in ["Product Name", "SKU", "Core Price"]
            ]
        }