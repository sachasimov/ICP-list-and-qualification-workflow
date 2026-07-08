# Choosing A Workflow

There are two ways to use this. Pick one based on whether a candidate list already exists.

## Decision

```
Does the client already have a candidate company list
(from their own database, a CRM export, or a firmographic filter)?

├── YES → Qualify a List: qualify_existing_list.py
│         Skips discovery entirely. The input list IS the candidate pool.
│
└── NO  → Build a List: build_and_qualify_list.py
          Linkup finds the candidates AND validates them.
```

If unsure, default to **Qualify a List** when a list exists, even a rough one — validating a real list
is cheaper and faster than discovering one from scratch. Use **Build a List** only when no list exists
yet.

## Qualify a List — `qualify_existing_list.py`

**Input:** a JSON array of company names (or `{"company_name", "website"}` objects) — see
[`../schemas/company_list_input.schema.json`](../schemas/company_list_input.schema.json) — plus a
config file (below).

**What it does:** validates every company in the input list against the qualitative criterion, sends
anything ambiguous to a background check, and returns the companies that survived. It never calls the
discovery endpoints.

**When to use it:**
- The client's own database or CRM already has a firmographically-filtered list.
- A previous run of Build a List already produced a candidate pool, and it just needs re-validating
  (for example, on a schedule, to catch new evidence).
- The client wants to check a *new* qualitative criterion against a list they already trust
  firmographically.

**Command:**

```bash
python qualify_existing_list.py --config config.json --companies companies.json --out qualified_list.json
```

## Build a List — `build_and_qualify_list.py`

**Input:** just a config file (below). No candidate list required.

**What it does:** runs the full pipeline — discovers a wide candidate pool (combining a broad research
call with a targeted search call), validates every candidate found, sends ambiguous cases to a
background check, and returns the companies that survived.

**When to use it:**
- The client has no existing list for this ICP and wants one built from scratch.
- The client wants to see what public evidence surfaces beyond what their own database already knows
  about.

**Command:**

```bash
python build_and_qualify_list.py --config config.json --out final_list.json
```

## Shared configuration

Both workflows read the same config format —
[`../schemas/config.schema.json`](../schemas/config.schema.json) — and both accept an optional
`--derive-criterion` flag that derives the qualitative criterion from the client's own case studies
first, when it cannot be stated cleanly up front. See [`04-implementation.md`](04-implementation.md)
for what that step actually does.

`industry`, `geography`, and `reference_competitor` in the config are only used by Build a List's
discovery step; Qualify a List ignores them since it has no discovery step.

## Output

Both workflows produce the same output shape —
[`../schemas/qualified_company_output.schema.json`](../schemas/qualified_company_output.schema.json)
— so downstream systems (a CRM import, a spreadsheet, an outbound workflow) do not need to know which
one produced the list.
