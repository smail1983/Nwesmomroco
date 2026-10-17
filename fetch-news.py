import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
import hashlib

# NewsMorocco focuses on Moroccan news, with extra priority for breaking
# stories and Moroccan sports.
FEEDS = {
    "sports": [
        "عاجل الرياضة المغرب", "أخبار الرياضة المغرب", "عاجل المنتخب المغربي",
        "Morocco breaking sports", "Morocco football", "Raja Wydad Morocco football",
        "المنتخب المغربي كرة القدم", "Morocco sports"
    ],
    "general": [
        "عاجل المغرب", "آخر أخبار المغرب عاجل", "أخبار المغرب اليوم", "آخر أخبار المغرب",
        "Morocco breaking news", "Morocco latest news", "Morocco Maroc news"
    ],
    "business": [
        "عاجل اقتصاد المغرب", "أخبار الاقتصاد المغربي اليوم", "اقتصاد المغرب",
        "Morocco economy breaking news", "Morocco economy", "Morocco business"
    ],
    "technology": [
        "عاجل تكنولوجيا المغرب", "تكنولوجيا المغرب اليوم", "أخبار التكنولوجيا المغرب",
        "Morocco technology breaking news", "Morocco technology", "Morocco tech"
    ],
    "policy": [
        "عاجل السياسة المغرب", "أخبار سياسية المغرب اليوم", "سياسة المغرب عاجل",
        "Morocco politics breaking news", "Morocco politics", "Morocco government news"
    ]
}

SITE_URL = "https://nwesmomroco.com"
FALLBACK_IMAGE = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80"
RECENT_DAYS = 3


def fetch_feed(query):
    query = f"{query} when:{RECENT_DAYS}d"
    params = urllib.parse.urlencode({"q": query, "hl": "ar", "gl": "MA", "ceid": "MA:ar"})
    url = "https://news.google.com/rss/search?" + params
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 NewsMorocco/4.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read()


def text_of(parent, tag):
    node = parent.find(tag)
    return (node.text or "").strip() if node is not None else ""


def clean_text(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def clean_title(title, source):
    title = clean_text(title)
    source = clean_text(source)
    if source:
        patterns = [rf"\s*[|–—-]\s*{re.escape(source)}\s*$"]
        for pattern in patterns:
            title = re.sub(pattern, "", title, flags=re.IGNORECASE).strip()
    return re.sub(r"\s{2,}", " ", title)


def item_image(item):
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
    raw = raw.replace("Google News", "").strip(" -|–—")
    if not raw or raw.lower() == clean_text(source).lower():
        return f"آخر المستجدات حول: {title}."
    return raw[:360].rstrip() + ("…" if len(raw) > 360 else "")


def is_recent(pub_date):
    try:
        dt = parsedate_to_datetime(pub_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= datetime.now(timezone.utc) - timedelta(days=RECENT_DAYS)
    except Exception:
        return False


def local_article_name(title):
    # Stable first-party URL for every automatically collected story.
    digest = hashlib.sha1(title.encode("utf-8")).hexdigest()[:12]
    return f"article-{digest}.html"


def esc(value):
    return html.escape(str(value or ""), quote=True)


def write_article_page(article):
    path = Path(article["local_url"].lstrip("/"))
    title = article["title"]
    description = article.get("description") or f"آخر المستجدات حول: {title}."
    image = article.get("image") or FALLBACK_IMAGE
    source = article.get("domain") or "المصدر الأصلي"
    source_link = article.get("url") or "#"
    date_value = article.get("date", "")
    try:
        published = parsedate_to_datetime(date_value).astimezone(timezone.utc).isoformat()
    except Exception:
        published = date_value

    # This is a concise NewsMorocco summary, not a copy of the publisher's full article.
    content = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)} | NewsMorocco</title>
