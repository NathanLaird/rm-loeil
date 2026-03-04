"""
GitHub scraper using the GitHub API

Fetches organization/user repositories, stats, and activity.
"""

import os
import logging
from typing import Optional
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)

# GitHub API base URL
GITHUB_API = "https://api.github.com"


def get_github_headers() -> dict:
    """Get headers for GitHub API requests, including auth if available."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    
    # Use token if available (higher rate limits)
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
        logger.debug("Using GitHub token for authentication")
    
    return headers


async def find_github_org(client: httpx.AsyncClient, company: str, domain: str) -> Optional[str]:
    """
    Try to find the GitHub organization/user for a company.
    
    Tries several strategies:
    1. Search for organization matching company name
    2. Look for common variations
    3. Check if domain name matches
    
    Args:
        client: httpx async client
        company: Company name
        domain: Company domain
        
    Returns:
        GitHub username/org name or None
    """
    # Clean up company name for search
    company_lower = company.lower().replace(" ", "").replace("-", "").replace(".", "")
    domain_name = domain.split(".")[0].lower()
    
    # Candidates to try (in order of likelihood)
    candidates = [
        domain_name,  # cursor for cursor.sh
        company_lower,  # cursor for "Cursor"
        f"{domain_name}ai",  # cursorai
        f"{domain_name}-ai",  # cursor-ai
        f"{domain_name}hq",  # cursorhq
        f"{company_lower}inc",  # cursorinc
    ]
    
    # Deduplicate while preserving order
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique_candidates.append(c)
    
    for candidate in unique_candidates:
        try:
            # Try as organization first
            response = await client.get(
                f"{GITHUB_API}/orgs/{candidate}",
                timeout=10.0
            )
            if response.status_code == 200:
                logger.info(f"Found GitHub org: {candidate}")
                return candidate
            
            # Try as user
            response = await client.get(
                f"{GITHUB_API}/users/{candidate}",
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                # Verify it's not just a random user
                if data.get("type") == "Organization" or data.get("public_repos", 0) > 0:
                    logger.info(f"Found GitHub user: {candidate}")
                    return candidate
                    
        except httpx.RequestError:
            continue
    
    logger.warning(f"Could not find GitHub org for {company}")
    return None


async def fetch_repos(client: httpx.AsyncClient, org: str) -> list[dict]:
    """
    Fetch all public repositories for an organization/user.
    
    Args:
        client: httpx async client
        org: GitHub organization or username
        
    Returns:
        List of repository data
    """
    repos = []
    page = 1
    
    while True:
        try:
            response = await client.get(
                f"{GITHUB_API}/users/{org}/repos",
                params={"per_page": 100, "page": page, "sort": "stars", "direction": "desc"},
                timeout=15.0
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch repos page {page}: {response.status_code}")
                break
            
            data = response.json()
            if not data:
                break
                
            repos.extend(data)
            page += 1
            
            # Safety limit
            if page > 10:
                break
                
        except httpx.RequestError as e:
            logger.warning(f"Error fetching repos: {e}")
            break
    
    return repos


def is_recently_active(updated_at: str, days: int = 90) -> bool:
    """Check if a repo was updated within the given number of days."""
    try:
        updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        cutoff = datetime.now(updated.tzinfo) - timedelta(days=days)
        return updated > cutoff
    except (ValueError, TypeError):
        return False


async def scrape_github(company: str, domain: str) -> dict:
    """
    Scrape GitHub data for a company.
    
    Args:
        company: Company name
        domain: Company domain
        
    Returns:
        Dictionary with GitHub data:
        {
            "org_name": "...",
            "repos": [...],
            "total_stars": N,
            "total_forks": N,
            "top_repos": [...],
            "languages": [...],
            "error": None or "..."
        }
    """
    logger.info(f"Scraping GitHub for {company} ({domain})")
    
    headers = get_github_headers()
    
    async with httpx.AsyncClient(headers=headers) as client:
        # Find the organization
        org = await find_github_org(client, company, domain)
        
        if not org:
            return {
                "org_name": None,
                "error": f"Could not find GitHub organization for {company}",
                "repos": [],
                "total_stars": 0,
                "total_forks": 0,
            }
        
        # Fetch org info
        try:
            org_response = await client.get(f"{GITHUB_API}/users/{org}", timeout=10.0)
            org_info = org_response.json() if org_response.status_code == 200 else {}
        except httpx.RequestError:
            org_info = {}
        
        # Fetch repositories
        repos = await fetch_repos(client, org)
        
        # Calculate aggregate stats
        total_stars = sum(r.get("stargazers_count", 0) for r in repos)
        total_forks = sum(r.get("forks_count", 0) for r in repos)
        
        # Get top repos (by stars)
        top_repos = []
        for repo in sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:10]:
            top_repos.append({
                "name": repo.get("name"),
                "description": repo.get("description"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language"),
                "updated_at": repo.get("updated_at"),
                "is_active": is_recently_active(repo.get("updated_at", "")),
                "url": repo.get("html_url"),
            })
        
        # Collect languages
        languages = {}
        for repo in repos:
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
        
        primary_languages = sorted(languages.keys(), key=lambda l: languages[l], reverse=True)[:5]
        
        return {
            "org_name": org,
            "org_bio": org_info.get("bio") or org_info.get("description"),
            "org_url": org_info.get("html_url"),
            "public_repos": len(repos),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "top_repos": top_repos,
            "primary_languages": primary_languages,
            "language_breakdown": languages,
            "repos_raw": repos[:20],  # Keep some raw data for extraction
            "error": None,
        }


def scrape_github_sync(company: str, domain: str) -> dict:
    """Synchronous wrapper for scrape_github."""
    import asyncio
    return asyncio.run(scrape_github(company, domain))


# For testing
if __name__ == "__main__":
    import asyncio
    import json
    
    async def test():
        result = await scrape_github("Cursor", "cursor.sh")
        print(json.dumps(result, indent=2, default=str))
        
    asyncio.run(test())
