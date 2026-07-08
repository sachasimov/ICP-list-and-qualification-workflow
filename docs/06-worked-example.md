# Worked Example

This walks through the workflow for a representative case: a B2B spend-management platform that sells
to European mid-market companies, where the qualitative criterion is structural rather than a matter of
opinion.

The main walkthrough below follows **Build a List** (`build_and_qualify_list.py`), since it exercises
every phase, including discovery. See [the Qualify a List variant](#qualify-a-list-variant-starting-from-an-existing-list)
at the end for how this changes when a candidate list already exists.

## Setup

- **Client:** a spend-management platform selling to European companies with roughly 50–1,000
  employees.
- **Qualitative criterion:** the company operates across multiple legal entities, subsidiaries, or
  country offices, and is likely still managing spend manually or with fragmented tools per entity.
- **Firmographic band:** 50–1,000 employees, headquartered in Europe.

## Phase 1 — Deriving the criterion

Scraping the client's own customer case studies surfaces a recurring pattern across several named
customers: rapid headcount growth, multiple offices or subsidiaries, and a move away from shared
corporate cards or spreadsheets. One case study states the problem explicitly:

> "Centralised payments across four entities, reducing transaction management from three people to one
> person handling the entire process."

That sentence is the qualitative criterion, stated as something checkable.

## Phase 2 — Discovery

The broad discovery call (phase 2a) surfaces companies through several evidence types:

| Discovery signal | Example finding |
|---|---|
| Job posting for a Head of Finance | "Hiring a Head of Finance for group-wide financial consolidation across multiple entities and jurisdictions." |
| Job posting for a Group Financial Controller | "Recruiting a Group Financial Controller to act as a subject matter expert for group structures." |
| Funding announcement | "Raised €50M to open a new office in a second country, doubling headcount over 12 months." |
| Company directory / registry evidence | "Operates through two distinct legal entities registered in different countries." |

A discovery call at broad reasoning depth against this kind of ICP typically returns a candidate pool
ranging from several dozen to over a hundred named companies, each with its own source.

## Phase 3 — Validation, at scale

For a pool of, say, 65 named candidates, a validation pass batched into groups of roughly 11 companies
per call typically resolves like this:

| Outcome | Count | What it means |
|---|---|---|
| Confirmed | ~51 | Public evidence (careers page, filings, press) directly supports the criterion. |
| Unclear | ~13 | No public evidence either way, or evidence is ambiguous. |
| Not found | ~2 | No real company could be matched to the name. |

Two categories of confirmed results are worth a manual sanity check before they reach phase 5:

- **Entity mismatches.** A validation call checking "Plum" can return evidence about an unrelated
  company that also happens to be named Plum — for example, a skincare brand instead of the intended
  fintech. The fix is to cross-check the evidence's industry and country against the context that
  originally surfaced the company in phase 2.
- **Firmographic mismatches.** A validation call can correctly confirm the qualitative trait for a
  company that is far outside the target size band — a company with thousands of employees, or a
  national subsidiary of a much larger multinational rather than an independent buyer. These get
  excluded in phase 5, not phase 3, since the criterion itself genuinely held up.

## Phase 4 — Background verification

The ~13 unclear cases are submitted as parallel background jobs. A typical batch of this size resolves
within roughly 8–10 minutes, split something like:

| Outcome | Count |
|---|---|
| Resolved confirmed | ~11 |
| Resolved not found | ~2 |

One frequent reason a case resolves "not found" at this stage: the company genuinely operates as a
single legal entity in a single country, with no international presence — the deeper, multi-source
check settles what a single scrape could not.

## Phase 5 — Final list

Combining phase 3 and phase 4 results, then excluding entity mismatches and firmographic mismatches,
turns a pool that started at roughly 65 named candidates into a final validated list in the neighborhood
of 55 companies — each with a specific piece of evidence and a source URL, ready to hand to a CRM or
outbound workflow.

The exact numbers will vary by ICP, industry, and how much public evidence exists for the criterion —
some categories (well-documented, well-funded sectors) will validate at a higher rate than others
(private, low-visibility sectors). The shape of the funnel — wide discovery, full validation, and a
smaller but trustworthy final list — is the consistent part.

## Qualify a List variant: starting from an existing list

Suppose the client's CRM already exports 200 companies that passed a firmographic filter (50–1,000
employees, headquartered in Europe), and the ask is simply: "which of these actually operate across
multiple entities?"

This is `qualify_existing_list.py` (Qualify a List), not `build_and_qualify_list.py` (Build a List). The
difference from the walkthrough above:

- **Phase 1** still runs if the criterion needs deriving, exactly as before.
- **Phase 2 does not run at all.** The 200 companies from the CRM export are the candidate pool — no
  discovery call is made, no new companies are added to or removed from that list at this stage.
- **Phase 3 onward is identical.** All 200 companies go through the same validation call (batched into
  groups of ~15), the same unclear cases go to phase 4 background verification, and phase 5 applies the
  same firmographic and entity-identity cross-checks before producing the final list.

The practical effect: Qualify a List is faster and cheaper per run (no 5–10 minute discovery call), and
it is the natural choice for a recurring job — re-validating the same CRM list weekly to catch new
evidence, without re-discovering candidates that were already ruled in or out.
