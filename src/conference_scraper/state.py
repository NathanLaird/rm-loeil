"""
State definitions for the Conference Scraper pipeline.

This module defines:
- Data models (Event, Speaker, Source)
- Scraper configuration and health tracking
- LangGraph state TypedDict
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, TypedDict, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Data Models
# =============================================================================


class Speaker(BaseModel):
    """A speaker at a conference event."""

    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    company_normalized: Optional[str] = None  # For matching against targets
    linkedin_url: Optional[str] = None
    bio: Optional[str] = None

    def matches_target(self, target_companies: list[dict]) -> Optional[dict]:
        """Check if this speaker is from a target company."""
        if not self.company:
            return None
        company_lower = self.company.lower()
        company_norm = self.company_normalized.lower() if self.company_normalized else company_lower

        for target in target_companies:
            target_name = target.get("name", "").lower()
            if target_name in company_lower or target_name in company_norm:
                return target
        return None


class EventTier(str, Enum):
    """Event importance tier based on attendance patterns."""

    TIER_1 = "tier_1"  # Major conferences (Web Summit, TechCrunch Disrupt)
    TIER_2 = "tier_2"  # Industry-specific (SaaStr, DevConnect)
    TIER_3 = "tier_3"  # Smaller/regional events
    UNKNOWN = "unknown"


class Event(BaseModel):
    """A conference or event with potential target company speakers."""

    # Core fields
    name: str
    source_url: str

    # Dates
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    date_raw: Optional[str] = None  # Original date string for debugging

    # Location
    location: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    is_virtual: bool = False

    # Speakers
    speakers: list[Speaker] = Field(default_factory=list)

    # Metadata
    tier: EventTier = EventTier.UNKNOWN
    description: Optional[str] = None
    event_url: Optional[str] = None  # Official event website
    registration_url: Optional[str] = None

    # Provenance
    source_name: Optional[str] = None  # e.g., "techcrunch_disrupt"
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    extraction_confidence: float = 1.0

    # Deduplication
    canonical_id: Optional[str] = None  # Set after entity resolution

    def has_target_speakers(self, target_companies: list[dict]) -> list[tuple[Speaker, dict]]:
        """Find speakers from target companies."""
        matches = []
        for speaker in self.speakers:
            target = speaker.matches_target(target_companies)
            if target:
                matches.append((speaker, target))
        return matches


# =============================================================================
# Scraper Configuration & Health
# =============================================================================


class ScraperType(str, Enum):
    """Type of scraper implementation."""

    SELECTOR_BASED = "selector_based"  # CSS/XPath selectors
    LLM_GENERIC = "llm_generic"  # Full LLM extraction
    HYBRID = "hybrid"  # Selectors + LLM cleanup


@dataclass
class SourceHealth:
    """Track health metrics for a scraper."""

    source_name: str
    consecutive_failures: int = 0
    total_failures: int = 0
    total_successes: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    last_error: Optional[str] = None
    repair_attempts: int = 0
    is_escalated: bool = False  # True if needs human intervention

    def record_success(self) -> None:
        """Record a successful scrape."""
        self.consecutive_failures = 0
        self.total_successes += 1
        self.last_success = datetime.utcnow()

    def record_failure(self, error: str) -> None:
        """Record a failed scrape."""
        self.consecutive_failures += 1
        self.total_failures += 1
        self.last_failure = datetime.utcnow()
        self.last_error = error

    def needs_repair(self, threshold: int = 3) -> bool:
        """Check if scraper needs repair agent intervention."""
        return self.consecutive_failures >= threshold and not self.is_escalated

    def record_repair_attempt(self) -> None:
        """Record a repair attempt."""
        self.repair_attempts += 1

    def should_escalate(self, max_repairs: int = 5) -> bool:
        """Check if should escalate to human."""
        return self.repair_attempts >= max_repairs


@dataclass
class ScraperConfig:
    """Configuration for a specific source scraper."""

    source_name: str
    source_url: str
    scraper_type: ScraperType = ScraperType.LLM_GENERIC

    # Selector-based config (for SELECTOR_BASED or HYBRID)
    selectors: dict[str, str] = field(default_factory=dict)
    # Example: {"event_list": ".event-item", "name": "h2.title", "date": ".date"}

    # LLM-generated scraper code (stored as string for self-healing)
    scraper_code: Optional[str] = None

    # Scheduling
    scrape_interval_hours: int = 24
    last_scraped: Optional[datetime] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1


# =============================================================================
# LangGraph State
# =============================================================================


class ScraperState(TypedDict, total=False):
    """
    State for the LangGraph scraping pipeline.

    This state flows through all nodes in the pipeline.
    """

    # Input
    target_companies: list[dict]  # Companies to watch for
    source_configs: list[ScraperConfig]  # Sources to scrape
    source_health: dict[str, SourceHealth]  # Health per source

    # Discovery phase
    discovered_urls: list[str]  # New URLs found via search
    search_queries: list[str]  # Queries used

    # Scraping phase
    raw_html: dict[str, str]  # source_name -> HTML content
    scrape_errors: dict[str, str]  # source_name -> error message

    # Extraction phase
    extracted_events: list[Event]  # Events extracted from sources

    # Resolution phase
    deduplicated_events: list[Event]  # After entity resolution
    event_clusters: dict[str, list[str]]  # canonical_id -> [source_urls]

    # Matching phase
    matched_events: list[dict]  # Events with target company speakers
    # Each dict: {"event": Event, "matches": [(Speaker, target_company)]}

    # Repair phase
    sources_needing_repair: list[str]  # source_names that failed
    repair_results: dict[str, str]  # source_name -> new scraper code
    escalated_sources: list[str]  # Sources needing human help

    # Alert phase
    alerts_sent: list[dict]  # Record of sent alerts

    # Metadata
    run_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    errors: list[str]


# =============================================================================
# Target Companies (Example Portfolio)
# =============================================================================

TARGET_COMPANIES = [
    {"name": "LangChain", "ceo": "Harrison Chase", "aliases": ["langchain-ai"]},
    {"name": "Temporal", "ceo": "Maxim Fateev", "aliases": ["temporal.io"]},
    {"name": "Glean", "ceo": "Arvind Jain", "aliases": ["glean.com"]},
    {"name": "Anthropic", "ceo": "Dario Amodei", "aliases": []},
    {"name": "OpenAI", "ceo": "Sam Altman", "aliases": []},
    {"name": "Databricks", "ceo": "Ali Ghodsi", "aliases": []},
    {"name": "Stripe", "ceo": "Patrick Collison", "aliases": []},
    {"name": "Figma", "ceo": "Dylan Field", "aliases": []},
]
