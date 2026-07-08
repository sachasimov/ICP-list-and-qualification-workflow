"""Phase 2 - Discover a wide candidate pool.

Two complementary calls: a broad research-based sweep (the primary source of
volume) and a targeted search-based top-up. Pool both outputs before moving to
phase 3 - they are not alternatives to choose between.
"""

from __future__ import annotations

import linkup_client

BROAD_DISCOVERY_SCHEMA = {
    "type": "object",
    "properties": {
        "companies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "evidence": {"type": "string"},
                    "source_url": {"type": "string"},
                },
                # Keep this minimal. Requiring evidence/source_url on every entry
                # causes the model to silently drop companies it found but could
                # not cleanly cite, shrinking the result list.
                "required": ["company_name"],
            },
        }
    },
    "required": ["companies"],
}


def discover_broad(client_name: str, natural_language_icp: str, qualitative_criterion: str) -> str:
    """Submit the broad discovery research job and return its job id."""
    q = (
        f"Find as many potential ICP customers as possible for {client_name}. "
        f"ICP definition: {natural_language_icp} with this qualitative trait as a hard "
        f"requirement: {qualitative_criterion}. Look broadly across funding/expansion news, "
        f"company directories, job boards (especially finance/CFO/controller hiring posts that "
        f"describe {qualitative_criterion} as part of the role), and industry press. Do not stop "
        f"at a small sample - list as many distinct qualifying companies as you can find, even if "
        f"evidence for some is thinner than others. For each company, return company name and a "
        f"short evidence note with a source URL."
    )
    return linkup_client.submit_research(
        q, mode="research", reasoning_depth="L", output_type="structured",
        structured_output_schema=BROAD_DISCOVERY_SCHEMA,
    )


def discover_targeted(industry: str, geography: str, qualitative_criterion: str,
                       natural_language_icp: str, reference_competitor: str) -> dict:
    """Run the fast, narrow top-up search. Returns raw search results."""
    q = (
        f"Find companies in {industry} and {geography} that may match this qualitative trait: "
        f"{qualitative_criterion}. The broader target profile is {natural_language_icp}. Run "
        f"separate web searches for: forum and community threads recommending or comparing "
        f"{industry} tools with {qualitative_criterion}, \"alternatives to {reference_competitor}\" "
        f"or \"vs\" comparison pages that mention {qualitative_criterion}, directory or \"best of\" "
        f"list pages for {industry} tools with {qualitative_criterion}, finance/CFO/controller job "
        f"postings that describe {qualitative_criterion} as part of the role, and recent funding, "
        f"expansion, or hiring announcements in {industry} and {geography} that indicate "
        f"{qualitative_criterion}. Return company name, website, the exact quote or snippet showing "
        f"the trait, and source URL."
    )
    return linkup_client.search(q, depth="standard", output_type="searchResults")


def dedupe_by_name(company_names: list[str]) -> list[str]:
    """Deduplicate a list of company names, dropping non-addressable placeholder entries."""
    seen = set()
    result = []
    for name in company_names:
        key = name.strip().lower()
        if not key or "undisclosed" in key:
            continue
        if key in seen:
            continue
        seen.add(key)
        result.append(name.strip())
    return result


if __name__ == "__main__":
    import json
    import sys

    with open(sys.argv[1] if len(sys.argv) > 1 else "config.json") as f:
        config = json.load(f)

    job_id = discover_broad(config["client_name"], config["natural_language_icp"],
                             config["qualitative_criterion"])
    print(f"Submitted broad discovery job: {job_id}")
    result = linkup_client.poll_research(job_id)
    print(json.dumps(result.get("output"), indent=2))
