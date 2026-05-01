// Service Worker per Sempre Sol PWA
const CACHE_NAME = 'sempresol-v3';  // ← V3 per forçar actualització
const urlsToCache = [
    '/',
    '/index.html',
    '/manifest.json',
    '/privacy-policy.html',
    '/avis-legal.html'
];

// Install event - cache les coses bàsiques
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Cache obert');
                return cache.addAll(urlsToCache);
            })
            .catch(err => {
                console.log('Error cacheando recursos:', err);
            })
    );
    self.skipWaiting();
});

// Activate event - neteja caches velles
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Eliminando cache antigua:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch event - network first, fallback a cache
self.addEventListener('fetch', event => {
    // No interceptar POST requests
    if (event.request.method !== 'GET') {
        return;
    }

    // Per a recursos externs (CDN, API), prioritat a network
    if (event.request.url.includes('cdnjs') || event.request.url.includes('api')) {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    // Clonar i cachear si és OK
                    if (response && response.status === 200) {
                        const responseToCache = response.clone();
                        caches.open(CACHE_NAME).then(cache => {
                            cache.put(event.request, responseToCache);
                        });
                    }
                    return response;
                })
                .catch(() => {
                    // Si falla la xarxa, intentar cache
                    return caches.match(event.request);
                })
        );
        return;
    }

    // Per a recursos locals, cache first
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                if (response) {
                    return response;
                }
                return fetch(event.request)
                    .then(response => {
                        if (!response || response.status !== 200) {
                            return response;
                        }
                        const responseToCache = response.clone();
                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, responseToCache);
                            });
                        return response;
                    })
                    .catch(error => {
                        console.log('Error fetch:', error);
                    });
            })
    );
});

