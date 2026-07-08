# Implementation Guide

Each phase below includes the request shape, the reasoning behind it, and the response shape to expect.
A full reference implementation of every phase is in [`../src`](../src). See
[`03-entry-points.md`](03-entry-points.md) first if you have not already — it explains which phases
each entry point actually runs. Phase 2 (discovery) belongs to Entry Point B only; phases 1, 3, 4, and 5
are shared by both entry points.

## Phase 1 — Derive the ICP (optional)

Skip this phase if the qualitative criterion is already stated as a concrete, checkable statement. Run
it when the client can describe their business but not the specific trait that makes a lead worth
prioritizing.

**Request** — `POST /v1/search`

```json
{
  "q": "Scrape {client_website} customer stories, case studies, and testimonials pages. Also run a separate web search for independent reviews and press coverage of {client_name}'s customers. Extract, for each customer mentioned, company size, industry, geography, and the specific operational problem {client_name} solved for them. Return the recurring patterns across customers and source URLs for each.",
  "depth": "standard",
  "outputType": "structured",
  "structuredOutputSchema": {
    "type": "object",
    "properties": {
      "customer_examples": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "company_name": {"type": "string"},
            "company_size": {"type": "string"},
            "problem_solved": {"type": "string"},
            "source_url": {"type": "string"}
          },
          "required": ["company_name", "problem_solved", "source_url"]
        }
      },
      "recurring_patterns": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["customer_examples", "recurring_patterns"]
  }
}
```

