const newsContainer = document.getElementById("newsContainer");
const searchInput = document.getElementById("searchInput");
const searchButton = document.getElementById("searchButton");
const sectionTitle = document.getElementById("sectionTitle");

let allNews = [];
let currentCategory = "general";

const categoryLabels = {
  general: "أحدث الأخبار المغربية",
  business: "أخبار الاقتصاد المغربي",
  technology: "أخبار التكنولوجيا في المغرب",
  sports: "أبرز أخبار الرياضة المغربية"
};

const featuredNews = {
  category: "sports",
  title: "زياش يصنع الحدث في البرازيل.. أكثر من 262 ألف متابع من المغرب لبوتافوغو",
  description: "أكثر من 300 ألف متابع جديد لبوتافوغو خلال الفترة من 7 إلى 30 شتنبر، بينهم أكثر من 262 ألفاً من المغرب، وفق ge.globo.",
  image: "https://s02.video.glbimg.com/x240/14956797.jpg",
  url: "article-ziyech-botafogo-morocco-october-6-2026.html",
  domain: "ge.globo / NewsMorocco",
  date: "Tue, 06 Oct 2026 15:30:00 GMT"
};

const genericNewsImage = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80";
const categoryImages = {
  sports: ["https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=900&q=80", "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=900&q=80", "https://images.unsplash.com/photo-1526232761682-d26e03ac148e?auto=format&fit=crop&w=900&q=80", "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?auto=format&fit=crop&w=900&q=80"],
  business: ["https://images.unsplash.com/photo-1556761175-b413da4baf72?auto=format&fit=crop&w=900&q=80", "https://images.unsplash.com/photo-1559526324-593bc073d938?auto=format&fit=crop&w=900&q=80", "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=900&q=80", "https://images.unsplash.com/photo-1551836022-d5d88e9218df?auto=format&fit=crop&w=900&q=80"],
  technology: ["https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=900&q=80", "https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?auto=format&fit=crop&w=900&q=80", "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=900&q=80", "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=80"],
  general: [genericNewsImage, "https://images.unsplash.com/photo-1495020689067-958852a7765e?auto=format&fit=crop&w=900&q=80", "https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=900&q=80", "https://images.unsplash.com/photo-1504711331083-9c895941bf81?auto=format&fit=crop&w=900&q=80"]
};

function sortByDate(articles) {
  return [...articles].sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));
}

function getNewsImage(article, index) {
  const image = article.image || "";
  if (image && image !== genericNewsImage) return image;
  const images = categoryImages[article.category] || categoryImages.general;
  return images[index % images.length];
}

function showLoading(message) {
  if (newsContainer) newsContainer.innerHTML = `<div class="loading">${message}</div>`;
}

function displayNews(articles) {
  if (!newsContainer) return;
  newsContainer.innerHTML = "";
  const valid = articles.filter(a => a && a.title && a.url);
  if (!valid.length) {
    newsContainer.innerHTML = '<div class="empty">لا توجد أخبار متاحة حاليًا.</div>';
    return;
  }
  valid.forEach((article, index) => {
    const card = document.createElement("article");
    card.className = "news-card";
    const img = document.createElement("img");
    img.src = getNewsImage(article, index);
    img.alt = article.title;
    img.loading = "lazy";
    img.onerror = () => { img.src = genericNewsImage; };
    const content = document.createElement("div");
    content.className = "news-content";
    const h3 = document.createElement("h3");
    h3.textContent = article.title;
    const p = document.createElement("p");
    p.textContent = article.description || ("المصدر: " + (article.domain || ""));
    const a = document.createElement("a");
    a.href = article.url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = "اقرأ الخبر كاملًا ←";
    content.append(h3, p, a);
    card.append(img, content);
    newsContainer.appendChild(card);
  });
}

async function fetchJsonWithTimeout(url, timeoutMs = 8000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url + (url.includes("?") ? "&" : "?") + "v=" + Date.now(), {
      cache: "no-store",
      signal: controller.signal
    });
    if (!response.ok) throw new Error("HTTP " + response.status);
    return await response.json();
  } finally {
    clearTimeout(timer);
  }
}

async function loadNews() {
  showLoading("جاري تحميل آخر الأخبار...");
  try {
    let data;
    try {
      data = await fetchJsonWithTimeout("news.json");
    } catch (primaryError) {
      console.warn("news.json failed, trying manual-news.json", primaryError);
      data = await fetchJsonWithTimeout("manual-news.json");
    }

    const articles = Array.isArray(data.articles) ? data.articles : [];
    allNews = [featuredNews, ...articles.filter(a => a && a.url !== featuredNews.url)];
    sectionTitle.textContent = categoryLabels.general;
    displayNews(sortByDate(allNews));
  } catch (error) {
    console.error("News loading error:", error);
    allNews = [featuredNews];
    sectionTitle.textContent = categoryLabels.general;
    displayNews(allNews);
  }
}

function searchNews() {
  if (!searchInput) return;
  const query = searchInput.value.trim().toLowerCase();
  if (!query) {
    sectionTitle.textContent = categoryLabels[currentCategory] || categoryLabels.general;
    displayNews(currentCategory === "general" ? sortByDate(allNews) : allNews.filter(a => a.category === currentCategory));
    return;
  }
  sectionTitle.textContent = "نتائج البحث عن: " + searchInput.value.trim();
  const results = allNews.filter(a => (a.title || "").toLowerCase().includes(query) || (a.description || "").toLowerCase().includes(query));
  displayNews(results);
}

function initNewsApp() {
  if (!newsContainer || !sectionTitle) {
    console.error("NewsMorocco: required HTML elements are missing.");
    return;
  }

  document.querySelectorAll("nav a").forEach(link => {
    link.addEventListener("click", e => {
      if (link.dataset.category) {
        e.preventDefault();
        currentCategory = link.dataset.category;
        sectionTitle.textContent = categoryLabels[currentCategory] || categoryLabels.general;
        displayNews(currentCategory === "general" ? sortByDate(allNews) : allNews.filter(a => a.category === currentCategory));
      }
    });
  });

  if (searchButton) searchButton.addEventListener("click", searchNews);
  if (searchInput) searchInput.addEventListener("keydown", e => { if (e.key === "Enter") searchNews(); });

  loadNews();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initNewsApp, { once: true });
} else {
  initNewsApp();
}
