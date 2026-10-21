import html
import json
import re
from pathlib import Path

FALLBACK_IMAGE = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80"


def clean(value):
    value = html.unescape(value or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


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
        "category": category_from(meta + " " + title),
        "title": title,
        "description": description,
        "image": image,
        "url": "/" + path.name,
        "domain": "NewsMorocco",
        "date": meta,
    })

# Keep the archive stable and deterministic. The article files themselves are the source of truth.
archive.sort(key=lambda item: (item.get("date", ""), item.get("title", "")), reverse=True)
Path("articles-index.json").write_text(
    json.dumps(archive, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(f"Built permanent article archive: {len(archive)} article pages.")
