# Model Selection

> Instead of hardcoding model names, assign each LLM task a complexity score and match it to the right tier.

---

## Why Complexity Scoring

Model names change every few months. Pricing shifts. New options appear. Rather than locking every task to a specific model, we rate each task by how hard it is and pick from a tier.

Because we [trace every LLM call](tracing.md), we can experiment: run a task on a cheaper model, compare output quality against the previous tier, and shift down when it works. Over time, costs decrease without manual re-architecture.

---

## Complexity Scale

| Score | What It Means | Example Tasks |
|---|---|---|
| **1–3** | Structured extraction, classification, simple reformatting. Low ambiguity, clear right answers. | Extract event JSON from HTML. Classify a page as "conference" vs. "blog." Parse dates. |
| **4–5** | Multi-field extraction with judgment calls. Some ambiguity, needs context. | Normalize company names across sources. Detect scraping frequency from site signals. |
| **6–7** | Cross-source reasoning, pattern recognition, moderate synthesis. | Cross-reference facts from 4+ sources. Identify contradictions. Write a company overview. |
| **8–9** | Complex narrative generation, adversarial analysis, multi-step code reasoning. | Write investment-grade memo sections. Diagnose and rewrite a broken scraper. |
| **10** | Open-ended strategic reasoning with incomplete data. | Full investment thesis with risk assessment. |

---

## Model Tiers

| Tier | Complexity | Current Picks (early 2025) | Typical Cost |
|---|---|---|---|
| **Fast / cheap** | 1–4 | GPT-4o-mini, Claude Haiku, Gemini Flash | $0.10–0.60 / 1M tokens |
| **Mid-tier** | 5–7 | GPT-4o, Claude Sonnet | $2–15 / 1M tokens |
| **Premium** | 8–10 | Claude Opus, GPT-4.5, o1 | $15–75 / 1M tokens |

These picks will be stale within months — that's the point of the abstraction. When a new model drops, slot it into the right tier and re-run your traces to validate.

---

## How Tasks Map Across Both Pipelines

| Pipeline | Task | Complexity | Tier |
|---|---|---|---|
| Conference | Extract event/attendee data from HTML | 2 | Fast/cheap |
| Conference | Determine scraping frequency | 4 | Fast/cheap |
| Conference | Diagnose + rewrite broken scraper | 9 | Premium |
| Research Memo | Extract structured facts per source | 3 | Fast/cheap |
| Research Memo | Contextualize against industry trends | 5 | Mid-tier |
| Research Memo | Cross-reference facts, find patterns | 6 | Mid-tier |
| Research Memo | Write memo sections | 8 | Premium |
| Research Memo | Adversarial risk analysis | 8 | Premium |

---

## The Optimization Loop

With [traces](tracing.md) capturing every call's input, output, model, cost, and latency:

1. **Identify expensive tasks** — sort by weekly spend
2. **Test one tier down** — run the same inputs through a cheaper model
3. **Compare quality** — does the output still pass your acceptance criteria?
4. **Shift if it works** — update the config, monitor for regression
5. **Repeat** — this is continuous, not one-time

Most teams find that 60–70% of their LLM spend is on tasks that a cheaper model handles equally well. The traces make this visible.
