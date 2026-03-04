"""
Conference Scraper Pipeline - LangGraph orchestration

This pipeline implements the self-healing scraper pattern:
1. Discovery: Find conference sources via search
2. Scrape: Run scrapers against known sources
3. Repair: Fix broken scrapers with LLM
4. Extract: Structure raw HTML into Event objects
5. Resolve: Deduplicate events from multiple sources
6. Match: Find target company speakers
7. Alert: Notify via Slack
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from langgraph.graph import StateGraph, START, END

from .state import (
    ScraperState,
    ScraperConfig,
    SourceHealth,
    Event,
    TARGET_COMPANIES,
)
from .scrapers import scrape_source, scrape_generic_llm, fetch_page

logger = logging.getLogger(__name__)


# =============================================================================
# Pipeline Nodes
# =============================================================================

async def init_node(state: ScraperState) -> ScraperState:
    """Initialize pipeline state."""
    logger.info("Initializing conference scraper pipeline")
    
    return {
        **state,
        "run_id": str(uuid4()),
        "started_at": datetime.utcnow(),
        "errors": [],
        "extracted_events": [],
        "matched_events": [],
        "alerts_sent": [],
    }


async def scrape_node(state: ScraperState) -> ScraperState:
    """
    Scrape all configured sources.
    
    Runs scrapers in parallel, tracks failures for self-healing.
    """
    logger.info(f"Scraping {len(state.get('source_configs', []))} sources")
    
    configs = state.get("source_configs", [])
    health = state.get("source_health", {})
    errors = list(state.get("errors", []))
    raw_html = {}
    scrape_errors = {}
    sources_needing_repair = []
    
    # Run all scrapers in parallel
    async def scrape_one(config: ScraperConfig) -> tuple:
        source_name = config.source_name
        try:
            html = await fetch_page(config.source_url)
            if html:
                # Record success
                if source_name in health:
                    health[source_name].record_success()
                return (source_name, html, None)
            else:
                return (source_name, None, "Empty response")
        except Exception as e:
            return (source_name, None, str(e))
    
    results = await asyncio.gather(
        *[scrape_one(config) for config in configs],
        return_exceptions=True
    )
    
    for result in results:
        if isinstance(result, Exception):
            errors.append(f"Scraper exception: {result}")
            continue
        
        source_name, html, error = result
        
        if html:
            raw_html[source_name] = html
            logger.info(f"✓ Scraped {source_name}: {len(html)} bytes")
        else:
            scrape_errors[source_name] = error or "Unknown error"
            logger.warning(f"✗ Failed {source_name}: {error}")
            
            # Track failure for self-healing
            if source_name not in health:
                health[source_name] = SourceHealth(source_name=source_name)
            health[source_name].record_failure(error or "Unknown")
            
            # Check if needs repair
            if health[source_name].needs_repair():
                sources_needing_repair.append(source_name)
    
    return {
        **state,
        "raw_html": raw_html,
        "scrape_errors": scrape_errors,
        "source_health": health,
        "sources_needing_repair": sources_needing_repair,
        "errors": errors,
    }


async def repair_node(state: ScraperState) -> ScraperState:
    """
    Self-healing: Repair broken scrapers using LLM.
    
    When a scraper fails 3+ times, this node:
    1. Fetches the current page
    2. Asks LLM to generate new extraction logic
    3. Updates the scraper config
    """
    sources_needing_repair = state.get("sources_needing_repair", [])
    
    if not sources_needing_repair:
        return state
    
    logger.info(f"Attempting to repair {len(sources_needing_repair)} scrapers")
    
    health = state.get("source_health", {})
    repair_results = {}
    escalated = list(state.get("escalated_sources", []))
    errors = list(state.get("errors", []))
    
    for source_name in sources_needing_repair:
        source_health = health.get(source_name)
        
        if source_health and source_health.should_escalate():
            logger.warning(f"Escalating {source_name} - max repairs exceeded")
            escalated.append(source_name)
            source_health.is_escalated = True
            continue
        
        # Attempt repair (would call LLM to generate new scraper)
        # For now, just log and mark as attempted
        logger.info(f"Repair attempt for {source_name}")
        if source_health:
            source_health.record_repair_attempt()
        
        repair_results[source_name] = "repair_attempted"
    
    return {
        **state,
        "repair_results": repair_results,
        "escalated_sources": escalated,
        "source_health": health,
        "errors": errors,
    }


async def extract_node(state: ScraperState) -> ScraperState:
    """
    Extract structured Event data from raw HTML.
    
    Uses source-specific extractors or falls back to LLM.
    """
    raw_html = state.get("raw_html", {})
    configs = {c.source_name: c for c in state.get("source_configs", [])}
    
    logger.info(f"Extracting events from {len(raw_html)} sources")
    
    extracted_events = list(state.get("extracted_events", []))
    errors = list(state.get("errors", []))
    
    for source_name, html in raw_html.items():
        config = configs.get(source_name)
        if not config:
            continue
        
        try:
            # Use the scraper module's extraction
            events = await scrape_source(config)
            extracted_events.extend(events)
            logger.info(f"Extracted {len(events)} events from {source_name}")
        except Exception as e:
            errors.append(f"Extraction failed for {source_name}: {e}")
            logger.error(f"Extraction failed for {source_name}: {e}")
    
    return {
        **state,
        "extracted_events": extracted_events,
        "errors": errors,
    }


async def resolve_node(state: ScraperState) -> ScraperState:
    """
    Entity resolution: Deduplicate events from multiple sources.
    
    Same event may appear on multiple conference listing sites.
    This node identifies and merges duplicates.
    """
    events = state.get("extracted_events", [])
    
    logger.info(f"Resolving {len(events)} events")
    
    # Simple dedup by event name + date
    seen = {}
    deduplicated = []
    clusters = {}
    
    for event in events:
        # Create a key for matching
        key = (
            event.name.lower().strip(),
            event.start_date.strftime("%Y-%m") if event.start_date else "unknown",
        )
        
        if key in seen:
            # Merge: add to cluster
            canonical_id = seen[key]
            if canonical_id not in clusters:
                clusters[canonical_id] = []
            clusters[canonical_id].append(event.source_url)
            
            # Merge speakers from duplicate
            existing = next(e for e in deduplicated if e.canonical_id == canonical_id)
            existing_names = {s.name for s in existing.speakers}
            for speaker in event.speakers:
                if speaker.name not in existing_names:
                    existing.speakers.append(speaker)
        else:
            # New event
            canonical_id = str(uuid4())[:8]
            event.canonical_id = canonical_id
            seen[key] = canonical_id
            deduplicated.append(event)
            clusters[canonical_id] = [event.source_url]
    
    logger.info(f"Deduplicated to {len(deduplicated)} unique events")
    
    return {
        **state,
        "deduplicated_events": deduplicated,
        "event_clusters": clusters,
    }


async def match_node(state: ScraperState) -> ScraperState:
    """
    Match speakers against target portfolio companies.
    """
    events = state.get("deduplicated_events", [])
    targets = state.get("target_companies", TARGET_COMPANIES)
    
    logger.info(f"Matching {len(events)} events against {len(targets)} targets")
    
    matched_events = []
    
    for event in events:
        matches = event.has_target_speakers(targets)
        if matches:
            matched_events.append({
                "event": event,
                "matches": matches,
            })
            logger.info(f"Found {len(matches)} target speakers at {event.name}")
    
    logger.info(f"Total: {len(matched_events)} events with target speakers")
    
    return {
        **state,
        "matched_events": matched_events,
    }


async def alert_node(state: ScraperState) -> ScraperState:
    """
    Send alerts for matched events.
    
    In production, this would send Slack messages.
    For now, it logs and records the alerts.
    """
    matched = state.get("matched_events", [])
    escalated = state.get("escalated_sources", [])
    
    alerts_sent = []
    
    # Alert for matched events
    for match in matched:
        event = match["event"]
        speakers = match["matches"]
        
        alert = {
            "type": "target_speaker",
            "event_name": event.name,
            "event_date": str(event.start_date) if event.start_date else None,
            "location": event.location,
            "speakers": [
                {"name": s.name, "company": t["name"]}
                for s, t in speakers
            ],
            "url": event.source_url,
            "sent_at": datetime.utcnow().isoformat(),
        }
        
        logger.info(f"🔔 ALERT: {len(speakers)} target speakers at {event.name}")
        alerts_sent.append(alert)
    
    # Alert for escalated scrapers
    for source_name in escalated:
        alert = {
            "type": "scraper_escalation",
            "source_name": source_name,
            "message": "Scraper needs manual repair",
            "sent_at": datetime.utcnow().isoformat(),
        }
        
        logger.warning(f"⚠️ ESCALATION: {source_name} needs manual repair")
        alerts_sent.append(alert)
    
    return {
        **state,
        "alerts_sent": alerts_sent,
        "completed_at": datetime.utcnow(),
    }


# =============================================================================
# Build Pipeline
# =============================================================================

def build_conference_pipeline() -> StateGraph:
    """
    Build the LangGraph pipeline for conference scraping.
    
    Flow:
    init -> scrape -> repair (if needed) -> extract -> resolve -> match -> alert
    """
    graph = StateGraph(ScraperState)
    
    # Add nodes
    graph.add_node("init", init_node)
    graph.add_node("scrape", scrape_node)
    graph.add_node("repair", repair_node)
    graph.add_node("extract", extract_node)
    graph.add_node("resolve", resolve_node)
    graph.add_node("match", match_node)
    graph.add_node("alert", alert_node)
    
    # Define flow
    graph.add_edge(START, "init")
    graph.add_edge("init", "scrape")
    graph.add_edge("scrape", "repair")
    graph.add_edge("repair", "extract")
    graph.add_edge("extract", "resolve")
    graph.add_edge("resolve", "match")
    graph.add_edge("match", "alert")
    graph.add_edge("alert", END)
    
    return graph.compile()


# =============================================================================
# Entry Points
# =============================================================================

async def run_pipeline(
    source_configs: Optional[List[ScraperConfig]] = None,
    target_companies: Optional[List[Dict]] = None,
) -> ScraperState:
    """
    Run the conference scraping pipeline.
    
    Args:
        source_configs: List of sources to scrape (defaults to built-in)
        target_companies: Companies to watch for (defaults to Sapphire portfolio)
        
    Returns:
        Final pipeline state with matched events and alerts
    """
    # Default sources
    if source_configs is None:
        source_configs = [
            ScraperConfig(
                source_name="techcrunch_disrupt",
                source_url="https://techcrunch.com/events/techcrunch-disrupt-2024/speakers/",
            ),
            ScraperConfig(
                source_name="websummit",
                source_url="https://websummit.com/speakers",
            ),
        ]
    
    # Default targets
    if target_companies is None:
        target_companies = TARGET_COMPANIES
    
    # Build initial state
    initial_state: ScraperState = {
        "source_configs": source_configs,
        "target_companies": target_companies,
        "source_health": {},
    }
    
    # Build and run pipeline
    pipeline = build_conference_pipeline()
    
    logger.info("Starting conference scraper pipeline")
    final_state = await pipeline.ainvoke(initial_state)
    logger.info("Pipeline complete")
    
    return final_state


def run_pipeline_sync(
    source_configs: Optional[List[ScraperConfig]] = None,
    target_companies: Optional[List[Dict]] = None,
) -> ScraperState:
    """Synchronous wrapper for run_pipeline."""
    return asyncio.run(run_pipeline(source_configs, target_companies))


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import json
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    
    async def main():
        result = await run_pipeline()
        
        print("\n" + "=" * 60)
        print("PIPELINE RESULTS")
        print("=" * 60)
        
        print(f"\nRun ID: {result.get('run_id')}")
        print(f"Sources scraped: {len(result.get('raw_html', {}))}")
        print(f"Events extracted: {len(result.get('extracted_events', []))}")
        print(f"Events deduplicated: {len(result.get('deduplicated_events', []))}")
        print(f"Matched events: {len(result.get('matched_events', []))}")
        print(f"Alerts sent: {len(result.get('alerts_sent', []))}")
        
        if result.get("errors"):
            print(f"\nErrors: {len(result['errors'])}")
            for err in result["errors"]:
                print(f"  - {err}")
        
        if result.get("alerts_sent"):
            print("\nAlerts:")
            print(json.dumps(result["alerts_sent"], indent=2, default=str))
    
    asyncio.run(main())
