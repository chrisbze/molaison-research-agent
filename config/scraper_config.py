from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


@dataclass
class ScrapingTarget:
    """Configuration for a specific scraping target"""
    name: str
    base_url: str
    catalog_path: str = "/catalog/"
    selectors: Dict[str, str] = None
    pagination: Dict[str, Any] = None
    headers: Dict[str, str] = None
    delay: float = 1.0
    
    def __post_init__(self):
        if self.selectors is None:
            self.selectors = {}
        if self.pagination is None:
            self.pagination = {}
        if self.headers is None:
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }


class ProductSchema(BaseModel):
    """Schema for product data validation"""
    product_name: Optional[str] = Field(None, alias="Product Name")
    category: Optional[str] = Field(None, alias="Category")
    sku: Optional[str] = Field(None, alias="SKU")
    variant_strength: Optional[str] = Field(None, alias="Variant/Strength")
    units_size: Optional[str] = Field(None, alias="Units/Size")
    core_price: Optional[str] = Field(None, alias="Core Price")
    premier_price: Optional[str] = Field(None, alias="Premier Price")
    suggested_retail: Optional[str] = Field(None, alias="Suggested Retail")
    bulk_10: Optional[str] = Field(None, alias="Bulk 10+")
    bulk_50: Optional[str] = Field(None, alias="Bulk 50+")
    bulk_100: Optional[str] = Field(None, alias="Bulk 100+")
    product_url: Optional[str] = Field(None, alias="Product URL")
    margin_fields: Optional[Dict] = Field(None, alias="Margin Fields")


# Default configuration for common e-commerce platforms
DEFAULT_CONFIGS = {
    "peptide_brand": ScrapingTarget(
        name="Peptide Brand Site",
        base_url="https://yourpeptidebrand.com",
        catalog_path="/catalog/",
        selectors={
            "product_container": ".product-item, .product-card, .product",
            "product_name": ".product-title, .product-name, h2, h3",
            "category": ".category, .product-category, .breadcrumb",
            "sku": ".sku, .product-sku, [data-sku]",
            "variant": ".variant, .strength, .product-variant",
            "units": ".units, .size, .product-size",
            # Updated selectors for YourPeptideBrand.com structure
            "meta_description": "meta[name='description']",
            "meta_og_description": "meta[property='og:description']",
            "product_link": "a[href*='product'], a[href*='item']",
            "next_page": ".next, .pagination-next, a[rel='next']"
        },
        pagination={
            "type": "url",  # Changed to URL-based pagination
            "selector": ".next, .pagination-next",
            "max_pages": 100
        },
        delay=2.0
    ),
    
    "generic_ecommerce": ScrapingTarget(
        name="Generic E-commerce",
        base_url="",
        selectors={
            "product_container": ".product, .item, .card",
            "product_name": "h1, h2, h3, .title, .name",
            "price": ".price, .cost, .amount",
            "description": ".description, .desc, .summary",
            "product_link": "a",
            "next_page": ".next, .pagination-next"
        }
    )
}


class ScrapingConfig:
    """Main configuration class for the scraping framework"""
    
    def __init__(self, config_name: str = "peptide_brand"):
        self.target = DEFAULT_CONFIGS.get(config_name, DEFAULT_CONFIGS["generic_ecommerce"])
        self.schema = ProductSchema
        
    def get_target_config(self) -> ScrapingTarget:
        return self.target
    
    def update_selectors(self, selectors: Dict[str, str]):
        """Update CSS selectors for specific site"""
        self.target.selectors.update(selectors)
    
    def update_headers(self, headers: Dict[str, str]):
        """Update request headers"""
        self.target.headers.update(headers)