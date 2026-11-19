const newsContainer = document.getElementById("newsContainer");
const searchInput = document.getElementById("searchInput");
const searchButton = document.getElementById("searchButton");
const sectionTitle = document.getElementById("sectionTitle");

const CATEGORIES = new Set(["morocco", "world", "economy", "technology", "sports"]);
const LEGACY_CATEGORIES = {
  policy: "morocco",
  general: "morocco",
  business: "economy",
  international: "world"
};

let allNews = [];
let currentCategory = "morocco";

const categoryLabels = {
  morocco: "أخبار المغرب",
  world: "أخبار العالم",
  economy: "أخبار الاقتصاد",
  technology: "أخبار التكنولوجيا",
  sports: "أخبار الرياضة"
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
  sports: ["https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=900&q=80", "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=900&q=80"],
  economy: ["https://images.unsplash.com/photo-1556761175-b413da4baf72?auto=format&fit=crop&w=900&q=80", "https://images.unsplash.com/photo-1559526324-593bc073d938?auto=format&fit=crop&w=900&q=80"],
  technology: ["https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=900&q=80", "https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?auto=format&fit=crop&w=900&q=80"],
  morocco: [genericNewsImage, "https://images.unsplash.com/photo-1495020689067-958852a7765e?auto=format&fit=crop&w=900&q=80"],
  world: [genericNewsImage, "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?auto=format&fit=crop&w=900&q=80"]
};

function sortByDate(articles) {
  return [...articles].sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));
}

function normalizeCategory(article) {
  if (!article) return "morocco";
  const storedCategory = String(article.category || "").toLowerCase();
  if (LEGACY_CATEGORIES[storedCategory]) return LEGACY_CATEGORIES[storedCategory];
  if (CATEGORIES.has(storedCategory)) return storedCategory;

  const text = `${article.title || ""} ${article.description || ""}`.toLowerCase();
  if (/رياض|كرة|الوداد|الرجاء|المنتخب|كأس|مباراة|لاعب|فيفا|كاف|botafogo|futsal|sport|football/.test(text)) return "sports";
  if (/اقتصاد|اقتصادي|بنك|استثمار|أسعار|الأسواق|النمو|الدرهم|مالية|ميزانية|business|economy/.test(text)) return "economy";
  if (/تكنولوجيا|تقنية|ذكاء اصطناعي|رقمي|معلوميات|هاتف|برمج|technology|artificial intelligence/.test(text)) return "technology";
  if (/المغرب|مغربي|مغربية|morocco|moroccan|ملك|الحكومة|حكومة|وزير|برلمان|انتخابات|حزب|سياسة|سياسي|العثماني|بنكيران|الصحراء|policy/.test(text)) return "morocco";
  if (/دولي|العالم|international|world|global/.test(text)) return "world";
  return "morocco";
}

function prepareArticles(articles) {
  return articles.map(article => ({ ...article, category: normalizeCategory(article) }));
}

function getNewsImage(article, index) {
  const image = article.image || "";
  if (image && image !== genericNewsImage) return image;
  const images = categoryImages[normalizeCategory(article)] || categoryImages.morocco;
  return images[index % images.length];
}

function showLoading(message) {
  if (newsContainer) newsContainer.innerHTML = `<div class="loading">${message}</div>`;
}

function displayNews(articles) {
  if (!newsContainer) return;
  newsContainer.innerHTML = "";
  const valid = articles.filter(article => article && article.title && article.url);
  if (!valid.length) {
    newsContainer.innerHTML = '<div class="empty">لا توجد أخبار متاحة حاليًا في هذا القسم.</div>';
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
    const badge = document.createElement("div");
    badge.className = "news-category";
    badge.textContent = categoryLabels[normalizeCategory(article)];
    const heading = document.createElement("h3");
    heading.textContent = article.title;
    const summary = document.createElement("p");
    summary.textContent = article.description || ("المصدر: " + (article.domain || ""));
    const link = document.createElement("a");
    link.href = article.local_url || article.url;
    link.textContent = "اقرأ الخبر كاملًا ←";
    content.append(badge, heading, summary, link);
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

function moveLatestNewsToTop() {
  if (!newsContainer) return;
  const title = document.querySelector("main")?.querySelector(".section-title");
  if (title && title.nextElementSibling !== newsContainer) title.insertAdjacentElement("afterend", newsContainer);
}

function toggleFeaturedSections(category) {
  document.querySelectorAll("main > section:not(#newsContainer)").forEach(section => {
    section.style.display = category === "morocco" ? "" : "none";
  });
}

function renderCategory(category) {
  currentCategory = CATEGORIES.has(category) ? category : "morocco";
  sectionTitle.textContent = categoryLabels[currentCategory];
  toggleFeaturedSections(currentCategory);
  const filtered = sortByDate(allNews.filter(article => normalizeCategory(article) === currentCategory));
  displayNews(filtered);
  window.scrollTo({ top: document.querySelector("main")?.offsetTop || 0, behavior: "smooth" });
}

async function loadNews() {
  showLoading("جاري تحميل آخر الأخبار...");
  try {
    let data;
    try {
      data = await fetchJsonWithTimeout("news.json");
    } catch (error) {
      console.warn("news.json failed", error);
      data = { articles: [] };
    }

    const articles = Array.isArray(data.articles) ? data.articles : [];
    let manualArticles = [];
    try {
      const manualData = await fetchJsonWithTimeout("manual-news.json");
      manualArticles = Array.isArray(manualData) ? manualData : (Array.isArray(manualData.articles) ? manualData.articles : []);
    } catch (error) {
      console.warn("manual-news.json unavailable", error);
    }
    const combined = [...manualArticles, ...articles];
    allNews = prepareArticles([featuredNews, ...combined.filter(article => article && article.url !== featuredNews.url)]);
    renderCategory("morocco");
  } catch (error) {
    console.error("News loading error:", error);
    allNews = prepareArticles([featuredNews]);
    renderCategory("morocco");
  }
}

function searchNews() {
  if (!searchInput) return;
  const query = searchInput.value.trim().toLowerCase();
  if (!query) {
    renderCategory(currentCategory);
    return;
  }
  sectionTitle.textContent = "نتائج البحث عن: " + searchInput.value.trim();
  toggleFeaturedSections("search");
  const results = allNews.filter(article => {
    const text = `${article.title || ""} ${article.description || ""}`.toLowerCase();
    return text.includes(query) && normalizeCategory(article) === currentCategory;
  });
  displayNews(sortByDate(results));
}

function initNewsApp() {
  if (!newsContainer || !sectionTitle) {
    console.error("NewsMorocco: required HTML elements are missing.");
    return;
  }
  moveLatestNewsToTop();
  document.querySelectorAll("nav a[data-category]").forEach(link => {
    link.addEventListener("click", event => {
      const category = link.dataset.category;
      if (CATEGORIES.has(category)) {
        event.preventDefault();
        renderCategory(category);
      }
    });
  });
  if (searchButton) searchButton.addEventListener("click", searchNews);
  if (searchInput) searchInput.addEventListener("keydown", event => { if (event.key === "Enter") searchNews(); });
  loadNews();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initNewsApp, { once: true });
} else {
  initNewsApp();
}
