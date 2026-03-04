# L'oeil — Investment Intelligence Through Agentic Systems

**[View the full documentation →](https://nathanlaird.github.io/rm-loeil/)**

---

## Overview

L'oeil is a suite of AI-powered research tools for venture deal sourcing and diligence, built on **LangGraph**.

| Task | What It Does | Documentation |
|---|---|---|
| **Conference Scraper** | Discover conferences where target executives will attend or present. Alert partners via Slack. | [Full docs →](https://nathanlaird.github.io/rm-loeil/conference-scraper/) |
| **Research Memo Generator** | Generate outside-in research memos for companies showing inflection. | [Full docs →](https://nathanlaird.github.io/rm-loeil/research-memo/) |
| **Investment Memo** | 3-5 page memo on Nightfall AI. | [PDF →](Nightfall_AI_Investment_Memo.pdf) |

---

## Quick Answers

### Task 1: Conference Scraper

| Question | Answer |
|---|---|
| What tools? | LangGraph, httpx + BeautifulSoup, browser-use + Playwright, Slack Bolt. [Details →](https://nathanlaird.github.io/rm-loeil/conference-scraper/#recommended-tools) |
| Which LLM? | Complexity-tiered selection — fast/cheap for extraction, premium for repair. [Details →](https://nathanlaird.github.io/rm-loeil/cost-and-observability/model-selection/) |
| Example prompts? | Extraction, repair, discovery. [Details →](https://nathanlaird.github.io/rm-loeil/conference-scraper/#example-prompts) |
| Weekly cost? | ~$1/week at 500 sources. [Details →](https://nathanlaird.github.io/rm-loeil/conference-scraper/cost/) |

### Task 2: Research Memo

| Question | Answer |
|---|---|
| What other inputs? | GitHub, Crunchbase, Apollo, press, Twitter, LinkedIn, industry trends. [Details →](https://nathanlaird.github.io/rm-loeil/research-memo/inputs/) |
| Architecture & tools? | 7-stage LangGraph pipeline with tiered LLM strategy. [Details →](https://nathanlaird.github.io/rm-loeil/research-memo/#architecture-tools) |
| LLM limitations? | Hallucination, overconfidence, positivity bias, staleness, contradictions, truncation. [Details →](https://nathanlaird.github.io/rm-loeil/research-memo/limitations/) |

---

## Project Structure

```
rm-loeil/
├── docs/                          # Documentation (GitHub Pages source)
│   ├── index.md                   # Landing page
│   ├── conference-scraper/        # Task 1 docs
│   ├── research-memo/             # Task 2 docs
│   └── cost-and-observability/    # Cost controls, model selection & tracing
├── src/                           # Working code
│   ├── pipeline.py                # Research memo LangGraph pipeline
│   ├── scrapers/                  # Website, GitHub, news scrapers
│   ├── extractors/                # LLM fact extraction
│   ├── synthesis/                 # Enrichment & section writing
│   ├── output/                    # Memo assembly
│   └── conference_scraper/        # Conference scraper pipeline
├── examples/                      # Example outputs
│   └── conference_scrape_example.json
├── demo.py                        # Research memo CLI
├── conference_demo.py             # Conference scraper CLI
├── Nightfall_AI_Investment_Memo.pdf  # Task 3
└── mkdocs.yml                     # Docs site config
```

---

## Running the Demos

```bash
pip install -r requirements.txt

# Conference scraper demo (no API keys needed — uses example data)
python conference_demo.py

# Research memo (requires OPENAI_API_KEY + ANTHROPIC_API_KEY)
python demo.py cursor.sh -v
```

---

## Browsing the Docs Locally

```bash
pip install mkdocs-material
mkdocs serve
# Open http://localhost:8000
```
