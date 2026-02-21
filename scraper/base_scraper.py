import requests
from bs4 import BeautifulSoup


class BaseScraper:
    def fetch_page(self, url):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching page: {e}")
            return None

    def parse(self, html):
        raise NotImplementedError("Subclasses must implement parse method")

    def scrape(self):
        raise NotImplementedError("Subclasses must implement scrape method")