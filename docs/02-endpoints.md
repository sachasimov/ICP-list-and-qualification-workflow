# Linkup Endpoints Used In This Workflow

All requests are authenticated with:

```
Authorization: Bearer <LINKUP_API_KEY>
```

## `/v1/search` — synchronous search and scrape

Used for: deriving the ICP from known pages, a fast/narrow discovery pass, and validating each
candidate's own site.

| Parameter | Purpose |
|---|---|
| `q` | The retrieval instruction. See `04-implementation.md` for exact wording per phase. |
| `depth` | `standard` for a known URL plus independent parallel searches; `deep` when the exact page must be found before it can be read (e.g. "find the pricing page, then scrape it"). |
| `outputType` | `searchResults` for a raw list another step will process; `structured` for fields a program will consume directly (requires `structuredOutputSchema`). |
| `structuredOutputSchema` | A JSON Schema describing the fields to extract. Keep required fields minimal — see the note on schema strictness below. |

`depth: standard` runs one planning pass and can execute several independent searches in parallel, or
scrape a URL that is already known. It cannot reliably discover a URL and then scrape that same,
newly-discovered URL within a single request.

`depth: deep` can search, inspect the results, and then scrape whatever page that search turned up, in
one request. Use it whenever the exact page is not known in advance — which is the normal case for
"check the pricing page" or "check the careers page" against a company you have only a name for.

## `/v1/research` — asynchronous, multi-source investigation

Used for: broad candidate discovery at scale, and background verification of ambiguous cases.

Research runs as an agent that plans, searches, and cross-checks across many sources before returning a
synthesized, cited answer. It is asynchronous:

```
POST /v1/research   → { id, status: "pending" }
GET  /v1/research/:id → poll until status is "completed" or "failed"
```

| Parameter | Purpose |
|---|---|
| `q` | The investigation brief. Broader and more detailed prompts produce more predictable output — state the entities to consider, the fields to extract, and what counts as sufficient evidence. |
| `mode` | `research` for broad, multi-entity discovery (used in phase 2); `investigate` for a focused, single-entity question (used in phase 4). |
| `reasoningDepth` | `S` (2–5 min) for a single-entity background check; `L` (5–10 min) for a broad, multi-entity discovery sweep. |
| `outputType` | `structured`, with a `structuredOutputSchema`, for both discovery and verification use cases in this workflow. |

**Polling:** use exponential backoff (e.g. start at 2s, double up to a cap of ~10s) rather than
constant-interval polling. Submitting several research jobs and polling them together is far more
efficient than running them one at a time — they execute independently once submitted.

## Endpoint choice by phase

| Phase | Endpoint | Depth / Mode | Why |
|---|---|---|---|
| 1. Derive the ICP | `/v1/search` | `standard` | The client's own site is a known URL; a handful of parallel searches cover independent cross-checks. |
| 2. Discover candidates (fast, narrow) | `/v1/search` | `standard` | Good for a quick top-up or a small preview; not the primary source of volume. |
| 2. Discover candidates (broad) | `/v1/research` | `mode: research`, `reasoningDepth: L` | A single call can independently investigate many sources in parallel and return a large, named, sourced list — this is the primary source of volume for a large candidate pool. |
| 3. Validate each candidate | `/v1/search` | `deep` | The exact page proving or disproving the criterion (pricing, careers, docs) is not known in advance; `deep` finds it and reads it in one request. |
| 4. Background verification | `/v1/research` | `mode: investigate`, `reasoningDepth: S` | A focused, single-entity investigation with built-in cross-checking, for cases a single search pass left ambiguous. |
| 5. Build the final list | `/v1/search` | `standard` | Pure synthesis over data already collected; no new retrieval is needed. |

## A note on structured schema strictness

`structuredOutputSchema`'s `required` array controls how much of what the model finds actually makes it
into the response. If a field like `source_url` is marked required on every array item, and the model
finds a company but cannot cleanly attach a citation to it, the entire entry is dropped rather than
returned with a missing field.

For a discovery call where the goal is volume (phase 2, broad discovery), keep the required fields to
just `company_name`. For a validation call where the goal is precision (phase 3), it is reasonable to
require `criterion_status` alongside `company_name`, since a validation result without a clear status is
not useful anyway.
