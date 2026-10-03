import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

FEEDS = {
    "sports": [
        "أخبار الرياضة المغرب",
        "Morocco football",
        "Raja Wydad Morocco football",
        "المنتخب المغربي كرة القدم",
        "Morocco sports"
    ],
    "general": [
        "أخبار المغرب",
        "آخر أخبار المغرب",
        "Morocco latest news",
        "Morocco Maroc news"
    ],
    "business": [
        "اقتصاد المغرب",
        "أخبار الاقتصاد المغربي",
        "Morocco economy",
        "Morocco business"
    ],
    "technology": [
        "تكنولوجيا المغرب",
        "أخبار التكنولوجيا المغرب",
        "Morocco technology",
        "Morocco tech"
    ]
}

FALLBACK_IMAGE = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80"

def fetch_feed(query):
    params = urllib.parse.urlencode({
        "q": query,
        "hl": "ar",
        "gl": "MA",
        "ceid": "MA:ar"
    })
    url = "https://news.google.com/rss/search?" + params
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 NewsMorocco/1.0"}
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read()

def text_of(parent, tag):
    node = parent.find(tag)
    return (node.text or "").strip() if node is not None else ""

# Keep a separate pool for each category so sports cannot fill all 80 slots.
articles_by_category = {category: [] for category in FEEDS}
seen = set()

for category, queries in FEEDS.items():
    category_seen = set()

    for query in queries:
        try:
            root = ET.fromstring(fetch_feed(query))
            for item in root.findall("./channel/item"):
                title = text_of(item, "title")
                url = text_of(item, "link")
                pub_date = text_of(item, "pubDate")
                source = text_of(item, "source")

                if not title or not url or url in seen or url in category_seen:
                    continue

                category_seen.add(url)
                seen.add(url)

                articles_by_category[category].append({
                    "category": category,
                    "title": title,
                    "description": "المصدر: " + (source or "Google News"),
                    "image": FALLBACK_IMAGE,
                    "url": url,
                    "domain": source,
                    "date": pub_date
                })
        except Exception as exc:
            print("Warning:", category, query, exc)

# Keep manually published articles in the shared feed.
# Both the website and the app read news.json, so these items must survive
# every automatic refresh.
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

# Maximum 20 automatically fetched articles per category, then add the
# manually published articles without allowing duplicate URLs.
articles = []
for category in FEEDS:
    items = articles_by_category[category]
    items.sort(key=lambda x: x.get("date", ""), reverse=True)
    articles.extend(items[:20])

generated_urls = {item.get("url") for item in articles}
articles = manual_articles + [
    item for item in articles
    if item.get("url") not in manual_urls and item.get("url") not in generated_urls.intersection(manual_urls)
]

# Keep newest items first while ensuring every manually published item is retained.
generated_articles = [
    item for item in articles
    if item.get("url") not in manual_urls
]
articles = manual_articles + generated_articles[:max(0, 80 - len(manual_articles))]
articles.sort(key=lambda x: x.get("date", ""), reverse=True)

if not articles:
    raise SystemExit("No news was fetched; deployment stopped to avoid an empty feed.")

with open("news.json", "w", encoding="utf-8") as f:
    json.dump({
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "articles": articles
    }, f, ensure_ascii=False, indent=2)

print("Fetched", len(articles), "articles.")
print("By category:", {k: len(v) for k, v in articles_by_category.items()})
