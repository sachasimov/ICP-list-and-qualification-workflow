"""Build a List: discover candidates with Linkup, then qualify them.

Use this when the client does not already have a candidate list and wants
Linkup to both discover companies and validate them against a qualitative
criterion.

Phases run: 1 (optional) -> 2 -> 3 -> 4 (as needed) -> 5.
See docs/04-implementation.md for the full phase-by-phase reference, and
docs/03-choosing-a-workflow.md for how this differs from Qualify a List
(qualify_existing_list.py).

Usage:
    export LINKUP_API_KEY=your-api-key-here
    python build_and_qualify_list.py --config config.json --out final_list.json
    python build_and_qualify_list.py --config config.json --derive-criterion --out final_list.json
"""

from __future__ import annotations

import argparse
import json
import sys

import linkup_client
import phase1_derive_icp
import phase2_discover
import phase3_validate
import phase4_background_verify
import phase5_finalize


def run(config: dict, derive_criterion: bool = False) -> dict:
    natural_language_icp = config.get("natural_language_icp", "")
    qualitative_criterion = config["qualitative_criterion"]

    if derive_criterion:
        print("Phase 1: deriving the qualitative criterion from the client's own evidence...",
              file=sys.stderr)
        icp_result = phase1_derive_icp.derive_icp_patterns(config["client_name"], config["client_website"])
        print(json.dumps(icp_result.get("output", icp_result), indent=2), file=sys.stderr)
        print("Review the recurring patterns above. Update qualitative_criterion in the config "
              "with a concrete, checkable statement before trusting the rest of this run.",
              file=sys.stderr)

    print("Phase 2: discovering a wide candidate pool...", file=sys.stderr)
    broad_job_id = phase2_discover.discover_broad(config["client_name"], natural_language_icp,
                                                   qualitative_criterion)
    print(f"  submitted broad discovery job {broad_job_id}, polling (5-10 min typical)...",
          file=sys.stderr)
    broad_result = linkup_client.poll_research(broad_job_id)
    broad_companies = [c["company_name"] for c in broad_result.get("output", {}).get("companies", [])]

    targeted_result = phase2_discover.discover_targeted(
        config.get("industry", ""), config.get("geography", ""), qualitative_criterion,
        natural_language_icp, config.get("reference_competitor", ""),
    )
    # In production, parse company names out of targeted_result["results"] (titles/snippets)
    # and merge them into candidate_pool below. Left as raw output here since the extraction
    # logic depends on how the caller wants to interpret search snippets.
    targeted_raw = targeted_result.get("results", [])

    candidate_pool = phase2_discover.dedupe_by_name(broad_companies)
    print(f"  candidate pool: {len(candidate_pool)} companies (plus {len(targeted_raw)} raw "
          f"targeted-search results available for manual review)", file=sys.stderr)

    return _validate_and_finalize(candidate_pool, config)


def _validate_and_finalize(candidate_pool: list[str], config: dict) -> dict:
    qualitative_criterion = config["qualitative_criterion"]

    print(f"Phase 3: validating all {len(candidate_pool)} candidates...", file=sys.stderr)
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
    parser.add_argument("--derive-criterion", action="store_true",
                         help="Run phase 1 to derive the qualitative criterion before discovery.")
    parser.add_argument("--out", default="final_list.json", help="Path to write the final qualified list")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    final = run(config, derive_criterion=args.derive_criterion)

    with open(args.out, "w") as f:
        json.dump(final, f, indent=2)
    print(f"Final list written to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
