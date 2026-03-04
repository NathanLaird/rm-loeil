"""
Enrichment - Cross-reference facts and generate insights.

This stage takes extracted facts from all sources and:
1. Cross-references for contradictions
2. Identifies patterns
3. Calculates derived metrics
4. Surfaces non-obvious insights
5. Identifies gaps in our knowledge
"""

import json
import logging
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI

from ..state import ExtractedFacts, Enrichment

logger = logging.getLogger(__name__)


ENRICHMENT_PROMPT = """You are a senior investment analyst at a top-tier VC firm.

You have extracted facts about {company} from multiple sources. Your job is to:
1. Cross-reference facts across sources and flag contradictions
2. Identify patterns that suggest company trajectory
3. Calculate useful derived metrics
4. Surface non-obvious insights from combining information
5. Note critical gaps in our knowledge

EXTRACTED FACTS:
{facts}

Analyze these facts and return a JSON object:
{{
    "contradictions": [
        {{"fact1": "...", "fact2": "...", "sources": ["website", "news"], "resolution": "..."}}
    ],
    "patterns": [
        {{
            "observation": "What you noticed",
            "signals": ["Signal 1", "Signal 2"],
            "implication": "What this means for investment thesis"
        }}
    ],
    "derived_metrics": {{
        "stars_per_employee": 500,
        "funding_efficiency": "Low burn rate based on team size vs funding",
        "growth_velocity": "Assessment based on available signals"
    }},
    "gaps": [
        {{
            "missing": "What we don't know",
            "importance": "high|medium|low",
            "how_to_get": "How to fill this gap"
        }}
    ],
    "insights": [
        {{
            "insight": "Non-obvious observation",
            "supporting_evidence": ["Evidence 1", "Evidence 2"],
            "confidence": "high|medium|low"
        }}
    ],
    "risks": [
        {{
            "risk": "Identified risk",
            "severity": "high|medium|low",
            "mitigants": ["Potential mitigant 1"]
        }}
    ],
    "overall_assessment": "2-3 sentence synthesis of what we learned"
}}

Be specific and evidence-based. Don't invent information.
Return ONLY valid JSON."""


async def enrich_facts(
    company: str,
    facts: ExtractedFacts,
    llm_model: str = "gpt-4o"
) -> Optional[Enrichment]:
    """
    Cross-reference and enrich extracted facts.
    
    Uses a more capable model (GPT-4o) for this reasoning-heavy task.
    
    Args:
        company: Company name
        facts: Extracted facts from all sources
        llm_model: Model to use (default GPT-4o for quality)
        
    Returns:
        Enrichment analysis or None if failed
    """
    if not facts:
        logger.warning("No facts to enrich")
        return None
    
    try:
        llm = ChatOpenAI(model=llm_model, temperature=0.1)
        prompt = ChatPromptTemplate.from_template(ENRICHMENT_PROMPT)
        parser = JsonOutputParser()
        
        chain = prompt | llm | parser
        
        # Format facts for prompt
        facts_str = json.dumps(facts, indent=2, default=str)
        
        result = await chain.ainvoke({
            "company": company,
            "facts": facts_str
        })
        
        logger.info(f"Enrichment complete: {len(result.get('insights', []))} insights generated")
        return result
        
    except Exception as e:
        logger.error(f"Enrichment failed: {e}")
        return None


def enrich_facts_sync(company: str, facts: ExtractedFacts, llm_model: str = "gpt-4o") -> Optional[Enrichment]:
    """Synchronous wrapper for enrich_facts."""
    import asyncio
    return asyncio.run(enrich_facts(company, facts, llm_model))
