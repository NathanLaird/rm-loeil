# Tracing Architecture

> A lightweight alternative to LangSmith for cost tracking and observability.

---

## Why DIY?

LangSmith is excellent for development. At ~$4 per 1,000 traces, it's fine at low volume. But at scale it adds up:

| Volume | Weekly Traces | LangSmith Cost |
|---|---|---|
| 500 sources + 10 memos | ~600 | ~$2.40/week |
| 2,000 sources + 50 memos | ~2,500 | ~$10/week |

A DIY layer — structured logging to SQLite — costs nothing and gives us the same operational visibility.

**Recommendation:** Use LangSmith during development. Switch to DIY when trace volume exceeds ~2K/week.

---

## What We Track

Every LLM call logs a trace record with:

- **Identity:** `trace_id` (per pipeline run), `call_id` (per LLM call), pipeline name
- **What was called:** tool name, model, step number (for agents)
- **Context:** target company, data source
- **Tokens:** input count, output count, declared budget for comparison
- **Cost:** calculated from model pricing
- **Performance:** latency, success/failure, error message

Storage is SQLite with indexes on `trace_id`, `tool`, and `timestamp`. At enterprise scale, this moves to a data warehouse — but SQLite handles thousands of records per week.

---

## Key Queries

The tracing data answers the operational questions that matter:

| Question | How |
|---|---|
| Weekly spend? | `SUM(cost) WHERE timestamp > 7 days ago` |
| Most expensive tool? | `SUM(cost) GROUP BY tool` |
| Most expensive company to research? | `SUM(cost) GROUP BY company` |
| Budget utilization? | `AVG(input_tokens / max_budget) GROUP BY tool` |
| Could a tool use a cheaper model? | Compare success rates across [complexity tiers](model-selection.md) |
| Agents hitting step limits? | `COUNT WHERE steps = max_steps` |

---

## Optimization Signals

| Signal | Meaning | Action |
|---|---|---|
| Tool utilization >80% | Regularly near the limit | Increase budget or investigate large inputs |
| Agent hits max steps >10% of runs | Task may be too hard for the model | Try stronger model or simplify |
| Agent succeeds on step 1 >95% of runs | Doesn't need agent capabilities | Replace with single call or script |
| Tool failure rate >5% | Model struggling | Try stronger model or simplify prompt |

---

## Migration Path

| Stage | Tool | When |
|---|---|---|
| Development | LangSmith (free tier) | Building and debugging |
| Early production | LangSmith (paid) | <2K traces/week |
| Scale | DIY SQLite | >2K traces/week |
| Enterprise | DIY + data warehouse | >10K traces/week |
