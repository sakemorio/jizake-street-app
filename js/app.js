// ==== 設定 ====
// 会場スタッフがスマホから更新する「完売」「お知らせ」のライブ状況を読み込むURL。
// Google Apps Script（doGet）で完売ブース番号とお知らせ文を返すウェブアプリを設定する。
// 未設定の間はこの機能はオフ（完売バッジ・お知らせバーは出ない）。設定手順は README.md 参照。
const LIVE_ENDPOINT = "";
const LIVE_POLL_MS = 60000; // ポーリング間隔（1分）

// ==== タブ切り替え ====
const tabButtons = document.querySelectorAll(".tab-btn");
const views = document.querySelectorAll(".view");

function showView(name){
  if(!document.getElementById(`view-${name}`)) name = "map"; // 廃止されたタブが残っていた場合の保険
  views.forEach(v => v.classList.toggle("active", v.id === `view-${name}`));
  tabButtons.forEach(b => b.classList.toggle("active", b.dataset.view === name));
  localStorage.setItem("js_last_tab", name);
}

tabButtons.forEach(btn => {
  btn.addEventListener("click", () => showView(btn.dataset.view));
});

// ==== 酒帳（飲んだ記録） ====
const SAKECHO_KEY = "js_sakecho_2026";

function makeId(){
  return "s" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

function saveSakecho(list){
  localStorage.setItem(SAKECHO_KEY, JSON.stringify(list));
}

function getSakecho(){
  let list;
  try{ list = JSON.parse(localStorage.getItem(SAKECHO_KEY)) || []; }
  catch(e){ list = []; }
  // 旧形式（銘柄名の文字列配列）からの移行
  let migrated = false;
  list = list.map(entry => {
    if(typeof entry === "string"){
      migrated = true;
      return { id: makeId(), name: entry, label: entry, rating: 0 };
    }
    return entry;
  });
  if(migrated) saveSakecho(list);
  return list;
}

// 同じ蔵元で複数本飲んだ場合も記録できるよう、タップのたびに新しい記録を追加する
// （2本目以降は「銘柄名 2」のように自動採番。区別したい場合は酒帳タブで銘柄名を書き換える）
function addSakechoQuick(name){
  const list = getSakecho();
  const count = list.filter(e => e.name === name).length;
  const label = count === 0 ? name : `${name} ${count + 1}`;
  list.push({ id: makeId(), name, label, rating: 0 });
  saveSakecho(list);
  return list;
}

function addSakechoBlank(){
  const list = getSakecho();
  list.unshift({ id: makeId(), name: "", label: "", rating: 0 });
  saveSakecho(list);
  renderSakecho();
  requestAnimationFrame(() => {
    const first = document.querySelector("#sakecho-list .sakecho-label");
    if(first) first.focus();
  });
}

function updateSakechoLabel(id, value){
  const list = getSakecho();
  const entry = list.find(e => e.id === id);
  if(entry){ entry.label = value; saveSakecho(list); }
}

function updateSakechoRating(id, rating){
  const list = getSakecho();
  const entry = list.find(e => e.id === id);
  if(!entry) return;
  entry.rating = (entry.rating === rating) ? 0 : rating; // 同じ星を再タップで解除
  saveSakecho(list);
  renderSakecho();
}

function removeSakecho(id){
  const list = getSakecho().filter(e => e.id !== id);
  saveSakecho(list);
  renderSakecho();
  renderBreweryList();
}

function starsHtml(entryId, rating){
  let html = `<div class="stars" data-id="${entryId}">`;
  for(let i = 1; i <= 5; i++){
    html += `<button type="button" class="star ${i <= rating ? "on" : ""}" data-rating="${i}" aria-label="${i}つ星評価">★</button>`;
  }
  html += `</div>`;
  return html;
}

function renderSakecho(){
  const list = getSakecho();
  const box = document.getElementById("sakecho-list");
  const empty = document.getElementById("sakecho-empty");
  if(list.length === 0){
    box.innerHTML = "";
    empty.style.display = "block";
    return;
  }
  empty.style.display = "none";
  box.innerHTML = `<div class="item-list">${list.map(entry => `
    <div class="sakecho-row" data-id="${entry.id}">
      <div class="sakecho-main">
        <input type="text" class="sakecho-label" value="${escapeHtml(entry.label)}" placeholder="銘柄を記入">
        ${entry.name && entry.name !== entry.label ? `<div class="sakecho-sub">蔵元：${escapeHtml(entry.name)}</div>` : ""}
        ${starsHtml(entry.id, entry.rating)}
      </div>
      <button type="button" class="sakecho-remove" aria-label="削除">✕</button>
    </div>
  `).join("")}</div>`;

  box.querySelectorAll(".sakecho-label").forEach(input => {
    input.addEventListener("change", () => {
      updateSakechoLabel(input.closest(".sakecho-row").dataset.id, input.value);
    });
  });
  box.querySelectorAll(".star").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.closest(".stars").dataset.id;
      updateSakechoRating(id, Number(btn.dataset.rating));
    });
  });
  box.querySelectorAll(".sakecho-remove").forEach(btn => {
    btn.addEventListener("click", () => {
      removeSakecho(btn.closest(".sakecho-row").dataset.id);
    });
  });
}

