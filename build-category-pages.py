import json
from pathlib import Path
from html import escape

SITE = 'https://www.nwesmomroco.com'
CATEGORIES = {
 'politics': ('السياسة المغربية', 'آخر أخبار السياسة المغربية، الحكومة، القرارات، والدبلوماسية.', ['policy']),
 'morocco': ('أخبار المغرب', 'آخر الأخبار المغربية من مختلف المجالات.', ['policy','general']),
 'business': ('الاقتصاد', 'أخبار الاقتصاد المغربي، الأسواق، الأعمال، والاستثمار.', ['business']),
 'technology': ('التكنولوجيا', 'آخر أخبار التكنولوجيا والذكاء الاصطناعي والابتكار.', ['technology']),
 'sports': ('الرياضة', 'أخبار الرياضة المغربية والمنتخبات والأندية.', ['sports']),
}
for slug,(title,description,cats) in CATEGORIES.items():
  canonical = SITE + '/category/' + slug + '/'
  target = Path('category') / slug / 'index.html'
  target.parent.mkdir(parents=True, exist_ok=True)
  cat_json=json.dumps(cats,ensure_ascii=False)
  html_doc='''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>'''+escape(title)+''' | NewsMorocco</title><meta name="description" content="'''+escape(description)+'''">
  <link rel="canonical" href="'''+canonical+'''"><meta property="og:type" content="website"><meta property="og:url" content="'''+canonical+'''">
  <meta property="og:title" content="'''+escape(title)+''' | NewsMorocco"><meta property="og:description" content="'''+escape(description)+'''">
  <meta property="og:image" content="'''+SITE+'''/news-morocco-og-1200x630.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="'''+SITE+'''/news-morocco-og-1200x630.png">
  <style>body{margin:0;background:#f5f7f9;color:#17212b;font-family:Arial,sans-serif;line-height:1.8}header{background:#17212b;color:white;text-align:center;padding:16px}header a{color:white;text-decoration:none}nav{display:flex;flex-wrap:wrap;justify-content:center;gap:10px;background:#fff;padding:12px}nav a{color:#087f5b;text-decoration:none}main{max-width:1100px;margin:22px auto;padding:0 14px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}.card{background:white;border-radius:14px;overflow:hidden;box-shadow:0 2px 12px #0001}.card a{color:inherit;text-decoration:none}.card img{width:100%;height:190px;object-fit:cover}.body{padding:14px}.date{font-size:13px;color:#667}</style></head><body>
  <header><a href="/">NewsMorocco — نبض المغرب والعالم</a></header><nav><a href="/">الرئيسية</a><a href="/category/politics/">سياسة</a><a href="/category/morocco/">أخبار المغرب</a><a href="/category/business/">اقتصاد</a><a href="/category/technology/">تكنولوجيا</a><a href="/category/sports/">رياضة</a></nav>
  <main><h1>'''+escape(title)+'''</h1><p>'''+escape(description)+'''</p><div id="news" class="grid"></div></main>
  <script>const categories='''+cat_json+''';function esc(s){return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  function datef(v){const d=new Date(v);return isNaN(d)?'':d.toLocaleDateString('ar-MA',{year:'numeric',month:'long',day:'numeric'});}
  fetch('/articles-index.json?ts='+Date.now()).then(r=>r.json()).then(data=>{const arr=Array.isArray(data)?data:(data.articles||[]);const items=arr.filter(x=>categories.includes(x.category)).sort((a,b)=>new Date(b.date||0)-new Date(a.date||0));
  document.getElementById('news').innerHTML=items.map(x=>'<article class="card"><a href="'+esc(x.url||x.local_url||'#')+'"><img src="'+esc(x.image)+'" alt="'+esc(x.title)+'" loading="lazy"><div class="body"><h2>'+esc(x.title)+'</h2><p>'+esc(x.description)+'</p><div class="date">'+esc(datef(x.date))+'</div></div></a></article>').join('')||'لا توجد أخبار في هذا القسم حالياً.';}).catch(()=>document.getElementById('news').textContent='تعذر تحميل الأخبار.');</script></body></html>'
  target.write_text(html_doc,encoding='utf-8')
print('Generated 5 SEO category pages.')