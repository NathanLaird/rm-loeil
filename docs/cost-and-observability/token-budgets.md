# Token Budgets

> Hard limits on what any single tool call or agent run can consume.

---

Without budgets, a scraper returning 100K tokens of HTML turns a $0.01 extraction into $1.50. Multiply by 500 sources and one run blows the weekly budget. Budgets provide cost predictability, error detection (oversized content = likely scraper bug), and quality signals.

---

## Conference Scraper

| Tool | Max Input | Max Output | Max Cost | Notes |
|---|---|---|---|---|
| Extraction (per page) | 8K | 1K | $0.01 | Exceeding 8K → truncate to keyword section, flag |
| Repair (per step) | 5K | 3K | ~$0.02 | Code + error log + page snippet |
| Repair (full run) | 50K (10 steps) | 30K | $0.21 | Hits step 10 without fix → escalate to human |
| **Per-run total (500 sources)** | | | **$1.13 typical, $5.00 hard cap** | |

## Research Memo

| Tool | Max Input | Max Output | Max Cost | Notes |
|---|---|---|---|---|
| Extract (per source, ×8) | 5K | 1K | $0.005 | Content exceeding 5K truncated with marker |
| Enrich (all facts) | 10K | 2K | $0.05 | All extracted facts + prompt |
| Synthesize (per section, ×6) | 3K | 1.5K | $0.03 | Section-specific facts + enrichment |
| **Per-memo total** | | | **$0.26 typical, $2.00 hard cap** | |

---

## Oversized Content Detection

When a scraper returns significantly more text than expected, it's usually a bug:

| Ratio (actual / expected) | Response |
|---|---|
| ≤ 3x | Normal — proceed |
| 3–10x | Warning — truncate, log health issue |
| > 10x | Error — skip, increment failure counter |

The pipeline tracks `content_size_ratio` per source. Persistent oversized content triggers a scraper health review.