document.getElementById("sakecho-add").addEventListener("click", addSakechoBlank);

function escapeHtml(str){
  return String(str).replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }[c]));
}

// ==== ライブ状況（完売・お知らせ） ====
let liveData = { soldOut: [], notice: "" };

async function loadLiveStatus(){
  if(!LIVE_ENDPOINT) return;
  try{
    const res = await fetch(LIVE_ENDPOINT, { cache: "no-store" });
    const data = await res.json();
    liveData = {
      soldOut: Array.isArray(data.soldOut) ? data.soldOut.map(Number) : [],
      notice: typeof data.notice === "string" ? data.notice : ""
    };
  }catch(e){
    // 通信できない場合は直前の状態を維持（会場の電波混雑を想定）
  }
  renderNotice();
  renderBreweryList();
}

function renderNotice(){
  const bar = document.getElementById("notice-bar");
  if(liveData.notice){
    bar.textContent = "📢 " + liveData.notice;
    bar.hidden = false;
  }else{
    bar.hidden = true;
  }
}

function startLivePolling(){
  if(!LIVE_ENDPOINT) return;
  loadLiveStatus();
  setInterval(loadLiveStatus, LIVE_POLL_MS);
  document.addEventListener("visibilitychange", () => {
    if(document.visibilityState === "visible") loadLiveStatus();
  });
}

// ==== 蔵元・銘柄 ====
let breweryData = null;
let activeCategory = "all";
let activeZone = "all";
const ZONES = [
  { id: "A", label: "Aゾーン", min: 1, max: 20 },
  { id: "B", label: "Bゾーン", min: 21, max: 42 },
  { id: "C", label: "Cゾーン", min: 43, max: 62 }
];
function zoneOf(booth){
  const z = ZONES.find(z => booth >= z.min && booth <= z.max);
  return z ? z.id : null;
}

async function loadBreweries(){
  const res = await fetch("data/breweries.json", { cache: "no-store" });
  breweryData = await res.json();
  renderBreweryFilters();
  renderBreweryList();
}

function setZoneFilter(zoneId){
  activeZone = zoneId;
  renderBreweryFilters();
  renderBreweryList();
}

function renderBreweryFilters(){
  const catBox = document.getElementById("brewery-filters");
  const cats = [{id:"all", label:"すべて"}, ...breweryData.categories.map(c => ({id:c.id, label:c.label}))];
  catBox.innerHTML = cats.map(c => `
    <button class="filter-chip ${c.id === activeCategory ? "active" : ""}" data-cat="${c.id}">${escapeHtml(c.label)}</button>
  `).join("");
  catBox.querySelectorAll(".filter-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      activeCategory = chip.dataset.cat;
      renderBreweryFilters();
      renderBreweryList();
    });
  });

  const zoneBox = document.getElementById("brewery-zone-filters");
  const zones = [{id:"all", label:"エリア: すべて"}, ...ZONES.map(z => ({id:z.id, label:z.label}))];
  zoneBox.innerHTML = zones.map(z => `
    <button class="filter-chip ${z.id === activeZone ? "active" : ""}" data-zone="${z.id}">${escapeHtml(z.label)}</button>
  `).join("");
  zoneBox.querySelectorAll(".filter-chip").forEach(chip => {
    chip.addEventListener("click", () => setZoneFilter(chip.dataset.zone));
  });
}

