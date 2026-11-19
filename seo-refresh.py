from pathlib import Path
from datetime import datetime, timezone
import html, json, re, unicodedata
SITE="https://www.nwesmomroco.com"; TODAY=datetime.now(timezone.utc).date().isoformat()
FALLBACK=SITE+"/news-og-1200x630.jpg"
paths=sorted(Path(".").glob("article-*.html"))
def clean(s): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",s or ""))).strip()
def title(raw,path):
 m=re.search(r"<h1[^>]*>(.*?)</h1>",raw,re.I|re.S) or re.search(r"<title[^>]*>(.*?)</title>",raw,re.I|re.S)
 return clean(m.group(1)) if m else path.stem
def desc(raw,t):
 m=re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',raw,re.I|re.S) or re.search(r'<p[^>]+class=["\']summary["\'][^>]*>(.*?)</p>',raw,re.I|re.S)
 d=clean(m.group(1)) if m else t
 d=d.replace(t,"").strip(" -|")
 if len(d)<60:d=t+" — آخر الأخبار والتفاصيل من NewsMorocco."
 if len(d)>160:d=d[:157].rsplit(" ",1)[0].rstrip(" .،")+"…"
 while len(d)<140:
  d+=" تابع آخر أخبار المغرب والعالم على NewsMorocco."
  d=d[:160]
 return d[:160]
def slug(t):
 s=unicodedata.normalize("NFKC",t).lower()
 s=re.sub(r"[^\w\u0600-\u06ff]+","-",s,flags=re.UNICODE).strip("-")
 return s[:90].strip("-") or "news"
def cat(raw,t):
 s=(raw+" "+t).lower()
 for c,rx in [("sports",r"رياض|كرة|منتخب|كأس|لاعب|مباراة"),("business",r"اقتصاد|استثمار|أسعار|سوق|درهم"),("technology",r"تقنية|تكنولوجيا|ذكاء اصطناعي|رقمي"),("policy",r"سياسة|ملك|الحكومة|وزير|برلمان|صحراء|الأمم المتحدة")]:
  if re.search(rx,s):return c
 return "general"
def ogimg(raw):
 m=re.search(r'<img[^>]+src=["\']([^"\']+)["\']',raw,re.I)
 im=html.unescape(m.group(1)) if m else FALLBACK
 return FALLBACK if im.lower().endswith(".svg") else im
def add_related(raw,c,current):
 related=[]
 for p in paths:
  if p==current:continue
  r=p.read_text(encoding="utf-8",errors="ignore"); h=re.search(r"<h1[^>]*>(.*?)</h1>",r,re.I|re.S)
  t=clean(h.group(1)) if h else ""
  if t and cat(r,t)==c:related.append((p,t))
  if len(related)==3:break
 if len(related)<3:
  for p in paths:
   if p==current or any(x[0]==p for x in related):continue
   r=p.read_text(encoding="utf-8",errors="ignore");h=re.search(r"<h1[^>]*>(.*?)</h1>",r,re.I|re.S)
   t=clean(h.group(1)) if h else ""
   if t:related.append((p,t))
   if len(related)==3:break
 block='<section class="related-articles"><h2>مقالات ذات صلة</h2><ul>'+''.join('<li><a href="/'+p.name+'">'+html.escape(t)+'</a></li>' for p,t in related)+'</ul></section>'
 if 'related-articles' in raw:return re.sub(r'<section class="related-articles">.*?</section>',block,raw,flags=re.I|re.S)
 return raw.replace("</article>",block+"</article>",1)
mapping={}
for p in paths:
 r=p.read_text(encoding="utf-8",errors="ignore");t=title(r,p)
 new="article-"+slug(t)+".html"
 if new==p.name:continue
 if Path(new).exists():new="article-"+slug(t)+"-"+p.stem[-6:]+".html"
 mapping[p.name]=new
