import requests
from bs4 import BeautifulSoup
from typing import List, Dict


class IITScraper:
    """
    Scrapes opportunities from official IIT Madras RSS feed.
    Reliable, structured, and real-time.
    """

    SOURCE_URL = "https://www.iitm.ac.in/rss.xml"

    def scrape(self) -> List[Dict[str, str]]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            response = requests.get(self.SOURCE_URL, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print("Error fetching RSS:", e)
            return []

        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")

        opportunities = []

        for item in items[:20]:
            title = item.title.text if item.title else "No Title"
            title_lower = title.lower()
            keywords = ["internship", "workshop", "conference", "fellowship", "research", "program", "training", "summer"]
            if not any(k in title_lower for k in keywords):
                continue
            link = item.link.text if item.link else ""
            description_html = item.description.text if item.description else ""
            description = BeautifulSoup(description_html, "html.parser").get_text(" ", strip=True)
            description = description[:300]
            if len(opportunities) >= 10:
                break

            opportunities.append({
                "title": title.strip(),
                "link": link.strip(),
                "description": description.strip(),
                "university": "IIT Madras",
                "source": "IIT"
            })

        return opportunities