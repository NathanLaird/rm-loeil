"""
Research Memo Generator - LangGraph Pipeline

This is the main orchestration pipeline that coordinates:
1. Parallel data scraping from multiple sources
2. LLM-powered fact extraction
3. Cross-source enrichment and analysis
4. Memo section synthesis
5. Final assembly and delivery

Built on LangGraph (Sapphire portfolio company).
"""

import logging
import asyncio
from datetime import datetime
from typing import Annotated, Literal

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from .state import MemoState, TriggerInfo
from .scrapers.website import scrape_website
from .scrapers.github import scrape_github
from .scrapers.news import scrape_news
from .scrapers.crunchbase import scrape_crunchbase
from .extractors.facts import (
    extract_website_facts,
    extract_github_facts,
    extract_news_facts,
)
from .synthesis.enrichment import enrich_facts
from .synthesis.sections import generate_sections
from .output.markdown import assemble_memo

logger = logging.getLogger(__name__)


# === Pipeline Nodes ===

async def intake_node(state: MemoState) -> MemoState:
    """
    Intake stage - validate inputs and prepare for scraping.
    """
    logger.info(f"Starting research memo for: {state['company']}")
    
    return {
        **state,
        "errors": [],
        "sources_used": [],
        "generated_at": datetime.now().isoformat(),
    }


async def scrape_node(state: MemoState) -> MemoState:
    """
    Scraping stage - fetch data from all sources in parallel.
    """
    logger.info(f"Scraping data for {state['domain']}")
    
    errors = list(state.get("errors", []))
    sources_used = []
    
    # Run scrapers in parallel
    results = await asyncio.gather(
        scrape_website(state["domain"]),
        scrape_github(state["company"], state["domain"]),
        scrape_news(state["company"]),
        scrape_crunchbase(state["company"], state["domain"]),
        return_exceptions=True
    )
    
    raw_website, raw_github, raw_news, raw_crunchbase = results
    
    # Process results, logging errors
    update = {}
    
    if isinstance(raw_website, Exception):
        errors.append(f"Website scrape failed: {raw_website}")
        logger.warning(f"Website scrape failed: {raw_website}")
    elif raw_website and raw_website.get("raw_content"):
        update["raw_website"] = raw_website["raw_content"]
        sources_used.append("website")
        logger.info(f"Website: scraped {len(raw_website.get('pages_found', []))} pages")
    
    if isinstance(raw_github, Exception):
        errors.append(f"GitHub scrape failed: {raw_github}")
        logger.warning(f"GitHub scrape failed: {raw_github}")
    elif raw_github and raw_github.get("repos"):
        update["raw_github"] = raw_github
        sources_used.append("github")
        logger.info(f"GitHub: found {len(raw_github.get('repos', []))} repos")
    
    if isinstance(raw_news, Exception):
        errors.append(f"News scrape failed: {raw_news}")
        logger.warning(f"News scrape failed: {raw_news}")
    elif raw_news and raw_news.get("articles"):
        update["raw_news"] = raw_news["articles"]
        sources_used.append("news")
        logger.info(f"News: found {len(raw_news.get('articles', []))} articles")
    
    if isinstance(raw_crunchbase, Exception):
        errors.append(f"Crunchbase scrape failed: {raw_crunchbase}")
        logger.warning(f"Crunchbase scrape failed: {raw_crunchbase}")
    elif raw_crunchbase and not raw_crunchbase.get("error"):
        update["raw_crunchbase"] = raw_crunchbase
        sources_used.append("crunchbase")
        logger.info("Crunchbase: data retrieved")
    
    return {
        **state,
        **update,
        "errors": errors,
        "sources_used": sources_used,
    }


async def extract_node(state: MemoState) -> MemoState:
    """
    Extraction stage - use LLMs to extract structured facts.
    """
    logger.info("Extracting structured facts...")
    
    errors = list(state.get("errors", []))
    facts = {}
    
    # Extract from each source in parallel
    extraction_tasks = []
    task_names = []
    
    if state.get("raw_website"):
        extraction_tasks.append(extract_website_facts(state["raw_website"]))
        task_names.append("website")
    
    if state.get("raw_github"):
        extraction_tasks.append(extract_github_facts(state["raw_github"]))
        task_names.append("github")
    
    if state.get("raw_news"):
        extraction_tasks.append(extract_news_facts(state["raw_news"]))
        task_names.append("news")
    
    if extraction_tasks:
        results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
        
        for name, result in zip(task_names, results):
            if isinstance(result, Exception):
                errors.append(f"{name} extraction failed: {result}")
                logger.warning(f"{name} extraction failed: {result}")
            elif result:
                facts[name] = result
                logger.info(f"{name}: facts extracted")
    
    # Add Crunchbase data directly (already structured)
    if state.get("raw_crunchbase"):
        facts["crunchbase"] = state["raw_crunchbase"]
    
    return {
        **state,
        "facts": facts,
        "errors": errors,
    }


