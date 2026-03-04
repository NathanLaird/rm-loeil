"""
LLM-powered fact extraction from scraped data.

Uses structured output to extract consistent facts from raw website,
GitHub, and news data.
"""

import os
import json
import logging
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from ..state import WebsiteFacts, GitHubFacts, NewsFacts

logger = logging.getLogger(__name__)


def get_llm(model: str = "gpt-4o-mini"):
    """Get LLM instance based on model name."""
    if "claude" in model.lower():
        return ChatAnthropic(model=model, temperature=0)
    else:
        return ChatOpenAI(model=model, temperature=0)


# === Website Extraction ===

WEBSITE_EXTRACTION_PROMPT = """You are an expert at extracting structured company information from website content.

Analyze the following website content and extract key facts.

WEBSITE CONTENT:
{content}

Extract the following information as JSON. Use null for fields you cannot determine.
Do NOT invent information - only extract what is explicitly stated or clearly implied.

Return a JSON object with these fields:
{{
    "company_name": "Official company name",
    "tagline": "Company tagline or slogan",
    "description": "1-2 sentence description of what they do",
    "key_features": ["List of main product features"],
    "target_customers": "Who the product is for",
    "use_cases": ["List of use cases mentioned"],
    "pricing_model": "Pricing approach (freemium, subscription, etc.)",
    "team_members": [
        {{"name": "Person name", "role": "Their role", "background": "Notable background"}}
    ],
    "notable_customers": ["List of customer names mentioned"],
    "integrations": ["List of integrations or platforms mentioned"],
    "founded_year": 2020,
    "headquarters": "City, State/Country"
}}

Return ONLY valid JSON, no additional text."""

async def extract_website_facts(raw_content: str, llm_model: str = "gpt-4o-mini") -> Optional[WebsiteFacts]:
    """
    Extract structured facts from raw website content.
    
    Args:
        raw_content: Combined text from website pages
        llm_model: Model to use for extraction
        
    Returns:
        WebsiteFacts or None if extraction fails
    """
    if not raw_content or len(raw_content) < 100:
        logger.warning("Website content too short for extraction")
        return None
    
    try:
        llm = get_llm(llm_model)
        prompt = ChatPromptTemplate.from_template(WEBSITE_EXTRACTION_PROMPT)
        parser = JsonOutputParser()
        
        chain = prompt | llm | parser
        
        # Truncate content if too long
        content = raw_content[:30000] if len(raw_content) > 30000 else raw_content
        
        result = await chain.ainvoke({"content": content})
        logger.info(f"Extracted website facts for {result.get('company_name', 'unknown')}")
        return result
        
    except Exception as e:
        logger.error(f"Website extraction failed: {e}")
        return None


# === GitHub Extraction ===

GITHUB_EXTRACTION_PROMPT = """You are an expert at analyzing GitHub organization data for investment research.

Analyze the following GitHub data and extract insights.

GITHUB DATA:
{data}

Extract the following as JSON:
{{
    "organization_name": "GitHub org/user name",
    "bio": "Organization bio/description",
    "public_repos_count": 10,
    "total_stars": 5000,
    "total_forks": 500,
    "top_repositories": [
        {{
            "name": "repo-name",
            "description": "What it does",
            "stars": 1000,
            "forks": 100,
            "primary_language": "Python",
            "last_updated": "2024-01-15",
            "is_actively_maintained": true
        }}
    ],
    "primary_languages": ["Python", "TypeScript"],
    "contributor_estimate": 50,
    "open_source_strategy": "Assessment of their OSS approach"
}}

Return ONLY valid JSON."""

async def extract_github_facts(raw_data: dict, llm_model: str = "gpt-4o-mini") -> Optional[GitHubFacts]:
    """
    Extract structured facts from raw GitHub API data.
    
    Args:
        raw_data: Dictionary from GitHub scraper
        llm_model: Model to use for extraction
        
    Returns:
        GitHubFacts or None if extraction fails
    """
    if not raw_data:
        logger.warning("No GitHub data to extract from")
        return None
    
    try:
        llm = get_llm(llm_model)
        prompt = ChatPromptTemplate.from_template(GITHUB_EXTRACTION_PROMPT)
        parser = JsonOutputParser()
        
        chain = prompt | llm | parser
        
        # Convert dict to string for prompt
        data_str = json.dumps(raw_data, indent=2, default=str)[:20000]
        
        result = await chain.ainvoke({"data": data_str})
        logger.info(f"Extracted GitHub facts: {result.get('total_stars', 0)} total stars")
        return result
        
    except Exception as e:
        logger.error(f"GitHub extraction failed: {e}")
        return None


# === News Extraction ===

NEWS_EXTRACTION_PROMPT = """You are an expert at analyzing news coverage for investment research.

Analyze the following news articles about a company and extract insights.

NEWS ARTICLES:
{articles}

Extract the following as JSON:
{{
    "articles": [
        {{
            "title": "Article title",
            "source": "Publication name",
            "date": "2024-01-15",
            "url": "https://...",
            "summary": "2-3 sentence summary",
            "sentiment": "positive|negative|neutral"
        }}
    ],
    "overall_narrative": "What's the dominant story about this company?",
    "notable_coverage": ["List of particularly significant coverage"],
    "red_flags": ["Any concerning mentions or patterns"],
    "momentum_signal": "Assessment: growing buzz, steady, declining, or unclear"
}}

Return ONLY valid JSON."""

async def extract_news_facts(raw_articles: list, llm_model: str = "gpt-4o-mini") -> Optional[NewsFacts]:
    """
    Extract structured facts from raw news articles.
    
    Args:
        raw_articles: List of article dictionaries from news scraper
        llm_model: Model to use for extraction
        
    Returns:
        NewsFacts or None if extraction fails
    """
    if not raw_articles:
        logger.warning("No news articles to extract from")
        return None
    
    try:
        llm = get_llm(llm_model)
        prompt = ChatPromptTemplate.from_template(NEWS_EXTRACTION_PROMPT)
        parser = JsonOutputParser()
        
        chain = prompt | llm | parser
        
        # Format articles for prompt
        articles_str = json.dumps(raw_articles, indent=2, default=str)[:25000]
        
        result = await chain.ainvoke({"articles": articles_str})
        logger.info(f"Extracted news facts: {len(result.get('articles', []))} articles analyzed")
        return result
        
    except Exception as e:
        logger.error(f"News extraction failed: {e}")
        return None


# === Sync wrappers for non-async contexts ===

def extract_website_facts_sync(raw_content: str, llm_model: str = "gpt-4o-mini") -> Optional[WebsiteFacts]:
    """Synchronous wrapper for extract_website_facts."""
    import asyncio
    return asyncio.run(extract_website_facts(raw_content, llm_model))

def extract_github_facts_sync(raw_data: dict, llm_model: str = "gpt-4o-mini") -> Optional[GitHubFacts]:
    """Synchronous wrapper for extract_github_facts."""
    import asyncio
    return asyncio.run(extract_github_facts(raw_data, llm_model))

def extract_news_facts_sync(raw_articles: list, llm_model: str = "gpt-4o-mini") -> Optional[NewsFacts]:
    """Synchronous wrapper for extract_news_facts."""
    import asyncio
    return asyncio.run(extract_news_facts(raw_articles, llm_model))
