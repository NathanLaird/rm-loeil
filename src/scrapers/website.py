"""
Company website scraper

Scrapes key pages from a company's website:
- About page
- Product/features page
- Pricing page
- Team page
"""

import os
import logging
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Common paths to try for each page type
PAGE_PATHS = {
    "about": ["/about", "/about-us", "/company", "/about/company"],
    "product": ["/product", "/features", "/platform", "/solutions"],
    "pricing": ["/pricing", "/plans", "/pricing-plans"],
    "team": ["/team", "/about/team", "/about#team", "/people", "/leadership"],
    "customers": ["/customers", "/case-studies", "/success-stories"],
}

# User agent to use for requests
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def clean_html(html: str) -> str:
    """
    Extract readable text from HTML, removing scripts, styles, and navigation.
    
    Args:
        html: Raw HTML string
        
    Returns:
        Cleaned text content
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove unwanted elements
    for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        element.decompose()
    
    # Get text with some structure preserved
    text = soup.get_text(separator="\n", strip=True)
    
    # Clean up excessive whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)
    
    # Truncate if too long (LLM context limits)
    if len(text) > 15000:
        text = text[:15000] + "\n\n[Content truncated...]"
    
    return text


async def fetch_page(client: httpx.AsyncClient, url: str) -> Optional[str]:
    """
    Fetch a single page with error handling.
    
    Args:
        client: httpx async client
        url: URL to fetch
        
    Returns:
        Cleaned text content or None if failed
    """
    try:
        response = await client.get(url, follow_redirects=True, timeout=15.0)
        
        if response.status_code == 200:
            return clean_html(response.text)
        else:
            logger.debug(f"Got {response.status_code} for {url}")
            return None
            
    except httpx.TimeoutException:
        logger.warning(f"Timeout fetching {url}")
        return None
    except httpx.RequestError as e:
        logger.warning(f"Error fetching {url}: {e}")
        return None


async def scrape_website(domain: str) -> dict:
    """
    Scrape key pages from a company website.
    
    Args:
        domain: Company domain (e.g., "cursor.sh")
        
    Returns:
        Dictionary with scraped content:
        {
            "home": "...",
            "about": "...",
            "product": "...",
            "pricing": "...",
            "team": "...",
            "customers": "...",
            "raw_content": "..."  # Combined for LLM
        }
    """
    # Normalize domain to URL
    if not domain.startswith("http"):
        base_url = f"https://{domain}"
    else:
        base_url = domain
        domain = urlparse(domain).netloc
    
    logger.info(f"Scraping website: {base_url}")
    
    results = {}
    
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    async with httpx.AsyncClient(headers=headers) as client:
        # Fetch homepage
        home_content = await fetch_page(client, base_url)
        if home_content:
            results["home"] = home_content
            logger.debug("Fetched homepage")
        
        # Fetch other pages by trying common paths
        for page_type, paths in PAGE_PATHS.items():
            for path in paths:
                url = urljoin(base_url, path)
                content = await fetch_page(client, url)
                if content:
                    results[page_type] = content
                    logger.debug(f"Fetched {page_type} from {path}")
                    break  # Found it, move to next page type
    
    # Combine all content for LLM processing
    combined_parts = []
    for page_type, content in results.items():
        combined_parts.append(f"=== {page_type.upper()} PAGE ===\n{content}\n")
    
    results["raw_content"] = "\n".join(combined_parts)
    results["domain"] = domain
    results["pages_found"] = list(results.keys())
    
    logger.info(f"Scraped {len(results) - 3} pages from {domain}")
    
    return results


def scrape_website_sync(domain: str) -> dict:
    """
    Synchronous wrapper for scrape_website.
    
    Args:
        domain: Company domain
        
    Returns:
        Scraped content dictionary
    """
    import asyncio
    return asyncio.run(scrape_website(domain))


# For testing
if __name__ == "__main__":
    import asyncio
    import json
    
    async def test():
        result = await scrape_website("cursor.sh")
        print(f"Pages found: {result.get('pages_found', [])}")
        print(f"Total content length: {len(result.get('raw_content', ''))}")
        
    asyncio.run(test())
