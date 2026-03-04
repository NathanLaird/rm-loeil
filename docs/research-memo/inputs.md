# Research Memo — Data Inputs

> What to feed the pipeline, ranked by signal quality vs. integration effort.

---

## Primary Inputs (From the Brief)

| Input | Source | Integration |
|---|---|---|
| Company website | httpx + BeautifulSoup | Automated scrape of about, product, team, pricing pages |
| LinkedIn headcount growth | Proprietary data | Injected at intake from internal feed |
| CRM notes | Salesforce / HubSpot | API pull at intake |

---

## Recommended Additional Inputs

### Tier 1: Always Include

**GitHub Activity** — Engineering velocity, developer adoption, open-source strategy. A company with accelerating star counts and growing contributor base has organic developer pull. Free (5K requests/hour with token).

**Crunchbase** — Authoritative funding history, investor composition, valuation benchmarks. $149/month for API. If unavailable, the pipeline flags the gap — it doesn't guess.

**Apollo Enrichment API** — Up-to-date employment data roughly as complete as what you'd find scraping LinkedIn as a logged-out user. Team composition by department, executive titles and tenure, hiring patterns, company size validation. Avoids the compliance complexity of direct LinkedIn scraping while providing comparable coverage.

**Recent Press & News** — Product launches, partnerships, executive hires, competitive positioning. Tavily ($0.01/query) with DuckDuckGo fallback.

**Twitter / X** — Founder and executive posts reveal strategic intent, speaking engagement plans, and product direction before press releases. Company mentions surface market perception and community engagement. Also serves as a discovery signal for conference appearances (Task 1 integration).

**LinkedIn** — Team composition by department, recent senior hires, hiring velocity, executive backgrounds. Complements Apollo with relationship-graph data (mutual connections, endorsements, career trajectories).

### Tier 2: Include When Available

**Job Postings** — Complements Apollo/LinkedIn hiring data with role-level detail (tech stack requirements, seniority, location). Source from career pages or Indeed.

**G2 / TrustRadius Reviews** — Enterprise customer sentiment, competitive comparisons, feature complaints. Independent of company narrative.

**ProductHunt Launches** — Developer/prosumer traction and early community sentiment. Most useful for PLG and dev tools companies.

### Tier 3: Company-Type Specific

| Input | Best For | Source |
|---|---|---|
| Patent filings | Deep-tech, hardware | USPTO API (free) |
| Academic citations | AI/ML built on published research | Semantic Scholar (free) |
| Web traffic estimates | PLG where traffic = pipeline | SimilarWeb ($200/mo) |
| Regulatory filings | Fintech, healthtech | SEC EDGAR, FDA |

---

## Industry Trends Collection

A curated, RAG-indexed corpus of market macro content that the pipeline's contextualize stage searches against:

**What goes in:** Gartner reports, Forrester Wave analyses, VC/PE thought leadership essays (e.g. a16z, Bessemer, Battery), market sizing reports, industry conference keynote summaries.

**Why it matters:** The "why now" thesis is stronger when the company's trajectory aligns with independently-identified macro trends. "Headcount growing 85% QoQ" is interesting. "Headcount growing 85% QoQ in a segment Gartner just identified as a new Magic Quadrant category" is compelling.

**Maintenance:** Updated quarterly. New reports are embedded and indexed. Stale reports (>18 months) are downweighted but retained for historical context.

---

## Proprietary Data

These are the inputs no external tool has access to — the biggest differentiator vs. generic AI research:

**LinkedIn headcount growth** — The triggering signal. Proprietary, not available to competitors.

**CRM interaction history** — Prior meetings, partner impressions, reasons for passing last time.

**Portfolio network effects** — Does the target sell to or partner with existing portfolio companies?

**Co-investor intelligence** — Which peer funds are looking at this company? From CRM tracking + conference sighting data from Task 1.

---

## Input Priority (B2B SaaS / Dev Tools)

| Priority | Input | In Pipeline |
|---|---|---|
| 1 | Company website | ✅ |
| 2 | LinkedIn headcount | ✅ (injected) |
| 3 | CRM notes | ✅ (injected) |
| 4 | GitHub activity | ✅ |
| 5 | Crunchbase | ✅ (with API key) |
| 6 | Apollo enrichment | ✅ |
| 7 | Recent press | ✅ |
| 8 | Twitter / X | ✅ |
| 9 | LinkedIn profiles | ✅ |
| 10 | Industry trends | ✅ (RAG corpus) |
| 11 | Job postings | Designed |
| 12 | G2 / ProductHunt | Designed |
