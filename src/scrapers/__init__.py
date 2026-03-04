"""
Data scrapers for various sources
"""

from .website import scrape_website
from .github import scrape_github
from .news import scrape_news
from .crunchbase import scrape_crunchbase

__all__ = ["scrape_website", "scrape_github", "scrape_news", "scrape_crunchbase"]
