from __future__ import annotations

import logging
import re
from typing import Dict, List, Set

from bs4 import BeautifulSoup

from scraper.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class IvyLeagueScraper(BaseScraper):
    """Scrape Ivy/global academic opportunities from reliable RSS feeds."""

    FEED_URLS = (
        "https://www.opportunitiesforafricans.com/feed/",
        "https://www.scholarshippositions.com/feed/",
    )
    MAX_RESULTS = 10
    KEYWORDS = {
        "internship",
        "fellowship",
        "scholarship",
        "conference",
        "workshop",
        "research",
        "program",
        "summer",
    }

    def scrape(self) -> List[Dict[str, str]]:
        opportunities: List[Dict[str, str]] = []
        seen_links: Set[str] = set()

        for feed_url in self.FEED_URLS:
            xml = self.fetch_page(feed_url)
            if not xml:
                logger.warning("Failed to fetch feed: %s", feed_url)
                continue

            parsed = self.parse(xml)
            parsed = [item for item in parsed if item["link"] not in seen_links]
            opportunities.extend(parsed)
            seen_links.update(item["link"] for item in parsed)

            if len(opportunities) >= self.MAX_RESULTS:
                return opportunities[: self.MAX_RESULTS]

        return opportunities[: self.MAX_RESULTS]

    def parse(self, xml: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(xml, "xml")
        entries = soup.find_all("item") or soup.find_all("entry")
        opportunities: List[Dict[str, str]] = []
        seen_links: Set[str] = set()

        for entry in entries:
            title = self._extract_title(entry)
            link = self._extract_link(entry)
            description = self._extract_description(entry)

            if not title or not link:
                continue
            if link in seen_links:
                continue
            if not self._contains_keyword(f"{title} {description}".lower()):
                continue

            opportunities.append(
                {
                    "title": title,
                    "link": link,
                    "description": description,
                    "university": "Ivy / Global",
                    "source": "IVY",
                }
            )
            seen_links.add(link)

            if len(opportunities) >= self.MAX_RESULTS:
                break

        return opportunities

    @staticmethod
    def _clean_text(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def _contains_keyword(cls, text: str) -> bool:
        return any(keyword in text for keyword in cls.KEYWORDS)

    def _extract_title(self, entry) -> str:
        if entry.title:
            return self._clean_text(entry.title.get_text(" ", strip=True))
        return ""

    def _extract_link(self, entry) -> str:
        if entry.link:
            href = entry.link.get("href")
            if href:
                return self._clean_text(href)
            link_text = self._clean_text(entry.link.get_text(" ", strip=True))
            if link_text:
                return link_text

        guid = entry.find("guid")
        if guid:
            guid_text = self._clean_text(guid.get_text(" ", strip=True))
            if guid_text.startswith("http"):
                return guid_text
        return ""

    def _extract_description(self, entry) -> str:
        candidate = (
            entry.find("description")
            or entry.find("summary")
            or entry.find("content")
            or entry.find("content:encoded")
        )
        if not candidate:
            return ""

        raw = candidate.get_text(" ", strip=True)
        plain = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
        return self._clean_text(plain)[:320]
