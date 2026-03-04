# Cost & Observability

> How to know what you're spending, why, and whether it's worth it.

---

## The Problem

LLM pipelines are easy to prototype and hard to budget. A single misconfigured agent can burn $50 in a debugging loop. An oversized input can turn a $0.01 call into $0.50. Without visibility, costs are invisible until the invoice arrives.

L'oeil addresses this at three levels:

1. **Token budgets** — Hard limits on any single tool call or agent run
2. **Tracing** — Every LLM call mapped to a pipeline run, enabling per-tool and per-company cost attribution
3. **Spend caps** — Pipeline-level maximums that abort before things get expensive

> **Design principle:** Every tool call, agent step, and pipeline run should have a known maximum cost before it executes.

---

## Token Budgets

Every tool that touches an LLM has a declared budget. See [full budget tables →](token-budgets.md).

### Conference Scraper

| Tool | [Complexity](model-selection.md) | Max Input | Max Output | Max Cost |
|---|---|---|---|---|
| Extraction | 2–3 (fast/cheap) | 8K | 1K | $0.01/call |
| Repair (10 steps max) | 8–9 (premium) | 50K total | 30K total | $0.21/repair |

### Research Memo

| Tool | [Complexity](model-selection.md) | Max Input | Max Output | Max Cost |
|---|---|---|---|---|
| Extract (per source) | 2–3 (fast/cheap) | 5K | 1K | $0.005 |
| Enrich | 6–7 (mid-tier) | 10K | 2K | $0.05 |
| Synthesize (6 sections) | 8 (premium) | 18K total | 9K total | $0.18 |

---

## Tracing

LangSmith works well for development (~$4/1K traces) but adds up at scale. We spec a lightweight DIY layer — structured logging to SQLite — that costs nothing and answers the questions that matter:

- How much did we spend this week? Per tool? Per company?
- Are token budgets right-sized? (avg utilization vs. budget)
- Could a tool use a cheaper model? (compare success rates across [complexity tiers](model-selection.md))
- Are agents hitting their step limits? (step limit = possible task misfit)

> [Full tracing architecture →](tracing.md)

---

## Spend Caps

| Pipeline | Max LLM Spend | At Limit |
|---|---|---|
| Conference scraper (weekly) | $5.00 | Abort, send alert |
| Research memo (per memo) | $2.00 | Abort, return partial |

Hourly throughput limits prevent runaway costs from misconfigured schedulers: conference scraper max 1 run/hour, research memo max 10/hour. Queue overflow triggers a Slack alert.

---

## The Optimization Loop

Cost data + [traces](tracing.md) + [complexity scoring](model-selection.md) enable continuous optimization:

1. **Observe** — "Extraction uses 60% of weekly spend"
2. **Question** — "Could a cheaper model handle this?"
3. **Experiment** — Run 100 examples with the next tier down, compare output
4. **Deploy** — If quality holds, shift down and save

Other signals the data surfaces:

- If an agent succeeds on step 1 every time → replace with a deterministic function
- If a tool never outputs contradictions → it may not need mid-tier reasoning
- If avg input is 2K but budget is 8K → budget is fine (headroom is good)
- If avg input is 7.5K on an 8K budget → regularly truncating useful data
