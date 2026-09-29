const newsContainer=document.getElementById("newsContainer");
const searchInput=document.getElementById("searchInput");
const searchButton=document.getElementById("searchButton");
const sectionTitle=document.getElementById("sectionTitle");

let allNews=[];
let currentCategory="sports";

const categoryLabels={
  general:"أحدث الأخبار المغربية",
  business:"أخبار الاقتصاد المغربي",
  technology:"أخبار التكنولوجيا في المغرب",
  sports:"أبرز أخبار الرياضة المغربية"
};

document.addEventListener("DOMContentLoaded",loadNews);

document.querySelectorAll("nav a").forEach(link=>{
  link.addEventListener("click",e=>{
    e.preventDefault();
    currentCategory=link.dataset.category||"sports";
    sectionTitle.textContent=categoryLabels[currentCategory]||categoryLabels.general;
    displayNews(allNews.filter(a=>a.category===currentCategory));
  });
});

searchButton.addEventListener("click",searchNews);
searchInput.addEventListener("keydown",e=>{
  if(e.key==="Enter") searchNews();
});

async function loadNews(){
  showLoading("جاري تحميل آخر الأخبار...");
  try{
    const response=await fetch("news.json?v="+Date.now(),{cache:"no-store"});
    if(!response.ok) throw new Error("news.json HTTP "+response.status);
    const data=await response.json();
    allNews=Array.isArray(data.articles)?data.articles:[];
    if(!allNews.length) throw new Error("No articles");
    sectionTitle.textContent=categoryLabels.sports;
    displayNews(allNews.filter(a=>a.category==="sports"));
  }catch(error){
    console.error("News loading error:",error);
    showError("تعذر تحميل الأخبار حاليًا. سيتم تحديث الأخبار تلقائيًا، أعد تحميل الصفحة بعد قليل.");
  }
}

function searchNews(){
  const query=searchInput.value.trim().toLowerCase();
  if(!query){
    sectionTitle.textContent=categoryLabels[currentCategory]||categoryLabels.general;
    displayNews(allNews.filter(a=>a.category===currentCategory));
    return;
  }

  sectionTitle.textContent="نتائج البحث عن: "+searchInput.value.trim();
  const results=allNews.filter(a=>
    (a.title||"").toLowerCase().includes(query) ||
    (a.description||"").toLowerCase().includes(query)
  );
  displayNews(results);
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
    img.src=article.image||"https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80";
    img.alt=article.title;
    img.loading="lazy";
    img.onerror=()=>{img.src="https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80";};

    const content=document.createElement("div");
    content.className="news-content";

    const h3=document.createElement("h3");
    h3.textContent=article.title;

    const p=document.createElement("p");
    p.textContent=article.description||("المصدر: "+(article.domain||""));

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
