import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

# Canonical category keys used by news.json and every generated article page.
FEEDS = {
    "morocco": [
        "عاجل المغرب سياسة حكومة ملك", "أخبار المغرب اليوم سياسة", "البرلمان المغربي اليوم",
        "الحكومة المغربية اليوم", "Morocco politics breaking news", "Morocco government news",
        "عاجل المغرب", "آخر أخبار المغرب اليوم", "أخبار المغرب اليوم عاجل",
        "Morocco breaking news today", "Morocco latest news",
    ],
    "world": [
        "عاجل العالم اليوم", "أهم الأخبار الدولية اليوم", "international breaking news today",
        "world breaking news today", "Reuters world breaking news",
    ],
    "economy": [
        "عاجل اقتصاد المغرب اليوم", "اقتصاد المغرب اليوم", "الأسواق المغرب اليوم",
        "Morocco economy breaking news", "Morocco business today",
    ],
    "technology": [
        "عاجل الذكاء الاصطناعي اليوم", "أخبار الذكاء الاصطناعي AI اليوم", "تكنولوجيا اليوم",
        "الذكاء الاصطناعي المغرب", "AI breaking news", "artificial intelligence latest news",
        "technology breaking news",
    ],
    "sports": [
        "عاجل الرياضة المغرب", "المنتخب المغربي اليوم", "كرة القدم المغربية اليوم",
        "الرجاء الوداد الجيش الملكي المغرب", "Morocco football breaking", "Morocco sports today",
    ],
}
NORMALIZED_CATEGORIES = set(FEEDS)
LEGACY_CATEGORY_MAP = {
    "policy": "morocco",
    "general": "morocco",
    "business": "economy",
    "international": "world",
}

SITE_URL = "https://www.nwesmomroco.com"
FALLBACK_IMAGE = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80"
RECENT_DAYS = 2
TRUSTED_SOURCES = {
    "reuters", "associated press", "ap", "afp", "bbc", "al jazeera", "france 24",
    "snrt", "map", "maghress", "hespress", "le360", "telquel", "medias24",
    "2m", "alyaoum24", "h24info", "le matin", "assabah", "l economiste",
    "morocco world news", "the guardian", "financial times", "bloomberg", "cnn",
    "dw", "euronews", "politico", "the associated press",
}
RUMOR_TERMS = re.compile(
    r"شائعة|إشاعة|غير مؤكد|لم يتأكد|قد يكون|يُعتقد|يعتقد|ربما|أنباء غير مؤكدة|مصدر مجهول|"
    r"rumou?r|unconfirmed|alleged|allegedly|speculation|possibly|may have",
    re.IGNORECASE,
)
URGENT_TERMS = re.compile(r"عاجل|آخر الأخبار|breaking|urgent|latest|now|today", re.IGNORECASE)
MOROCCO_TERMS = re.compile(
    r"المغرب|مغربي|مغربية|المغربية|morocco|moroccan|سياسة|سياسي|حكومة|الملك|ملك|"
    r"البرلمان|وزير|الصحراء|policy",
    re.IGNORECASE,
)
SPORTS_TERMS = re.compile(r"رياضة|كرة|الوداد|الرجاء|المنتخب|كأس|مباراة|لاعب|فيفا|كاف|sport|football|futsal", re.I)
ECONOMY_TERMS = re.compile(r"اقتصاد|اقتصادي|business|economy|أسعار|الأسواق|استثمار|ميزانية", re.I)
TECH_TERMS = re.compile(r"تكنولوجيا|تقنية|technology|ذكاء اصطناعي|artificial intelligence", re.I)
WORLD_TERMS = re.compile(r"دولي|العالم|international|world news|global|world", re.I)


def normalize_category(category, title="", description=""):
    """Return a canonical key; Moroccan stories outrank international references."""
    legacy = str(category or "").strip().lower()
    if legacy in LEGACY_CATEGORY_MAP:
        category = LEGACY_CATEGORY_MAP[legacy]
    elif legacy in NORMALIZED_CATEGORIES:
        category = legacy
    else:
        category = ""

    text = f"{title or ''} {description or ''}"
    if category == "world" and MOROCCO_TERMS.search(text):
        return "morocco"
    if category:
        return category

    if SPORTS_TERMS.search(text):
        return "sports"
    if ECONOMY_TERMS.search(text):
        return "economy"
    if TECH_TERMS.search(text):
        return "technology"
    if MOROCCO_TERMS.search(text):
        return "morocco"
    if WORLD_TERMS.search(text):
        return "world"
    return "morocco"


