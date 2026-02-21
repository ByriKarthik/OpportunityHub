from scraper.iit_scraper import IITScraper

scraper = IITScraper()
data = scraper.scrape()

for item in data:
    print(item["title"])
    print(item["link"])
    print("-" * 50)

print("Total:", len(data))