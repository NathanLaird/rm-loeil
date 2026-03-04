# Conference Scraper — Cost Model

> How to calculate and approximate the cost of running this pipeline weekly.

---

## The Formula

```
Weekly LLM Cost = (extraction_calls × ~$0.01) + (repairs × ~$0.15)

Where:
  extraction_calls = sources_scraped × 0.10  (90% rejected by pre-filter)
  repairs          = sources_scraped × 0.02  (2% weekly failure rate)
```

---

## Weekly Cost by Scale

| | 50 sources | 500 sources | 2,000 sources |
|---|---|---|---|
| **LLM extractions** | 5 × $0.01 = $0.05 | 50 × $0.01 = $0.50 | 200 × $0.01 = $2.00 |
| **LLM repairs** | ~1 × $0.15 | ~3 × $0.15 = $0.45 | ~10 × $0.15 = $1.50 |
| Infrastructure | $0 | $0 | ~$10/week |
| **Weekly total** | **$0.20** | **$0.95** | **$13.50** |
| **Annual total** | **$10** | **$50** | **$700** |

---

## What Makes It Cheap

1. **Pre-filter rejection** — 90% of pages never touch an LLM
2. **Repair amortization** — fix a scraper once, it runs free for months
3. **Frequency-aware scheduling** — monthly sources run 1/4 as often as weekly ones
4. **Tombstoning** — confirmed-irrelevant sources stop running entirely

---

## Hard Limits Per Run

| Limit | Default |
|---|---|
| Max extraction calls | 200 |
| Max repairs | 3 |
| Max tokens per extraction | 8K in, 1K out |
| Max repair agent steps | 10 |
| **Max total LLM spend** | **$5.00** (pipeline aborts if exceeded) |

---

## Build vs. Buy

| Option | Monthly Cost | What You Get |
|---|---|---|
| PredictHQ API | $500-2,000 | Event database, no speaker matching |
| Manual analyst | ~$2,000 | Perfect coverage, doesn't scale |
| **L'oeil (500 sources)** | **~$4** | Customizable, speaker matching, Slack alerts |
