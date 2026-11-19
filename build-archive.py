import html
import json
import re
from pathlib import Path

FALLBACK_IMAGE = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80"
CATEGORIES = {"morocco", "world", "economy", "technology", "sports"}
LEGACY_CATEGORIES = {
    "policy": "morocco",
    "general": "morocco",
    "business": "economy",
    "international": "world",
}


def clean(value):
    value = html.unescape(value or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def category_from(text, legacy_category=""):
    """Normalize legacy categories and classify article text into the five sections.

    Category-specific sections (sports, economy, technology) are recognized first.
    Moroccan policy and general-news signals then take precedence over international
    references, since Moroccan stories often mention foreign governments or bodies.
    """
    legacy = (legacy_category or "").strip().lower()
    if legacy in LEGACY_CATEGORIES:
        return LEGACY_CATEGORIES[legacy]
    if legacy in CATEGORIES and legacy != "world":
        return legacy

    text = clean(text).lower()

    if any(term in text for term in ("رياضة", "كرة", "sport", "football", "futsal")):
        return "sports"
    if any(term in text for term in ("اقتصاد", "اقتصادي", "business", "economy", "أسعار", "الأسواق")):
        return "economy"
    if any(term in text for term in ("تكنولوجيا", "تقنية", "technology", "ذكاء اصطناعي", "artificial intelligence")):
        return "technology"

    morocco_terms = (
        "المغرب", "مغربي", "المغربية", "مغربية", "morocco", "moroccan",
        "سياسة", "سياسي", "حكومة", "الملك", "ملك", "البرلمان", "وزير",
        "الصحراء", "policy",
    )
    if any(term in text for term in morocco_terms):
        return "morocco"

    world_terms = ("دولي", "العالم", "international", "world news", "global", "world")
    if any(term in text for term in world_terms):
        return "world"

    # Unspecified/general legacy stories belong to the site's Moroccan section.
    return "morocco"


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
