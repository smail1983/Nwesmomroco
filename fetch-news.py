import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API="https://api.gdeltproject.org/api/v2/doc/doc"

queries={
    "sports":"Morocco football OR Morocco soccer OR Raja OR Wydad OR Moroccan football",
    "general":"Morocco OR Maroc",
    "business":"Morocco economy OR Morocco business",
    "technology":"Morocco technology OR Morocco tech"
}

fallback="https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80"

def fetch(query):
    params=urllib.parse.urlencode({
        "query":query,
        "mode":"artlist",
        "maxrecords":"18",
        "timespan":"2d",
        "format":"json",
        "sort":"datedesc"
    })
    with urllib.request.urlopen(API+"?"+params, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

articles=[]
seen=set()

for category, query in queries.items():
    try:
        data=fetch(query)
        for item in data.get("articles", []):
            url=item.get("url")
            title=item.get("title")
            if not url or not title or url in seen:
                continue
            seen.add(url)
            articles.append({
                "category":category,
                "title":title,
                "description":"المصدر: "+(item.get("domain") or "GDELT"),
                "image":item.get("socialimage") or fallback,
                "url":url,
                "domain":item.get("domain") or "",
                "date":item.get("seendate") or ""
            })
    except Exception as exc:
        print(f"Warning: {category}: {exc}")

with open("news.json","w",encoding="utf-8") as f:
    json.dump({
        "updated_at":datetime.now(timezone.utc).isoformat(),
        "articles":articles
    },f,ensure_ascii=False,indent=2)

if not articles:
    raise SystemExit("No news was fetched; keeping deployment from publishing an empty feed.")
print(f"Fetched {len(articles)} articles.")
