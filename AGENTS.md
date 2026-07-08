# AGENTS.md

This repository specifies a workflow for qualifying companies against an Ideal Customer Profile (ICP)
using the [Linkup](https://www.linkup.so) web data API, for the part of the ICP that a firmographic
database cannot answer — a pricing model, an operational behavior, an organizational structure, or any
other qualitative trait. Read this file first, then follow the order below. Do not start writing
integration code before step 3.

## Before writing any code

1. Read [`docs/01-overview.md`](docs/01-overview.md) — the problem this solves and its inputs/outputs.
2. Read [`docs/02-endpoints.md`](docs/02-endpoints.md) — the Linkup endpoints involved and why each is
   used where it is.
3. Read [`docs/03-entry-points.md`](docs/03-entry-points.md) and pick one:
   - **Entry Point A** (`src/qualify_existing_list.py`) if the client already has a candidate company
     list.
   - **Entry Point B** (`src/build_and_qualify_list.py`) if the list needs to be discovered from
     scratch.
4. Read [`docs/04-implementation.md`](docs/04-implementation.md) in full for every phase your chosen
   entry point uses — it has the exact request and response JSON for every Linkup call, not just a
   description of what it does.
5. Read [`docs/05-pitfalls.md`](docs/05-pitfalls.md) before writing the validation and finalization
   logic. These are not optional flavor text — skipping them produces a list with real, silent errors:
   wrong companies from name collisions, oversized companies from a missed firmographic cross-check,
   and "confirmed" verdicts that a deeper check would have overturned.

## What to actually build

- Follow the schemas in [`schemas/`](schemas/) for every input and output. They are the contract,
  independent of language — validate against them, don't just eyeball the shape.
- [`src/`](src/) is a working Python reference implementation, one file per phase
  (`phase1_derive_icp.py` … `phase5_finalize.py`), plus the two entry-point scripts that chain them.
  If implementing in another language or framework, port the phase functions one to one — same request
  shapes, same schemas, same phase order — rather than redesigning the flow from the doc prose alone.
- Do not skip phase 4 (background verification) for anything phase 3 marks `unclear`. Do not skip it
  either for something phase 3 marks `confirmed` if the entity identity looks ambiguous — see
  `docs/05-pitfalls.md` for why a single validation pass is not always reliable for small or
  lesser-known companies.
- Do not present `not_found` companies, or companies confirmed on the criterion but excluded for a
  firmographic mismatch, as recommendations. They belong in an audit log matching
  `schemas/excluded_company_log.schema.json`, not in the final list.
- Discovery (phase 2) is intentionally over-inclusive. Do not add a pre-filtering step before
  validation to "clean up" the candidate pool — validation is that cleanup step, and doing it twice
  (once by hand, once by phase 3) risks dropping real matches for looking unlikely.

## Common tasks

| Task | Where to look |
|---|---|
| Wire this into an existing app or CRM | `docs/03-entry-points.md` for which entry point to call; `schemas/qualified_company_output.schema.json` for the response shape to expect back |
| Change which Linkup endpoint or depth a phase uses | `docs/02-endpoints.md` for the reasoning, then the matching phase section in `docs/04-implementation.md` for the exact request |
| Configure this for a new client or a new qualitative criterion | No code changes — edit `config.json`'s `qualitative_criterion` and `natural_language_icp` per `schemas/config.schema.json` |
| Debug an obviously wrong company in the output | `docs/05-pitfalls.md` — most likely an entity-name collision or a missed firmographic cross-check, both covered there with concrete examples |
| Re-implement in TypeScript or another stack | Port `src/phase1_derive_icp.py` through `src/phase5_finalize.py` one to one, keeping the request shapes from `docs/04-implementation.md` and the schemas in `schemas/` unchanged |
| Decide how often to re-run this | Entry Point A is cheap enough to re-run on a schedule against the same list to catch new evidence; Entry Point B's discovery phase is the expensive part and is better run on demand |

## Operational constraints

- Every Linkup call needs `LINKUP_API_KEY` set as an environment variable. There is no other
  authentication path.
- Phase 2's broad discovery call and every phase 4 background-verification call use `/v1/research`,
  which is asynchronous (submit, then poll — typically minutes, not seconds). Never await these
  synchronously inside a user-facing request/response cycle; run them as background jobs and notify or
  poll from the client side.
- Phase 4 submits one job per unclear company. Submit them all before polling any of them — polling a
  batch in parallel is what keeps this phase's wall-clock time close to its slowest single job instead
  of the sum of all of them.
- Phase 3 must validate the entire candidate pool, not a sample of it. Batch it (10-15 companies per
  call, per `docs/05-pitfalls.md`) instead of skipping candidates to save calls.
