from datetime import datetime
from json import loads
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, render_template

app = Flask(__name__)

API_URL = "https://tr.wikipedia.org/api/rest_v1/feed/onthisday/all/{month}/{day}"
USER_AGENT = "TarihteBugunApp/2.0 (https://github.com/zapotec001)"
CATEGORIES = ("selected", "events", "births", "deaths", "holidays", "observances")
CATEGORY_LABELS = {
    "selected": "Öne Çıkanlar",
    "events": "Olay",
    "births": "Doğum",
    "deaths": "Ölüm",
    "holidays": "Özel Gün",
    "observances": "Anma",
}
MONTH_NAMES_TR = [
    "Ocak",
    "Şubat",
    "Mart",
    "Nisan",
    "Mayıs",
    "Haziran",
    "Temmuz",
    "Ağustos",
    "Eylül",
    "Ekim",
    "Kasım",
    "Aralık",
]
MAX_EVENTS = 9
LENGTH_LIMIT = 240


def _normalise_title(value: Optional[str]) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def _normalise_pages(pages: Optional[List[Dict[str, Any]]]) -> List[Dict[str, str]]:
    normalised: List[Dict[str, str]] = []
    for page in pages or []:
        content_urls = page.get("content_urls") or {}
        desktop_url = (content_urls.get("desktop") or {}).get("page")
        mobile_url = (content_urls.get("mobile") or {}).get("page")
        url = desktop_url or mobile_url
        title = _normalise_title((page.get("titles") or {}).get("display") or page.get("title"))

        if not url or not title:
            continue

        description = _normalise_title(page.get("description"))
        image_source = (page.get("originalimage") or {}).get("source") or (
            (page.get("thumbnail") or {}).get("source")
        )

        normalised.append(
            {
                "title": title,
                "url": url,
                "description": description,
                "image_source": image_source or "",
            }
        )
    return normalised


def fetch_today_events(limit: int = MAX_EVENTS, max_length: int = LENGTH_LIMIT) -> List[Dict[str, Any]]:
    """Fetch notable events for today's date from Wikipedia and normalise them."""

    today = datetime.utcnow()
    url = API_URL.format(month=today.month, day=today.day)

    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Language": "tr",
        },
    )

    try:
        with urlopen(request, timeout=10) as response:
            data = loads(response.read().decode("utf-8"))
    except (URLError, HTTPError, ValueError):
        return []

    aggregated: List[Dict[str, Any]] = []
    for category in CATEGORIES:
        for event in data.get(category, []) or []:
            text = _normalise_title(event.get("text"))
            if not text or len(text) > max_length:
                continue
            aggregated.append({"category": category, "event": event, "text": text})

    aggregated.sort(key=lambda item: item["event"].get("year", 0), reverse=True)

    normalised_events: List[Dict[str, Any]] = []
    seen = set()

    for item in aggregated:
        event = item["event"]
        year = event.get("year")
        text = item["text"]
        dedup_key = f"{year}-{text}".lower()
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        pages = _normalise_pages(event.get("pages"))
        content_urls = event.get("content_urls") or {}
        direct_image_src = (event.get("originalimage") or {}).get("source") or (
            (event.get("thumbnail") or {}).get("source")
        )
        direct_image_url = (content_urls.get("desktop") or {}).get("page") or (
            (content_urls.get("mobile") or {}).get("page")
        )
        extract = _normalise_title(event.get("extract"))

        image: Optional[Dict[str, Optional[str]]] = None
        if direct_image_src:
            image = {
                "src": direct_image_src,
                "alt": text,
                "url": direct_image_url or (pages[0]["url"] if pages else None),
                "caption": extract or None,
            }
        else:
            page_with_image = next((page for page in pages if page.get("image_source")), None)
            if page_with_image:
                image = {
                    "src": page_with_image["image_source"],
                    "alt": page_with_image["title"],
                    "url": page_with_image["url"],
                    "caption": page_with_image["description"] or None,
                }

        normalised_events.append(
            {
                "year": year,
                "text": text,
                "category": item["category"],
                "category_label": CATEGORY_LABELS.get(item["category"], item["category"]),
                "pages": [{"title": page["title"], "url": page["url"]} for page in pages[:3]],
                "image": image,
            }
        )

        if len(normalised_events) >= limit:
            break

    return normalised_events


@app.route("/")
def home():
    events = fetch_today_events()
    today = datetime.utcnow()
    return render_template(
        "index.html",
        events=events,
        date_string=f"{today.day:02d} {MONTH_NAMES_TR[today.month - 1]} {today.year}",
    )


if __name__ == "__main__":
    app.run(debug=True)
