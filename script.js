const newsContainer=document.getElementById("newsContainer");
const searchInput=document.getElementById("searchInput");
const searchButton=document.getElementById("searchButton");
const sectionTitle=document.getElementById("sectionTitle");

const GDELT_API="https://api.gdeltproject.org/api/v2/doc/doc";

const categoryQueries={
  general:'Morocco',
  business:'Morocco economy',
  technology:'Morocco technology',
  sports:'Morocco football OR Morocco soccer OR Raja OR Wydad'
};

document.addEventListener("DOMContentLoaded",()=>fetchNews("sports"));

document.querySelectorAll("nav a").forEach(link=>{
  link.addEventListener("click",e=>{
    e.preventDefault();
    const category=link.dataset.category;
    sectionTitle.textContent={
      general:"أحدث الأخبار المغربية",
      business:"أخبار الاقتصاد المغربي",
      technology:"أخبار التكنولوجيا في المغرب",
      sports:"أبرز أخبار الرياضة المغربية"
    }[category]||"أحدث الأخبار المغربية";
    fetchNews(category);
  });
});

searchButton.addEventListener("click",searchNews);
searchInput.addEventListener("keydown",e=>{
  if(e.key==="Enter") searchNews();
});

/* GDELT supports JSON and JSONP. JSON via fetch is more reliable on GitHub Pages
   than dynamically injecting JSONP scripts. */
async function gdeltRequest(query,timespan="2d"){
  const params=new URLSearchParams({
    query,
    mode:"artlist",
    maxrecords:"18",
    timespan,
    format:"json",
    sort:"datedesc"
  });

  const response=await fetch(GDELT_API+"?"+params.toString(),{
    method:"GET",
    cache:"no-store",
    headers:{Accept:"application/json"}
  });

  if(!response.ok) throw new Error("GDELT HTTP "+response.status);

  const data=await response.json();
  return data||{};
}

function normalizeArticles(data){
  return (data.articles||[]).map(a=>({
    title:a.title||"خبر مغربي",
    description:a.domain?("المصدر: "+a.domain):"خبر حديث",
    image:a.socialimage||"https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80",
    url:a.url,
    date:a.seendate||""
  }));
}

async function fetchNews(category="general"){
  showLoading("جاري تحميل آخر الأخبار...");
  try{
    let data=await gdeltRequest(categoryQueries[category]||categoryQueries.general,"2d");
    let articles=normalizeArticles(data);

    if(!articles.length && category==="sports"){
      data=await gdeltRequest("Morocco sports","7d");
      articles=normalizeArticles(data);
    }

    displayNews(articles);
  }catch(error){
    console.error("News loading error:",error);
    showError("تعذر الاتصال بمصدر الأخبار الآن. اضغط تحديث الصفحة وحاول مرة أخرى.");
  }
}

async function searchNews(){
  const query=searchInput.value.trim();
  if(!query)return;

  sectionTitle.textContent="نتائج البحث عن: "+query;
  showLoading("جاري البحث عن الأخبار...");

  try{
    const data=await gdeltRequest("Morocco "+query,"7d");
    displayNews(normalizeArticles(data));
  }catch(error){
    console.error("Search error:",error);
    showError("حدث خطأ أثناء البحث. حاول مرة أخرى.");
  }
}

function displayNews(articles){
  newsContainer.innerHTML="";
  const valid=articles.filter(a=>a&&a.title&&a.url);

  if(!valid.length){
    newsContainer.innerHTML='<div class="empty">لا توجد أخبار متاحة حاليًا.</div>';
    return;
  }

  valid.forEach(article=>{
    const card=document.createElement("article");
    card.className="news-card";

    const img=document.createElement("img");
    img.src=article.image;
    img.alt=article.title;
    img.loading="lazy";
    img.onerror=()=>{img.src="https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80";};

    const content=document.createElement("div");
    content.className="news-content";

    const h3=document.createElement("h3");
    h3.textContent=article.title;

    const p=document.createElement("p");
    p.textContent=article.description||"خبر حديث";

    const a=document.createElement("a");
    a.href=article.url;
    a.target="_blank";
    a.rel="noopener noreferrer";
    a.textContent="اقرأ الخبر كاملًا ←";

    content.append(h3,p,a);
    card.append(img,content);
    newsContainer.appendChild(card);
  });
}

function showLoading(message){
  newsContainer.innerHTML='<div class="loading">'+message+"</div>";
}

function showError(message){
  newsContainer.innerHTML='<div class="error"><h3>تعذر تحميل الأخبار</h3><p>'+message+"</p></div>";
}
