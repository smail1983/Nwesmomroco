const API_KEY="YOUR_API_KEY_HERE";
const newsContainer=document.getElementById("newsContainer");
const searchInput=document.getElementById("searchInput");
const searchButton=document.getElementById("searchButton");
const sectionTitle=document.getElementById("sectionTitle");

const demoNews=[
{title:"أحدث الأخبار والتحديثات",description:"يمكنك ربط الموقع بمصدر أخبار خارجي لعرض الأخبار بشكل تلقائي.",image:"https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80",url:"#"},
{title:"أخبار التكنولوجيا",description:"تابع آخر التطورات في عالم التكنولوجيا والذكاء الاصطناعي.",image:"https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=900&q=80",url:"#"},
{title:"آخر الأخبار الرياضية",description:"أهم الأخبار والنتائج والتحديثات الرياضية.",image:"https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=900&q=80",url:"#"}];

document.addEventListener("DOMContentLoaded",()=>displayNews(demoNews));

document.querySelectorAll("nav a").forEach(link=>{
  link.addEventListener("click",e=>{
    e.preventDefault();
    const category=link.dataset.category;
    sectionTitle.textContent={general:"أحدث الأخبار",business:"أخبار الاقتصاد",technology:"أخبار التكنولوجيا",sports:"أخبار الرياضة"}[category];
    if(API_KEY!=="YOUR_API_KEY_HERE") fetchNews(category);
  });
});

searchButton.addEventListener("click",searchNews);
searchInput.addEventListener("keydown",e=>{if(e.key==="Enter")searchNews()});

async function fetchNews(category="general"){
  if(API_KEY==="YOUR_API_KEY_HERE"){showError("أضف API Key صالحًا لتفعيل جلب الأخبار تلقائيًا.");return}
  newsContainer.innerHTML='<div class="loading">جاري تحميل الأخبار...</div>';
  try{
    const response=await fetch(`https://newsapi.org/v2/top-headlines?country=us&category=${category}&pageSize=12&apiKey=${API_KEY}`);
    if(!response.ok)throw new Error();
    const data=await response.json();
    displayNews((data.articles||[]).map(a=>({title:a.title,description:a.description,image:a.urlToImage,url:a.url})));
  }catch(e){showError("حدث خطأ أثناء تحميل الأخبار. تحقق من API Key ومصدر الأخبار.")}
}

async function searchNews(){
  const query=searchInput.value.trim(); if(!query)return;
  if(API_KEY==="YOUR_API_KEY_HERE"){showError("البحث يحتاج إلى ربط الموقع بمصدر أخبار API.");return}
  sectionTitle.textContent=`نتائج البحث عن: ${query}`;
  newsContainer.innerHTML='<div class="loading">جاري البحث...</div>';
  try{
    const response=await fetch(`https://newsapi.org/v2/everything?q=${encodeURIComponent(query)}&language=ar&pageSize=12&sortBy=publishedAt&apiKey=${API_KEY}`);
    if(!response.ok)throw new Error();
    const data=await response.json();
    displayNews((data.articles||[]).map(a=>({title:a.title,description:a.description,image:a.urlToImage,url:a.url})));
  }catch(e){showError("حدث خطأ أثناء البحث.")}
}

function displayNews(articles){
  newsContainer.innerHTML="";
  const valid=articles.filter(a=>a&&a.title&&a.image);
  if(!valid.length){newsContainer.innerHTML='<div class="empty">لا توجد أخبار متاحة حاليًا.</div>';return}
  valid.forEach(article=>{
    const card=document.createElement("article");card.className="news-card";
    card.innerHTML=`<img src="${escapeHTML(article.image)}" alt="${escapeHTML(article.title)}" loading="lazy"><div class="news-content"><h3>${escapeHTML(article.title)}</h3><p>${escapeHTML(article.description||"لا يوجد وصف لهذا الخبر.")}</p><a href="${escapeHTML(article.url||"#")}" target="_blank" rel="noopener noreferrer">اقرأ المزيد ←</a></div>`;
    newsContainer.appendChild(card);
  });
}
function showError(message){newsContainer.innerHTML=`<div class="error"><h3>مصدر الأخبار غير متصل</h3><p>${message}</p></div>`}
function escapeHTML(value){const div=document.createElement("div");div.textContent=value||"";return div.innerHTML}
