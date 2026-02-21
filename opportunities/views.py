import re

import requests
from bs4 import BeautifulSoup
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Case, IntegerField, Q, Value, When
from django.views.decorators.http import require_POST
from .services import run_iit_scraper
from django.shortcuts import get_object_or_404, redirect, render
from .models import Opportunity

UNWANTED_KEYWORDS = (
    "disclaimer",
    "join our",
    "community",
    "follow us",
    "subscribe",
    "expired",
    "other opportunities",
    "advertisement",
    "footer",
    "all rights reserved",
)
JUNK_PHRASES = (
    "internships city",
    "online courses",
    "trending",
    "expire opportunities",
)
STOP_SECTION_MARKERS = (
    "disclaimer",
    "advertisement",
    "all rights reserved",
    "expired",
    "related posts",
    "you may also like",
    "popular posts",
    "recent posts",
    "leave a reply",
    "comments",
    "footer",
)

def health_check(request):
    return JsonResponse({'status': 'ok'})

def home(request):
    return render(request, "home.html")

def scrape_iit(request):
    count = run_iit_scraper()
    if _wants_json(request):
        return JsonResponse({"message": f"Scraped successfully. New items added: {count}"})
    messages.success(request, "Opportunities refreshed successfully")
    return redirect("opportunities:opportunity-list")

