# Qualitative ICP Qualification Workflow

A pattern for finding and validating companies that match an Ideal Customer Profile (ICP) when part of
that profile is qualitative — a pricing model, an operational behavior, an organizational structure, or
any other trait that a firmographic database (revenue, headcount, location, industry code) cannot
answer on its own.

**If a coding agent is implementing this, read [`AGENTS.md`](AGENTS.md) first.**

## The problem

Firmographic filters answer questions like "companies with 50–1,000 employees in France, Germany, or
the UK." They cannot answer questions like "companies that operate across multiple legal entities and
are still managing spend manually" or "companies that offer a self-serve, pay-as-you-go plan." Those
traits are real, they are exactly what makes a lead worth prioritizing, and they only exist in public,
unstructured evidence: company websites, job postings, funding announcements, and public filings.

This workflow closes that gap. It uses the [Linkup](https://www.linkup.so) web data API to find
candidate companies and check the qualitative trait against each one's own public evidence, returning
only the companies where that evidence holds up.

## Two entry points

| | Entry Point A | Entry Point B |
|---|---|---|
| **Use when** | A candidate list already exists (own database, CRM export, firmographic filter) | No candidate list exists yet |
| **Script** | [`src/qualify_existing_list.py`](src/qualify_existing_list.py) | [`src/build_and_qualify_list.py`](src/build_and_qualify_list.py) |
| **Input** | An existing company list + a config | Just a config — Linkup finds the candidates |
| **Phases run** | 1 (optional) → 3 → 4 → 5 | 1 (optional) → 2 → 3 → 4 → 5 |
| **Output** | Same shape in both cases: [`schemas/qualified_company_output.schema.json`](schemas/qualified_company_output.schema.json) | |

See [`docs/03-entry-points.md`](docs/03-entry-points.md) for the full decision guide.

## The shape of the workflow

Regardless of entry point, once there is a candidate pool the workflow runs the same two remaining
steps:

1. **Validate every candidate.** Check the qualitative trait against each candidate's own public
   evidence — their website, careers page, filings, or press coverage. This is the phase that turns a
   noisy pool into a trustworthy list; a wide, over-inclusive discovery step is expected, not a bug.
2. **Return only what survived.** The deliverable contains companies whose evidence confirmed the
   trait, plus anything still pending a deeper background check. Companies whose evidence contradicted
   the trait, or who turned out to be a different company with the same name, are dropped.

```
Entry Point A                          Entry Point B
(existing list)                        (no list yet)

┌─────────────────┐                   ┌─────────────────┐
│  Phase 1        │                   │  Phase 1        │
│  Derive the     │                   │  Derive the     │
│  criterion      │                   │  criterion      │
│  (optional)     │                   │  (optional)     │
└────────┬────────┘                   └────────┬────────┘
         │                                     │
         │                            ┌────────▼────────┐
         │                            │  Phase 2        │
         │                            │  Discover a     │
         │                            │  wide candidate │
         │                            │  pool           │
         │                            └────────┬────────┘
         │                                     │
         └──────────────┬──────────────────────┘
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
- [`docs/03-entry-points.md`](docs/03-entry-points.md) — **start here to choose an entry point.**
- [`docs/04-implementation.md`](docs/04-implementation.md) — a phase-by-phase build guide with request
  and response shapes.
- [`docs/05-pitfalls.md`](docs/05-pitfalls.md) — failure modes worth designing around from the start.
- [`docs/06-worked-example.md`](docs/06-worked-example.md) — an end-to-end illustration with realistic
  sample data, for both entry points.

## Data contracts

[`schemas/`](schemas/) has the JSON Schema for every input and output this workflow uses, independent of
any programming language:

- [`config.schema.json`](schemas/config.schema.json) — the config both entry points read.
- [`company_list_input.schema.json`](schemas/company_list_input.schema.json) — Entry Point A's input list.
- [`qualified_company_output.schema.json`](schemas/qualified_company_output.schema.json) — the final output, from either entry point.
- [`excluded_company_log.schema.json`](schemas/excluded_company_log.schema.json) — the audit log of dropped candidates and why.

## Reference implementation

[`src/`](src/) contains a working, phase-by-phase implementation in Python. Each `phaseN_*.py` file
implements one phase and can be run standalone; the two entry-point scripts chain them together.

```bash
cd src
pip install -r requirements.txt
export LINKUP_API_KEY=your-api-key-here
cp config.example.json config.json   # then edit config.json for your client, ICP, and criterion

# Entry Point A - you already have a list
cp companies.example.json companies.json   # then edit with your real candidates
python qualify_existing_list.py --config config.json --companies companies.json --out qualified_list.json

# Entry Point B - no list yet, let Linkup build one
python build_and_qualify_list.py --config config.json --out final_list.json
```

Each phase also runs standalone, which is useful for testing or re-running a single step:

```bash
python phase1_derive_icp.py "Client Name" "https://client-website.com"
python phase3_validate.py config.json candidates.json
python phase4_background_verify.py config.json unclear.json
```

The Python implementation is a reference, not a requirement — the request/response shapes in
`docs/04-implementation.md` and the schemas in `schemas/` are what matter if reimplementing this in a
different language or framework.
