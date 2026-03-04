#!/usr/bin/env python3
"""
Conference Scraper Demo

Demonstrates the self-healing scraper pipeline by:
1. Scraping known conference sources
2. Matching speakers against target portfolio companies
3. Generating mock alerts
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.conference_scraper.state import TARGET_COMPANIES, Event, Speaker
from src.conference_scraper.scrapers import (
    scrape_techcrunch_disrupt,
    scrape_websummit,
    fetch_page,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("conference_demo")


# =============================================================================
# Example Data (for demo when live scraping fails)
# =============================================================================

EXAMPLE_EVENTS = [
    Event(
        name="TechCrunch Disrupt 2024",
        source_url="https://techcrunch.com/events/techcrunch-disrupt-2024/",
        start_date=datetime(2024, 10, 28),
        end_date=datetime(2024, 10, 30),
        location="San Francisco, CA",
        city="San Francisco",
        country="USA",
        is_virtual=False,
        speakers=[
            Speaker(name="Harrison Chase", title="CEO", company="LangChain"),
            Speaker(name="Dario Amodei", title="CEO", company="Anthropic"),
            Speaker(name="Sam Altman", title="CEO", company="OpenAI"),
            Speaker(name="Satya Nadella", title="CEO", company="Microsoft"),
            Speaker(name="Jensen Huang", title="CEO", company="NVIDIA"),
            Speaker(name="Ali Ghodsi", title="CEO", company="Databricks"),
            Speaker(name="Dylan Field", title="CEO", company="Figma"),
        ],
        source_name="techcrunch_disrupt_example",
    ),
    Event(
        name="Web Summit 2024",
        source_url="https://websummit.com/",
        start_date=datetime(2024, 11, 11),
        end_date=datetime(2024, 11, 14),
        location="Lisbon, Portugal",
        city="Lisbon",
        country="Portugal",
        is_virtual=False,
        speakers=[
            Speaker(name="Maxim Fateev", title="CEO", company="Temporal"),
            Speaker(name="Arvind Jain", title="CEO", company="Glean"),
            Speaker(name="Patrick Collison", title="CEO", company="Stripe"),
            Speaker(name="Brian Chesky", title="CEO", company="Airbnb"),
            Speaker(name="Tobi Lütke", title="CEO", company="Shopify"),
        ],
        source_name="websummit_example",
    ),
    Event(
        name="AI Engineer Summit 2024",
        source_url="https://www.ai.engineer/summit",
        start_date=datetime(2024, 10, 8),
        end_date=datetime(2024, 10, 10),
        location="San Francisco, CA",
        city="San Francisco",
        country="USA",
        is_virtual=False,
        speakers=[
            Speaker(name="Harrison Chase", title="CEO", company="LangChain"),
            Speaker(name="Guillermo Rauch", title="CEO", company="Vercel"),
            Speaker(name="Simon Willison", title="Creator", company="Datasette"),
            Speaker(name="Andrej Karpathy", title="Founder", company="Eureka Labs"),
        ],
        source_name="ai_engineer_summit_example",
    ),
]


def match_speakers_to_targets(events: list[Event], targets: list[dict]) -> list[dict]:
    """Find speakers from target companies."""
    matches = []
    
    for event in events:
        event_matches = event.has_target_speakers(targets)
        if event_matches:
            matches.append({
                "event": event,
                "matches": event_matches,
            })
    
    return matches


def format_alert(match: dict) -> str:
    """Format a match as a Slack alert."""
    event = match["event"]
    speakers = match["matches"]
    
    lines = [
        f"🎤 *Target Company Speaker Alert*",
        f"",
        f"*Event:* {event.name}",
        f"*Dates:* {event.start_date.strftime('%b %d') if event.start_date else 'TBD'} - {event.end_date.strftime('%b %d, %Y') if event.end_date else 'TBD'}",
        f"*Location:* {event.location or 'TBD'}",
        f"",
        f"*Target Speakers Found:*",
    ]
    
    for speaker, target in speakers:
        lines.append(f"  • *{speaker.name}* ({speaker.title or 'N/A'}) — {target['name']}")
    
    lines.extend([
        f"",
        f"🔗 {event.source_url}",
    ])
    
    return "\n".join(lines)


async def main():
    print("=" * 70)
    print("CONFERENCE SCRAPER DEMO")
    print("=" * 70)
    print()
    
    # Show target companies
    print("📋 TARGET COMPANIES:")
    for target in TARGET_COMPANIES:
        print(f"  • {target['name']} (CEO: {target['ceo']})")
    print()
    
    # Try live scraping first
    print("🔍 ATTEMPTING LIVE SCRAPE...")
    live_events = []
    
    try:
        tc_events = await scrape_techcrunch_disrupt()
        if tc_events:
            live_events.extend(tc_events)
            print(f"  ✅ TechCrunch Disrupt: {len(tc_events[0].speakers)} speakers")
        else:
            print(f"  ⚠️  TechCrunch Disrupt: No data (JS-heavy site)")
    except Exception as e:
        print(f"  ❌ TechCrunch Disrupt: {e}")
    
    try:
        ws_events = await scrape_websummit()
        if ws_events:
            live_events.extend(ws_events)
            print(f"  ✅ Web Summit: {len(ws_events[0].speakers)} speakers")
        else:
            print(f"  ⚠️  Web Summit: No data (JS-heavy site)")
    except Exception as e:
        print(f"  ❌ Web Summit: {e}")
    
    print()
    
    # Use example data if live scraping failed
    if not live_events or sum(len(e.speakers) for e in live_events) < 5:
        print("📦 USING EXAMPLE DATA (live scraping returned limited results)")
        events = EXAMPLE_EVENTS
    else:
        events = live_events
    
    print()
    
    # Show extracted events
    print("📅 EVENTS FOUND:")
    for event in events:
        print(f"\n  *{event.name}*")
        print(f"    Location: {event.location}")
        print(f"    Speakers: {len(event.speakers)}")
        print(f"    Sample speakers:")
        for speaker in event.speakers[:3]:
            print(f"      - {speaker.name} ({speaker.company or 'N/A'})")
        if len(event.speakers) > 3:
            print(f"      ... and {len(event.speakers) - 3} more")
    print()
    
    # Match against targets
    print("🎯 MATCHING AGAINST TARGET PORTFOLIO...")
    matches = match_speakers_to_targets(events, TARGET_COMPANIES)
    
    if matches:
        print(f"\n✅ Found {len(matches)} events with target company speakers!\n")
        
        # Generate alerts
        print("=" * 70)
        print("GENERATED ALERTS")
        print("=" * 70)
        
        for match in matches:
            print()
            print(format_alert(match))
            print()
            print("-" * 50)
    else:
        print("\n⚠️  No target company speakers found in these events.")
    
    # Output JSON for reference
    output = {
        "scraped_at": datetime.now().isoformat(),
        "events": [
            {
                "name": e.name,
                "location": e.location,
                "dates": f"{e.start_date} - {e.end_date}" if e.start_date else None,
                "speaker_count": len(e.speakers),
                "speakers": [
                    {"name": s.name, "title": s.title, "company": s.company}
                    for s in e.speakers
                ],
            }
            for e in events
        ],
        "target_matches": [
            {
                "event": m["event"].name,
                "speakers": [
                    {"name": s.name, "company": t["name"]}
                    for s, t in m["matches"]
                ]
            }
            for m in matches
        ],
    }
    
    # Save to file
    output_path = Path("output/conference_scrape_example.json")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n💾 Full output saved to: {output_path}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
