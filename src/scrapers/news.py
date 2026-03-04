"""
News search scraper

Uses Tavily API if available, falls back to web search.
"""

import os
import logging
from typing import Optional
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)

TAVILY_API_URL = "https://api.tavily.com/search"


async def search_tavily(query: str, max_results: int = 10) -> list[dict]:
    """
    Search using Tavily API.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        List of search results
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        logger.warning("TAVILY_API_KEY not set, skipping Tavily search")
        return []
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TAVILY_API_URL,
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": max_results,
                    "include_domains": [],
                    "exclude_domains": [],
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                logger.warning(f"Tavily API error: {response.status_code}")
                return []
                
    except httpx.RequestError as e:
        logger.warning(f"Tavily request error: {e}")
        return []


async def search_duckduckgo(query: str, max_results: int = 10) -> list[dict]:
    """
    Fallback search using DuckDuckGo HTML (no API key needed).
    
    This is a lightweight fallback - not as good as Tavily but works.
    
    Args:
        query: Search query
        max_results: Maximum results
        
    Returns:
        List of search results
    """
    from bs4 import BeautifulSoup
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15.0,
                follow_redirects=True
            )
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            
            for result in soup.select(".result")[:max_results]:
                title_elem = result.select_one(".result__a")
                snippet_elem = result.select_one(".result__snippet")
                
                if title_elem:
                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "url": title_elem.get("href", ""),
                        "content": snippet_elem.get_text(strip=True) if snippet_elem else "",
                    })
            
            return results
            
    except Exception as e:
        logger.warning(f"DuckDuckGo search error: {e}")
        return []


async def scrape_news(company: str, domain: str) -> dict:
    """
    Search for recent news about a company.
    
    Args:
        company: Company name
        domain: Company domain
        
    Returns:
        Dictionary with news data:
        {
            "articles": [...],
            "query_used": "...",
            "source": "tavily" | "duckduckgo",
            "error": None or "..."
        }
    """
    logger.info(f"Searching news for {company}")
    
    # Build search query
    # Include company name and domain for better results
    query = f'"{company}" OR site:{domain} news funding startup'
    
    # Try Tavily first (better quality)
    results = await search_tavily(query)
    source = "tavily"
    
    # Fallback to DuckDuckGo if Tavily unavailable
    if not results:
        query = f"{company} {domain.split('.')[0]} news funding"
        results = await search_duckduckgo(query)
        source = "duckduckgo"
    
    # Process results into consistent format
    articles = []
    for r in results:
        article = {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", "") or r.get("snippet", ""),
            "source": extract_source_name(r.get("url", "")),
            "published_date": r.get("published_date"),  # Tavily provides this
        }
        articles.append(article)
    
    return {
        "articles": articles,
        "query_used": query,
        "source": source,
        "article_count": len(articles),
        "error": None if articles else "No news articles found",
    }


def extract_source_name(url: str) -> str:
    """Extract publication name from URL."""
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        # Common mappings
        mappings = {
            "techcrunch.com": "TechCrunch",
            "theverge.com": "The Verge",
            "wired.com": "Wired",
            "forbes.com": "Forbes",
            "bloomberg.com": "Bloomberg",
            "reuters.com": "Reuters",
            "nytimes.com": "New York Times",
            "wsj.com": "Wall Street Journal",
            "venturebeat.com": "VentureBeat",
            "businessinsider.com": "Business Insider",
            "crunchbase.com": "Crunchbase News",
        }
        return mappings.get(domain, domain)
    except Exception:
        return url


def scrape_news_sync(company: str, domain: str) -> dict:
    """Synchronous wrapper for scrape_news."""
    import asyncio
    return asyncio.run(scrape_news(company, domain))


# For testing
if __name__ == "__main__":
    import asyncio
    import json
    
    async def test():
        result = await scrape_news("Cursor", "cursor.sh")
        print(json.dumps(result, indent=2, default=str))
        
    asyncio.run(test())
