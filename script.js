const newsContainer=document.getElementById("newsContainer");
const searchInput=document.getElementById("searchInput");
const searchButton=document.getElementById("searchButton");
const sectionTitle=document.getElementById("sectionTitle");

const GDELT_API="https://api.gdeltproject.org/api/v2/doc/doc";

const categoryQueries={
  general:'(Morocco OR المغرب OR مغرب)',
  business:'(Morocco OR المغرب OR مغرب) (اقتصاد OR business OR economy)',
  technology:'(Morocco OR المغرب OR مغرب) (تكنولوجيا OR تقنية OR technology OR AI OR الذكاء الاصطناعي)',
  sports:'(Morocco OR المغرب OR مغرب) (رياضة OR كرة OR football OR sports)'
};

document.addEventListener("DOMContentLoaded",()=>fetchNews("general"));

document.querySelectorAll("nav a").forEach(link=>{
  link.addEventListener("click",e=>{
    e.preventDefault();
    const category=link.dataset.category;
    sectionTitle.textContent={
      general:"أحدث الأخبار",
      business:"أخبار الاقتصاد",
      technology:"أخبار التكنولوجيا",
      sports:"أخبار الرياضة"
    }[category]||"أحدث الأخبار";
    fetchNews(category);
  });
});

searchButton.addEventListener("click",searchNews);
searchInput.addEventListener("keydown",e=>{
  if(e.key==="Enter") searchNews();
});

/*
  GDELT supports JSONP. Using JSONP here avoids browser CORS/network
  issues that can leave the page stuck on "جاري تحميل آخر الأخبار...".
*/
function gdeltRequest(query,timespan="1d"){
  return new Promise((resolve,reject)=>{
    const callbackName="gdeltCallback_"+Date.now()+"_"+Math.random().toString(36).slice(2);
    const script=document.createElement("script");
    const timer=setTimeout(()=>{
      cleanup();
      reject(new Error("GDELT timeout"));
    },12000);

    function cleanup(){
      clearTimeout(timer);
      script.remove();
      try{ delete window[callbackName]; }catch(e){ window[callbackName]=undefined; }
    }

    window[callbackName]=(data)=>{
      cleanup();
      resolve(data||{});
    };

    script.onerror=()=>{
      cleanup();
      reject(new Error("GDELT network error"));
    };

    const params=new URLSearchParams({
      query,
      mode:"artlist",
      maxrecords:"18",
      timespan,
      format:"jsonp",
      callback:callbackName,
      sort:"datedesc"
    });

    script.src=`${GDELT_API}?${params.toString()}`;
    document.head.appendChild(script);
  });
}

function normalizeArticles(data){
  return (data.articles||[]).map(a=>({
    title:a.title,
    description:a.domain?("المصدر: "+a.domain):"خبر حديث من مصدر إخباري",
    image:a.socialimage||"https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80",
    url:a.url
  }));
}

async function fetchNews(category="general"){
  showLoading("جاري تحميل آخر الأخبار...");
  try{
    const query=categoryQueries[category]||categoryQueries.general;
    const data=await gdeltRequest(query,"1d");
    displayNews(normalizeArticles(data));
  }catch(error){
    showError("تعذر تحميل الأخبار الآن. حاول تحديث الصفحة بعد لحظات.");
  }
}

async function searchNews(){
  const query=searchInput.value.trim();
  if(!query)return;

  sectionTitle.textContent=`نتائج البحث عن: ${query}`;
  showLoading("جاري البحث عن الأخبار...");

  try{
    const searchQuery=`(Morocco OR المغرب OR مغرب) ${query}`;
    const data=await gdeltRequest(searchQuery,"7d");
    displayNews(normalizeArticles(data));
  }catch(error){
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
    card.innerHTML=`
      <img src="${escapeHTML(article.image)}" alt="${escapeHTML(article.title)}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80'">
      <div class="news-content">
        <h3>${escapeHTML(article.title)}</h3>
        <p>${escapeHTML(article.description||"خبر حديث")}</p>
        <a href="${escapeHTML(article.url)}" target="_blank" rel="noopener noreferrer">اقرأ الخبر كاملًا ←</a>
      </div>
    `;
    newsContainer.appendChild(card);
  });
}

function showLoading(message){
  newsContainer.innerHTML=`<div class="loading">${message}</div>`;
}

function showError(message){
  newsContainer.innerHTML=`<div class="error"><h3>تعذر تحميل الأخبار</h3><p>${message}</p></div>`;
}

function escapeHTML(value){
  const div=document.createElement("div");
  div.textContent=value||"";
  return div.innerHTML;
}
