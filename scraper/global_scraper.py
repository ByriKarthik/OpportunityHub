from __future__ import annotations

import logging
import re
from typing import Dict, List, Set
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class GlobalOpportunityScraper(BaseScraper):
    """Scrape global opportunities from a public RSS feed."""

    RSS_FEED_URL = "https://www.opportunitiesforafricans.com/feed/"
    MAX_RESULTS = 15
    KEYWORDS = {
        "internship",
        "fellowship",
        "conference",
        "workshop",
        "program",
        "scholarship",
        "research",
        "summer",
    }

    def scrape(self) -> List[Dict[str, str]]:
        xml = self.fetch_page(self.RSS_FEED_URL)
        if not xml:
            logger.warning("Unable to fetch global feed: %s", self.RSS_FEED_URL)
            return []
        return self.parse(xml)

    def parse(self, xml: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(xml, "xml")
        items = soup.find_all("item")
        opportunities: List[Dict[str, str]] = []
        seen_links: Set[str] = set()

        for item in items:
            title = self._clean_text(item.title.get_text(" ", strip=True) if item.title else "")
            link = self._clean_text(item.link.get_text(" ", strip=True) if item.link else "")
            description = self._extract_description(item)

            if not title or not link:
                continue

            normalized_link = urljoin(self.RSS_FEED_URL, link)
            if normalized_link in seen_links:
                continue

            searchable_text = f"{title} {description}".lower()
            if not self._contains_opportunity_keyword(searchable_text):
                continue

            opportunities.append(
                {
                    "title": title,
                    "link": normalized_link,
                    "description": description,
                    "university": "Global",
                    "source": "GLOBAL",
                }
            )
            seen_links.add(normalized_link)

            if len(opportunities) >= self.MAX_RESULTS:
                break

        return opportunities

    @classmethod
    def _contains_opportunity_keyword(cls, text: str) -> bool:
        return any(keyword in text for keyword in cls.KEYWORDS)

    @staticmethod
    def _clean_text(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _extract_description(self, item) -> str:
        if item.description:
            # RSS descriptions often include HTML markup.
            raw_description = item.description.get_text(" ", strip=True)
            plain_description = BeautifulSoup(raw_description, "html.parser").get_text(" ", strip=True)
            cleaned = self._clean_text(plain_description)
            if cleaned:
                return cleaned[:400]
        return ""
