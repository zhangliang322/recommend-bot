const state = { products: [], sources: [], category: "", query: "" };
const viewTitles = {
  products: "今日候选",
  sources: "数据源",
  feedback: "运营反馈",
  deliveries: "推送记录",
};
const capabilityLabels = {
  social_trends: "社媒热点",
  ecommerce_growth: "电商增长",
  fashion_trends: "时尚趋势",
  product_search: "商品搜索",
  product_detail: "商品详情",
  promotion_link: "推广链接",
  order_query: "订单查询",
};
const credentialLabels = {
  client_id: "应用编号",
  client_secret: "应用密钥",
  pid: "推广位编号",
  ms_token: "TikTok 授权",
  session_file: "Instagram 授权",
  cookie_file: "小红书授权",
};
const adapterLabels = {
  jsonl_signal: "文件信号导入",
  pdd_affiliate: "多多进宝联盟接口",
  tiktok_api_bridge: "TikTok 数据桥接",
  instaloader_bridge: "Instagram 数据桥接",
  mediacrawler_bridge: "小红书数据桥接",
};

function iconRefresh() {
  if (window.lucide) window.lucide.createIcons();
}

function toast(message, error = false) {
  const element = document.getElementById("toast");
  element.textContent = message;
  element.className = `toast show${error ? " error" : ""}`;
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => { element.className = "toast"; }, 2600);
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    let detail = "操作失败";
    try { detail = (await response.json()).detail || detail; } catch (_) { /* empty */ }
    if (typeof detail === "object") detail = detail.message || "配置不完整";
    throw new Error(detail);
  }
  return response.json();
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[char]);
}

function productRows(products) {
  if (!products.length) return `<div class="empty-state"><i data-lucide="package-open"></i><div>没有符合条件的商品</div></div>`;
  return products.map((item) => `
    <article class="product-row" data-product-id="${escapeHtml(item.product_id)}">
      <img class="product-image" src="${escapeHtml(item.card_url)}" alt="${escapeHtml(item.product_name)}推荐卡片" loading="lazy" />
      <div class="product-main">
        <strong title="${escapeHtml(item.product_name)}">${escapeHtml(item.product_name)}</strong>
        <small>${escapeHtml(item.product_id)} · ${escapeHtml(item.currency)} ${Number(item.price).toFixed(2)}</small>
        <div class="product-tags"><span class="tag category">${escapeHtml(item.category)}</span><span class="tag">${escapeHtml(item.hot_label)}</span></div>
      </div>
      <div class="reason">${escapeHtml(item.reasons[0] || "暂无推荐理由")}</div>
      <div class="score-wrap">
        <div class="score-line"><strong>${Math.round(item.hot_score)}</strong><span>/ 100</span></div>
        <div class="score-track"><span style="width:${Math.min(100, item.hot_score)}%"></span></div>
      </div>
      <button class="action-button ${item.approved ? "approved" : ""}" data-approve="${escapeHtml(item.product_id)}" data-approved="${item.approved}">
        <i data-lucide="${item.approved ? "check" : "stamp"}"></i><span>${item.approved ? "已批准" : "批准"}</span>
      </button>
    </article>`).join("");
}

function renderProducts() {
  const query = state.query.trim().toLowerCase();
  const filtered = state.products.filter((item) => {
    const matchesCategory = !state.category || item.category === state.category;
    const matchesQuery = !query || `${item.product_name} ${item.product_id}`.toLowerCase().includes(query);
    return matchesCategory && matchesQuery;
  });
  document.getElementById("product-list").innerHTML = productRows(filtered);
  const approved = state.products.filter((item) => item.approved).length;
  document.getElementById("stat-total").textContent = state.products.length;
  document.getElementById("stat-hot").textContent = state.products.filter((item) => item.hot_score >= 80).length;
  document.getElementById("stat-approved").textContent = approved;
  document.getElementById("stat-pending").textContent = state.products.length - approved;
  document.getElementById("sync-note").textContent = `已显示 ${filtered.length} 个商品`;
  iconRefresh();
}

async function loadProducts() {
  document.getElementById("product-list").innerHTML = `<div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div>`;
  state.products = await request("/api/recommendations?limit=100");
  renderProducts();
}

