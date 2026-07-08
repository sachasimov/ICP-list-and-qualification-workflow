"""Phase 3 - Validate every candidate from phase 2 against its own public evidence.

This phase must cover the entire candidate pool, not a sample of it - it is the
step that separates real matches from lookalikes.
"""

from __future__ import annotations

import linkup_client

VALIDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "website": {"type": "string"},
                    "employee_count": {"type": "string"},
                    "criterion_status": {"type": "string", "enum": ["confirmed", "not_found", "unclear"]},
                    "evidence_snippet": {"type": "string"},
                    "source_url": {"type": "string"},
                },
                "required": ["company_name", "criterion_status"],
            },
        }
    },
    "required": ["results"],
}


def batch(items: list, size: int) -> list[list]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def validate_batch(company_names: list[str], qualitative_criterion: str) -> list[dict]:
    """Validate one batch (roughly 10-15 companies) in a single deep search call."""
    company_list = ", ".join(company_names)
    q = (
        f"For each of these companies: {company_list}. First find their official website, "
        f"about/careers page, and any employee count. Then check whether the company "
        f"{qualitative_criterion}. Extract the exact supporting text and source URL. If a company "
        f"name is ambiguous or you cannot find a matching real company, mark it not_found instead "
        f"of guessing."
    )
    response = linkup_client.search(q, depth="deep", output_type="structured",
                                     structured_output_schema=VALIDATION_SCHEMA)
    return response.get("results", [])


def validate_all(company_names: list[str], qualitative_criterion: str, batch_size: int = 12) -> list[dict]:
    """Validate the full candidate pool, batched for efficiency."""
    all_results: list[dict] = []
    for group in batch(company_names, batch_size):
        all_results.extend(validate_batch(group, qualitative_criterion))
    return all_results


if __name__ == "__main__":
    import json
    import sys

    with open(sys.argv[1] if len(sys.argv) > 1 else "config.json") as f:
        config = json.load(f)
    with open(sys.argv[2] if len(sys.argv) > 2 else "candidates.json") as f:
        candidates = json.load(f)

    results = validate_all(candidates, config["qualitative_criterion"],
                            config.get("validation_batch_size", 12))
    print(json.dumps(results, indent=2))