<meta name="description" content="{esc(description[:155])}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{SITE_URL}/{path.name}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="NewsMorocco">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description[:200])}">
<meta property="og:image" content="{esc(image)}">
<script type="application/ld+json">
{json.dumps({
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": title,
    "description": description,
    "image": [image],
    "datePublished": published,
    "dateModified": published,
    "author": {"@type": "Organization", "name": "NewsMorocco"},
    "publisher": {"@type": "Organization", "name": "NewsMorocco", "url": SITE_URL},
    "mainEntityOfPage": {"@type": "WebPage", "@id": f"{SITE_URL}/{path.name}"}
}, ensure_ascii=False, indent=2)}
</script>
<style>
body{{margin:0;background:#f5f7f9;color:#17212b;font-family:Arial,sans-serif;line-height:1.9}}
header{{background:#17212b;padding:16px;text-align:center}} header a{{color:#fff;text-decoration:none;font-weight:700;font-size:22px}}
main{{max-width:820px;margin:25px auto;padding:0 16px}} article{{background:#fff;border-radius:16px;padding:22px;box-shadow:0 3px 15px rgba(0,0,0,.07)}}
h1{{font-size:30px;line-height:1.5;margin-top:0}} .meta{{color:#777;font-size:14px;margin-bottom:18px}}
.hero{{width:100%;max-height:480px;object-fit:cover;border-radius:12px}} .summary{{font-size:19px;margin:22px 0}}
.source{{display:inline-block;background:#17212b;color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none}}
.back{{display:inline-block;margin-top:18px;color:#1769aa;text-decoration:none}}
@media(max-width:600px){{h1{{font-size:23px}} .summary{{font-size:17px}}}}
</style>
</head>
<body>
<header><a href="/">NewsMorocco</a></header>
<main><article>
<h1>{esc(title)}</h1>
<div class="meta">{esc(source)}{(' • ' + esc(date_value)) if date_value else ''}</div>
<img class="hero" src="{esc(image)}" alt="{esc(title)}" loading="eager">
<p class="summary">{esc(description)}</p>
<p>تقدم NewsMorocco هذا الملخص الإخباري اعتماداً على المعلومات المتاحة في المصدر الأصلي، مع الحفاظ على رابط المصدر للرجوع إلى التفاصيل الكاملة.</p>
<a class="source" href="{esc(source_link)}" target="_blank" rel="noopener noreferrer nofollow">قراءة التفاصيل من المصدر الأصلي</a>
<br><a class="back" href="/">← العودة إلى آخر الأخبار</a>
</article></main>
</body></html>
'''
    path.write_text(content, encoding="utf-8")


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
                if not title or not url or not pub_date:
                    continue
                if len(title.strip()) < 25 or title.strip() == clean_text(source).strip():
                    continue
                if not is_recent(pub_date) or url in seen or url in category_seen:
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

manual_articles = []
try:
    with open("manual-news.json", "r", encoding="utf-8") as f:
        loaded_manual = json.load(f)
        if isinstance(loaded_manual, list):
            manual_articles = [item for item in loaded_manual if isinstance(item, dict) and item.get("title") and item.get("url")]
except FileNotFoundError:
    pass

manual_urls = {item.get("url") for item in manual_articles}
articles = []
for category in FEEDS:
    items = articles_by_category[category]
    items.sort(key=lambda x: x.get("date", ""), reverse=True)
    articles.extend(items[:20])

generated_articles = [item for item in articles if item.get("url") not in manual_urls]
articles = manual_articles + generated_articles[:max(0, 80 - len(manual_articles))]
articles.sort(key=lambda x: x.get("date", ""), reverse=True)

if not articles:
    raise SystemExit("No news was fetched; deployment stopped to avoid an empty feed.")

# Give automatic stories a first-party NewsMorocco page and generate the page now.
for article in articles:
    if article.get("url") not in manual_urls:
        article["local_url"] = "/" + local_article_name(article["title"])
        write_article_page(article)

with open("news.json", "w", encoding="utf-8") as f:
    json.dump({"updated_at": datetime.now(timezone.utc).isoformat(), "articles": articles}, f, ensure_ascii=False, indent=2)


def build_sitemap():
    today = datetime.now(timezone.utc).date().isoformat()
    urls = [
        ("/", today), ("/articles", today), ("/about.html", today),
        ("/contact.html", today), ("/privacy.html", today), ("/terms.html", today),
        ("/disclaimer.html", today), ("/editorial-policy.html", today)
    ]
    for path in sorted(Path(".").glob("article-*.html")):
        urls.append((f"/{path.name}", today))
    rows = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, lastmod in urls:
        rows.append(f"  <url><loc>{SITE_URL}{path}</loc><lastmod>{lastmod}</lastmod></url>")
    rows.append("</urlset>")
    Path("sitemap.xml").write_text("\n".join(rows) + "\n", encoding="utf-8")


build_sitemap()
print("Fetched", len(articles), "articles and generated first-party article pages.")
print("By category:", {k: len(v) for k, v in articles_by_category.items()})
print("Sitemap refreshed.")
