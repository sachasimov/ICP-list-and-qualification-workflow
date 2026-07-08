"""Phase 5 - Merge validation and background-verification results into the final list.

Firmographic fit is cross-checked here as a separate condition from criterion
confirmation - a company can pass the qualitative check and still be excluded
for being far outside the target size band.
"""

from __future__ import annotations

import json

import linkup_client

FINAL_LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "companies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "website": {"type": "string"},
                    "firmographic_fit": {"type": "string"},
                    "criterion_status": {"type": "string"},
                    "evidence": {"type": "string"},
                    "source_urls": {"type": "array", "items": {"type": "string"}},
                    "tier": {"type": "string"},
                    "background_verification_pending": {"type": "boolean"},
                },
                "required": ["company_name", "website", "criterion_status", "tier", "source_urls"],
            },
        }
    },
    "required": ["companies"],
}


def build_final_list(firmographic_band: str, tier_definition: str,
                      criterion_check_results: list[dict],
                      background_verification_results: dict[str, dict]) -> dict:
    q = (
        f"Using this target firmographic band: {firmographic_band}, these on-site criterion checks: "
        f"{json.dumps(criterion_check_results)}, and this completed background verification: "
        f"{json.dumps(background_verification_results)}, assign each company a tier using this "
        f"definition: {tier_definition}. Exclude any company whose criterion_status is not_found. "
        f"Also exclude any company confirmed for the criterion but clearly outside the firmographic "
        f"band (for example, far larger than the stated employee range, or a national subsidiary of "
        f"a much larger multinational rather than an independent buyer) - note the exclusion reason "
        f"instead of including it. Watch for name collisions: if a company's evidence describes a "
        f"different industry, country, or business than expected for that name, treat it as a "
        f"mismatch and exclude it rather than including it as confirmed. Return company name, "
        f"website, firmographic fit, criterion status, evidence, source URLs, tier, and whether "
        f"background verification is still pending."
    )
    return linkup_client.search(q, depth="standard", output_type="structured",
                                 structured_output_schema=FINAL_LIST_SCHEMA)


if __name__ == "__main__":
    import sys

    with open(sys.argv[1] if len(sys.argv) > 1 else "config.json") as f:
        config = json.load(f)
    with open(sys.argv[2] if len(sys.argv) > 2 else "criterion_results.json") as f:
        criterion_results = json.load(f)
    with open(sys.argv[3] if len(sys.argv) > 3 else "background_results.json") as f:
        background_results = json.load(f)

    result = build_final_list(config["firmographic_band"], config["tier_definition"],
                               criterion_results, background_results)
    print(json.dumps(result, indent=2))
