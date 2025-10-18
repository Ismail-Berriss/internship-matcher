from typing import List, Dict
from .wttj_playwright import scrape_wttj_jobs_async
from .linkedin_selenium import scrape_linkedin_selenium
from .cache import get_cached_jobs, set_cached_jobs
import asyncio


def scrape_internships(field: str, location: str = "") -> List[Dict]:
    """Scrape internships from multiple sources with caching."""

    # Use the updated cache functions that accept the location
    cached = get_cached_jobs(field=field, location=location)
    if cached is not None:
        print(
            f"[Cache] Returning {len(cached)} cached jobs for field: {field}, location: {location}"
        )
        return cached

    print(f"[Scraper] Fetching new jobs for field: {field}, location: {location}")
    jobs = []

    # Scrape WTTJ (async) - Pass the single field and the location
    try:
        wttj_jobs = asyncio.run(scrape_wttj_jobs_async(field, location))
        jobs.extend(wttj_jobs)
        print(
            f"[Scraper] Got {len(wttj_jobs)} WTTJ jobs for '{field}' with location '{location}'"
        )
    except Exception as e:
        print(f"[WTTJ Scraper Error for field '{field}']: {e}")

    # Scrape LinkedIn (sync) - Pass the single field and the location
    try:
        linkedin_jobs = scrape_linkedin_selenium(field, location)
        jobs.extend(linkedin_jobs)
        print(
            f"[Scraper] Got {len(linkedin_jobs)} LinkedIn jobs for '{field}' with location '{location}'"
        )
    except Exception as e:
        print(f"[LinkedIn Scraper Error for field '{field}']: {e}")

    # Deduplicate by URL after collecting jobs from all sources
    seen = set()
    unique_jobs = []
    for job in jobs:
        url = job.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique_jobs.append(job)

    # Use the updated set_cached_jobs function that accepts the location
    set_cached_jobs(field, unique_jobs, location)
    print(f"[Scraper] Cached {len(unique_jobs)} total unique jobs")
    return unique_jobs
