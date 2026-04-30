// Service Worker per Sempre Sol PWA
const CACHE_NAME = 'sempresol-v1';
const urlsToCache = [
    '/',
    '/index.html',
    '/manifest.json',
    '/privacy-policy.html',
    '/avis-legal.html',
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js'
];

// Install event - cache les coses
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Cache obert');
                return cache.addAll(urlsToCache.map(url => new Request(url, {cache: 'reload'})))
                    .catch(err => {
                        console.log('Error cacheando alguns recursos:', err);
                        // No fallar si no es pot descarregar tot
                    });
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

// Fetch event - servir des de cache, amb fallback a network
self.addEventListener('fetch', event => {
    // No cachejar les sol·licituds POST o altre mètode no GET
    if (event.request.method !== 'GET') {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Si hi ha a cache, retornar-ho
                if (response) {
                    return response;
                }

                // Si no, intentar des de xarxa
                return fetch(event.request)
                    .then(response => {
                        // No cachejar respostes no-OK
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clonar la resposta
                        const responseToCache = response.clone();

                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    })
                    .catch(error => {
                        console.log('Error a la fetch:', error);
                        // Aquí es pot retornar una pàgina offline si existeix
                        return new Response('Offline - Torna a intentar-ho quan tens connexió', {
                            status: 503,
                            statusText: 'Service Unavailable',
                            headers: new Headers({
                                'Content-Type': 'text/plain'
                            })
                        });
                    });
            })
    );
});

// Message handler per comunicació amb la pàgina principal
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
