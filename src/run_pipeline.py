"""Run the full qualitative ICP qualification pipeline end to end.

Usage:
    export LINKUP_API_KEY=your-api-key-here
    python run_pipeline.py --config config.json [--derive-icp] [--out final_list.json]
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


def run(config: dict, derive_icp: bool = False) -> dict:
    natural_language_icp = config["natural_language_icp"]
    qualitative_criterion = config["qualitative_criterion"]

    if derive_icp:
        print("Phase 1: deriving the ICP from the client's own evidence...", file=sys.stderr)
        icp_result = phase1_derive_icp.derive_icp_patterns(config["client_name"], config["client_website"])
        print(json.dumps(icp_result.get("output", icp_result), indent=2), file=sys.stderr)
        print("Review the recurring patterns above and confirm qualitative_criterion in the config "
              "before continuing.", file=sys.stderr)

    print("Phase 2: discovering a wide candidate pool...", file=sys.stderr)
    broad_job_id = phase2_discover.discover_broad(config["client_name"], natural_language_icp,
                                                   qualitative_criterion)
    print(f"  submitted broad discovery job {broad_job_id}, polling...", file=sys.stderr)
    broad_result = linkup_client.poll_research(broad_job_id)
    broad_companies = [c["company_name"] for c in broad_result.get("output", {}).get("companies", [])]

    targeted_result = phase2_discover.discover_targeted(
        config["industry"], config["geography"], qualitative_criterion,
        natural_language_icp, config["reference_competitor"],
    )
    # In a production pipeline, parse company names out of targeted_result["results"]
    # (titles/snippets) and add them to the pool. Left as raw output here since the
    # extraction logic depends on how the caller wants to interpret search snippets.
    targeted_raw = targeted_result.get("results", [])

    candidate_pool = phase2_discover.dedupe_by_name(broad_companies)
    print(f"  candidate pool: {len(candidate_pool)} companies (plus {len(targeted_raw)} raw "
          f"targeted-search results to review manually)", file=sys.stderr)

    print("Phase 3: validating every candidate...", file=sys.stderr)
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
    final = phase5_finalize.build_final_list(
        config["firmographic_band"], config["tier_definition"],
        validation_results, background_results,
    )
    return final


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--derive-icp", action="store_true",
                         help="Run phase 1 to derive the qualitative criterion before discovery.")
    parser.add_argument("--out", default="final_list.json")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    final = run(config, derive_icp=args.derive_icp)

    with open(args.out, "w") as f:
        json.dump(final, f, indent=2)
    print(f"Final list written to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
