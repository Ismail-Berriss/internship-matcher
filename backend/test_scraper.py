# test_scraper.py
from scraper import scrape_internships

jobs = scrape_internships("data engineer")
print(f"✅ Found {len(jobs)} internships")
for job in jobs[:3]:
    print(f"• {job['title']} @ {job['company']} ({job['source']})")
    print(f"  {job['url']}\n")
