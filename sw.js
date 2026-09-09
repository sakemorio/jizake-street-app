const CACHE_NAME = "jizake-street-2026-v4";
const CORE_ASSETS = [
  "./",
  "./index.html",
  "./css/style.css",
  "./js/app.js",
  "./manifest.json",
  "./data/breweries.json",
  "./data/food.json",
  "./data/info.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./assets/venue-map.jpg"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

const isDataFile = (url) => /\/data\/.*\.json($|\?)/.test(url);

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = event.request.url;

  if (isDataFile(url)) {
    // data/*.json はネットワーク優先：現地でJSONを更新したら即反映されるようにする。
    // 電波が悪い/失敗した場合のみ、最後にキャッシュした内容にフォールバック。
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.status === 200) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // それ以外（HTML/CSS/JS/画像）はキャッシュ優先、裏でネットワーク更新（会場内の電波混雑を想定）
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const network = fetch(event.request)
        .then((response) => {
          if (response && response.status === 200) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
