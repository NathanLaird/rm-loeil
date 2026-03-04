# Research Memo — Data Structures

> The core entities the pipeline creates as a memo moves from raw data to finished document.

---

Data gets progressively refined through the pipeline. Raw content → structured facts → cross-source analysis → trend contextualization → written narrative → assembled memo.

---

## Research Brief (Input)

What triggers the pipeline.

| Field | Type | Description |
|---|---|---|
| `company` / `domain` | string | Company name and website |
| `trigger` | object | Signal type, value, date (e.g. "headcount_growth", "85% QoQ") |
| `crm_notes` | string | Prior interaction history from CRM |

---

## Extracted Facts (Per Source)

Each source produces a typed fact structure. Key fields by source:

**Website:** company name, tagline, description, features, target customers, pricing model, team members, notable customers, integrations.

**GitHub:** org name, public repos, total stars/forks, top repos (with language and maintenance status), primary languages, contributor count, open-source strategy.

**News:** recent articles (title, source, date, summary, sentiment), overall narrative, red flags, momentum signal.

**Crunchbase:** total raised, last round (date, amount, type), investors, employee range. *Optional — pipeline flags "funding data unavailable" if no API key.*

**Apollo:** team composition by department, executive titles and tenure, recent hires, company size, industry classification. Roughly as complete as LinkedIn's logged-out view without the scraping compliance issues.

**Twitter:** founder/executive posts about product, industry, and events. Speaking engagement announcements. Engagement patterns.

**LinkedIn:** team composition, recent hires, hiring velocity, executive backgrounds, relationship-graph signals.

---

## Enrichment (Cross-Source Analysis)

Where the pipeline moves from "what we found" to "what it means."

| Entity | Description |
|---|---|
| **Patterns** | Connections across sources — "Hiring sales + GitHub stars growing → developer traction converting to enterprise" |
| **Contradictions** | Sources disagree — "Crunchbase: $30M, TechCrunch: $35M" with resolution attempt |
| **Gaps** | Missing data ranked by importance — "No revenue data. Critical. Ask in founder meeting." |
| **Insights** | Non-obvious conclusions with supporting evidence and confidence level |
| **Risks** | What could go wrong, with severity and mitigants |
| **Derived metrics** | Calculated values: funding/employee, star growth rate, source diversity ratio |

---

## Trend Contextualization

The enriched findings are matched against a curated RAG corpus of industry reports and thought leadership:

| Field | Description |
|---|---|
| **Matching trends** | Which macro themes align — "Company sits in the AI-native security segment Gartner just named as emerging" |
| **Trend sources** | Which reports/essays support the alignment |
| **Counter-trends** | Any macro headwinds — "Enterprise AI spending decelerating in Q3 per Forrester" |
| **Why-now strength** | How well the timing aligns with independently-identified market shifts |

---

## Memo Sections

Seven narrative sections, each generated with a tailored prompt:

| Section | Purpose | Length |
|---|---|---|
| Executive Summary | What + why now + bottom line | ~150 words |
| Company Overview | Product, team, customers, model | ~1 page |
| Market Context | TAM, competitors, tailwinds, trend alignment | ~0.5 page |
| Signal Analysis | Deep dive on the trigger | ~1 page |
| Why Now | Macro trend alignment, market timing | ~0.5 page |
| Risks | Adversarial analysis, data gaps | ~0.5 page |
| Appendix | Source citations, contradictions, trace ID | ~0.5 page |

---

## Assembled Memo

The final output adds a **data quality banner** ("Based on 8/9 sources. Gaps: [list]. Confidence: medium."), **source citations** with URLs and scrape timestamps, **contradiction flags**, **trend references**, and a **trace ID** linking to the full pipeline run.
