# Entry Points

There are two ways to use this workflow. Pick one based on whether a candidate list already exists.

## Decision

```
Does the client already have a candidate company list
(from their own database, a CRM export, or a firmographic filter)?

├── YES → Entry Point A: qualify_existing_list.py
│         Skips discovery entirely. The input list IS the candidate pool.
│         Phases used: 1 (optional) → 3 → 4 → 5
│
└── NO  → Entry Point B: build_and_qualify_list.py
          Linkup finds the candidates AND validates them.
          Phases used: 1 (optional) → 2 → 3 → 4 → 5
```

If unsure, default to Entry Point A when a list exists, even a rough one — validating a real list is
cheaper and faster than discovering one from scratch. Use Entry Point B only when no list exists yet.

## Entry Point A — `qualify_existing_list.py`

**Input:** a JSON array of company names (or `{"company_name", "website"}` objects) — see
[`../schemas/company_list_input.schema.json`](../schemas/company_list_input.schema.json) — plus a
config file (below).

**What it does:** validates every company in the input list against the qualitative criterion
(phase 3), sends anything ambiguous to background verification (phase 4), and returns the companies
that survived (phase 5). It never calls the discovery endpoints.

**When to use it:**
- The client's own database or CRM already has a firmographically-filtered list.
- A previous run of Entry Point B already produced a candidate pool, and it just needs re-validating
  (for example, on a schedule, to catch new evidence).
- The client wants to check a *new* qualitative criterion against a list they already trust
  firmographically.

**Command:**

```bash
python qualify_existing_list.py --config config.json --companies companies.json --out qualified_list.json
```

## Entry Point B — `build_and_qualify_list.py`

**Input:** just a config file (below). No candidate list required.

**What it does:** runs the full pipeline — discovers a wide candidate pool (phase 2, combining a broad
research call with a targeted search call), validates every candidate found (phase 3), sends ambiguous
cases to background verification (phase 4), and returns the companies that survived (phase 5).

**When to use it:**
- The client has no existing list for this ICP and wants one built from scratch.
- The client wants to see what public evidence surfaces beyond what their own database already knows
  about.

**Command:**

```bash
python build_and_qualify_list.py --config config.json --out final_list.json
```

## Shared configuration

Both entry points read the same config format —
[`../schemas/config.schema.json`](../schemas/config.schema.json) — and both accept an optional
`--derive-criterion` flag that runs phase 1 first, to derive the qualitative criterion from the
client's own case studies when it cannot be stated cleanly up front. See
[`04-implementation.md`](04-implementation.md) for what phase 1 actually does.

`industry`, `geography`, and `reference_competitor` in the config are only used by Entry Point B's
discovery phase; Entry Point A ignores them since it has no discovery step.

## Output

Both entry points produce the same output shape —
[`../schemas/qualified_company_output.schema.json`](../schemas/qualified_company_output.schema.json)
— so downstream systems (a CRM import, a spreadsheet, an outbound workflow) do not need to know which
entry point produced the list.
