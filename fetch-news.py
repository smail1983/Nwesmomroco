import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

# NewsMorocco focuses on Moroccan news, with extra priority for breaking
# stories and Moroccan sports.
FEEDS = {
    "sports": [
        "عاجل الرياضة المغرب",
        "أخبار الرياضة المغرب",
        "عاجل المنتخب المغربي",
        "Morocco breaking sports",
        "Morocco football",
        "Raja Wydad Morocco football",
        "المنتخب المغربي كرة القدم",
        "Morocco sports"
    ],
    "general": [
        "عاجل المغرب",
        "آخر أخبار المغرب عاجل",
        "أخبار المغرب اليوم",
        "آخر أخبار المغرب",
        "Morocco breaking news",
        "Morocco latest news",
        "Morocco Maroc news"
    ],
    "business": [
        "عاجل اقتصاد المغرب",
        "أخبار الاقتصاد المغربي اليوم",
        "اقتصاد المغرب",
        "Morocco economy breaking news",
        "Morocco economy",
        "Morocco business"
    ],
    "technology": [
        "عاجل تكنولوجيا المغرب",
        "تكنولوجيا المغرب اليوم",
        "أخبار التكنولوجيا المغرب",
        "Morocco technology breaking news",
        "Morocco technology",
        "Morocco tech"
    ],
    "policy": [
        "عاجل السياسة المغرب",
        "أخبار سياسية المغرب اليوم",
        "سياسة المغرب عاجل",
        "Morocco politics breaking news",
        "Morocco politics",
        "Morocco government news"
    ]
}

SITE_URL = "https://nwesmomroco.com"
FALLBACK_IMAGE = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80"
RECENT_DAYS = 3


def fetch_feed(query):
    # Restrict Google News RSS results to recent stories so old archive
    # results cannot fill the homepage.
    query = f"{query} when:{RECENT_DAYS}d"
    params = urllib.parse.urlencode({
        "q": query,
        "hl": "ar",
        "gl": "MA",
        "ceid": "MA:ar"
    })
    url = "https://news.google.com/rss/search?" + params
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 NewsMorocco/3.0"}
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read()


def text_of(parent, tag):
    node = parent.find(tag)
    return (node.text or "").strip() if node is not None else ""


