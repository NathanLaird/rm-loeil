"""
MemoState - TypedDict for LangGraph pipeline state
"""

from typing import TypedDict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


class TriggerInfo(TypedDict, total=False):
    """Information about what triggered this research"""
    signal: str
    value: str
    date: str


class TeamMember(TypedDict, total=False):
    """Extracted team member information"""
    name: str
    role: str
    background: Optional[str]


class WebsiteFacts(TypedDict, total=False):
    """Structured facts extracted from company website"""
    company_name: str
    tagline: Optional[str]
    description: Optional[str]
    key_features: list[str]
    target_customers: Optional[str]
    use_cases: list[str]
    pricing_model: Optional[str]
    team_members: list[TeamMember]
    notable_customers: list[str]
    integrations: list[str]
    founded_year: Optional[int]
    headquarters: Optional[str]


class RepoInfo(TypedDict, total=False):
    """GitHub repository information"""
    name: str
    description: Optional[str]
    stars: int
    forks: int
    primary_language: Optional[str]
    last_updated: str
    is_actively_maintained: bool


class GitHubFacts(TypedDict, total=False):
    """Structured facts extracted from GitHub"""
    organization_name: str
    bio: Optional[str]
    public_repos_count: int
    total_stars: int
    total_forks: int
    top_repositories: list[RepoInfo]
    primary_languages: list[str]
    contributor_estimate: int
    open_source_strategy: Optional[str]


class NewsArticle(TypedDict, total=False):
    """News article information"""
    title: str
    source: str
    date: str
    url: str
    summary: str
    sentiment: str


class NewsFacts(TypedDict, total=False):
    """Structured facts extracted from news"""
    articles: list[NewsArticle]
    overall_narrative: Optional[str]
    notable_coverage: list[str]
    red_flags: list[str]
    momentum_signal: Optional[str]


class CrunchbaseFacts(TypedDict, total=False):
    """Structured facts from Crunchbase"""
    total_raised: Optional[float]
    last_round_date: Optional[str]
    last_round_amount: Optional[float]
    last_round_type: Optional[str]
    investors: list[str]
    founded_date: Optional[str]
    employee_range: Optional[str]


class ExtractedFacts(TypedDict, total=False):
    """All extracted facts by source"""
    website: Optional[WebsiteFacts]
    github: Optional[GitHubFacts]
    news: Optional[NewsFacts]
    crunchbase: Optional[CrunchbaseFacts]


class Pattern(TypedDict, total=False):
    """Identified pattern from cross-referencing"""
    observation: str
    signals: list[str]
    implication: str


class Gap(TypedDict, total=False):
    """Identified gap in data"""
    missing: str
    importance: str
    how_to_get: Optional[str]


class Insight(TypedDict, total=False):
    """Non-obvious insight"""
    insight: str
    supporting_evidence: list[str]
    confidence: str


class Risk(TypedDict, total=False):
    """Identified risk"""
    risk: str
    severity: str
    mitigants: list[str]


class Enrichment(TypedDict, total=False):
    """Cross-referenced analysis and insights"""
    contradictions: list[dict]
    patterns: list[Pattern]
    derived_metrics: dict[str, Any]
    gaps: list[Gap]
    insights: list[Insight]
    risks: list[Risk]
    overall_assessment: Optional[str]


class MemoSections(TypedDict, total=False):
    """Generated memo sections"""
    executive_summary: str
    company_overview: str
    market_context: str
    signal_analysis: str
    risks: str
    recommendation: str


class MemoState(TypedDict, total=False):
    """
    Main state object that flows through the LangGraph pipeline.
    
    This TypedDict defines all the data that accumulates as the
    memo generation pipeline progresses through its stages.
    """
    # Input
    company: str  # Company name
    domain: str   # Company domain (e.g., cursor.sh)
    trigger: Optional[TriggerInfo]
    
    # Raw data from scrapers
    raw_website: Optional[str]
    raw_github: Optional[dict]
    raw_news: Optional[list[dict]]
    raw_crunchbase: Optional[dict]
    
    # Extracted facts
    facts: Optional[ExtractedFacts]
    
    # Enrichment analysis
    enrichment: Optional[Enrichment]
    
    # Synthesized sections
    sections: Optional[MemoSections]
    
    # Final output
    memo: Optional[str]
    
    # Metadata
    errors: list[str]
    sources_used: list[str]
    confidence: str  # high | medium | low
    generated_at: Optional[str]
