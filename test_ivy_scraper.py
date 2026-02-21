# test_ivy_scraper.py
from scraper.ivy_scraper import IvyLeagueScraper

scraper = IvyLeagueScraper()
data = scraper.scrape()

for item in data:
    print(item["title"])
    print(item["link"])
    print("-" * 40)

print("Total:", len(data))