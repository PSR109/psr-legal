// Service worker: caché offline básica, cache-first para estáticos.
// Subir la versión al cambiar cualquier archivo cacheado.
const CACHE = '{{APP_NOMBRE}}-v1';
const ASSETS = ['./', 'index.html', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png'];

self.addEventListener('install', (e) => {
    e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
    self.skipWaiting();
});

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', (e) => {
    // Nunca cachear anuncios ni analytics: solo mismo origen.
    if (new URL(e.request.url).origin !== location.origin) return;
    e.respondWith(
        caches.match(e.request).then((hit) => hit || fetch(e.request))
    );
});