def fetch_feed(query):
    query = f"{query} when:{RECENT_DAYS}d"
    params = urllib.parse.urlencode({"q": query, "hl": "ar", "gl": "MA", "ceid": "MA:ar"})
    request = urllib.request.Request(
        "https://news.google.com/rss/search?" + params,
        headers={"User-Agent": "Mozilla/5.0 NewsMorocco/5.0"},
    )
    with urllib.request.urlopen(request, timeout=25) as response:
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
        title = re.sub(rf"\s*[|–—-]\s*{re.escape(source)}\s*$", "", title, flags=re.IGNORECASE).strip()
    return re.sub(r"\s{2,}", " ", title)


def source_is_trusted(source):
    normalized = clean_text(source).lower()
    return any(name in normalized for name in TRUSTED_SOURCES)


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
    except (TypeError, ValueError, OverflowError):
        return False


def article_score(article):
    score = 12 if source_is_trusted(article.get("domain", "")) else -6
    title = article.get("title", "")
    if URGENT_TERMS.search(title):
        score += 5
    if RUMOR_TERMS.search(title):
        score -= 30
    score += {"morocco": 10, "sports": 9, "technology": 8, "economy": 5, "world": 5}.get(
        normalize_category(article.get("category"), title, article.get("description", "")), 0
    )
    return score


def local_article_name(title):
    digest = hashlib.sha1(title.encode("utf-8")).hexdigest()[:12]
    return f"article-{digest}.html"


def esc(value):
    return html.escape(str(value or ""), quote=True)


def write_article_page(article):
    path = Path(article["local_url"].lstrip("/"))
    title = clean_text(article.get("title", ""))
    description = clean_text(article.get("description") or "")
    source = clean_text(article.get("domain") or "المصدر الأصلي")
    source_link = article.get("url") or "#"
    image = article.get("image") or FALLBACK_IMAGE
    category = normalize_category(article.get("category"), title, description)
    article["category"] = category

    if description.lower().startswith(title.lower()):
        description = description[len(title):].strip(" .:-–—|")
    if not description:
        description = f"لا تتوفر في المقتطفات الحالية تفاصيل كافية حول: {title}."

    raw_date = article.get("date", "")
    try:
        parsed = parsedate_to_datetime(raw_date)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        published = parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        published = datetime.now(timezone.utc).isoformat()

    indexable = len(description) >= 180
    robots = "index, follow, max-image-preview:large" if indexable else "noindex, follow"
    modified = published  # Keep dateModified stable unless article content is actually revised.
    page_url = f"{SITE_URL}/{path.name}"
    schema = {
        "@context": "https://schema.org", "@type": "NewsArticle", "headline": title,
        "description": description[:300], "image": [image], "datePublished": published,
        "dateModified": modified, "inLanguage": "ar", "articleSection": category,
        "author": {"@type": "Organization", "name": "NewsMorocco", "url": SITE_URL},
        "publisher": {"@type": "Organization", "name": "NewsMorocco", "url": SITE_URL},
        "mainEntityOfPage": {"@type": "WebPage", "@id": page_url},
    }
    content = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)} | NewsMorocco</title>
