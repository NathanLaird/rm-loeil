# Task 2: Research Memo Generator

> Generate a structured outside-in research memo when a company shows inflection in outside-in data signals.

---

## The Problem

When the investment team sees a company with strong signals — 85% QoQ headcount growth, a breakout GitHub repo, a new enterprise customer win — an analyst pulls together a research memo. The process is tedious: most of the time goes to data collection, not analysis.

## The Solution

A seven-stage LangGraph pipeline that takes a company name + triggering signal and produces a structured, source-cited research memo in under 3 minutes:

1. **Intake** — validate the request, pull CRM context
2. **Scrape** — hit 9+ data sources in parallel (website, GitHub, news, Crunchbase, Apollo, Twitter, LinkedIn, job postings, ProductHunt)
3. **Extract** — pull structured facts from each source ([complexity 2–3](../cost-and-observability/model-selection.md))
4. **Enrich** — cross-reference facts to find patterns and contradictions ([complexity 6–7](../cost-and-observability/model-selection.md))
5. **Contextualize** — check findings against a curated collection of industry trend reports and market macro essays ([complexity 5–6](../cost-and-observability/model-selection.md))
6. **Synthesize** — write each memo section as investment-grade narrative ([complexity 8](../cost-and-observability/model-selection.md))
7. **Assemble** — format with citations, data tables, confidence flags (template)

The value isn't in collecting data — any tool does that. The value is in **connecting disparate signals into a coherent investment narrative** with full provenance, in minutes instead of hours.

> [Pipeline detail →](pipeline.md) · [Data structures →](data-structures.md) · [Data inputs →](inputs.md) · [LLM limitations →](limitations.md)

---

## Architecture & Tools

| Layer | Tool | Why |
|---|---|---|
| **Orchestration** | LangGraph | Stateful pipeline with checkpoints. If one source fails, the pipeline continues and flags the gap. |
| **Scraping** | httpx + BeautifulSoup, API clients | Async parallel scraping. GitHub API, Crunchbase API, Tavily search. |
| **People data** | Apollo enrichment API | Up-to-date employment data roughly as complete as LinkedIn's logged-out view. Team composition, titles, tenure. |
| **Social data** | Twitter API + LinkedIn | Founder thought leadership, hiring signals, relationship mapping. |
| **Industry context** | Curated trend reports (Gartner, VC/PE essays) | RAG-indexed collection of market macro pieces. The "why now" section checks if the company's trajectory aligns with broader industry trends. |
| **LLM tiers** | [Complexity-based selection](../cost-and-observability/model-selection.md) | Fast/cheap for extraction, mid-tier for cross-referencing, premium for narrative. ~$0.25/memo vs. ~$0.60 with one model. |
| **Observability** | [Custom tracing](../cost-and-observability/tracing.md) | Every LLM call traced with cost, latency, and output for optimization. |

---

## Additional Inputs to Consider

Beyond the three primary inputs (website, LinkedIn headcount, CRM notes):

| Tier | Inputs | Signal |
|---|---|---|
| **Always include** | GitHub, Crunchbase, Apollo, news, Twitter, LinkedIn | Engineering velocity, funding context, team composition, market narrative, founder signal |
| **When available** | Job postings, G2/TrustRadius, ProductHunt | Hiring velocity, customer sentiment, community traction |
| **Company-specific** | Patents, academic citations, web traffic | Defensible IP, research foundation, PLG pipeline |
| **Proprietary** | CRM history, portfolio network, co-investor intel (from Task 1), industry trend collection | Relationship context, competitive dynamics, deal signal, macro alignment |

> [Full input catalog →](inputs.md)

---

## LLM Limitations

When the investment team reads a generated memo, six systematic weaknesses to watch for:

1. **Hallucinated metrics** — fabricated numbers with no source. *Mitigation: every metric requires a source citation; gaps are explicitly flagged.*
2. **Overconfident narratives** — a 2-source memo reads as authoritatively as a 6-source one. *Mitigation: data quality banner with source count and gaps.*
3. **Positivity bias** — most inputs are company-produced, so the memo skews bullish. *Mitigation: adversarial risks prompt; source diversity tracking.*
4. **Knowledge cutoff leakage** — model blends training data with scraped facts. *Mitigation: "use ONLY provided facts" instruction; trace auditing.*
5. **Silent contradiction resolution** — model picks one number when sources disagree. *Mitigation: dedicated contradiction detection in enrichment.*
6. **Context window truncation** — large companies exceed limits. *Mitigation: staged processing; aggregate stats over raw data.*

> [Detailed limitations analysis →](limitations.md)

---

## Output & Cost

The memo follows a standard template: executive summary (~150 words), company overview, market context, signal analysis (including industry trend alignment), risks, and appendix with source citations and contradictions.

| Volume | Monthly Cost |
|---|---|
| 10 memos/month | ~$3-5 |
| 50 memos/month | ~$15-25 |

At 50 memos/month, L'oeil eliminates the tedious data collection work for $25 in LLM spend.
