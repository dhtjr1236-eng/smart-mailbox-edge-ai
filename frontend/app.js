"use strict";

const API_BASE = "";
let currentPage = 1, currentFilter = "all", currentDate = "", totalPages = 1;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = String(text);
  return node;
}

// Images must come from this application's upload directory, never an arbitrary
// remote host, javascript/data URL, credentials, query, or encoded path traversal.
function safeImageUrl(value) {
  if (typeof value !== "string" || !value) return "";
  try {
    const url = new URL(value, window.location.origin);
    if (!["http:", "https:"].includes(url.protocol) || url.origin !== window.location.origin ||
        url.username || url.password || url.search || url.hash ||
        !/^\/static\/images\/[A-Za-z0-9_-]+\.(?:jpe?g|png|webp)$/i.test(url.pathname)) return "";
    return url.href;
  } catch {
    return "";
  }
}

function showMessage(message) {
  document.getElementById("records-grid").replaceChildren(element("div", "loading", message));
}

async function loadData() {
  showMessage("데이터 불러오는 중...");
  const params = new URLSearchParams({page: currentPage, limit: 20});
  if (currentDate) params.set("date", currentDate);
  if (currentFilter === "detected") params.set("detected_only", "true");
  try {
    const res = await fetch(`${API_BASE}/api/detections?${params}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (!Array.isArray(data.results) || !Number.isFinite(data.total) || data.total < 0) {
      throw new Error("잘못된 서버 응답");
    }
    totalPages = Math.ceil(data.total / 20) || 1;
    renderStats(data.total, data.results);
    renderCards(data.results);
    updatePagination();
  } catch (error) {
    showMessage(`❌ 서버 연결 실패: ${error.message}`);
    console.error(error);
  }
}

function renderStats(total, results) {
  document.getElementById("total-count").textContent = total;
  document.getElementById("detected-count").textContent = results.filter(r => r.detected).length;
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("today-count").textContent = results.filter(
    r => typeof r.timestamp === "string" && r.timestamp.startsWith(today)
  ).length;
}

function imagePlaceholder() {
  return element("div", "record-img-placeholder", "📷 이미지를 불러올 수 없습니다.");
}

function renderCards(records) {
  const grid = document.getElementById("records-grid");
  if (!records.length) {
    showMessage("📭 기록이 없습니다.");
    return;
  }
  const cards = records.map(record => {
    const card = element("div", `record-card${record.detected ? " detected" : ""}`);
    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.setAttribute("aria-label", "감지 기록 상세 보기");
    const imageUrl = safeImageUrl(record.image_url);
    const description = String(record.gemini_result ?? "");
    const date = record.timestamp ? new Date(record.timestamp) : null;
    const time = date && !Number.isNaN(date.getTime()) ? date.toLocaleString("ko-KR") : "-";
    if (imageUrl) {
      const image = element("img", "record-img");
      image.alt = "감지 이미지";
      image.loading = "lazy";
      image.addEventListener("error", () => image.replaceWith(imagePlaceholder()), {once: true});
      image.src = imageUrl;
      card.append(image);
    } else {
      card.append(imagePlaceholder());
    }
    const info = element("div", "record-info");
    info.append(element("span", `record-badge ${record.detected ? "badge-detected" : "badge-none"}`,
      record.detected ? "📬 우편물 감지" : "📭 감지 없음"));
    info.append(element("div", "record-label", record.label || "미분류"));
    const confidence = typeof record.confidence === "number" && Number.isFinite(record.confidence)
      ? `${(record.confidence * 100).toFixed(1)}%` : "-";
    info.append(element("div", "record-conf", `신뢰도: ${confidence}`));
    if (description) info.append(element("div", "record-gemini", `💬 ${description}`));
    info.append(element("div", "record-time", `🕐 ${time}`));
    card.append(info);
    card.addEventListener("click", () => openModal(imageUrl, description, time));
    card.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openModal(imageUrl, description, time);
      }
    });
    return card;
  });
  grid.replaceChildren(...cards);
}

function filterAll() {
  currentFilter = "all";
  currentPage = 1;
  document.getElementById("btn-all").classList.add("active");
  document.getElementById("btn-detected").classList.remove("active");
  return loadData();
}
function filterDetected() {
  currentFilter = "detected";
  currentPage = 1;
  document.getElementById("btn-all").classList.remove("active");
  document.getElementById("btn-detected").classList.add("active");
  return loadData();
}
function applyDateFilter() {
  currentDate = document.getElementById("date-filter").value;
  currentPage = 1;
  return loadData();
}
function prevPage() { if (currentPage > 1) { currentPage--; return loadData(); } }
function nextPage() { if (currentPage < totalPages) { currentPage++; return loadData(); } }
function updatePagination() {
  document.getElementById("btn-prev").disabled = currentPage <= 1;
  document.getElementById("btn-next").disabled = currentPage >= totalPages;
  document.getElementById("page-info").textContent = `${currentPage} / ${totalPages} 페이지`;
}
function openModal(imageUrl, description, time) {
  const image = document.getElementById("modal-img");
  const fallback = document.getElementById("modal-image-fallback");
  const safeUrl = safeImageUrl(imageUrl);
  image.style.display = safeUrl ? "block" : "none";
  fallback.hidden = Boolean(safeUrl);
  if (safeUrl) image.src = safeUrl;
  else image.removeAttribute("src");
  document.getElementById("modal-desc").textContent = description
    ? `💬 ${description}\n🕐 ${time}` : `🕐 ${time}`;
  document.getElementById("image-modal").classList.add("open");
}
function closeModal() { document.getElementById("image-modal").classList.remove("open"); }

const html = document.documentElement;
const toggle = document.querySelector("[data-theme-toggle]");
let theme = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
function renderTheme() {
  html.setAttribute("data-theme", theme);
  toggle.textContent = theme === "dark" ? "☀️" : "🌙";
}
renderTheme();
toggle.addEventListener("click", () => { theme = theme === "dark" ? "light" : "dark"; renderTheme(); });
document.getElementById("btn-all").addEventListener("click", filterAll);
document.getElementById("btn-detected").addEventListener("click", filterDetected);
document.getElementById("date-filter").addEventListener("change", applyDateFilter);
document.getElementById("btn-refresh").addEventListener("click", loadData);
document.getElementById("btn-prev").addEventListener("click", prevPage);
document.getElementById("btn-next").addEventListener("click", nextPage);
document.getElementById("image-modal").addEventListener("click", closeModal);
document.querySelector(".modal-inner").addEventListener("click", event => event.stopPropagation());
document.querySelector(".modal-close").addEventListener("click", closeModal);
document.getElementById("modal-img").addEventListener("error", () => {
  document.getElementById("modal-img").style.display = "none";
  document.getElementById("modal-image-fallback").hidden = false;
});
document.addEventListener("keydown", event => { if (event.key === "Escape") closeModal(); });
setInterval(loadData, 30000);
loadData();
