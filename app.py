import os
from datetime import datetime
from functools import wraps
from json import JSONDecodeError, dump, load, loads
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

API_URL = "https://tr.wikipedia.org/api/rest_v1/feed/onthisday/all/{month}/{day}"
USER_AGENT = "TarihteBugunApp/3.0 (https://github.com/zapotec001)"
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
LENGTH_LIMIT = 260

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

DATA_PATH = Path(app.root_path) / "data" / "events.json"
DEFAULT_DATA: Dict[str, Any] = {"last_refreshed": None, "events": []}


def _normalise_whitespace(value: Optional[str]) -> str:
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
        title = _normalise_whitespace((page.get("titles") or {}).get("display") or page.get("title"))
        if not url or not title:
            continue
        description = _normalise_whitespace(page.get("description"))
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


def _format_timestamp(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        cleaned = value.replace("Z", "+00:00")
        moment = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    month_index = max(1, min(moment.month, len(MONTH_NAMES_TR))) - 1
    return f"{moment.day:02d} {MONTH_NAMES_TR[month_index]} {moment.year} {moment.hour:02d}:{moment.minute:02d}"


def _load_data() -> Dict[str, Any]:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        _save_data(DEFAULT_DATA)
        return {"last_refreshed": None, "events": []}

    try:
        with DATA_PATH.open("r", encoding="utf-8") as handle:
            data = load(handle)
    except (OSError, JSONDecodeError, ValueError):
        return {"last_refreshed": None, "events": []}

    raw_events = data.get("events") if isinstance(data, dict) else None
    if not isinstance(raw_events, list):
        raw_events = []
    events: List[Dict[str, Any]] = []
    for item in raw_events:
        if not isinstance(item, dict):
            continue
        event_copy = item.copy()
        event_copy.setdefault("id", str(uuid4()))
        category = event_copy.get("category")
        event_copy["category_label"] = CATEGORY_LABELS.get(category, category or "")
        event_copy.setdefault("date_label", _format_today())
        events.append(event_copy)
    last_refreshed = data.get("last_refreshed") if isinstance(data, dict) else None
    return {"last_refreshed": last_refreshed, "events": events}


def _save_data(data: Dict[str, Any]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    to_save = {
        "last_refreshed": data.get("last_refreshed"),
        "events": data.get("events", []),
    }
    with DATA_PATH.open("w", encoding="utf-8") as handle:
        dump(to_save, handle, ensure_ascii=False, indent=2)


def fetch_today_events(limit: int = MAX_EVENTS, max_length: int = LENGTH_LIMIT) -> List[Dict[str, Any]]:
    """Fetch notable events for today's date from Turkish Wikipedia."""

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
            payload = response.read().decode("utf-8")
            data = loads(payload)
    except (URLError, HTTPError, ValueError, TimeoutError, JSONDecodeError):
        return []

    aggregated: List[Dict[str, Any]] = []
    for category in CATEGORIES:
        for event in data.get(category, []) or []:
            text = _normalise_whitespace(event.get("text"))
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
        extract = _normalise_whitespace(event.get("extract"))

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
                "id": str(uuid4()),
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


def _create_entry_from_event(event: Dict[str, Any], date_label: str) -> Dict[str, Any]:
    primary_page = event.get("pages", [{}])[0] if event.get("pages") else {}
    image = event.get("image") or {}
    return {
        "id": event.get("id", str(uuid4())),
        "title": primary_page.get("title") or event.get("text", "Tarihte Bugün"),
        "summary": event.get("text", ""),
        "year": event.get("year"),
        "category": event.get("category"),
        "category_label": event.get("category_label"),
        "source_url": primary_page.get("url") or image.get("url") or "",
        "source_title": primary_page.get("title") or "Wikipedia",
        "image_url": image.get("src") or "",
        "image_caption": image.get("caption") or "",
        "image_credit_url": image.get("url") or primary_page.get("url") or "",
        "date_label": date_label,
        "created_at": datetime.utcnow().isoformat(),
    }


def ensure_events() -> Dict[str, Any]:
    data = _load_data()
    if data["events"]:
        return data

    today = datetime.utcnow()
    date_label = f"{today.day:02d} {MONTH_NAMES_TR[today.month - 1]} {today.year}"
    fetched = fetch_today_events(limit=6)
    if not fetched:
        return data

    events = [_create_entry_from_event(event, date_label) for event in fetched]
    payload = {"last_refreshed": datetime.utcnow().isoformat(), "events": events}
    _save_data(payload)
    return payload


def _format_today() -> str:
    today = datetime.utcnow()
    return f"{today.day:02d} {MONTH_NAMES_TR[today.month - 1]} {today.year}"


def _is_authenticated() -> bool:
    return session.get("is_authenticated", False) is True


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not _is_authenticated():
            flash("Yönetim paneline erişmek için lütfen oturum açın.", "warning")
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)

    return wrapper


def _get_event(event_id: str) -> Optional[Dict[str, Any]]:
    data = _load_data()
    for item in data["events"]:
        if item.get("id") == event_id:
            return item
    return None


def _save_event(event: Dict[str, Any]) -> None:
    data = _load_data()
    events = data.get("events", [])
    existing_index = next((index for index, item in enumerate(events) if item.get("id") == event["id"]), None)

    if existing_index is None:
        events.append(event)
    else:
        events[existing_index] = event

    data["events"] = events
    data["last_refreshed"] = data.get("last_refreshed") or datetime.utcnow().isoformat()
    _save_data(data)


def _delete_event(event_id: str) -> None:
    data = _load_data()
    events = [item for item in data.get("events", []) if item.get("id") != event_id]
    data["events"] = events
    _save_data(data)


def _event_from_form(form: Dict[str, str], *, event_id: Optional[str] = None) -> Dict[str, Any]:
    event = _get_event(event_id) if event_id else None
    base: Dict[str, Any] = event.copy() if event else {"id": event_id or str(uuid4())}

    year_value = form.get("year", "").strip()
    year = None
    if year_value:
        try:
            year = int(year_value)
        except ValueError:
            year = None

    base.update(
        {
            "title": _normalise_whitespace(form.get("title", "")),
            "summary": _normalise_whitespace(form.get("summary", "")),
            "year": year,
            "category": form.get("category") or "events",
            "category_label": CATEGORY_LABELS.get(form.get("category"), form.get("category", "")),
            "source_url": form.get("source_url", "").strip(),
            "source_title": _normalise_whitespace(form.get("source_title", "")),
            "image_url": form.get("image_url", "").strip(),
            "image_caption": _normalise_whitespace(form.get("image_caption", "")),
            "image_credit_url": form.get("image_credit_url", "").strip(),
            "date_label": form.get("date_label", _format_today()),
            "created_at": event.get("created_at") if event else datetime.utcnow().isoformat(),
        }
    )
    return base


@app.route("/")
def home():
    data = ensure_events()
    events = sorted(data.get("events", []), key=lambda item: item.get("year") or 0, reverse=True)
    return render_template(
        "index.html",
        events=events,
        last_refreshed=data.get("last_refreshed"),
        last_refreshed_human=_format_timestamp(data.get("last_refreshed")),
        today_label=_format_today(),
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["is_authenticated"] = True
            flash("Hoş geldiniz! Yönetim paneline giriş yaptınız.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Kullanıcı adı veya şifre hatalı.", "danger")
    return render_template("admin/login.html")


@app.route("/admin/logout")
@login_required
def admin_logout():
    session.pop("is_authenticated", None)
    flash("Oturum kapatıldı.", "info")
    return redirect(url_for("home"))


@app.route("/admin")
@login_required
def admin_dashboard():
    data = _load_data()
    events = sorted(data.get("events", []), key=lambda item: item.get("year") or 0, reverse=True)
    return render_template(
        "admin/dashboard.html",
        events=events,
        last_refreshed=data.get("last_refreshed"),
        last_refreshed_human=_format_timestamp(data.get("last_refreshed")),
    )


@app.route("/admin/new", methods=["GET", "POST"])
@login_required
def admin_new():
    if request.method == "POST":
        event = _event_from_form(request.form)
        _save_event(event)
        flash("İçerik başarıyla eklendi.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template(
        "admin/edit.html", event=None, categories=CATEGORY_LABELS, today_label=_format_today()
    )


@app.route("/admin/<event_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit(event_id: str):
    event = _get_event(event_id)
    if not event:
        abort(404)

    if request.method == "POST":
        updated_event = _event_from_form(request.form, event_id=event_id)
        _save_event(updated_event)
        flash("İçerik güncellendi.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template(
        "admin/edit.html",
        event=event,
        categories=CATEGORY_LABELS,
        today_label=_format_today(),
    )


@app.route("/admin/<event_id>/delete", methods=["POST"])
@login_required
def admin_delete(event_id: str):
    event = _get_event(event_id)
    if not event:
        abort(404)

    _delete_event(event_id)
    flash("İçerik silindi.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/refresh", methods=["POST"])
@login_required
def admin_refresh():
    today = datetime.utcnow()
    date_label = f"{today.day:02d} {MONTH_NAMES_TR[today.month - 1]} {today.year}"
    fetched = fetch_today_events(limit=8)
    if not fetched:
        flash("Wikipedia verisi alınamadı. Daha sonra tekrar deneyin.", "danger")
        return redirect(url_for("admin_dashboard"))

    events = [_create_entry_from_event(event, date_label) for event in fetched]
    payload = {"last_refreshed": datetime.utcnow().isoformat(), "events": events}
    _save_data(payload)
    flash("Bugünün olayları başarıyla yenilendi.", "success")
    return redirect(url_for("admin_dashboard"))


@app.context_processor
def inject_utilities() -> Dict[str, Any]:
    return {"datetime": datetime}


if __name__ == "__main__":
    app.run(debug=True)