function renderBreweryList(){
  const box = document.getElementById("brewery-list");
  const q = (document.getElementById("brewery-search").value || "").trim();
  const drankCounts = {};
  getSakecho().forEach(e => { drankCounts[e.name] = (drankCounts[e.name] || 0) + 1; });

  let cats = breweryData.categories;
  if(activeCategory !== "all") cats = cats.filter(c => c.id === activeCategory);

  let html = "";
  cats.forEach(cat => {
    let items = cat.items.filter(item => !q || item.name.includes(q) || String(item.booth) === q);
    if(activeZone !== "all") items = items.filter(item => zoneOf(item.booth) === activeZone);
    items = [...items].sort((a, b) => a.booth - b.booth);
    if(items.length === 0) return;
    html += `<div class="section-title">${escapeHtml(cat.label)}（${items.length}）</div>`;
    html += `<div class="item-list">`;
    html += items.map(item => {
      const count = drankCounts[item.name] || 0;
      const soldOut = liveData.soldOut.includes(item.booth);
      return `
      <div class="item-row ${soldOut ? "soldout" : ""}">
        <span class="booth-badge">${item.booth}</span>
        <div class="item-main">
          <div class="name">${escapeHtml(item.name)} ${soldOut ? '<span class="badge soldout">完売</span>' : ""}</div>
        </div>
        <button class="drank-btn ${count > 0 ? "on" : ""}" data-name="${escapeHtml(item.name)}" aria-label="飲んだ酒として記録（タップするたびに追加）">${count > 0 ? count : "✓"}</button>
      </div>
    `;
    }).join("");
    html += `</div>`;
  });

  box.innerHTML = html || `<div class="empty-note">該当する蔵元・銘柄が見つかりません。</div>`;

  box.querySelectorAll(".drank-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      addSakechoQuick(btn.dataset.name);
      renderBreweryList();
      renderSakecho();
    });
  });
}

document.getElementById("brewery-search").addEventListener("input", renderBreweryList);

// ==== フード ====
let foodShops = [];
let foodData = null;

async function loadFood(){
  const res = await fetch("data/food.json", { cache: "no-store" });
  foodData = await res.json();
  foodShops = [];
  const box = document.getElementById("food-list");
  box.innerHTML = foodData.groups.map(group => `
    <div class="section-title">${escapeHtml(group.label)}</div>
    <div class="item-list">
      ${group.shops.map(shop => {
        const idx = foodShops.push(shop) - 1;
        const zoneTag = shop.zone ? `<span class="booth-badge zone-badge">${escapeHtml(shop.zone)}ゾーン</span>` : "";
        return `
        <div class="item-row tappable" data-shop-idx="${idx}">
          ${shop.mapLabel ? `<span class="booth-badge">${escapeHtml(shop.mapLabel)}</span>` : zoneTag}
          ${shop.image ? `<img class="thumb" src="${shop.image}" alt="" loading="lazy" onerror="this.style.display='none'">` : ""}
          <div class="item-main">
            <div class="name">${escapeHtml(shop.name)} ${shop.toilet ? '<span class="badge toilet">お手洗い可</span>' : ""}</div>
            ${shop.menu ? `<div class="menu">${escapeHtml(shop.menu)}</div>` : ""}
          </div>
        </div>
      `;
      }).join("")}
    </div>
  `).join("");

  box.querySelectorAll(".item-row.tappable").forEach(row => {
    row.addEventListener("click", () => openDetail(foodShops[Number(row.dataset.shopIdx)]));
  });
}

// ==== 店舗詳細モーダル ====
const detailModal = document.getElementById("detail-modal");
const detailImage = document.getElementById("detail-image");
const detailImageWrap = detailImage.parentElement;

function openDetail(shop){
  document.getElementById("detail-name").textContent = shop.name;
  document.getElementById("detail-menu").textContent = shop.menu || "";
  if(shop.image){
    detailImage.src = shop.image;
    detailImage.alt = shop.name;
    detailImageWrap.classList.remove("no-image");
  }else{
    detailImageWrap.classList.add("no-image");
  }
  detailModal.classList.add("open");
  detailModal.setAttribute("aria-hidden", "false");
}

function closeDetail(){
  detailModal.classList.remove("open");
  detailModal.setAttribute("aria-hidden", "true");
}

document.getElementById("detail-close").addEventListener("click", closeDetail);
detailModal.addEventListener("click", (e) => { if(e.target === detailModal) closeDetail(); });

