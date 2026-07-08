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

## Two ways to use this

| | Qualify a List | Build a List |
|---|---|---|
| **Use when** | A candidate list already exists (own database, CRM export, firmographic filter) | No candidate list exists yet |
| **Script** | [`src/qualify_existing_list.py`](src/qualify_existing_list.py) | [`src/build_and_qualify_list.py`](src/build_and_qualify_list.py) |
| **Input** | An existing company list + a config | Just a config — Linkup finds the candidates |
| **Steps run** | Derive criterion (optional) → Validate → Background-check unclear cases → Final list | Derive criterion (optional) → Discover candidates → Validate → Background-check unclear cases → Final list |
| **Output** | Same shape in both cases: [`schemas/qualified_company_output.schema.json`](schemas/qualified_company_output.schema.json) | |

See [`docs/03-choosing-a-workflow.md`](docs/03-choosing-a-workflow.md) for the full decision guide.

## The shape of the workflow

Whichever one is used, once there is a candidate pool the workflow runs the same two remaining steps:

1. **Validate every candidate.** Check the qualitative trait against each candidate's own public
   evidence — their website, careers page, filings, or press coverage. This is the step that turns a
   noisy pool into a trustworthy list; a wide, over-inclusive candidate pool is expected, not a bug.
2. **Return only what survived.** The deliverable contains companies whose evidence confirmed the
   trait, plus anything still pending a deeper background check. Companies whose evidence contradicted
   the trait, or who turned out to be a different company with the same name, are dropped.

```
Qualify a List                         Build a List
(existing list)                        (no list yet)

┌─────────────────┐                   ┌─────────────────┐
│  Derive the     │                   │  Derive the     │
│  criterion      │                   │  criterion      │
│  (optional)     │                   │  (optional)     │
└────────┬────────┘                   └────────┬────────┘
         │                                     │
         │                            ┌────────▼────────┐
         │                            │  Discover a     │
         │                            │  wide candidate │
         │                            │  pool           │
         │                            └────────┬────────┘
         │                                     │
         └──────────────┬──────────────────────┘
                         │
                ┌────────▼────────┐
                │  Validate every │
                │  candidate      │
                └────────┬────────┘
                         │
             ┌───────────┴───────────┐
             │                       │
    ┌────────▼────────┐     ┌────────▼────────┐
    │  Confirmed /     │     │  Unclear         │
    │  not found       │     │  → Background    │
    └────────┬─────────┘     │  verification    │
             │                └────────┬─────────┘
             │                         │
             └────────────┬────────────┘
                           │
                  ┌────────▼────────┐
                  │  Build the      │
                  │  final list     │
                  └─────────────────┘
```

## Documentation

- [`docs/01-overview.md`](docs/01-overview.md) — the problem in more depth, and the inputs/outputs of
  the workflow.
- [`docs/02-endpoints.md`](docs/02-endpoints.md) — which Linkup endpoint to use at each step, and why.
- [`docs/03-choosing-a-workflow.md`](docs/03-choosing-a-workflow.md) — **start here to pick Qualify a
  List or Build a List.**
- [`docs/04-implementation.md`](docs/04-implementation.md) — a step-by-step build guide with request
  and response shapes.
- [`docs/05-pitfalls.md`](docs/05-pitfalls.md) — failure modes worth designing around from the start.
- [`docs/06-worked-example.md`](docs/06-worked-example.md) — an end-to-end illustration with realistic
  sample data, for both workflows.

## Data contracts

[`schemas/`](schemas/) has the JSON Schema for every input and output this workflow uses, independent of
any programming language:

- [`config.schema.json`](schemas/config.schema.json) — the config both workflows read.
- [`company_list_input.schema.json`](schemas/company_list_input.schema.json) — the input list for
  Qualify a List.
- [`qualified_company_output.schema.json`](schemas/qualified_company_output.schema.json) — the final
  output, from either workflow.
- [`excluded_company_log.schema.json`](schemas/excluded_company_log.schema.json) — the audit log of
  dropped candidates and why.

## Reference implementation

[`src/`](src/) contains a working implementation in Python, one file per step. The two top-level scripts
chain those steps together into the two workflows described above.

```bash
cd src
pip install -r requirements.txt
export LINKUP_API_KEY=your-api-key-here
cp config.example.json config.json   # then edit config.json for your client, ICP, and criterion

# Qualify a List - you already have companies to check
cp companies.example.json companies.json   # then edit with your real candidates
python qualify_existing_list.py --config config.json --companies companies.json --out qualified_list.json

# Build a List - no list yet, let Linkup find candidates
python build_and_qualify_list.py --config config.json --out final_list.json
```

Each step also runs standalone, which is useful for testing or re-running a single part:

```bash
python phase1_derive_icp.py "Client Name" "https://client-website.com"
python phase3_validate.py config.json candidates.json
python phase4_background_verify.py config.json unclear.json
```

The Python implementation is a reference, not a requirement — the request/response shapes in
`docs/04-implementation.md` and the schemas in `schemas/` are what matter if reimplementing this in a
different language or framework.