def clean_text(value):
    """Turn RSS HTML snippets into short readable Arabic text."""
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def clean_title(title, source):
    """Remove the repeated source suffix added by Google News RSS."""
    title = clean_text(title)
    source = clean_text(source)
    if source:
        patterns = [
            rf"\s*[|–—-]\s*{re.escape(source)}\s*$",
            rf"\s*[|–—-]\s*{re.escape(source.replace('https://', '').replace('http://', ''))}\s*$"
        ]
        for pattern in patterns:
            title = re.sub(pattern, "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"\s{2,}", " ", title)
    return title


def item_image(item):
    """Use an RSS image when the publisher exposes one; otherwise use the fallback."""
    for child in list(item):
        tag = child.tag.split("}")[-1].lower()
        if tag in {"content", "thumbnail", "enclosure"}:
            url = child.attrib.get("url") or child.attrib.get("href") or ""
            media_type = child.attrib.get("type", "")
            if url and ("image" in media_type or tag in {"content", "thumbnail"}):
                return url

    description = text_of(item, "description")
    match = re.search(r'<img[^>]+(?:src|url)=["\']([^"\']+)', description, flags=re.I)
    return match.group(1) if match else FALLBACK_IMAGE


def item_description(item, title, source):
    raw = clean_text(text_of(item, "description"))
    # Remove a repeated title/source prefix if the RSS feed includes it.
    if raw and raw != title:
        raw = raw.replace("Google News", "").strip(" -|–—")
    if not raw or raw.lower() == clean_text(source).lower():
        if source:
            return f"آخر المستجدات حول: {title}. المصدر: {source}."
        return f"آخر المستجدات حول: {title}."
    if source and raw.lower() == source.lower():
        return f"آخر المستجدات حول: {title}. المصدر: {source}."
    # Keep the homepage cards concise.
    return raw[:360].rstrip() + ("…" if len(raw) > 360 else "")


def is_recent(pub_date):
    try:
        dt = parsedate_to_datetime(pub_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= datetime.now(timezone.utc) - timedelta(days=RECENT_DAYS)
    except Exception:
        return False


# Keep a separate pool for each category so one topic cannot fill the whole feed.
articles_by_category = {category: [] for category in FEEDS}
seen = set()

for category, queries in FEEDS.items():
    category_seen = set()

    for query in queries:
        try:
            root = ET.fromstring(fetch_feed(query))
            for item in root.findall("./channel/item"):
                raw_title = text_of(item, "title")
                url = text_of(item, "link")
                pub_date = text_of(item, "pubDate")
                source_node = item.find("source")
                source = (source_node.text or "").strip() if source_node is not None and source_node.text else ""
                source_url = source_node.attrib.get("url", "") if source_node is not None else ""
                title = clean_title(raw_title, source)

                # Ignore empty, duplicate, source-only and stale RSS results.
                if not title or not url or not pub_date:
                    continue
                if len(title.strip()) < 25 or title.strip() == clean_text(source).strip():
                    continue
                if not is_recent(pub_date):
                    continue
                if url in seen or url in category_seen:
                    continue

                category_seen.add(url)
                seen.add(url)

                articles_by_category[category].append({
                    "category": category,
                    "title": title,
                    "description": item_description(item, title, source),
                    "image": item_image(item),
                    "url": url,
                    "domain": source,
                    "source_url": source_url,
                    "date": pub_date
                })
        except Exception as exc:
            print("Warning:", category, query, exc)

# Keep manually published NewsMorocco articles in the shared feed.
manual_articles = []
try:
    with open("manual-news.json", "r", encoding="utf-8") as f:
        loaded_manual = json.load(f)
        if isinstance(loaded_manual, list):
            manual_articles = [
                item for item in loaded_manual
                if isinstance(item, dict) and item.get("title") and item.get("url")
            ]
except FileNotFoundError:
    pass

manual_urls = {item.get("url") for item in manual_articles}

# Keep up to 20 automatically fetched stories per category.
articles = []
for category in FEEDS:
    items = articles_by_category[category]
    items.sort(key=lambda x: x.get("date", ""), reverse=True)
    articles.extend(items[:20])

# Remove anything already published manually.
generated_articles = [
    item for item in articles
    if item.get("url") not in manual_urls
]

# Keep a maximum of 80 stories while always retaining manual stories.
articles = manual_articles + generated_articles[:max(0, 80 - len(manual_articles))]
articles.sort(key=lambda x: x.get("date", ""), reverse=True)

if not articles:
    raise SystemExit("No news was fetched; deployment stopped to avoid an empty feed.")

with open("news.json", "w", encoding="utf-8") as f:
    json.dump({
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "articles": articles
    }, f, ensure_ascii=False, indent=2)


def build_sitemap():
    """Keep the sitemap focused on first-party pages, not external RSS URLs."""
    today = datetime.now(timezone.utc).date().isoformat()
    urls = [
        ("/", today),
        ("/articles", today),
        ("/about.html", today),
        ("/contact.html", today),
        ("/privacy.html", today),
        ("/terms.html", today),
        ("/disclaimer.html", today),
        ("/editorial-policy.html", today),
    ]

    for path in sorted(Path(".").glob("article-*.html")):
        urls.append((f"/{path.name}", today))

    rows = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for path, lastmod in urls:
        rows.append(f"  <url><loc>{SITE_URL}{path}</loc><lastmod>{lastmod}</lastmod></url>")
    rows.append("</urlset>")

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")


build_sitemap()
print("Fetched", len(articles), "articles.")
print("By category:", {k: len(v) for k, v in articles_by_category.items()})
print("Sitemap refreshed.")
