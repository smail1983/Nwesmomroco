import html
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

FALLBACK_IMAGE = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80"


def clean(value):
    value = html.unescape(value or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def sortable_date(raw, meta):
    # Prefer the machine-readable NewsArticle date; use visible metadata only as fallback.
    match = re.search(r'"datePublished"\\s*:\\s*"([^"]+)"', raw, re.I)
    value = match.group(1) if match else meta
    if not value:
        return 0
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.timestamp()
        except (TypeError, ValueError, OverflowError):
            return 0


def category_from(text):
    text = text.lower()
    if "رياضة" in text or "sport" in text:
        return "sports"
    if "اقتصاد" in text or "business" in text:
        return "business"
    if "تكنولوجيا" in text or "تقنية" in text or "technology" in text:
        return "technology"
    if "سياسة" in text or "حكومة" in text or "صحراء" in text or "policy" in text:
        return "policy"
    return "general"


archive = []
for path in sorted(Path(".").glob("article-*.html")):
    raw = path.read_text(encoding="utf-8", errors="ignore")
    # Keep noindex pages out of the public archive so it does not promote thin pages.
    if re.search(r"<meta\\s+name=.robots.\\s+content=.[^>]*noindex", raw, re.I):
        continue
    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.I | re.S)
    if not title_match:
        title_match = re.search(r"<title[^>]*>(.*?)</title>", raw, re.I | re.S)
    title = clean(title_match.group(1)) if title_match else path.stem

    desc_match = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        raw, re.I | re.S
    )
    description = html.unescape(desc_match.group(1)).strip() if desc_match else ""

    image_match = re.search(r'<img[^>]+src=["\']([^"\']+)', raw, re.I | re.S)
    image = html.unescape(image_match.group(1)).strip() if image_match else FALLBACK_IMAGE

    meta_match = re.search(
        r'<(?:div|p)[^>]+class=["\'][^"\']*meta[^"\']*["\'][^>]*>(.*?)</(?:div|p)>',
        raw, re.I | re.S
    )
    meta = clean(meta_match.group(1)) if meta_match else ""

    archive.append({
        "_sort_date": sortable_date(raw, meta),
        "category": category_from(meta + " " + title),
        "title": title,
        "description": description,
        "image": image,
        "url": "/" + path.name,
        "domain": "NewsMorocco",
        "date": meta,
    })

# Sort by the actual publication timestamp, not the display string.
archive.sort(key=lambda item: (item.get("_sort_date", 0), item.get("title", "")), reverse=True)
for item in archive:
    item.pop("_sort_date", None)
Path("articles-index.json").write_text(
    json.dumps(archive, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(f"Built permanent article archive: {len(archive)} article pages.")
