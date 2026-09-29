import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# Google News RSS: no API key required.
# Morocco-focused queries, with extra emphasis on Moroccan sport.
FEEDS = {
    "sports": [
        "Morocco football",
        "Raja Wydad Morocco football",
        "Moroccan national team football",
        "Morocco sports"
    ],
    "general": [
        "Morocco Maroc news",
        "Morocco latest news"
    ],
    "business": [
        "Morocco economy",
        "Morocco business"
    ],
    "technology": [
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

articles = []
seen = set()

for category, queries in FEEDS.items():
    for query in queries:
        try:
            root = ET.fromstring(fetch_feed(query))
            for item in root.findall("./channel/item"):
                title = text_of(item, "title")
                url = text_of(item, "link")
                pub_date = text_of(item, "pubDate")
                source = text_of(item, "source")

                if not title or not url or url in seen:
                    continue

                seen.add(url)
                articles.append({
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

# Put Moroccan sports first, then the other categories.
articles.sort(key=lambda x: (x["category"] != "sports", x.get("date", "")))

if not articles:
    raise SystemExit("No news was fetched; deployment stopped to avoid an empty feed.")

with open("news.json", "w", encoding="utf-8") as f:
    json.dump({
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "articles": articles[:80]
    }, f, ensure_ascii=False, indent=2)

print("Fetched", len(articles), "articles.")
