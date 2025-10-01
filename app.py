from datetime import datetime
from json import loads
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, render_template

app = Flask(__name__)

API_URL = "https://tr.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
USER_AGENT = "TarihteBugunApp/1.0 (https://github.com/zapotec001)"
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


def _normalise_title(value: Optional[str]) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def fetch_today_events(limit: int = 4) -> List[Dict[str, Any]]:
    """Fetch notable events for today's date from Wikipedia."""
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

    events = data.get("events", [])

    # Sort by the year descending so the most recent events appear first
    events.sort(key=lambda event: event.get("year", 0), reverse=True)

    formatted_events = []
    for event in events:
        text = _normalise_title(event.get("text"))
        if not text:
            continue

        page_links: List[Dict[str, str]] = []
        primary_image: Optional[Dict[str, Any]] = None

        for page in event.get("pages", []):
            content_urls = (page.get("content_urls") or {}).get("desktop") or {}
            desktop_url = content_urls.get("page")
            title = _normalise_title((page.get("titles") or {}).get("display") or page.get("title"))

            if not desktop_url or not title:
                continue

            description = _normalise_title(page.get("description"))
            image_url = (page.get("originalimage") or {}).get("source") or (
                (page.get("thumbnail") or {}).get("source")
            )

            page_links.append({"title": title, "url": desktop_url})

            if not primary_image and image_url:
                primary_image = {
                    "src": image_url,
                    "alt": title,
                    "url": desktop_url,
                    "caption": description or None,
                }

            if len(page_links) >= 2 and primary_image:
                break

        formatted_events.append(
            {
                "year": event.get("year"),
                "text": text,
                "pages": page_links[:2],
                "image": primary_image,
            }
        )

        if len(formatted_events) >= limit:
            break

    return formatted_events


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
