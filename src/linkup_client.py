"""Thin client for the Linkup Search and Research endpoints.

Only the pieces needed by this workflow are implemented: synchronous search,
and the submit/poll lifecycle for asynchronous research jobs.
"""

from __future__ import annotations

import os
import time
import requests

BASE_URL = "https://api.linkup.so/v1"


def _api_key() -> str:
    key = os.environ.get("LINKUP_API_KEY")
    if not key:
        raise RuntimeError("Set the LINKUP_API_KEY environment variable before running the pipeline.")
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }


def search(q: str, depth: str = "standard", output_type: str = "searchResults",
           structured_output_schema: dict | None = None, timeout: int = 180) -> dict:
    """Call POST /v1/search and return the parsed JSON response."""
    payload = {"q": q, "depth": depth, "outputType": output_type}
    if structured_output_schema is not None:
        payload["structuredOutputSchema"] = structured_output_schema
    response = requests.post(f"{BASE_URL}/search", json=payload, headers=_headers(), timeout=timeout)
    response.raise_for_status()
    return response.json()


def submit_research(q: str, mode: str = "research", reasoning_depth: str = "L",
                     output_type: str = "structured",
                     structured_output_schema: dict | None = None) -> str:
    """Call POST /v1/research and return the job id."""
    payload = {
        "q": q,
        "mode": mode,
        "reasoningDepth": reasoning_depth,
        "outputType": output_type,
    }
    if structured_output_schema is not None:
        payload["structuredOutputSchema"] = structured_output_schema
    response = requests.post(f"{BASE_URL}/research", json=payload, headers=_headers(), timeout=30)
    response.raise_for_status()
    return response.json()["id"]


def poll_research(job_id: str, initial_interval: float = 2.0, max_interval: float = 10.0,
                   timeout_s: float = 1200.0) -> dict:
    """Poll GET /v1/research/:id with exponential backoff until completed or failed."""
    interval = initial_interval
    elapsed = 0.0
    while elapsed < timeout_s:
        response = requests.get(f"{BASE_URL}/research/{job_id}", headers=_headers(), timeout=30)
        response.raise_for_status()
        body = response.json()
        if body["status"] in ("completed", "failed"):
            return body
        time.sleep(interval)
        elapsed += interval
        interval = min(interval * 2, max_interval)
    raise TimeoutError(f"Research job {job_id} did not complete within {timeout_s}s")


def poll_research_batch(job_ids: dict[str, str], initial_interval: float = 5.0,
                         max_interval: float = 15.0, timeout_s: float = 1200.0) -> dict[str, dict]:
    """Poll a batch of research jobs together, returning each job's output as it completes.

    job_ids maps an arbitrary label (e.g. a company name) to a research job id.
    Submitting jobs in parallel and polling them as a batch is far more efficient
    than waiting for each job sequentially, since jobs run independently once submitted.
    """
    pending = dict(job_ids)
    results: dict[str, dict] = {}
    interval = initial_interval
    elapsed = 0.0
    while pending and elapsed < timeout_s:
        for label, job_id in list(pending.items()):
            response = requests.get(f"{BASE_URL}/research/{job_id}", headers=_headers(), timeout=30)
            response.raise_for_status()
            body = response.json()
            if body["status"] in ("completed", "failed"):
                results[label] = body
                del pending[label]
        if pending:
            time.sleep(interval)
            elapsed += interval
            interval = min(interval * 2, max_interval)
    if pending:
        raise TimeoutError(f"Research jobs did not complete within {timeout_s}s: {list(pending)}")
    return results
