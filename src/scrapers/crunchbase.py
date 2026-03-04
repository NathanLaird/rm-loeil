"""
Crunchbase data fetcher

Note: Crunchbase API requires a paid subscription.
This module provides a stub implementation that can be extended
when API access is available.
"""

import os
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

CRUNCHBASE_API_URL = "https://api.crunchbase.com/api/v4"


async def scrape_crunchbase(company: str, domain: str) -> dict:
    """
    Fetch company data from Crunchbase.
    
    Note: Requires CRUNCHBASE_API_KEY environment variable.
    Without it, returns a stub response indicating the data source is unavailable.
    
    Args:
        company: Company name
        domain: Company domain
        
    Returns:
        Dictionary with Crunchbase data or stub
    """
    api_key = os.environ.get("CRUNCHBASE_API_KEY")
    
    if not api_key:
        logger.info("CRUNCHBASE_API_KEY not set, returning stub data")
        return {
            "available": False,
            "error": "Crunchbase API key not configured",
            "company": company,
            "domain": domain,
            # Return None for all fields so extraction knows this data is missing
            "total_raised": None,
            "last_round": None,
            "investors": [],
            "founded_date": None,
            "employee_range": None,
        }
    
    try:
        async with httpx.AsyncClient() as client:
            # Search for the company
            search_response = await client.get(
                f"{CRUNCHBASE_API_URL}/autocompletes",
                params={
                    "query": company,
                    "collection_ids": "organizations",
                    "limit": 5,
                },
                headers={"X-cb-user-key": api_key},
                timeout=15.0
            )
            
            if search_response.status_code != 200:
                logger.warning(f"Crunchbase search failed: {search_response.status_code}")
                return {
                    "available": False,
                    "error": f"API error: {search_response.status_code}",
                }
            
            search_data = search_response.json()
            entities = search_data.get("entities", [])
            
            if not entities:
                return {
                    "available": False,
                    "error": f"Company '{company}' not found on Crunchbase",
                }
            
            # Find best match (by domain if possible)
            org_id = None
            for entity in entities:
                props = entity.get("properties", {})
                if props.get("website_url", "").find(domain) >= 0:
                    org_id = entity.get("identifier", {}).get("uuid")
                    break
            
            if not org_id:
                org_id = entities[0].get("identifier", {}).get("uuid")
            
            # Fetch organization details
            org_response = await client.get(
                f"{CRUNCHBASE_API_URL}/entities/organizations/{org_id}",
                params={
                    "field_ids": "short_description,founded_on,num_employees_enum,funding_total,last_funding_type,last_funding_at,investor_identifiers",
                },
                headers={"X-cb-user-key": api_key},
                timeout=15.0
            )
            
            if org_response.status_code != 200:
                return {
                    "available": False,
                    "error": f"Failed to fetch org details: {org_response.status_code}",
                }
            
            org_data = org_response.json()
            props = org_data.get("properties", {})
            
            return {
                "available": True,
                "error": None,
                "company": company,
                "domain": domain,
                "short_description": props.get("short_description"),
                "founded_date": props.get("founded_on"),
                "employee_range": props.get("num_employees_enum"),
                "total_raised": props.get("funding_total", {}).get("value_usd"),
                "last_round_type": props.get("last_funding_type"),
                "last_round_date": props.get("last_funding_at"),
                "investors": [
                    inv.get("value") for inv in props.get("investor_identifiers", [])
                ],
            }
            
    except httpx.RequestError as e:
        logger.error(f"Crunchbase request error: {e}")
        return {
            "available": False,
            "error": str(e),
        }


def scrape_crunchbase_sync(company: str, domain: str) -> dict:
    """Synchronous wrapper for scrape_crunchbase."""
    import asyncio
    return asyncio.run(scrape_crunchbase(company, domain))


# For testing
if __name__ == "__main__":
    import asyncio
    import json
    
    async def test():
        result = await scrape_crunchbase("Cursor", "cursor.sh")
        print(json.dumps(result, indent=2, default=str))
        
    asyncio.run(test())
