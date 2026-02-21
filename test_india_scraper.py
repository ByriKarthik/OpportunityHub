# test_india_scraper.py
from scraper.india_scraper import IndiaOpportunityScraper

scraper = IndiaOpportunityScraper()
data = scraper.scrape()

for item in data:
    print(item["title"])
    print(item["link"])
    print("-" * 40)

print("Total:", len(data))