// Time's Up — offline support
// Caches the app on first load so it opens without internet after that.
// Bump CACHE_NAME whenever you update times-up.html so old caches get replaced.

const CACHE_NAME = 'times-up-v1';
const FILES_TO_CACHE = [
  './times-up.html',
  './manifest.json',
  './pwa-assets/icon-192.png',
  './pwa-assets/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(FILES_TO_CACHE))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

// Cache-first: try the cache, fall back to the network, and cache new copies as they come in.
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          return response;
        })
        .catch(() => caches.match('./times-up.html'));
    })
  );
});
