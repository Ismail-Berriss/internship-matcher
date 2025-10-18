# backend/scraper/wttj_playwright.py
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import urllib.parse
from typing import List, Dict


async def scrape_wttj_jobs_async(field: str, location: str = "") -> List[Dict]:
    """
    Scrape WTTJ internships for a given field using Playwright + BeautifulSoup.
    Includes location filtering in the URL if provided.
    Returns list of job dicts.
    """
    # Base query
    query = f"query={field}"

    # Build URL components
    base_url = "https://www.welcometothejungle.com/fr/jobs?"
    params = [
        "refinementList%5Boffices.country_code%5D%5B%5D=FR",  # Default to France
        "refinementList%5Bcontract_type%5D%5B%5D=internship",
        "page=1",
        query,
    ]

    # Add location filter if provided
    if location:
        # Note: WTTJ URLs might need specific city/country codes, not just free text.
        # This example assumes a city name that might work. You might need to map
        # user-friendly names to WTTJ's internal codes.
        # Example: "Paris" might be handled by a refinementList filter if available.
        # For now, let's try adding a city refinement if it's a known French city.
        # A more robust solution would map locations or use the search bar for location too.
        # For simplicity, adding it to the main query if it's not a generic term like "Remote"
        if location.lower() not in ["remote", "onsite", "hybrid", ""]:
            # This is a simplification; WTTJ might have specific refinement parameters for cities.
            # If WTTJ supports searching location within the main query, this might work.
            # Otherwise, you need to find the correct refinementList parameter for city/region.
            # e.g., f"&refinementList%5Boffices.city%5D%5B%5D={urllib.parse.quote(location)}"
            # You might need to inspect WTTJ's actual search requests to find the correct parameter.
            # For now, appending to query might be the fallback.
            params[-1] = (
                f"query={f'{field} {location}'}"  # Append location to search query
            )
            # If location is 'Remote', 'Onsite', 'Hybrid', WTTJ might not have a direct filter for these
            # in the main internship search for France, so filtering might happen post-scrape or be ignored.
            # For country-wide filters, the country_code param is already set to FR.

    url = base_url + "&".join(params)

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="fr-FR",
        )

        page = await context.new_page()
        await page.set_extra_http_headers(
            {
                "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Upgrade-Insecure-Requests": "1",
                "Referer": "https://www.welcometothejungle.com/",
                "DNT": "1",
            }
        )

        print(f"[WTTJ] Loading: {url}")
        await page.goto(url, timeout=60000)
        try:
            await page.wait_for_selector(
                "li[data-testid='search-results-list-item-wrapper']", timeout=20000
            )
        except:
            print("[WTTJ] No job cards found or timeout")
            await browser.close()
            return []

        await asyncio.sleep(3)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)

        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    job_items = soup.select("li[data-testid='search-results-list-item-wrapper']")
    jobs = []

    for item in job_items:
        title_tag = item.select_one("div[role='mark']")
        company_tag = item.select_one("span.sc-izXThL.fFdRYJ")

        # Location extraction (same logic as your script)
        location_found = None
        location_strategy = None
        location_divs = item.find_all("div", class_="sc-fibHhp")
        for div in location_divs:
            icon = div.find("i", attrs={"name": "location"})
            if icon:
                location_span = (
                    div.find("span", class_="sc-ddixHk")
                    or div.find("span", class_="sc-dMVKqj")
                    or div.find("span", recursive=False)
                )
                if location_span:
                    inner_span = location_span.find("span")
                    location_found = (
                        inner_span.get_text(strip=True)
                        if inner_span
                        else location_span.get_text(strip=True)
                    )
                    location_strategy = "Strategy 1"
                    break
        if not location_found:
            for div in location_divs:
                icon = div.find("i", attrs={"name": "location"})
                if icon:
                    text = div.get_text(strip=True)
                    if text:
                        location_found = text
                        location_strategy = "Strategy 2"
                        break

        date_tag = item.select_one("time")
        link_tag = item.select_one("a[href*='/jobs/']")
        image_tag = item.select_one("img[data-testid^='job-thumb-cover']")

        job_data = {
            "title": title_tag.get_text(strip=True) if title_tag else None,
            "company": company_tag.get_text(strip=True) if company_tag else None,
            # Use the location found on the page, defaulting if not found
            "location": location_found or "France (WTTJ)",
            "description": "",
            "url": (
                "https://www.welcometothejungle.com" + link_tag["href"]
                if link_tag
                else None
            ),
            "email": None,
            "source": "wttj",
        }
        jobs.append(job_data)

    return jobs
