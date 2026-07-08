"""Phase 4 - Background verification for candidates phase 3 marked "unclear".

Jobs are submitted in parallel and polled as a batch, since each job runs
independently once submitted.
"""

from __future__ import annotations

import linkup_client

VERIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "verdict": {"type": "string", "enum": ["confirmed", "not_found", "unclear"]},
        "employee_count": {"type": "string"},
        "evidence": {"type": "string"},
        "source_urls": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["company_name", "verdict"],
}


def submit_verification(company_name: str, qualitative_criterion: str) -> str:
    q = (
        f"Investigate whether {company_name} {qualitative_criterion}. Check their careers page, "
        f"product pages, press coverage, and funding announcements. Also determine their "
        f"approximate employee count. Cross-check any conflicting claims between sources. Return "
        f"a clear confirmed / not_found / unclear verdict, employee count, the strongest "
        f"supporting evidence, and source URLs."
    )
    return linkup_client.submit_research(
        q, mode="investigate", reasoning_depth="S", output_type="structured",
        structured_output_schema=VERIFICATION_SCHEMA,
    )


def verify_unclear_companies(company_names: list[str], qualitative_criterion: str) -> dict[str, dict]:
    """Submit one background job per unclear company, then poll all of them together."""
    job_ids = {name: submit_verification(name, qualitative_criterion) for name in company_names}
    completed = linkup_client.poll_research_batch(job_ids)
    return {name: body.get("output", {}) for name, body in completed.items()}


if __name__ == "__main__":
    import json
    import sys

    with open(sys.argv[1] if len(sys.argv) > 1 else "config.json") as f:
        config = json.load(f)
    with open(sys.argv[2] if len(sys.argv) > 2 else "unclear.json") as f:
        unclear_companies = json.load(f)

    results = verify_unclear_companies(unclear_companies, config["qualitative_criterion"])
    print(json.dumps(results, indent=2))
