"""
Conference Scraper - Self-healing web scraping for event discovery.

This package implements the "genetic evolution" pattern for web scrapers:
1. LLM generates scrapers based on website structure
2. Scrapers run deterministically (cheap, no LLM needed)
3. When scrapers fail 3+ times, a repair agent rewrites them
4. If repair fails 5+ times, escalate to human

Key components:
- state: Data models and LangGraph state definitions
- scrapers: Self-healing scraper infrastructure
"""

from .state import (
    Event,
    Speaker,
    EventTier,
    ScraperConfig,
    ScraperState,
    SourceHealth,
    TARGET_COMPANIES,
)
from .pipeline import build_conference_pipeline, run_pipeline, run_pipeline_sync
from .scrapers import scrape_source, scrape_generic_llm

__version__ = "0.1.0"

__all__ = [
    "Event",
    "Speaker",
    "EventTier",
    "ScraperConfig",
    "ScraperState",
    "SourceHealth",
    "TARGET_COMPANIES",
    "build_conference_pipeline",
    "run_pipeline",
    "run_pipeline_sync",
    "scrape_source",
    "scrape_generic_llm",
]
