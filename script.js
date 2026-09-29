const newsContainer=document.getElementById("newsContainer");
const searchInput=document.getElementById("searchInput");
const searchButton=document.getElementById("searchButton");
const sectionTitle=document.getElementById("sectionTitle");

const GDELT_API="https://api.gdeltproject.org/api/v2/doc/doc";

const categoryQueries={
  general:'Morocco',
  business:'Morocco economy',
  technology:'Morocco technology',
  sports:'Morocco football'
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

/* GDELT supports JSONP. We use short English queries because GDELT
   searches multilingual news through English machine translation. */
function gdeltRequest(query,timespan="2d"){
  return new Promise((resolve,reject)=>{
    const callbackName="gdeltCallback_"+Date.now()+"_"+Math.random().toString(36).slice(2);
    const script=document.createElement("script");
    let finished=false;

    const timer=setTimeout(()=>{
      finish();
      reject(new Error("GDELT timeout"));
    },10000);

    function finish(){
      if(finished)return;
      finished=true;
      clearTimeout(timer);
      script.remove();
      try{delete window[callbackName];}catch(e){window[callbackName]=undefined;}
    }

    window[callbackName]=(data)=>{
      finish();
      resolve(data||{});
    };

    script.onerror=()=>{
      finish();
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

    script.src=GDELT_API+"?"+params.toString();
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
    let data=await gdeltRequest(categoryQueries[category]||categoryQueries.general,"2d");
    let articles=normalizeArticles(data);

    /* If the sports query is temporarily sparse, broaden it slightly. */
    if(!articles.length && category==="sports"){
      data=await gdeltRequest("Morocco sports","3d");
      articles=normalizeArticles(data);
    }

    displayNews(articles);
  }catch(error){
    showError("تعذر تحميل الأخبار الآن. حاول تحديث الصفحة بعد لحظات.");
  }
}

async function searchNews(){
  const query=searchInput.value.trim();
  if(!query)return;

  sectionTitle.textContent="نتائج البحث عن: "+query;
  showLoading("جاري البحث عن الأخبار...");

  try{
    const searchQuery="Morocco "+query;
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
