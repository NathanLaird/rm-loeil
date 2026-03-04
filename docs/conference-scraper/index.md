# Task 1: Conference & Event Scraper

> Automatically discover conferences where target company executives will attend or present in the next 3-6 months, and alert partners via Slack.

---

## The Problem

Partners need advance notice when portfolio founders are attending or speaking at conferences — these are key opportunities to network, mentor, and provide hands-on support. Today this means an analyst manually checking dozens of conference websites every week. Events get missed. The work doesn't scale.

## The Solution

A self-healing scraping pipeline that runs weekly:

1. **Discover** new conference sources via web search and social signals (Twitter/LinkedIn posts about upcoming speaking engagements)
2. **Scrape** event pages in parallel using deterministic code (no LLM)
3. **Pre-filter** against a target keyword corpus before any LLM call — this kills 90% of LLM spend
4. **Extract** structured attendee/event data from the pages that pass the filter
5. **Deduplicate** events seen across multiple sources
6. **Match** attendees against the target company list, cross-reference partner calendars
7. **Alert** via Slack with weekly digests and threaded event detail

The key design constraint: **scrapers are deterministic and free. LLMs only intervene when a scraper breaks or when judgment is needed.** This keeps weekly cost under $1 at 500 sources.

> [Pipeline detail →](pipeline.md) · [Data structures →](data-structures.md) · [Scraper lifecycle →](scraper-lifecycle.md) · [Cost model →](cost.md)

---

## Recommended Tools

| Layer | Tool | Why |
|---|---|---|
| **Orchestration** | LangGraph | Durable execution with checkpoints. Conditional branching lets the repair agent fire only when needed. |
| **HTTP scraping** | httpx + BeautifulSoup | Async HTTP + HTML parsing. Handles most conference sites without browser overhead. |
| **JS-heavy sites** | browser-use + Playwright | Agent-driven browser for sites that require JS rendering. Also used by the repair agent. |
| **Social signals** | Twitter API + LinkedIn | Executive posts about upcoming speaking engagements serve as both a discovery source and a validation signal. |
| **Calendar** | Google Calendar / Outlook API | Cross-reference partner calendars before alerting — don't surface events they're already committed to. |
| **Observability** | [Custom tracing layer](../cost-and-observability/tracing.md) | Trace IDs per run, per-tool token tracking, cost aggregation. |
| **Alerts** | Slack Bolt SDK | Block Kit formatting, threading, emoji reactions for partner feedback. |
| **Storage** | SQLite + JSON | Scraper registry, event history, tombstones. Entity resolution is a string-matching problem at this scale — no graph DB needed. |

---

## LLM Selection

LLMs only appear in two operations. Everything else is deterministic Python. Each task is assigned a [complexity score](../cost-and-observability/model-selection.md) rather than a hardcoded model:

| Operation | Complexity | Tier | Why |
|---|---|---|---|
| **Extraction** — structure event data from HTML | 2–3 | Fast/cheap | Structured JSON output, low ambiguity, high volume |
| **Repair** — diagnose and rewrite a broken scraper | 8–9 | Premium | Multi-step code reasoning, but repairs are rare (~2%/week) |
| **Scraper generation** — write initial scraper from site inspection | 8–9 | Premium | One-time cost per source |

Using a premium model for all extraction would cost ~7x more with no quality gain on simple tasks. The [model selection page](../cost-and-observability/model-selection.md) explains the tiering strategy and how traces let us optimize over time.

---

## Example Prompts

### Extraction — Structuring Event Data from HTML

```text
Extract conference/event information from this HTML content.
Return JSON with: event_name, date_start (ISO 8601), date_end, location
(city/country/venue), format (in-person/virtual/hybrid), attendees
(name/title/company/is_presenting/session_title), registration_url,
confidence (high/medium/low).

Rules:
- Normalize company names: "Anthropic, Inc." → "Anthropic"
- Set is_presenting=true for speakers, panelists, keynoters. False for general attendees.
- Use null for missing fields. Do not invent data.
- Set confidence to "low" if key fields (date, attendees) are missing.
```

### Repair — Fixing a Broken Scraper

```text
A scraper for {source_url} has failed {n} consecutive times.

Previous scraper code: {scraper_code}
Error log (last 3 runs): {error_log}
Snapshot test expectations: {snapshot_spec}

Navigate to the URL, identify what changed, and write a corrected scraper
that passes the snapshot test.
```

---

## Cost Model

### The Formula

```
Weekly LLM Cost = (pages passing pre-filter × ~$0.01) + (broken scrapers × ~$0.15)
```

At 500 sources with 90% pre-filter rejection and ~2% weekly breakage: **~$1/week**.

Build vs. buy: PredictHQ ($500-2K/mo), manual analyst (~$2K/mo), **L'oeil at 500 sources (~$4/mo)**.

> [Full cost breakdown with worked examples →](cost.md)