<meta name="description" content="{esc(description[:155] or title)}">
<meta name="robots" content="{robots}">
<meta name="author" content="NewsMorocco">
<link rel="canonical" href="{esc(page_url)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="NewsMorocco">
<meta property="og:url" content="{esc(page_url)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description[:200] or title)}">
<meta property="og:image" content="{esc(image)}">
<meta property="article:published_time" content="{esc(published)}">
<meta property="article:modified_time" content="{esc(modified)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description[:200] or title)}">
<meta name="twitter:image" content="{esc(image)}">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f5f7f9;color:#17212b;font-family:Arial,sans-serif;line-height:1.9}}
header{{background:#17212b;padding:16px;text-align:center}}header a{{color:#fff;text-decoration:none;font-weight:700;font-size:22px}}
main{{max-width:820px;margin:25px auto;padding:0 16px}}article{{background:#fff;border-radius:16px;padding:22px;box-shadow:0 3px 15px rgba(0,0,0,.07)}}
h1{{font-size:30px;line-height:1.5;margin-top:0}}.meta{{color:#777;font-size:14px;margin-bottom:18px}}
.hero{{width:100%;max-height:480px;object-fit:cover;border-radius:12px}}.summary{{font-size:19px;margin:22px 0;white-space:pre-line}}
.source{{display:inline-block;background:#17212b;color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none}}
.notice{{background:#f4f6f8;border-right:4px solid #087f5b;padding:12px 15px;border-radius:8px;color:#475467}}
.back{{display:inline-block;margin-top:18px;color:#1769aa;text-decoration:none}}@media(max-width:600px){{h1{{font-size:23px}}.summary{{font-size:17px}}}}
</style>
</head>
<body><header><a href="/">NewsMorocco</a></header><main><article>
<h1>{esc(title)}</h1><div class="meta">{esc(source)}{(" • " + esc(raw_date)) if raw_date else ""}</div>
<img class="hero" src="{esc(image)}" alt="{esc(title)}" loading="eager"><h2>ملخص الخبر</h2>
<p class="summary">{esc(description)}</p>
<p class="notice">للاطلاع على التفاصيل الكاملة والتصريحات الأصلية، يرجى الرجوع إلى المصدر المذكور أدناه.</p>
<a class="source" href="{esc(source_link)}" target="_blank" rel="noopener noreferrer nofollow">قراءة المصدر الأصلي: {esc(source)}</a>
<br><a class="back" href="/">← العودة إلى آخر الأخبار</a>
</article></main></body></html>'''
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
                if not title or not url or not pub_date or len(title.strip()) < 25 or title.strip() == clean_text(source).strip():
                    continue
                if RUMOR_TERMS.search(title) or not is_recent(pub_date) or url in seen or url in category_seen:
                    continue
                if not source_is_trusted(source):
                    continue
                description = item_description(item, title, source)
                normalized_category = normalize_category(category, title, description)
                category_seen.add(url)
                seen.add(url)
                articles_by_category[normalized_category].append({
                    "category": normalized_category, "title": title, "description": description,
                    "image": item_image(item), "url": url, "domain": source,
                    "source_url": source_url, "date": pub_date,
                })
        except Exception as exc:
            print("Warning:", category, query, exc)

manual_articles = []
try:
    with open("manual-news.json", "r", encoding="utf-8") as f:
        loaded_manual = json.load(f)
        if isinstance(loaded_manual, list):
            manual_articles = [
                {**item, "category": normalize_category(item.get("category"), item.get("title", ""), item.get("description", ""))}
                for item in loaded_manual
                if isinstance(item, dict) and item.get("title") and item.get("url")
            ]
except FileNotFoundError:
    pass

manual_urls = {item.get("url") for item in manual_articles}
articles = []
for category in FEEDS:
    items = articles_by_category[category]
    items.sort(key=lambda x: (article_score(x), x.get("date", "")), reverse=True)
    articles.extend(items[:20])

generated_articles = [item for item in articles if item.get("url") not in manual_urls]
articles = manual_articles + generated_articles[:max(0, 80 - len(manual_articles))]
for article in articles:
    article["category"] = normalize_category(article.get("category"), article.get("title", ""), article.get("description", ""))
articles.sort(key=lambda x: (article_score(x), x.get("date", "")), reverse=True)

if not articles:
    raise SystemExit("No trusted news was fetched; deployment stopped to avoid an empty feed.")

for article in articles:
    if article.get("url") not in manual_urls:
        article["local_url"] = "/" + local_article_name(article["title"])
        write_article_page(article)

with open("news.json", "w", encoding="utf-8") as f:
    json.dump({"updated_at": datetime.now(timezone.utc).isoformat(), "articles": articles}, f, ensure_ascii=False, indent=2)


def build_sitemap():
    # Do not stamp every unchanged page with today's date; omit lastmod until
    # reliable per-page modification tracking is available.
    urls = ["/", "/articles/", "/about.html", "/contact.html", "/editorial-policy.html"]
    for path in sorted(Path(".").glob("article-*.html")):
        page = path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r'<meta\s+name=["\']robots["\']\s+content=["\']noindex', page, re.IGNORECASE):
            continue
        urls.append(f"/{path.name}")
    rows = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path in urls:
        rows.append(f"  <url><loc>{SITE_URL}{path}</loc></url>")
    rows.append("</urlset>")
    Path("sitemap.xml").write_text("\n".join(rows) + "\n", encoding="utf-8")

build_sitemap()
print("Fetched", len(articles), "trusted articles and generated first-party pages.")
print("By category:", {key: len(value) for key, value in articles_by_category.items()})
print("Sitemap refreshed.")
