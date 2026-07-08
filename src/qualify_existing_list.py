"""Entry Point A: qualify a list of companies the client already has.

Use this when the client already has a firmographically-qualified candidate
list (from their own database, a CRM export, or any other source) and wants
each company checked against a qualitative criterion their schema cannot
answer on its own.

Phases run: 1 (optional) -> 3 -> 4 (as needed) -> 5. Discovery (phase 2) is
skipped entirely - the input list is the candidate pool.
See docs/04-implementation.md for the full phase-by-phase reference, and
docs/03-entry-points.md for how this differs from Entry Point B
(build_and_qualify_list.py).

Usage:
    export LINKUP_API_KEY=your-api-key-here
    python qualify_existing_list.py --config config.json --companies companies.json --out qualified_list.json
"""

from __future__ import annotations

import argparse
import json
import sys

import phase1_derive_icp
import phase3_validate
import phase4_background_verify
import phase5_finalize


def normalize_company_list(raw: list) -> list[str]:
    """Accept either bare strings or {"company_name": ..., "website": ...} objects.

    See schemas/company_list_input.schema.json for the accepted input shape.
    """
    names = []
    for item in raw:
        if isinstance(item, str):
            names.append(item.strip())
        elif isinstance(item, dict) and "company_name" in item:
            names.append(item["company_name"].strip())
        else:
            raise ValueError(f"Unrecognized company list entry: {item!r}")
    return [n for n in names if n]


def run(config: dict, companies: list, derive_criterion: bool = False) -> dict:
    qualitative_criterion = config["qualitative_criterion"]

    if derive_criterion:
        print("Phase 1: deriving the qualitative criterion from the client's own evidence...",
              file=sys.stderr)
        icp_result = phase1_derive_icp.derive_icp_patterns(config["client_name"], config["client_website"])
        print(json.dumps(icp_result.get("output", icp_result), indent=2), file=sys.stderr)
        print("Review the recurring patterns above. Update qualitative_criterion in the config "
              "with a concrete, checkable statement before trusting the rest of this run.",
              file=sys.stderr)

    candidate_pool = normalize_company_list(companies)
    print(f"Phase 3: validating all {len(candidate_pool)} companies from the provided list...",
          file=sys.stderr)
    validation_results = phase3_validate.validate_all(
        candidate_pool, qualitative_criterion, config.get("validation_batch_size", 12),
    )
    confirmed = [r for r in validation_results if r.get("criterion_status") == "confirmed"]
    unclear = [r for r in validation_results if r.get("criterion_status") == "unclear"]
    not_found = [r for r in validation_results if r.get("criterion_status") == "not_found"]
    print(f"  confirmed: {len(confirmed)}, unclear: {len(unclear)}, not_found: {len(not_found)}",
          file=sys.stderr)

    background_results = {}
    if unclear:
        print(f"Phase 4: background verification for {len(unclear)} unclear companies...",
              file=sys.stderr)
        unclear_names = [r["company_name"] for r in unclear]
        background_results = phase4_background_verify.verify_unclear_companies(
            unclear_names, qualitative_criterion,
        )

    print("Phase 5: building the final list...", file=sys.stderr)
    return phase5_finalize.build_final_list(
        config["firmographic_band"], config["tier_definition"],
        validation_results, background_results,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.json", help="Path to a config.json matching schemas/config.schema.json")
    parser.add_argument("--companies", default="companies.json",
                         help="Path to a company list matching schemas/company_list_input.schema.json")
    parser.add_argument("--derive-criterion", action="store_true",
                         help="Run phase 1 to derive the qualitative criterion before validating.")
    parser.add_argument("--out", default="qualified_list.json", help="Path to write the final qualified list")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)
    with open(args.companies) as f:
        companies = json.load(f)

    final = run(config, companies, derive_criterion=args.derive_criterion)

    with open(args.out, "w") as f:
        json.dump(final, f, indent=2)
    print(f"Qualified list written to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
