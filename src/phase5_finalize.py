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
            "description": "Only confirmed companies, plus unclear ones still pending background verification. Matches schemas/qualified_company_output.schema.json.",
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
        },
        "excluded": {
            "type": "array",
            "description": "Every dropped candidate and why. Matches schemas/excluded_company_log.schema.json. Not shown to end users as recommendations.",
            "items": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "reason": {"type": "string", "enum": ["not_found", "entity_mismatch", "firmographic_mismatch"]},
                    "detail": {"type": "string"},
                },
                "required": ["company_name", "reason"],
            },
        },
    },
    "required": ["companies", "excluded"],
}


def build_final_list(firmographic_band: str, tier_definition: str,
                      criterion_check_results: list[dict],
                      background_verification_results: dict[str, dict]) -> dict:
    q = (
        f"Using this target firmographic band: {firmographic_band}, these on-site criterion checks: "
        f"{json.dumps(criterion_check_results)}, and this completed background verification: "
        f"{json.dumps(background_verification_results)}, assign each surviving company a tier using "
        f"this definition: {tier_definition}. Build two separate lists. First, 'companies': every "
        f"company whose criterion_status is confirmed, or unclear pending background verification, "
        f"and that fits the firmographic band - for each, return company name, website, firmographic "
        f"fit, criterion status, evidence, source URLs, tier, and whether background verification is "
        f"still pending. Second, 'excluded': every company left out, with a reason of not_found "
        f"(no real company matched the name), entity_mismatch (the evidence describes a different "
        f"company with the same or a similar name - check for industry, country, or business type "
        f"inconsistent with the original discovery context), or firmographic_mismatch (the criterion "
        f"was confirmed but the company is far outside the firmographic band, or is a subsidiary of a "
        f"much larger multinational rather than an independent buyer)."
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
