import requests
import json
from typing import List, Optional
from bs4 import BeautifulSoup
import re
from langchain.tools.tavily_search import TavilySearchResults
from models import ProductOffer
from config import TAVILY_API_KEY, MAX_SEARCH_RESULTS

class WebSearcher:
    """Handles web search and product offer extraction using Tavily"""

    def __init__(self):
        self.tavily_api_key = TAVILY_API_KEY
        self.tavily_search = None

        # Initialize Tavily search if API key is available
        if self.tavily_api_key:
            try:
                self.tavily_search = TavilySearchResults(
                    api_key=self.tavily_api_key,
                    max_results=MAX_SEARCH_RESULTS
                )
            except Exception as e:
                print(f"Failed to initialize Tavily search: {e}")

    def search_products(self, query: str) -> List[ProductOffer]:
        """Search for products using Tavily API or fallback"""
        try:
            if self.tavily_search:
                return self._search_with_tavily(query)
            else:
                return self._search_with_fallback(query)
        except Exception as e:
            print(f"Search error: {e}")
            return self._search_with_fallback(query)

    def _search_with_tavily(self, query: str) -> List[ProductOffer]:
        """Search using Tavily API"""
        try:
            # Enhance query for product search
            enhanced_query = f"{query} buy online price comparison shopping deals"

            # Perform search
            search_results = self.tavily_search.invoke(enhanced_query)

            # Extract offers from results
            offers = []
            for result in search_results:
                offer = self._extract_offer_from_tavily_result(result)
                if offer:
                    offers.append(offer)

            return offers[:MAX_SEARCH_RESULTS]

        except Exception as e:
            print(f"Tavily search error: {e}")
            return self._search_with_fallback(query)

    def _extract_offer_from_tavily_result(self, result: dict) -> Optional[ProductOffer]:
        """Extract product offer from Tavily search result"""
        try:
            # Extract basic information
            title = result.get("title", "")
            url = result.get("url", "")
            content = result.get("content", "")

            if not title or not url:
                return None

            # Try to extract price from content
            price = self._extract_price(content)

            # Extract source domain from URL
            source = self._extract_domain(url)

            # Create offer
            offer = ProductOffer(
                title=title,
                price=price,
                url=url,
                source=source,
                description=content[:200] + "..." if len(content) > 200 else content
            )

            return offer

        except Exception as e:
            print(f"Error extracting offer from Tavily result: {e}")
            return None

    def _search_with_fallback(self, query: str) -> List[ProductOffer]:
        """Fallback search with simulated results"""
        offers = []

        # Simulate finding some offers
        sample_offers = [
            ProductOffer(
                title=f"Sample {query} Offer 1",
                price="$99.99",
                url="https://example.com/product1",
                source="Example Store",
                description=f"High-quality {query} with great features"
            ),
            ProductOffer(
                title=f"Premium {query} Deal",
                price="$149.99",
                url="https://example.com/product2",
                source="Premium Store",
                description=f"Premium {query} with warranty"
            )
        ]

        return sample_offers

    def _extract_price(self, text: str) -> Optional[str]:
        """Extract price from text using regex"""
        price_patterns = [
            r'\$\d+(?:\.\d{2})?',
            r'\d+(?:\.\d{2})?\s*(?:USD|dollars?)',
            r'Price:\s*\$?\d+(?:\.\d{2})?'
        ]

        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group()
        return None

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            # Fallback: simple extraction
            if '//' in url:
                domain = url.split('//')[1].split('/')[0]
                if domain.startswith('www.'):
                    domain = domain[4:]
                return domain
            return "Unknown"

    def extract_from_url(self, url: str) -> Optional[ProductOffer]:
        """Extract product information from a pasted URL"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Try to extract product information
            title = self._extract_title(soup)
            price = self._extract_price_from_page(soup)
            description = self._extract_description(soup)

            if title:
                return ProductOffer(
                    title=title,
                    price=price,
                    url=url,
                    source=url.split('/')[2] if len(url.split('/')) > 2 else "Unknown",
                    description=description
                )
        except Exception as e:
            print(f"Error extracting from URL {url}: {e}")

        return None

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product title from webpage"""
        title_selectors = [
            'h1',
            '[class*="title"]',
            '[class*="product-name"]',
            'title'
        ]

        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                return element.get_text().strip()
        return None

    def _extract_price_from_page(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract price from webpage"""
        price_selectors = [
            '[class*="price"]',
            '[class*="cost"]',
            'span[data-price]',
            '.price'
        ]

        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text().strip()
                price = self._extract_price(text)
                if price:
                    return price
        return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product description from webpage"""
        desc_selectors = [
            '[class*="description"]',
            '[class*="summary"]',
            'meta[name="description"]',
            '.description'
        ]

        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                else:
                    return element.get_text().strip()
        return None