// ==== 会場マップ拡大表示 ====
const mapLightbox = document.getElementById("map-lightbox");
document.getElementById("map-image-open").addEventListener("click", () => {
  mapLightbox.classList.add("open");
  mapLightbox.setAttribute("aria-hidden", "false");
});
document.getElementById("map-lightbox-close").addEventListener("click", () => {
  mapLightbox.classList.remove("open");
  mapLightbox.setAttribute("aria-hidden", "true");
});

// ==== インフォ ====
async function loadInfo(){
  const res = await fetch("data/info.json", { cache: "no-store" });
  const data = await res.json();

  document.getElementById("header-sub").textContent =
    `${data.event.venue} ／ ${data.event.date} ${data.event.time.split("（")[0]}`;

  document.getElementById("map-access").innerHTML = `
    <div class="info-block" style="margin-bottom:0;">
      <ul>${data.event.access.map(a => `<li>${escapeHtml(a)}</li>`).join("")}</ul>
    </div>
  `;

  // ゾーン帯（マップタブ）
  document.getElementById("zone-strip").innerHTML = `
    <div class="zone-station">🚉 JR清水駅 西口</div>
    ${data.zones.map(z => `
      <button type="button" class="zone-band" data-zone="${z.id}">
        <span class="zid">${z.id}</span>
        <span class="ztext">
          <span class="zlabel">${escapeHtml(z.label)}</span><br>
          <span class="zrange">${escapeHtml(z.range)}</span>
          <div class="zdesc">${escapeHtml(z.desc)}</div>
          <div class="zfood" id="zfood-${z.id}"></div>
        </span>
      </button>
    `).join("")}
  `;
  document.querySelectorAll(".zone-band").forEach(btn => {
    btn.addEventListener("click", () => {
      setZoneFilter(btn.dataset.zone);
      showView("breweries");
    });
  });

  // 会場設備（マップタブ）
  document.getElementById("facility-list").innerHTML = `
    <div class="card">
      ${data.facilities.map(f => `
        <div class="facility-row">
          <div class="flabel">${escapeHtml(f.label)}</div>
          <div class="fnote">${escapeHtml(f.note)}</div>
        </div>
      `).join("")}
    </div>
  `;

  document.getElementById("info-content").innerHTML = `
    <div class="info-block">
      <h3>開催概要</h3>
      <div class="fact"><dt>イベント</dt><dd>${escapeHtml(data.event.title)}</dd></div>
      <div class="fact"><dt>日程</dt><dd>${escapeHtml(data.event.date)}</dd></div>
      <div class="fact"><dt>時間</dt><dd>${escapeHtml(data.event.time)}</dd></div>
      <div class="fact"><dt>会場</dt><dd>${escapeHtml(data.event.venue)}</dd></div>
      <div class="fact"><dt>主催</dt><dd>${escapeHtml(data.event.organizer)}</dd></div>
    </div>
    <div class="info-block">
      <h3>チケット引換</h3>
      <ul>${data.ticketExchange.map(t => `<li>${escapeHtml(t)}</li>`).join("")}</ul>
    </div>
    <div class="info-block">
      <h3>タイムテーブル</h3>
      <ul>${data.sessions.map(s => `<li><strong>${escapeHtml(s.time)}</strong>　${escapeHtml(s.name)}</li>`).join("")}</ul>
    </div>
    <div class="info-block">
      <h3>会場ルール</h3>
      <ul>${data.rules.map(r => `<li>${escapeHtml(r)}</li>`).join("")}</ul>
    </div>
  `;
}

// ゾーンカードに、そのエリアの屋台を一覧で追記する（マップタブ）
function renderZoneFood(){
  if(!foodData) return;
  const yatai = foodData.groups.find(g => g.id === "yatai");
  if(!yatai) return;
  ZONES.forEach(z => {
    const el = document.getElementById(`zfood-${z.id}`);
    if(!el) return;
    const names = yatai.shops.filter(s => s.zone === z.id).map(s => s.name);
    el.textContent = names.length ? `屋台: ${names.join("・")}` : "";
  });
}

// ==== 初期化 ====
(async function init(){
  showView(localStorage.getItem("js_last_tab") || "map");
  renderSakecho();
  await Promise.all([loadBreweries(), loadFood(), loadInfo()]);
  renderZoneFood();
  startLivePolling();

  if("serviceWorker" in navigator){
    navigator.serviceWorker.register("sw.js").catch(() => {});
  }
})();
