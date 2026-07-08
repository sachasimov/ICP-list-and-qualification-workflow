# Qualitative ICP Qualification Workflow

A pattern for finding and validating companies that match an Ideal Customer Profile (ICP) when part of
that profile is qualitative — a pricing model, an operational behavior, an organizational structure, or
any other trait that a firmographic database (revenue, headcount, location, industry code) cannot
answer on its own.

## The problem

Firmographic filters answer questions like "companies with 50–1,000 employees in France, Germany, or
the UK." They cannot answer questions like "companies that operate across multiple legal entities and
are still managing spend manually" or "companies that offer a self-serve, pay-as-you-go plan." Those
traits are real, they are exactly what makes a lead worth prioritizing, and they only exist in public,
unstructured evidence: company websites, job postings, funding announcements, and public filings.

This workflow closes that gap. It uses the [Linkup](https://www.linkup.so) web data API to discover a
broad pool of candidate companies, then checks the qualitative trait against each candidate's own
public evidence, and returns only the companies where that evidence holds up.

## The shape of the workflow

The workflow runs in three phases:

1. **Discover wide.** Build a large, intentionally over-inclusive pool of candidate companies. A name on
   this list is a lead, not a confirmed match.
2. **Validate every candidate.** Check the qualitative trait against each candidate's own public
   evidence — their website, careers page, filings, or press coverage. This is the phase that turns a
   noisy pool into a trustworthy list; it is not a sign that phase 1 did something wrong.
3. **Return only what survived.** The deliverable contains companies whose evidence confirmed the
   trait, plus anything still pending a deeper background check. Companies whose evidence contradicted
   the trait, or who turned out to be a different company with the same name, are dropped.

```
                 ┌─────────────────┐
  ICP definition │  Phase 1        │
  (given or      │  Derive / state │
   derived)  ──► │  the criterion  │
                 └────────┬────────┘
                          │
                 ┌────────▼────────┐
                 │  Phase 2        │
                 │  Discover a     │
                 │  wide candidate │
                 │  pool           │
                 └────────┬────────┘
                          │
                 ┌────────▼────────┐
                 │  Phase 3        │
                 │  Validate every │
                 │  candidate      │
                 └────────┬────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
     ┌────────▼────────┐     ┌────────▼────────┐
     │  Confirmed /     │     │  Unclear         │
     │  not found       │     │  → Phase 4       │
     └────────┬─────────┘     │  Background      │
              │                │  verification    │
              │                └────────┬─────────┘
              │                         │
              └────────────┬────────────┘
                            │
                   ┌────────▼────────┐
                   │  Phase 5        │
                   │  Build the      │
                   │  final list     │
                   └─────────────────┘
```

## Documentation

- [`docs/01-overview.md`](docs/01-overview.md) — the problem in more depth, and the inputs/outputs of
  the workflow.
- [`docs/02-endpoints.md`](docs/02-endpoints.md) — which Linkup endpoint to use for each phase, and why.
- [`docs/03-implementation.md`](docs/03-implementation.md) — a phase-by-phase build guide with request
  and response shapes.
- [`docs/04-pitfalls.md`](docs/04-pitfalls.md) — failure modes worth designing around from the start.
- [`docs/05-worked-example.md`](docs/05-worked-example.md) — an end-to-end illustration with realistic
  sample data.

## Reference implementation

[`src/`](src/) contains a working, phase-by-phase implementation in Python. Each file corresponds to one
phase of the workflow and can be run independently or chained together by `src/run_pipeline.py`.

```bash
cd src
pip install -r requirements.txt
export LINKUP_API_KEY=your-api-key-here
cp config.example.json config.json   # then edit config.json for your client, ICP, and criterion
python run_pipeline.py --config config.json --out final_list.json
```

Each phase also runs standalone, which is useful for testing or re-running a single step:

```bash
python phase1_derive_icp.py "Client Name" "https://client-website.com"
python phase3_validate.py config.json candidates.json
python phase4_background_verify.py config.json unclear.json
```
