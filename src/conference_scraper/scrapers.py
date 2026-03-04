"""
Conference scrapers - fetch and extract event data from conference websites.

This module provides:
1. Generic LLM-powered scraper for any conference page
2. Specific scrapers for known high-value sources
"""

import logging
import re
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from .state import Event, Speaker, EventTier, ScraperConfig

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


async def fetch_page(url: str) -> Optional[str]:
    """Fetch a page with error handling."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"User-Agent": USER_AGENT},
                follow_redirects=True,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.text
            logger.warning(f"Got {response.status_code} for {url}")
            return None
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def clean_text(text: str) -> str:
    """Clean extracted text."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()


# =============================================================================
# TechCrunch Disrupt Scraper
# =============================================================================

async def scrape_techcrunch_disrupt() -> list[Event]:
    """
    Scrape TechCrunch Disrupt speaker information.
    
    Note: TechCrunch uses JavaScript rendering, so this scrapes
    what's available in the initial HTML. For full data, would need
    browser-use or Playwright.
    """
    url = "https://techcrunch.com/events/techcrunch-disrupt-2024/speakers/"
    logger.info(f"Scraping TechCrunch Disrupt: {url}")
    
    html = await fetch_page(url)
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    speakers = []
    
    # TechCrunch speaker cards (structure may change)
    speaker_cards = soup.select('.speaker-card, .wp-block-tc24-speaker-card, article.speaker')
    
    for card in speaker_cards:
        name_el = card.select_one('h3, h2, .speaker-name, .name')
        title_el = card.select_one('.title, .speaker-title, .job-title')
        company_el = card.select_one('.company, .speaker-company, .organization')
        
        if name_el:
            speakers.append(Speaker(
                name=clean_text(name_el.get_text()),
                title=clean_text(title_el.get_text()) if title_el else None,
                company=clean_text(company_el.get_text()) if company_el else None,
            ))
    
    if speakers:
        event = Event(
            name="TechCrunch Disrupt 2024",
            source_url=url,
            start_date=datetime(2024, 10, 28),
            end_date=datetime(2024, 10, 30),
            location="San Francisco, CA",
            city="San Francisco",
            country="USA",
            is_virtual=False,
            speakers=speakers,
            tier=EventTier.TIER_1,
            description="TechCrunch's flagship startup conference",
            source_name="techcrunch_disrupt",
        )
        logger.info(f"Extracted {len(speakers)} speakers from TechCrunch Disrupt")
        return [event]
    
    logger.warning("No speakers found - page structure may have changed")
    return []


# =============================================================================
# Web Summit Scraper
# =============================================================================

async def scrape_websummit() -> list[Event]:
    """
    Scrape Web Summit speaker information.
    
    Web Summit publishes speaker lists at websummit.com/speakers
    """
    url = "https://websummit.com/speakers"
    logger.info(f"Scraping Web Summit: {url}")
    
    html = await fetch_page(url)
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    speakers = []
    
    # Web Summit speaker cards
    speaker_cards = soup.select('.speaker-card, [data-speaker], .speaker')
    
    for card in speaker_cards:
        name_el = card.select_one('.speaker-name, h3, h4, .name')
        title_el = card.select_one('.speaker-title, .title, .role')
        company_el = card.select_one('.speaker-company, .company, .org')
        
        if name_el:
            speakers.append(Speaker(
                name=clean_text(name_el.get_text()),
                title=clean_text(title_el.get_text()) if title_el else None,
                company=clean_text(company_el.get_text()) if company_el else None,
            ))
    
    if speakers:
        event = Event(
            name="Web Summit 2024",
            source_url=url,
            start_date=datetime(2024, 11, 11),
            end_date=datetime(2024, 11, 14),
            location="Lisbon, Portugal",
            city="Lisbon",
            country="Portugal",
            is_virtual=False,
            speakers=speakers,
            tier=EventTier.TIER_1,
            description="The world's largest tech conference",
            source_name="websummit",
        )
        logger.info(f"Extracted {len(speakers)} speakers from Web Summit")
        return [event]
    
    logger.warning("No speakers found - page structure may have changed")
    return []


