# Research Memo — LLM Limitations

> What the investment team should know when interpreting AI-generated memos.

---

L'oeil produces **draft memos**, not final analysis. LLMs have systematic failure modes that human reviewers need to compensate for. Understanding them turns AI memos from a liability into a superpower: get 80% of the research in 3 minutes, spend your judgment on the 20% that matters.

---

## 1. Hallucinated Metrics

LLMs fabricate plausible numbers. "$15M ARR with 200% growth" might appear when no source contains revenue data. Dangerous in IC discussions where specific numbers carry outsized weight.

**How we mitigate:** Synthesis receives only structured facts, not raw pages. Every metric requires a source citation. The enrichment stage explicitly outputs gaps — data it looked for but didn't find. Reviewers can trace any claim back to the exact LLM input via the [trace log](../cost-and-observability/tracing.md).

**What to check:** Does every number have a citation? Are there metrics in the narrative not in the data tables?

---

## 2. Overconfident Narratives

A memo based on 2 sources reads as authoritatively as one based on 6. Writing fluency doesn't correlate with evidence depth. This is the most dangerous limitation for investment decisions.

**How we mitigate:** Data quality banner at the top of every memo ("Based on N sources. Gaps: [list]"). Single-source sections get a warning flag.

**What to check:** How many sources contributed? Does the confidence score match the strength of the claims?

---

## 3. Positivity Bias

Company websites, press releases, and ProductHunt are promotional. When most inputs are company-produced, the memo skews bullish — not because the model is biased, but because it faithfully summarizes bullish inputs.

**How we mitigate:** Source diversity tracking (company-produced vs. independent). The Risks section uses a dedicated adversarial prompt.

**What to check:** What's the source diversity ratio? Does the Risks section feel substantive or boilerplate?

---

## 4. Knowledge Cutoff Leakage

The model might blend outdated training data with fresh scraped facts — referencing a CEO who left or a product that was sunset.

**How we mitigate:** "Base your analysis ONLY on the provided facts." All sources scraped at runtime. Scrape timestamps in the appendix.

---

## 5. Silent Contradiction Resolution

When sources disagree ("Crunchbase: $30M, TechCrunch: $35M"), the model may pick one number without flagging the discrepancy.

**How we mitigate:** Dedicated contradiction detection in the enrichment stage. Both values and sources surfaced in the appendix.

---

## 6. Context Window Truncation

Large companies generate more data than fits in a context window. The model works with whatever fits, potentially missing important information.

**How we mitigate:** Staged processing (extract per source, then only structured facts flow forward). Aggregate statistics over raw data. Truncation markers in output.

---

## Quick Reference

| Limitation | What to Check | Where |
|---|---|---|
| Hallucinated metrics | Numbers without citations | Data tables |
| Overconfidence | Source count vs. claim strength | Data quality banner |
| Positivity bias | Source diversity | Appendix |
| Stale knowledge | Info not from scraped sources | Trace log |
| Silent contradictions | Conflicting facts | Appendix |
| Truncation | Missing data for large companies | Truncation warnings |
