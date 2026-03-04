"""
Section synthesis - Generate memo sections from facts and enrichment.

Uses Claude for high-quality writing.
"""

import json
import logging
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic

from ..state import ExtractedFacts, Enrichment, MemoSections

logger = logging.getLogger(__name__)


# Section-specific prompts
EXECUTIVE_SUMMARY_PROMPT = """Write an executive summary for a VC research memo about {company}.

FACTS:
{facts}

ANALYSIS:
{enrichment}

TRIGGER SIGNAL: {trigger}

Write a compelling executive summary (150-200 words) that:
1. Opens with what the company does (1 sentence)
2. States why it's interesting NOW - the trigger signal (1 sentence)
3. Highlights 2-3 key supporting signals (2-3 sentences)
4. Closes with a clear bottom-line assessment (1 sentence)

Write for a senior investor who has 30 seconds. Be direct, no fluff.
Use specific numbers and facts where available."""

COMPANY_OVERVIEW_PROMPT = """Write a company overview section for a VC research memo about {company}.

FACTS:
{facts}

Write a comprehensive company overview (300-400 words) covering:
1. What they build (product description)
2. Target market and customers
3. Business model and pricing
4. Founding team backgrounds
5. Brief company history

Use specific facts. If information is missing, note it briefly and move on.
Write in a professional but engaging style."""

MARKET_CONTEXT_PROMPT = """Write a market context section for a VC research memo about {company}.

FACTS:
{facts}

ANALYSIS:
{enrichment}

Write a market context section (250-350 words) covering:
1. Market size and growth (if available)
2. Key trends driving the opportunity
3. Competitive landscape overview
4. Company's positioning and differentiation

Be specific about competitors if mentioned. Acknowledge gaps in market data."""

SIGNAL_ANALYSIS_PROMPT = """Write a signal analysis section for a VC research memo about {company}.

FACTS:
{facts}

ANALYSIS:
{enrichment}

Write a signal analysis section (300-400 words) covering:
1. Growth signals (headcount, GitHub activity, press coverage)
2. Product signals (launches, features, community engagement)
3. Traction indicators (customers, usage metrics if available)
4. Any concerning signals or red flags

Use tables where appropriate for metrics. Be evidence-based."""

RISKS_PROMPT = """Write a risks section for a VC research memo about {company}.

FACTS:
{facts}

ANALYSIS:
{enrichment}

Write a balanced risks section (200-300 words) covering:
1. Competitive risks
2. Execution risks
3. Market risks
4. Any other identified concerns

For each risk, briefly note potential mitigants. Be honest but not alarmist."""

RECOMMENDATION_PROMPT = """Write a recommendation section for a VC research memo about {company}.

FACTS:
{facts}

ANALYSIS:
{enrichment}

Write a clear recommendation section (150-200 words) with:
1. Verdict: Pursue / Pass / Monitor (and why)
2. Key reasons supporting the verdict (bullet points)
3. Critical questions for diligence
4. Suggested next step

Be decisive. Take a position."""


async def generate_section(
    prompt_template: str,
    company: str,
    facts: ExtractedFacts,
    enrichment: Optional[Enrichment] = None,
    trigger: str = "Signal-triggered review",
    llm_model: str = "claude-3-5-sonnet-20241022"
) -> str:
    """Generate a single memo section."""
    try:
        llm = ChatAnthropic(model=llm_model, temperature=0.3, max_tokens=1000)
        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        chain = prompt | llm
        
        facts_str = json.dumps(facts, indent=2, default=str) if facts else "{}"
        enrichment_str = json.dumps(enrichment, indent=2, default=str) if enrichment else "{}"
        
        result = await chain.ainvoke({
            "company": company,
            "facts": facts_str,
            "enrichment": enrichment_str,
            "trigger": trigger
        })
        
        return result.content
        
    except Exception as e:
        logger.error(f"Section generation failed: {e}")
        return f"[Section generation failed: {e}]"


async def generate_sections(
    company: str,
    facts: ExtractedFacts,
    enrichment: Enrichment,
    trigger: str = "Signal-triggered review",
    llm_model: str = "claude-3-5-sonnet-20241022"
) -> MemoSections:
    """
    Generate all memo sections.
    
    Args:
        company: Company name
        facts: Extracted facts from all sources
        enrichment: Cross-referenced analysis
        trigger: What triggered this research
        llm_model: Model to use for writing
        
    Returns:
        MemoSections with all generated content
    """
    logger.info(f"Generating memo sections for {company}")
    
    sections = {}
    
    # Generate each section (could parallelize for speed)
    section_configs = [
        ("executive_summary", EXECUTIVE_SUMMARY_PROMPT),
        ("company_overview", COMPANY_OVERVIEW_PROMPT),
        ("market_context", MARKET_CONTEXT_PROMPT),
        ("signal_analysis", SIGNAL_ANALYSIS_PROMPT),
        ("risks", RISKS_PROMPT),
        ("recommendation", RECOMMENDATION_PROMPT),
    ]
    
    for section_name, prompt_template in section_configs:
        logger.info(f"Generating {section_name}...")
        sections[section_name] = await generate_section(
            prompt_template=prompt_template,
            company=company,
            facts=facts,
            enrichment=enrichment,
            trigger=trigger,
            llm_model=llm_model
        )
    
    logger.info("All sections generated")
    return sections


def generate_sections_sync(
    company: str,
    facts: ExtractedFacts,
    enrichment: Enrichment,
    trigger: str = "Signal-triggered review",
    llm_model: str = "claude-3-5-sonnet-20241022"
) -> MemoSections:
    """Synchronous wrapper for generate_sections."""
    import asyncio
    return asyncio.run(generate_sections(company, facts, enrichment, trigger, llm_model))
