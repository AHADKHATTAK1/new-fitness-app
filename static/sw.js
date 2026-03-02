const CACHE_NAME = 'gym-manager-v7';
const STATIC_ASSETS = [
    '/auth',
    '/static/offline-db.js',
    '/static/css/mobile.min.css',
    '/static/css/loading.css',
    '/static/css/buttons.css',
    '/static/js/pwa-install.js',
    '/static/manifest.json',
    '/static/manifest.webmanifest'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[Service Worker] Caching static assets');
                return cache.addAll(STATIC_ASSETS).catch(err => {
                    console.log('[Service Worker] Cache failed for some assets', err);
                });
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activating...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch Strategy: Network First, fallback to Cache
self.addEventListener('fetch', event => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then(response => {
                const responseClone = response.clone();

                // Cache only static assets to avoid stale dynamic HTML/UI data
                const requestUrl = new URL(event.request.url);
                const isStaticAsset = requestUrl.pathname.startsWith('/static/');

                if (response && response.status === 200 && isStaticAsset) {
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, responseClone);
                    });
                }

                return response;
            })
            .catch(() => {
                return caches.match(event.request)
                    .then(response => {
                        if (response) {
                            return response;
                        }

                        if (event.request.mode === 'navigate') {
                            return caches.match('/auth');
                        }
                    });
            })
    );
});
