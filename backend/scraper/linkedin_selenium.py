# backend/scraper/linkedin_selenium.py
import time
import urllib.parse
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


def scrape_linkedin_selenium(
    field: str, location: str = ""
) -> List[Dict]:  # Add location parameter
    """
    Scrape LinkedIn internships for a given field and location.
    Returns list of job dicts with keys: title, company, location, url, description, email, source.
    """
    # Build LinkedIn URL
    keywords = f"{field} internship"
    # Use the provided location, defaulting to "Worldwide" if empty
    location_to_use = location if location else "Worldwide"
    encoded_keywords = urllib.parse.quote(keywords)
    encoded_location = urllib.parse.quote(location_to_use)
    # Construct the URL with the specified location
    url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_keywords}&location={encoded_location}&f_E=1&f_JT=I"  # Added f_JT=I for internship filter

    # Configure headless Chrome
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    jobs = []
    driver = None
    try:
        # Auto-manage ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        print(f"[LinkedIn] Loading: {url}")
        driver.get(url)
        time.sleep(5)

        # Scroll to load more jobs
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            print(f"[LinkedIn] Scrolled {i+1} times")

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Find job cards
        job_cards = soup.find_all("div", class_="base-card")
        if not job_cards:
            job_cards = soup.find_all("li", class_="jobs-search-results__list-item")

        print(f"[LinkedIn] Found {len(job_cards)} job cards")

        for idx, card in enumerate(job_cards[:20]):
            try:
                # Title
                title_tag = (
                    card.find("h3", class_="base-search-card__title")
                    or card.find("a", class_="base-card__full-link")
                    or card.find(
                        "span", {"class": lambda x: x and "job-card-list__title" in x}
                    )
                )
                title = title_tag.get_text(strip=True) if title_tag else None

                # Company
                company_tag = (
                    card.find("h4", class_="base-search-card__subtitle")
                    or card.find("a", class_="hidden-nested-link")
                    or card.find(
                        "span",
                        {
                            "class": lambda x: x
                            and "job-card-container__company-name" in x
                        },
                    )
                )
                company = company_tag.get_text(strip=True) if company_tag else None

                # Location
                loc_tag = card.find(
                    "span", class_="job-search-card__location"
                ) or card.find(
                    "span",
                    {"class": lambda x: x and "job-card-container__metadata-item" in x},
                )
                # Use the location found on the page, defaulting to the searched location if not found on card
                page_location = loc_tag.get_text(strip=True) if loc_tag else None
                location_result = page_location or f"{location_to_use} (LinkedIn)"

                # Link
                link_tag = card.find("a", href=True)
                link = None
                if link_tag:
                    href = link_tag["href"]
                    if href.startswith("/"):
                        link = "https://www.linkedin.com" + href
                    else:
                        link = href.split("?")[0]  # Clean params

                if title and company:
                    jobs.append(
                        {
                            "title": title,
                            "company": company,
                            "location": location_result,  # Use the determined location
                            "description": "",
                            "url": link,
                            "email": None,
                            "source": "linkedin",
                        }
                    )

            except Exception as e:
                print(f"[LinkedIn] Error parsing job {idx}: {e}")
                continue

    except Exception as e:
        print(f"[LinkedIn] Scraping error: {e}")
    finally:
        if driver:
            driver.quit()

    return jobs