function sourceRows(sources) {
  if (!sources.length) return `<div class="empty-state">暂无数据源</div>`;
  return sources.map((source) => {
    const missing = source.missing_credentials.map((item) => credentialLabels[item] || item);
    const statusText = source.configured ? "配置完整" : `缺少 ${missing.join("、")}`;
    const capabilities = source.capabilities.map((item) => capabilityLabels[item] || item);
    return `<div class="source-row">
      <div class="source-name"><span class="source-icon"><i data-lucide="plug-zap"></i></span><div><strong>${escapeHtml(source.display_name)}</strong><small>${escapeHtml(adapterLabels[source.adapter] || source.adapter)}</small></div></div>
      <div class="capabilities">${capabilities.map(escapeHtml).join(" · ")}</div>
      <span class="badge ${source.configured ? "ready" : ""}">${escapeHtml(statusText)}</span>
      <button class="toggle ${source.enabled ? "on" : ""}" data-source="${escapeHtml(source.name)}" data-enabled="${source.enabled}" aria-label="${source.enabled ? "停用" : "启用"}${escapeHtml(source.display_name)}"><span></span></button>
    </div>`;
  }).join("");
}

async function loadSources() {
  state.sources = await request("/api/sources");
  document.getElementById("source-list").innerHTML = sourceRows(state.sources);
  iconRefresh();
}

async function loadFeedback() {
  const [summary, items] = await Promise.all([request("/api/feedback/summary"), request("/api/feedback")]);
  document.getElementById("feedback-good").textContent = summary["好"] || 0;
  document.getElementById("feedback-normal").textContent = summary["一般"] || 0;
  document.getElementById("feedback-bad").textContent = summary["差"] || 0;
  document.getElementById("feedback-list").innerHTML = items.length ? items.map((item) => `
    <div class="table-row"><strong>${escapeHtml(item.product_id)}</strong><span>${escapeHtml(item.rating)}</span><span>${escapeHtml(item.note || "无备注")}</span><span>${new Date(item.created_at).toLocaleString("zh-CN")}</span></div>`).join("") : `<div class="empty-state"><i data-lucide="message-square"></i><div>还没有运营反馈</div></div>`;
  iconRefresh();
}

async function loadDeliveries() {
  const items = await request("/api/deliveries/latest");
  const rows = Object.entries(items);
  document.getElementById("delivery-list").innerHTML = rows.length ? rows.map(([productId, sentAt]) => `
    <div class="table-row"><strong>${escapeHtml(productId)}</strong><span>已发送</span><span>正式推荐</span><span>${new Date(sentAt).toLocaleString("zh-CN")}</span></div>`).join("") : `<div class="empty-state"><i data-lucide="send"></i><div>还没有正式推送记录</div></div>`;
  iconRefresh();
}

async function switchView(view) {
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === view));
  document.querySelectorAll(".view").forEach((item) => item.classList.toggle("active", item.id === `view-${view}`));
  document.getElementById("page-title").textContent = viewTitles[view];
  if (view === "sources") await loadSources();
  if (view === "feedback") await loadFeedback();
  if (view === "deliveries") await loadDeliveries();
}

document.addEventListener("click", async (event) => {
  const nav = event.target.closest(".nav-item");
  if (nav) { switchView(nav.dataset.view).catch((error) => toast(error.message, true)); return; }
  const category = event.target.closest("[data-category]");
  if (category) {
    document.querySelectorAll("[data-category]").forEach((item) => item.classList.remove("active"));
    category.classList.add("active"); state.category = category.dataset.category; renderProducts(); return;
  }
  const approval = event.target.closest("[data-approve]");
  if (approval) {
    approval.disabled = true;
    try {
      const productId = approval.dataset.approve;
      if (approval.dataset.approved === "true") await request(`/api/approvals/${encodeURIComponent(productId)}`, { method: "DELETE" });
      else await request("/api/approvals", { method: "POST", body: JSON.stringify({ product_id: productId }) });
      const product = state.products.find((item) => item.product_id === productId);
      product.approved = !product.approved; renderProducts(); toast(product.approved ? "商品已批准" : "已撤销批准");
    } catch (error) { approval.disabled = false; toast(error.message, true); }
    return;
  }
  const source = event.target.closest("[data-source]");
  if (source) {
    source.disabled = true;
    try {
      await request(`/api/sources/${encodeURIComponent(source.dataset.source)}`, { method: "PATCH", body: JSON.stringify({ enabled: source.dataset.enabled !== "true" }) });
      await loadSources(); toast("数据源状态已更新");
    } catch (error) { source.disabled = false; toast(error.message, true); }
  }
});

document.getElementById("product-search").addEventListener("input", (event) => { state.query = event.target.value; renderProducts(); });
document.getElementById("refresh-button").addEventListener("click", () => loadProducts().then(() => toast("数据已刷新")).catch((error) => toast(error.message, true)));
document.getElementById("page-eyebrow").textContent = new Intl.DateTimeFormat("zh-CN", { dateStyle: "long" }).format(new Date());

window.addEventListener("DOMContentLoaded", () => {
  iconRefresh();
  loadProducts().catch((error) => {
    document.getElementById("product-list").innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    toast(error.message, true);
  });
});
