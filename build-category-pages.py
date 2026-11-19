import json, html
from pathlib import Path
from email.utils import parsedate_to_datetime
from datetime import datetime
SITE="https://www.nwesmomroco.com"
DEFS={
 "politics":("السياسة المغربية","آخر أخبار السياسة المغربية، الحكومة، القرارات، والدبلوماسية.",{"policy"}),
 "morocco":("أخبار المغرب","آخر الأخبار المغربية من مختلف المجالات.",{"policy","general",""}),
 "business":("الاقتصاد","أخبار الاقتصاد المغربي، الأسواق، الأعمال، والاستثمار.",{"business"}),
 "technology":("التكنولوجيا","آخر أخبار التكنولوجيا والذكاء الاصطناعي والابتكار.",{"technology"}),
 "sports":("الرياضة","أخبار الرياضة المغربية والمنتخبات والأندية.",{"sports"}),
}
def e(v): return html.escape(str(v or ""),quote=True)
def load():
 n=json.loads(Path("news.json").read_text(encoding="utf-8"))
 m=json.loads(Path("manual-news.json").read_text(encoding="utf-8"))
 items=(n.get("articles",[]) if isinstance(n,dict) else n)+(m if isinstance(m,list) else [])
 seen=set(); result=[]
 for a in items:
  k=a.get("local_url") or a.get("url") or a.get("title")
  if k not in seen: seen.add(k); result.append(a)
 return result
def href(a):
 u=a.get("local_url") or a.get("url") or "#"
 return u if u.startswith("/") or u.startswith("http") else "/'+u
def image(a):
 u=a.get("image") or SITE+"/news-morocco-og-1200x630.png"
 return u if u.startswith("http") else "/"+u.lstrip("/")
def build():
 articles=load()
 for slug,(title,description,cats) in DEFS.items():
  selected=[a for a in articles if (a.get("category") or "") in cats]
  def sortdate(a):
   try:return parsedate_to_datetime(a.get("date",""))
   except:return datetime.min
  selected.sort(key=sortdate,reverse=True)
  url=SITE+"/category/"+slug+"/"
  breadcrumb={"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"الرئيسية","item":SITE+"/"},{"@type":"ListItem","position":2,"name":title,"item":url}]}
  cards=[]
  for a in selected:
   d=a.get("date","")
   cards.append('<article class="card"><a href="'+e(href(a))+'"><img src="'+e(image(a))+'" alt="'+e(a.get("title"))+'" loading="lazy"><div class="body"><h2>'+e(a.get("title"))+'</h2><p>'+e(a.get("description"))+'</p><time class="date" datetime="'+e(d)+'">'+e(d)+'</time></div></a></article>')
  page='''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>'''+e(title)+''' | NewsMorocco</title><meta name="description" content="'''+e(description)+'''"><link rel="canonical" href="'''+url+'''">
<meta property="og:type" content="website"><meta property="og:url" content="'''+url+'''"><meta property="og:title" content="'''+e(title)+''' | NewsMorocco"><meta property="og:description" content="'''+e(description)+'''">
<meta property="og:image" content="'''+SITE+'''/news-morocco-og-1200x630.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="'''+e(title)+''' | NewsMorocco"><meta name="twitter:description" content="'''+e(description)+'''"><meta name="twitter:image" content="'''+SITE+'''/news-morocco-og-1200x630.png">
<script type="application/ld+json">'''+json.dumps(breadcrumb,ensure_ascii=False)+'''</script>
<style>body{margin:0;background:#f5f7f9;color:#17212b;font-family:Arial,sans-serif;line-height:1.8}header{background:#17212b;color:white;text-align:center;padding:16px}header a{color:white;text-decoration:none}nav{display:flex;flex-wrap:wrap;justify-content:center;gap:10px;background:white;padding:12px}nav a{color:#087f5b;text-decoration:none}main{max-width:1100px;margin:22px auto;padding:0 14px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}.card{background:white;border-radius:14px;overflow:hidden;box-shadow:0 2px 12px #0001}.card a{color:inherit;text-decoration:none}.card img{width:100%;height:190px;object-fit:cover}.body{padding:14px}.date{font-size:13px;color:#667}</style></head><body><header><a href="/">NewsMorocco — نبض المغرب والعالم</a></header>
<nav><a href="/">الرئيسية</a><a href="/category/politics/">سياسة</a><a href="/category/morocco/">أخبار المغرب</a><a href="/category/business/">اقتصاد</a><a href="/category/technology/">تكنولوجيا</a><a href="/category/sports/">رياضة</a></nav>
<main><h1>'''+e(title)+'''</h1><p>'''+e(description)+'''</p><div class="grid">'''+chr(10).join(cards)+'''</div></main></body></html>'''
  p=Path("category")/slug/"index.html"; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(page,encoding="utf-8")
  print(f"Built {p}: {len(selected)} news cards")
if __name__=="__main__":build()
