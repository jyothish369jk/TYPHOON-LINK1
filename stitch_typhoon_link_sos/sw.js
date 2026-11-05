/**
 * TyphoonLink Service Worker (PWA Offline Shell Cache)
 * 
 * NOTICE & LIMITATION:
 * This service worker caches static UI assets (HTML, CSS, client scripts, icons)
 * so that the user interface loads instantly on disconnected devices.
 * It DOES NOT provide wireless radio transmission, BLE mesh routing, or satellite
 * communication during complete hardware network blackouts.
 */

const CACHE_NAME = 'typhoon-link-v1';
const ASSETS_TO_CACHE = [
  './citizen_offline_sos_dispatcher_simplified/code.html',
  './volunteer_triage_deduplication_feed/code.html',
  './hyper_local_cyclone_grid_resource_map/code.html',
  './satellite_intelligence_disaster_mapping_mobile/code.html',
  './js/offline_queue.js',
  'https://cdn.tailwindcss.com',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200',
  'https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[TyphoonLink SW] Pre-caching emergency UI shell assets...');
      return cache.addAll(ASSETS_TO_CACHE).catch((err) => {
        console.warn('[TyphoonLink SW] Pre-cache partial failure (non-blocking for CDN items):', err);
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[TyphoonLink SW] Purging obsolete cache:', key);
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Pass through backend API calls directly (handled by offline_queue.js IndexedDB)
  if (event.request.url.includes('/api/')) {
    return;
  }

  // Stale-while-revalidate or Network-first strategy for UI shell
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        // Fetch background refresh if online
        fetch(event.request)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              caches.open(CACHE_NAME).then((cache) => cache.put(event.request, networkResponse));
            }
          })
          .catch(() => {});
        return cachedResponse;
      }
      return fetch(event.request).catch(() => {
        // Fallback for document navigation
        if (event.request.mode === 'navigate') {
          return caches.match('./citizen_offline_sos_dispatcher_simplified/code.html');
        }
      });
    })
  );
});