# =============================================================================
# Generic LLM Scraper (for unknown pages)
# =============================================================================

EXTRACTION_PROMPT = """You are an expert at extracting structured event and speaker data from HTML.

Analyze this conference/event page and extract all speakers you can find.

HTML CONTENT:
{html}

Return a JSON array of speakers:
[
    {{
        "name": "Full Name",
        "title": "Job Title",
        "company": "Company Name"
    }}
]

Also extract event metadata if visible:
{{
    "event_name": "Conference Name",
    "dates": "Date string as shown",
    "location": "City, Country"
}}

Return ONLY valid JSON with "speakers" and "event" keys."""


async def scrape_generic_llm(
    url: str,
    source_name: str,
    llm_model: str = "gpt-4o-mini"
) -> list[Event]:
    """
    Generic scraper using LLM to extract event/speaker data.
    
    Args:
        url: Conference page URL
        source_name: Identifier for this source
        llm_model: Model to use for extraction
        
    Returns:
        List of extracted events
    """
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    from langchain_openai import ChatOpenAI
    
    logger.info(f"Scraping {source_name} with LLM: {url}")
    
    html = await fetch_page(url)
    if not html:
        return []
    
    # Clean HTML for LLM
    soup = BeautifulSoup(html, 'html.parser')
    for element in soup(['script', 'style', 'nav', 'footer', 'header']):
        element.decompose()
    
    text = soup.get_text(separator='\n', strip=True)
    # Truncate for context limits
    text = text[:30000]
    
    try:
        llm = ChatOpenAI(model=llm_model, temperature=0)
        prompt = ChatPromptTemplate.from_template(EXTRACTION_PROMPT)
        parser = JsonOutputParser()
        
        chain = prompt | llm | parser
        result = await chain.ainvoke({"html": text})
        
        speakers = [
            Speaker(
                name=s.get("name", "Unknown"),
                title=s.get("title"),
                company=s.get("company"),
            )
            for s in result.get("speakers", [])
            if s.get("name")
        ]
        
        event_data = result.get("event", {})
        
        event = Event(
            name=event_data.get("event_name", f"Event from {source_name}"),
            source_url=url,
            date_raw=event_data.get("dates"),
            location=event_data.get("location"),
            speakers=speakers,
            tier=EventTier.UNKNOWN,
            source_name=source_name,
        )
        
        logger.info(f"LLM extracted {len(speakers)} speakers from {source_name}")
        return [event]
        
    except Exception as e:
        logger.error(f"LLM extraction failed for {source_name}: {e}")
        return []


# =============================================================================
# Scraper Registry
# =============================================================================

SCRAPER_REGISTRY = {
    "techcrunch_disrupt": scrape_techcrunch_disrupt,
    "websummit": scrape_websummit,
}


async def scrape_source(config: ScraperConfig) -> list[Event]:
    """
    Scrape events from a configured source.
    
    Uses registered scraper if available, otherwise falls back to LLM.
    """
    source_name = config.source_name
    
    # Check for specific scraper
    if source_name in SCRAPER_REGISTRY:
        return await SCRAPER_REGISTRY[source_name]()
    
    # Fall back to LLM generic scraper
    return await scrape_generic_llm(
        url=config.source_url,
        source_name=source_name,
    )


# =============================================================================
# Testing
# =============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test TechCrunch
        events = await scrape_techcrunch_disrupt()
        print(f"\nTechCrunch: {len(events)} events")
        if events:
            print(f"  Speakers: {len(events[0].speakers)}")
            for s in events[0].speakers[:5]:
                print(f"    - {s.name} ({s.company})")
        
        # Test Web Summit
        events = await scrape_websummit()
        print(f"\nWeb Summit: {len(events)} events")
        if events:
            print(f"  Speakers: {len(events[0].speakers)}")
            for s in events[0].speakers[:5]:
                print(f"    - {s.name} ({s.company})")
    
    asyncio.run(test())
