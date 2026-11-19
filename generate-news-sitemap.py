#!/usr/bin/env python3
"""Build a compliant Google News sitemap from the current news feed only.

Only items with a valid publication date within the last 48 hours are included.
Older permanent article pages remain in sitemap.xml and are not deleted.
"""
import json
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import xml.etree.ElementTree as ET

SITE_URL = "https://www.nwesmomroco.com"
NEWS_FILE = Path("news.json")
OUTPUT_FILE = Path("sitemap-news.xml")
PUBLISHER = "NewsMorocco"
LANGUAGE = "ar"
MAX_URLS = 1000
WINDOW = timedelta(hours=48)

SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
NEWS_NS = "http://www.google.com/schemas/sitemap-news/0.9"
ET.register_namespace("", SITEMAP_NS)
ET.register_namespace("news", NEWS_NS)


def parse_publication_date(value):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            return None


def escape_xml_text(value):
    return str(value or "").strip()


def article_url(article):
    value = article.get("local_url") or article.get("url") or ""
    if value.startswith("/"):
        return SITE_URL + value
    if value.startswith(SITE_URL + "/"):
        return value
    return ""


def build():
    if not NEWS_FILE.exists():
        raise SystemExit("news.json not found; refusing to overwrite the news sitemap.")

    data = json.loads(NEWS_FILE.read_text(encoding="utf-8"))
    articles = data.get("articles", []) if isinstance(data, dict) else []
    now = datetime.now(timezone.utc)
    cutoff = now - WINDOW
    eligible = []
    seen = set()

    for article in articles:
        if not isinstance(article, dict):
            continue
        title = escape_xml_text(article.get("title"))
        url = article_url(article)
        published = parse_publication_date(article.get("date"))
        if not title or not url or not published:
            continue
        if published < cutoff or published > now + timedelta(minutes=5):
            continue
        if url in seen:
            continue
        seen.add(url)
        eligible.append((published, title, url))

    eligible.sort(key=lambda row: row[0], reverse=True)
    eligible = eligible[:MAX_URLS]

    root = ET.Element(f"{{{SITEMAP_NS}}}urlset")
    for published, title, url in eligible:
        url_node = ET.SubElement(root, f"{{{SITEMAP_NS}}}url")
        loc = ET.SubElement(url_node, f"{{{SITEMAP_NS}}}loc")
        loc.text = url
        news_node = ET.SubElement(url_node, f"{{{NEWS_NS}}}news")
        publication = ET.SubElement(news_node, f"{{{NEWS_NS}}}publication")
        name = ET.SubElement(publication, f"{{{NEWS_NS}}}name")
        name.text = PUBLISHER
        language = ET.SubElement(publication, f"{{{NEWS_NS}}}language")
        language.text = LANGUAGE
        pub_date = ET.SubElement(news_node, f"{{{NEWS_NS}}}publication_date")
        pub_date.text = published.isoformat().replace("+00:00", "Z")
        news_title = ET.SubElement(news_node, f"{{{NEWS_NS}}}title")
        news_title.text = title

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
    print(f"Google News sitemap generated: {len(eligible)} recent articles (48-hour window).")


if __name__ == "__main__":
    build()
