from datetime import datetime
from json import loads
from typing import List, Dict, Any
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

from flask import Flask, render_template

app = Flask(__name__)

API_URL = "https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
USER_AGENT = "TarihteBugunApp/1.0 (https://github.com/zapotec001)"


def fetch_today_events(limit: int = 4) -> List[Dict[str, Any]]:
    """Fetch notable events for today's date from Wikipedia."""
    today = datetime.utcnow()
    url = API_URL.format(month=today.month, day=today.day)

    request = Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urlopen(request, timeout=10) as response:
            data = loads(response.read().decode("utf-8"))
    except (URLError, HTTPError, ValueError):
        return []

    events = data.get("events", [])

    # Sort by the year descending so the most recent events appear first
    events.sort(key=lambda event: event.get("year", 0), reverse=True)

    formatted_events = []
    for event in events[:limit]:
        pages = []
        for page in event.get("pages", [])[:2]:
            desktop_url = (
                (page.get("content_urls") or {}).get("desktop") or {}
            ).get("page")
            title = (page.get("titles") or {}).get("display") or page.get("title")
            if desktop_url and title:
                pages.append({"title": title, "url": desktop_url})

        formatted_events.append(
            {
                "year": event.get("year"),
                "text": event.get("text"),
                "pages": pages,
            }
        )

    return formatted_events


@app.route("/")
def home():
    events = fetch_today_events()
    today = datetime.utcnow()
    return render_template(
        "index.html",
        events=events,
        date_string=today.strftime("%d %B %Y"),
    )


if __name__ == "__main__":
    app.run(debug=True)
