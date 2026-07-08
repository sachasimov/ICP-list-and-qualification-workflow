# Overview

## Why firmographic filtering isn't enough

A typical company database can filter on structured fields: revenue band, employee count, headquarters
location, industry code, funding stage, recent news. These fields answer a large share of ICP
questions, but not all of them.

Consider two ICP statements:

- "Companies with 100–500 employees in the software industry, headquartered in Europe." — fully
  answerable from a structured schema.
- "Companies with 100–500 employees in the software industry, headquartered in Europe, that offer a
  self-serve pay-as-you-go pricing plan." — the size and location are structured; "self-serve
  pay-as-you-go pricing" is not a field any firmographic database stores. It has to be read off the
  company's own pricing page.

The second kind of criterion is common and valuable: it is often the exact detail that determines
whether a company is a good fit, a good time to reach out, or a good candidate for a specific offer
tier. It just cannot be answered by a schema lookup — it requires reading public evidence about each
company individually.

## What this workflow adds

Given:

- an ICP, in natural language or split into structured fields plus one or more qualitative criteria,
- a qualitative criterion that a firmographic schema cannot answer,

the workflow produces:

- a pool of candidate companies, discovered from public evidence rather than only from a pre-existing
  database,
- for each candidate, a status (confirmed / not found / unclear) for the qualitative criterion, with the
  exact supporting text and a source URL,
- a final list containing only the companies whose evidence held up, ready to hand to a CRM, a
  spreadsheet, or a sales workflow.

## Inputs

| Input | Required | Notes |
|---|---|---|
| Client name and website | Yes | Used to derive the ICP if it isn't already stated cleanly. |
| Natural-language ICP | Recommended | If missing, derive it from the client's own case studies (phase 1). |
| Qualitative criterion | Yes | Must be phrased as a concrete, checkable statement. "Flexible pricing" is not checkable; "offers a self-serve pay-as-you-go plan without a sales call" is. |
| Firmographic band | Recommended | Employee count range, geography, industry — used to cross-check candidates that pass the qualitative check but are a poor structural fit. |
| Existing candidate list | Optional | If the client already has a firmographically-qualified list, validate it directly instead of discovering one from scratch. |
| Tier or acceptance definition | Optional | What separates a strong match from a partial one, if the output needs to be tiered rather than binary. |

## Outputs

- A validated company list: `company_name`, `website`, `employee_count`, `criterion_status`,
  `evidence`, `source_url`, and (optionally) `tier`.
- A log of excluded candidates and the reason for exclusion (not found, entity mismatch, firmographic
  mismatch) — useful for auditing the pipeline, not meant to be shown as a "failed leads" list.
- A list of companies still pending background verification, for cases where the initial evidence was
  ambiguous.

## Where the workflow stops

This workflow finds and verifies public evidence. It does not:

- guarantee coverage of every company that matches the criterion — only what public evidence surfaces,
- replace a CRM, lead-scoring system, or outbound sequencer — it produces the evidence those systems
  need,
- resolve criteria with no public trace (e.g., private pricing shared only after a sales call) without
  a human or a sales conversation filling that gap.
