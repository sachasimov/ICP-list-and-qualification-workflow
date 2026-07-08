"""Phase 1 - Derive the qualitative ICP criterion from the client's own evidence.

Skip this phase if the client can already state the qualitative criterion as a
concrete, checkable sentence.
"""

from __future__ import annotations

import linkup_client

SCHEMA = {
    "type": "object",
    "properties": {
        "customer_examples": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "company_size": {"type": "string"},
                    "problem_solved": {"type": "string"},
                    "source_url": {"type": "string"},
                },
                "required": ["company_name", "problem_solved", "source_url"],
            },
        },
        "recurring_patterns": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["customer_examples", "recurring_patterns"],
}


def derive_icp_patterns(client_name: str, client_website: str) -> dict:
    q = (
        f"Scrape {client_website} customer stories, case studies, and testimonials pages. "
        f"Also run a separate web search for independent reviews and press coverage of "
        f"{client_name}'s customers. Extract, for each customer mentioned, company size, "
        f"industry, geography, and the specific operational problem {client_name} solved for "
        f"them. Return the recurring patterns across customers and source URLs for each."
    )
    return linkup_client.search(q, depth="standard", output_type="structured",
                                 structured_output_schema=SCHEMA)


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 3:
        print("Usage: python phase1_derive_icp.py <client_name> <client_website>")
        sys.exit(1)
    result = derive_icp_patterns(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2))