for p in paths:
 raw=p.read_text(encoding="utf-8",errors="ignore");t=title(raw,p);d=desc(raw,t);c=cat(raw,t)
 new=mapping.get(p.name,p.name);url=SITE+"/"+new;pub=TODAY+"T00:00:00Z";modified=pub;image=ogimg(raw)
 schema={"@context":"https://schema.org","@type":"NewsArticle","headline":t,"description":d,"image":[image],"datePublished":pub,"dateModified":modified,"author":{"@type":"Organization","name":"NewsMorocco"},"publisher":{"@type":"Organization","name":"NewsMorocco"},"mainEntityOfPage":{"@type":"WebPage","@id":url}}
 raw=re.sub(r"<title[^>]*>.*?</title>","",raw,flags=re.I|re.S)
 raw=re.sub(r'<meta[^>]+name=["\']description["\'][^>]*>',"",raw,flags=re.I|re.S)
 raw=re.sub(r'<link[^>]+rel=["\']canonical["\'][^>]*>',"",raw,flags=re.I|re.S)
 raw=re.sub(r'<meta[^>]+(?:property=["\']og:|name=["\']twitter:)[^>]*>',"",raw,flags=re.I|re.S)
 raw=raw.replace("</head>",'<title>'+html.escape(t[:50])+' | NewsMorocco</title><meta name="description" content="'+html.escape(d,quote=True)+'"><link rel="canonical" href="'+url+'"><meta property="og:type" content="article"><meta property="og:site_name" content="NewsMorocco"><meta property="og:title" content="'+html.escape(t,quote=True)+'"><meta property="og:description" content="'+html.escape(d,quote=True)+'"><meta property="og:image" content="'+image+'"><meta name="twitter:card" content="summary_large_image"><script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False)+'</script></head>',1)
 raw=add_related(raw,c,p)
 raw=raw.replace('NewsMoroco','NewsMorocco').replace('News Morocco','NewsMorocco')
 Path(new).write_text(raw,encoding="utf-8")
 if new!=p.name:
  red='<html lang="ar"><head><meta charset="utf-8"><meta name="robots" content="noindex,follow"><link rel="canonical" href="'+url+'"><meta http-equiv="refresh" content="0;url='+url+'"><title>تم نقل المقال</title></head><body><a href="'+url+'">تم نقل المقال، اضغط هنا.</a><script>location.replace('+json.dumps(url)+');</script></body></html>'
  p.write_text(red,encoding="utf-8")
for jf in ["news.json","priority-news.json","articles-index.json"]:
 p=Path(jf)
 if not p.exists():continue
 try:data=json.loads(p.read_text(encoding="utf-8"))
 except Exception:continue
 def fix(x):
  if isinstance(x,dict):
   for k,v in list(x.items()):
    if isinstance(v,str):
     for old,new in mapping.items():
      if v in ("/"+old,old):x[k]=v.replace(old,new);break
    else:fix(v)
  elif isinstance(x,list):
   for v in x:fix(v)
 fix(data);p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
urls=[("/",TODAY),("/articles/",TODAY),("/about.html",TODAY),("/contact.html",TODAY),("/editorial-policy.html",TODAY)]
for p in sorted(Path(".").glob("article-*.html")):
 r=p.read_text(encoding="utf-8",errors="ignore")
 if 'http-equiv="refresh"' in r or re.search(r'<meta\s+name=["\']robots["\']\s+content=["\']noindex',r,re.I):continue
 urls.append(("/"+p.name,TODAY))
lines=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for path,last in urls:lines.append('<url><loc>'+SITE+path+'</loc><lastmod>'+last+'</lastmod></url>')
lines.append('</urlset>');Path("sitemap.xml").write_text("\n".join(lines)+"\n",encoding="utf-8")
Path("robots.txt").write_text("User-agent: *\nAllow: /\n\nSitemap: https://www.nwesmomroco.com/sitemap.xml\n",encoding="utf-8")
print("SEO refresh completed: "+str(len(paths))+" article pages; slug updates: "+str(len(mapping)))
