# L'oeil — Investment Intelligence Through Agentic Systems

---

## What This Project Is

Venture capital runs on information asymmetry. The firms that move fastest on the best companies win. Two recurring bottlenecks slow investment teams down:

1. **Conference intelligence.** Partners need to know when portfolio founders are attending or speaking at upcoming events — these are key opportunities to network, mentor, and provide hands-on support. Today an analyst manually checks conference websites. It doesn't scale, and events get missed.

2. **Company research.** When a company shows strong inflection signals (headcount growth, GitHub traction, press buzz), an analyst pulls together a research memo. The process is tedious — most of the time goes to data collection, not thinking.

**L'oeil automates both.** Two agentic pipelines — one for conference monitoring, one for research memo generation — built mostly on cheap deterministic code that only calls LLMs when judgment is actually required. Conference alerts cost under $1/week. Research memos cost under $0.50 each.

Both systems are built on [LangGraph](https://www.langchain.com/langgraph) and share a [model selection strategy](cost-and-observability/model-selection.md) that assigns each LLM task a complexity score rather than hardcoding model names.

---

## The Three Tasks

| | [Task 1: Conference Scraper](conference-scraper/index.md) | [Task 2: Research Memo](research-memo/index.md) | [Task 3: Investment Memo](investment-memo/index.md) |
|---|---|---|---|
| **What it does** | Scrapes conference sites, matches attendees against target companies, sends Slack alerts with calendar cross-referencing | Takes a company + signal, produces a source-cited research memo | 3-5 page outside-in memo on Nightfall AI |
| **When it runs** | Weekly on a schedule | On-demand when a signal fires | — |
| **Key design idea** | Self-healing scrapers with snapshot tests | Tiered LLM strategy with industry trend contextualization | AI-native DLP positioning as "Netskope for AI Agents" |
| **Typical cost** | ~$1/week at 500 sources | ~$0.30-0.55 per memo | — |

The systems feed each other: conference scraper output (which funds are showing up at which companies' events) becomes a proprietary input to the research memo — co-investor intelligence that no external tool can provide.

---

## Where to Find Each Interview Answer

### Task 1: Conference Scraper

| Question | Page |
|---|---|
| What tools would you recommend? | [Recommended tools](conference-scraper/index.md#recommended-tools) |
| Which LLM is the best fit? | [Model selection](cost-and-observability/model-selection.md) |
| Example prompts you'd use? | [Prompts](conference-scraper/index.md#example-prompts) |
| How to approximate weekly cost? | [Cost model](conference-scraper/cost.md) |

### Task 2: Research Memo

| Question | Page |
|---|---|
| What other inputs should we consider? | [Additional inputs](research-memo/inputs.md) |
| End-to-end architecture and tools? | [Architecture](research-memo/index.md#architecture-tools) |
| LLM limitations when interpreting output? | [LLM limitations](research-memo/limitations.md) |

### Task 3: Investment Memo

[Nightfall AI Investment Memo →](investment-memo/index.md)