def opportunity_list(request):
    query = (request.GET.get("q") or "").strip()
    page_number = request.GET.get("page")
    bookmarks = _get_bookmark_ids(request)
    all_opportunities = Opportunity.objects.all()
    opportunities_qs = all_opportunities.order_by("-scraped_at")
    if query:
        words = re.findall(r"[A-Za-z0-9]+", query)
        for word in words:
            pattern = rf"(?<!\w){re.escape(word)}(?!\w)"
            opportunities_qs = opportunities_qs.filter(
                Q(title__iregex=pattern) | Q(description__iregex=pattern)
            )
        opportunities_qs = opportunities_qs.annotate(
            title_match_boost=Case(
                When(title__icontains=query, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
    else:
        opportunities_qs = opportunities_qs.annotate(
            title_match_boost=Value(1, output_field=IntegerField())
        )

    opportunities_qs = opportunities_qs.annotate(
        deadline_null_rank=Case(
            When(deadline__isnull=True, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by("title_match_boost", "deadline_null_rank", "deadline", "-scraped_at")

    paginator = Paginator(opportunities_qs, 10)
    page_obj = paginator.get_page(page_number)
    latest = all_opportunities.order_by("-scraped_at").values_list("scraped_at", flat=True).first()
    return render(
        request,
        "opportunities/list.html",
        {
            "opportunities": page_obj,
            "page_obj": page_obj,
            "q": query,
            "bookmarks": bookmarks,
            "page_title": "Opportunity Dashboard",
            "is_saved_page": False,
            "total_count": all_opportunities.count(),
            "india_count": all_opportunities.filter(
                Q(source__iexact="INDIA") | Q(source__iexact="IIT")
            ).count(),
            "global_count": all_opportunities.filter(source__iexact="GLOBAL").count(),
            "saved_count": len(bookmarks),
            "latest_scrape_time": latest,
        },
    )


def saved_opportunities(request):
    page_number = request.GET.get("page")
    bookmarks = _get_bookmark_ids(request)
    opportunities_qs = Opportunity.objects.filter(pk__in=bookmarks).order_by("-scraped_at")
    paginator = Paginator(opportunities_qs, 10)
    page_obj = paginator.get_page(page_number)
    all_opportunities = Opportunity.objects.all()
    latest = all_opportunities.order_by("-scraped_at").values_list("scraped_at", flat=True).first()
    return render(
        request,
        "opportunities/list.html",
        {
            "opportunities": page_obj,
            "page_obj": page_obj,
            "q": "",
            "bookmarks": bookmarks,
            "page_title": "Saved Opportunities",
            "is_saved_page": True,
            "total_count": all_opportunities.count(),
            "india_count": all_opportunities.filter(
                Q(source__iexact="INDIA") | Q(source__iexact="IIT")
            ).count(),
            "global_count": all_opportunities.filter(source__iexact="GLOBAL").count(),
            "saved_count": len(bookmarks),
            "latest_scrape_time": latest,
        },
    )


@require_POST
def toggle_bookmark(request, pk):
    get_object_or_404(Opportunity, pk=pk)
    bookmarks = _get_bookmark_ids(request)
    if pk in bookmarks:
        bookmarks.remove(pk)
        bookmarked = False
    else:
        bookmarks.append(pk)
        bookmarked = True
    request.session["bookmarks"] = bookmarks
    request.session.modified = True
    return JsonResponse(
        {
            "status": "ok",
            "bookmarked": bookmarked,
            "id": pk,
            "saved_count": len(bookmarks),
        }
    )


def opportunity_detail(request, pk):
    opportunity = get_object_or_404(Opportunity, pk=pk)
    full_content = _fetch_full_opportunity_content(opportunity.link)
    if not full_content:
        full_content = opportunity.description or "No detailed content available."
    return render(
        request,
        "opportunities/detail.html",
        {
            "opportunity": opportunity,
            "full_content": full_content,
        },
    )


def _fetch_full_opportunity_content(url: str) -> str:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        response.raise_for_status()
    except Exception:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove noisy blocks before text extraction.
    for node in soup.select("script, style, nav, footer, header, aside, form"):
        node.decompose()

    selectors = (
        "article",
        ".entry-content",
        ".post-content",
        ".article-content",
        ".main-content",
        "main",
    )
    for selector in selectors:
        container = soup.select_one(selector)
        extracted = _extract_paragraph_content(container, fallback_mode=False)
        if extracted:
            return extracted

    # Absolute fallback only when article containers are unavailable.
    fallback_text = _extract_paragraph_content(soup, fallback_mode=True)
    if fallback_text:
        return fallback_text

    return ""


def _extract_paragraph_content(node, fallback_mode: bool = False) -> str:
    if not node:
        return ""

    paragraphs = []
    for p in node.find_all("p"):
        text = _clean_text(p.get_text(" ", strip=True))
        if not text:
            continue

        if _is_stop_section(text):
            break

        if fallback_mode and len(text) < 40:
            break

        if _contains_unwanted(text):
            if fallback_mode:
                break
            continue

        if _is_paragraph_noise(p, text):
            if fallback_mode:
                break
            continue

        if len(text) < 40:
            continue

        paragraphs.append(text)

        if fallback_mode and len(paragraphs) >= 12:
            break

    deduped = _dedupe_paragraphs(paragraphs)
    if deduped:
        if fallback_mode:
            deduped = deduped[:12]
            if len(deduped) > 8:
                deduped = deduped[:10]
        return "\n\n".join(deduped[:25])

    if fallback_mode:
        return ""

    text = _clean_text(node.get_text(" ", strip=True))
    if _contains_unwanted(text) or _is_stop_section(text):
        return ""
    return text if len(text) >= 120 else ""


def _contains_unwanted(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in UNWANTED_KEYWORDS)


def _is_stop_section(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in STOP_SECTION_MARKERS)


def _is_paragraph_noise(node, text: str) -> bool:
    lowered = text.lower()

    if any(phrase in lowered for phrase in JUNK_PHRASES):
        return True

    link_count = len(node.find_all("a"))
    if link_count >= 4:
        return True

    url_count = len(re.findall(r"https?://|www\.", lowered))
    if url_count > 3:
        return True

    comma_count = text.count(",")
    if comma_count >= 8 and len(text.split()) <= comma_count * 3:
        return True

    opportunity_mentions = len(re.findall(r"\bopportunities\b", lowered))
    if opportunity_mentions >= 4:
        return True

    return False


def _dedupe_paragraphs(paragraphs):
    seen = set()
    output = []
    for paragraph in paragraphs:
        canonical = _canonicalize(paragraph)
        if not canonical or canonical in seen:
            continue
        seen.add(canonical)
        output.append(_dedupe_sentences(paragraph))
    return [p for p in output if p]


def _dedupe_sentences(text: str) -> str:
    chunks = re.split(r"(?<=[.!?])\s+", text)
    seen = set()
    kept = []
    for chunk in chunks:
        sentence = _clean_text(chunk)
        if not sentence:
            continue
        canonical = _canonicalize(sentence)
        if canonical in seen:
            continue
        seen.add(canonical)
        kept.append(sentence)
    return " ".join(kept)


def _canonicalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _get_bookmark_ids(request):
    raw = request.session.get("bookmarks", [])
    cleaned = []
    for value in raw:
        try:
            cleaned.append(int(value))
        except (TypeError, ValueError):
            continue
    if raw != cleaned:
        request.session["bookmarks"] = cleaned
    return cleaned


def _wants_json(request) -> bool:
    if request.GET.get("format") == "json":
        return True
    accept = request.headers.get("Accept", "")
    if "application/json" in accept:
        return True
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"
