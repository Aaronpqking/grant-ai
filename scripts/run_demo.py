#!/usr/bin/env python3
"""
Quick demo runner for the Grant AI service.

- Tries the full MAS service first (vertex_grant_agent.py on localhost:8080 or Cloud Run URL if provided)
- Falls back to the simplified cloud agent (simple_cloud_agent.py)
- If neither service is reachable, runs a local offline demo that prints a mock proposal

Usage:
  python scripts/run_demo.py

Environment:
  DEMO_SERVICE_URL: Optional base URL of a running service (e.g., Cloud Run)
"""

import os
import sys
import json
import time
from datetime import datetime

import httpx


DEFAULT_PAYLOAD = {
    "organization_info": {"name": "Demo Nonprofit", "mission": "Improve community health"},
    "funder_info": {"name": "Demo Foundation", "type": "foundation"},
    "requirements": {
        "project_title": "Community Health Outreach",
        "amount_requested": "50000",
        "project_description": "Mobile clinics and health education programs"
    },
}


def pretty(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)


async def try_endpoint(base_url: str) -> str:
    url = f"{base_url.rstrip('/')}/generate_grant_proposal"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=DEFAULT_PAYLOAD)
        r.raise_for_status()
        data = r.json()
        return data.get("proposal") or data


async def main():
    base_url = os.getenv("DEMO_SERVICE_URL") or "http://localhost:8080"

    # Try main service
    try:
        print(f"Attempting main service at {base_url} ...")
        proposal = await try_endpoint(base_url)
        print("\n=== Demo Proposal (main service) ===\n")
        print(proposal if isinstance(proposal, str) else pretty(proposal))
        return 0
    except Exception as e:
        print(f"Main service not available: {e}")

    # Try fallback local service port if provided
    fallback_url = os.getenv("DEMO_FALLBACK_URL") or "http://localhost:8081"
    try:
        print(f"Attempting fallback service at {fallback_url} ...")
        proposal = await try_endpoint(fallback_url)
        print("\n=== Demo Proposal (fallback service) ===\n")
        print(proposal if isinstance(proposal, str) else pretty(proposal))
        return 0
    except Exception as e:
        print(f"Fallback service not available: {e}")

    # Offline demo
    print("\nNeither service reachable. Showing offline demo output:\n")
    offline = f"""
    Grant Proposal: {DEFAULT_PAYLOAD['requirements']['project_title']}

    Organization: {DEFAULT_PAYLOAD['organization_info']['name']}
    Mission: {DEFAULT_PAYLOAD['organization_info']['mission']}

    Summary: This demo outlines a community health outreach program including mobile clinics,
    educational workshops, and partnerships with local providers. The program will reach 2,000+
    residents with preventive care and health education over 12 months.

    Budget: ${DEFAULT_PAYLOAD['requirements']['amount_requested']}
    Expected Outcomes: Increased screenings, improved health literacy, and reduced ER visits.
    """
    print(offline)
    return 0


if __name__ == "__main__":
    try:
        import asyncio
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("Interrupted")
        raise SystemExit(130)