async def enrich_node(state: MemoState) -> MemoState:
    """
    Enrichment stage - cross-reference facts and generate insights.
    """
    logger.info("Enriching and cross-referencing facts...")
    
    errors = list(state.get("errors", []))
    
    if not state.get("facts"):
        errors.append("No facts to enrich")
        return {**state, "errors": errors, "enrichment": None}
    
    try:
        enrichment = await enrich_facts(
            company=state["company"],
            facts=state["facts"]
        )
        logger.info("Enrichment complete")
        return {**state, "enrichment": enrichment, "errors": errors}
        
    except Exception as e:
        errors.append(f"Enrichment failed: {e}")
        logger.error(f"Enrichment failed: {e}")
        return {**state, "enrichment": None, "errors": errors}


async def synthesize_node(state: MemoState) -> MemoState:
    """
    Synthesis stage - generate memo sections.
    """
    logger.info("Synthesizing memo sections...")
    
    errors = list(state.get("errors", []))
    
    # Format trigger for display
    trigger = state.get("trigger", {})
    trigger_str = trigger.get("signal", "Manual review")
    if trigger.get("value"):
        trigger_str += f": {trigger['value']}"
    
    try:
        sections = await generate_sections(
            company=state["company"],
            facts=state.get("facts", {}),
            enrichment=state.get("enrichment", {}),
            trigger=trigger_str,
        )
        logger.info("All sections generated")
        return {**state, "sections": sections, "errors": errors}
        
    except Exception as e:
        errors.append(f"Synthesis failed: {e}")
        logger.error(f"Synthesis failed: {e}")
        return {**state, "sections": None, "errors": errors}


async def assemble_node(state: MemoState) -> MemoState:
    """
    Assembly stage - combine sections into final memo.
    """
    logger.info("Assembling final memo...")
    
    # Determine confidence based on sources and errors
    sources_count = len(state.get("sources_used", []))
    errors_count = len(state.get("errors", []))
    
    if sources_count >= 3 and errors_count == 0:
        confidence = "high"
    elif sources_count >= 2:
        confidence = "medium"
    else:
        confidence = "low"
    
    state_with_confidence = {**state, "confidence": confidence}
    
    try:
        memo = assemble_memo(state_with_confidence)
        logger.info(f"Memo assembled ({len(memo)} chars, confidence: {confidence})")
        return {**state_with_confidence, "memo": memo}
        
    except Exception as e:
        logger.error(f"Assembly failed: {e}")
        return {
            **state_with_confidence,
            "memo": f"[Memo assembly failed: {e}]",
            "errors": state.get("errors", []) + [f"Assembly failed: {e}"]
        }


# === Build the Graph ===

def build_pipeline() -> StateGraph:
    """
    Build the LangGraph pipeline for memo generation.
    
    Pipeline flow:
    intake -> scrape -> extract -> enrich -> synthesize -> assemble
    """
    # Create graph with MemoState
    graph = StateGraph(MemoState)
    
    # Add nodes
    graph.add_node("intake", intake_node)
    graph.add_node("scrape", scrape_node)
    graph.add_node("extract", extract_node)
    graph.add_node("enrich", enrich_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("assemble", assemble_node)
    
    # Define edges (linear flow for now)
    graph.add_edge(START, "intake")
    graph.add_edge("intake", "scrape")
    graph.add_edge("scrape", "extract")
    graph.add_edge("extract", "enrich")
    graph.add_edge("enrich", "synthesize")
    graph.add_edge("synthesize", "assemble")
    graph.add_edge("assemble", END)
    
    return graph.compile()


# === Main Entry Point ===

async def generate_memo(
    company: str,
    domain: str,
    trigger: TriggerInfo = None,
) -> MemoState:
    """
    Generate a research memo for a company.
    
    Args:
        company: Company name (e.g., "Cursor")
        domain: Company domain (e.g., "cursor.sh")
        trigger: Optional trigger information
        
    Returns:
        Final MemoState with generated memo
    """
    # Build initial state
    initial_state: MemoState = {
        "company": company,
        "domain": domain,
        "trigger": trigger or {"signal": "Manual review"},
        "errors": [],
        "sources_used": [],
    }
    
    # Build and run pipeline
    pipeline = build_pipeline()
    
    logger.info(f"Starting memo generation for {company} ({domain})")
    final_state = await pipeline.ainvoke(initial_state)
    logger.info(f"Memo generation complete for {company}")
    
    return final_state


def generate_memo_sync(
    company: str,
    domain: str,
    trigger: TriggerInfo = None,
) -> MemoState:
    """Synchronous wrapper for generate_memo."""
    return asyncio.run(generate_memo(company, domain, trigger))