**What to do with the response:** look for a pattern that repeats across several customer examples and
is not already captured by a firmographic field — that pattern is the qualitative criterion for phase 2
onward. State it as a concrete sentence before moving on (e.g. "operates across multiple legal entities
and is likely still managing spend manually across them"), not as a vague theme.

## Phase 2 — Discover a wide candidate pool (Entry Point B only)

Skip this phase entirely for Entry Point A — the client's existing list is the candidate pool, and goes
straight to phase 3.

Run both calls below and pool their output before moving to phase 3. They are complementary, not
alternatives: the research call is the primary source of volume, the search call fills in anything the
research call missed (a specific named competitor, a specific directory).

### 2a. Broad discovery — `POST /v1/research`

```json
{
  "q": "Find as many potential ICP customers as possible for {client_name}. ICP definition: {natural_language_icp} with this qualitative trait as a hard requirement: {qualitative_criterion}. Look broadly across funding/expansion news, company directories, job boards (especially finance/CFO/controller hiring posts that describe {qualitative_criterion} as part of the role), and industry press. Do not stop at a small sample — list as many distinct qualifying companies as you can find, even if evidence for some is thinner than others. For each company, return company name and a short evidence note with a source URL.",
  "mode": "research",
  "reasoningDepth": "L",
  "outputType": "structured",
  "structuredOutputSchema": {
    "type": "object",
    "properties": {
      "companies": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "company_name": {"type": "string"},
            "evidence": {"type": "string"},
            "source_url": {"type": "string"}
          },
          "required": ["company_name"]
        }
      }
    },
    "required": ["companies"]
  }
}
```

Note that only `company_name` is required — see `02-endpoints.md` for why. Expect this call to take
5–10 minutes at `reasoningDepth: L`, and to return a list ranging from dozens to over a hundred
companies depending on how much public evidence exists for the criterion.

Hiring posts are an especially strong facet for organizational or structural criteria (multi-entity
operations, rapid headcount growth, a specific tech stack): a company's own job listing describing what
the role will manage is first-party evidence of its own structure.

### 2b. Targeted top-up — `POST /v1/search`

```json
{
  "q": "Find companies in {industry} and {geography} that may match this qualitative trait: {qualitative_criterion}. The broader target profile is {natural_language_icp}. Run separate web searches for: forum and community threads recommending or comparing {industry} tools with {qualitative_criterion}, \"alternatives to {reference_competitor}\" or \"vs\" comparison pages that mention {qualitative_criterion}, directory or \"best of\" list pages for {industry} tools with {qualitative_criterion}, finance/CFO/controller job postings that describe {qualitative_criterion} as part of the role, and recent funding, expansion, or hiring announcements in {industry} and {geography} that indicate {qualitative_criterion}. Return company name, website, the exact quote or snippet showing the trait, and source URL.",
  "depth": "standard",
  "outputType": "searchResults"
}
```

If this single call underperforms on one particular facet (for example, funding news gets crowded out
by "best of" list content), split that facet into its own follow-up call rather than assuming the
signal does not exist — see `05-pitfalls.md`.

Community sources (forums, Reddit) are strongest for opinion-based criteria where people describe their
own setup or a tool they dislike, but posters are usually anonymous. Treat a community thread as
confirmation that the underlying pattern exists, not as a named candidate on its own.

## Phase 3 — Validate every candidate

This is the phase that turns the pool from phase 2 into a trustworthy list. Every candidate from phase 2
must pass through this check — do not treat any name from phase 2 as pre-qualified.

**Request** — `POST /v1/search`

```json
{
  "q": "For each of these companies: {company_list}. First find their official website, about/careers page, and any employee count. Then check whether the company {qualitative_criterion}. Extract the exact supporting text and source URL. If a company name is ambiguous or you cannot find a matching real company, mark it not_found instead of guessing.",
  "depth": "deep",
  "outputType": "structured",
  "structuredOutputSchema": {
    "type": "object",
    "properties": {
      "results": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "company_name": {"type": "string"},
            "website": {"type": "string"},
            "employee_count": {"type": "string"},
            "criterion_status": {"type": "string", "enum": ["confirmed", "not_found", "unclear"]},
            "evidence_snippet": {"type": "string"},
            "source_url": {"type": "string"}
          },
          "required": ["company_name", "criterion_status"]
        }
      }
    },
    "required": ["results"]
  }
}
```

**Batch size:** for a pool of 50–150 candidates, batch into groups of roughly 10–15 companies per call.
One call per company is wasteful; one call for the entire pool makes it too easy for the model to give
each company only shallow attention. 10–15 per call is a reasonable middle ground.

**Before trusting a "confirmed" result:** cross-check the evidence's industry, country, and rough size
against the context that first surfaced the company in phase 2 (its source URL, the facet it came
from). A generic company name matching an unrelated business with the same name is a real risk at scale
— see `05-pitfalls.md` for a concrete example of how this shows up.

## Phase 4 — Background verification for unclear cases

Only companies marked `unclear` in phase 3 go through this phase — not the full pool, and not companies
already marked `confirmed` or `not_found` (unless a confirmed result's entity identity looks ambiguous;
see `05-pitfalls.md`).

Submit all background verification jobs in parallel, then poll them together, rather than running them
one at a time.

**Request** — `POST /v1/research`, once per company

```json
{
  "q": "Investigate whether {company_name} {qualitative_criterion}. Check their careers page, product pages, press coverage, and funding announcements. Also determine their approximate employee count. Cross-check any conflicting claims between sources. Return a clear confirmed / not_found / unclear verdict, employee count, the strongest supporting evidence, and source URLs.",
  "mode": "investigate",
  "reasoningDepth": "S",
  "outputType": "structured",
  "structuredOutputSchema": {
    "type": "object",
    "properties": {
      "company_name": {"type": "string"},
      "verdict": {"type": "string", "enum": ["confirmed", "not_found", "unclear"]},
      "employee_count": {"type": "string"},
      "evidence": {"type": "string"},
      "source_urls": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["company_name", "verdict"]
  }
}
```

Expect each job to take 2–5 minutes at `reasoningDepth: S`. Thirteen jobs submitted together typically
all complete within about 8–10 minutes, since they run independently once submitted.

## Phase 5 — Build the final list

Merge phase 3's results with phase 4's resolved verdicts, apply the firmographic band as a separate
cross-check, and exclude anything that did not survive.

**Request** — `POST /v1/search`

```json
{
  "q": "Using firmographic fit for {firmographic_qualified_companies}, on-site criterion checks {criterion_check_results}, and any completed background verification {background_verification_results}, assign each company a tier using this definition: {tier_definition}. Exclude any company whose criterion_status is not_found from the returned list. Return company name, website, firmographic fit, criterion status, evidence, source URLs, tier, and whether background verification is still pending.",
  "depth": "standard",
  "outputType": "structured",
  "structuredOutputSchema": {
    "type": "object",
    "properties": {
      "companies": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "company_name": {"type": "string"},
            "website": {"type": "string"},
            "firmographic_fit": {"type": "string"},
            "criterion_status": {"type": "string"},
            "evidence": {"type": "string"},
            "source_urls": {"type": "array", "items": {"type": "string"}},
            "tier": {"type": "string"},
            "background_verification_pending": {"type": "boolean"}
          },
          "required": ["company_name", "website", "criterion_status", "tier", "source_urls"]
        }
      }
    },
    "required": ["companies"]
  }
}
```

The delivered list should contain only `confirmed` companies plus `unclear` ones still pending
background verification. `not_found` companies, and anything excluded for a firmographic mismatch
(too large, too small, or a subsidiary of a much larger company rather than an independent buyer),
should be kept in an internal audit log rather than shown to the end user as a recommendation.
