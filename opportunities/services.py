import re
from datetime import date, timedelta
from typing import Optional

from dateutil import parser as date_parser

from scraper.iit_scraper import IITScraper
from scraper.global_scraper import GlobalOpportunityScraper
from scraper.ivy_scraper import IvyLeagueScraper
from scraper.india_scraper import IndiaOpportunityScraper
from .models import Opportunity


def _classify_opportunity_type(title: str, description: str) -> str:
    text = f"{title} {description}".lower()
    if re.search(r"\bintern(ship|ships|)\b", text):
        return "INTERNSHIP"
    if re.search(r"\bfellow(ship|ships|)\b", text):
        return "FELLOWSHIP"
    if re.search(r"\bscholar(ship|ships|)\b", text):
        return "SCHOLARSHIP"
    if re.search(r"\bworkshop(s)?\b", text):
        return "WORKSHOP"
    if re.search(r"\bconference(s)?\b", text):
        return "CONFERENCE"
    return "OTHER"


def _extract_deadline(text: str) -> Optional[date]:
    if not text:
        return None

    today = date.today()
    text = text.strip()
    candidates = []
    lowered = text.lower()
    has_deadline_hint = any(
        token in lowered
        for token in (
            "deadline",
            "apply by",
            "last date",
            "closing date",
            "closes on",
            "valid till",
            "submit by",
        )
    )

    date_token = r"(?:\d{1,2}(?:st|nd|rd|th)?)"

    labeled_patterns = [
        rf"(?i)(?:deadline|apply by|last date|application deadline|closing date|closes on|valid till|submit by)\s*[:\-]?\s*([A-Za-z]{{3,9}}\s+{date_token},?\s+\d{{4}})",
        rf"(?i)(?:deadline|apply by|last date|application deadline|closing date|closes on|valid till|submit by)\s*[:\-]?\s*({date_token}\s+[A-Za-z]{{3,9}}\s+\d{{4}})",
        r"(?i)(?:deadline|apply by|last date|application deadline|closing date|closes on|valid till|submit by)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    ]
    for pattern in labeled_patterns:
        candidates.extend(re.findall(pattern, text))

    if not candidates and has_deadline_hint:
        generic_patterns = [
            rf"\b[A-Za-z]{{3,9}}\s+{date_token},?\s+\d{{4}}\b",
            rf"\b{date_token}\s+[A-Za-z]{{3,9}}\s+\d{{4}}\b",
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        ]
        for pattern in generic_patterns:
            candidates.extend(re.findall(pattern, text))

    parsed_dates = []
    for candidate in candidates:
        try:
            cleaned_candidate = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", candidate, flags=re.I)
            parsed = date_parser.parse(cleaned_candidate, fuzzy=True, dayfirst=True).date()
        except (ValueError, OverflowError):
            continue
        if today - timedelta(days=180) <= parsed <= today + timedelta(days=5 * 365):
            parsed_dates.append(parsed)

    if not parsed_dates:
        return None

    upcoming = sorted(d for d in parsed_dates if d >= today)
    if upcoming:
        return upcoming[0]
    return sorted(parsed_dates)[-1]


def run_iit_scraper():
    scrapers = [
        IndiaOpportunityScraper(),
        GlobalOpportunityScraper(),
        IITScraper(),   # keep or remove later
    ]

    created_count = 0

    for scraper in scrapers:
        data = scraper.scrape()

        for item in data:
            title = item.get("title", "")
            description = item.get("description", "")
            classified_type = _classify_opportunity_type(title, description)
            deadline = _extract_deadline(f"{title} {description}")
            obj, created = Opportunity.objects.get_or_create(
                link=item["link"],
                defaults={
                    "title": title,
                    "description": description,
                    "opportunity_type": classified_type,
                    "deadline": deadline,
                    "university": item["university"],
                    "source": item["source"],
                }
            )
            if created:
                created_count += 1
            else:
                # Keep existing entries fresh and fix previously defaulted OTHER values.
                updates = {}
                if title and obj.title != title:
                    updates["title"] = title
                if description and obj.description != description:
                    updates["description"] = description
                if item.get("university") and obj.university != item["university"]:
                    updates["university"] = item["university"]
                if item.get("source") and obj.source != item["source"]:
                    updates["source"] = item["source"]
                if obj.opportunity_type != classified_type:
                    updates["opportunity_type"] = classified_type
                if obj.deadline != deadline:
                    updates["deadline"] = deadline
                if updates:
                    Opportunity.objects.filter(pk=obj.pk).update(**updates)

    return created_count
