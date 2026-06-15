const CACHE = 'estoque3d-v3';
const STATIC_CACHE = 'estoque3d-static-v3';

const STATIC_ASSETS = [
  '/static/manifest.json',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/img/harborio-logo.png',
  '/static/img/icon-192.svg',
  '/static/img/icon-512.svg',
  '/static/favicon.ico',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
];

self.addEventListener('install', function(e) {
  e.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE).then(function(cache) {
        return cache.addAll(STATIC_ASSETS);
      }),
      caches.open(CACHE).then(function(cache) {
        return cache.add('/offline');
      })
    ])
  );
  self.skipWaiting();
});

self.addEventListener('activate', function(e) {
  e.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(k) { return k !== CACHE && k !== STATIC_CACHE; }).map(function(k) { return caches.delete(k); })
      );
    })
  );
  self.clients.claim();
});

function isStaticAsset(url) {
  var path = url.pathname || url;
  return STATIC_ASSETS.some(function(asset) {
    return path.indexOf(asset) !== -1;
  }) || /\.(css|js|woff2?|png|svg|ico|jpg|jpeg|webp)(\?.*)?$/.test(path);
}

function isApiRequest(url) {
  return url.pathname && url.pathname.indexOf('/api/') !== -1;
}

function isPageRequest(url) {
  return !isStaticAsset(url) && !isApiRequest(url);
}

self.addEventListener('fetch', function(e) {
  var url = new URL(e.request.url);

  // Static assets: cache-first
  if (isStaticAsset(url)) {
    e.respondWith(
      caches.match(e.request).then(function(cached) {
        return cached || fetch(e.request).then(function(response) {
          if (response && response.ok) {
            var copy = response.clone();
            caches.open(STATIC_CACHE).then(function(cache) { cache.put(e.request, copy); });
          }
          return response;
        });
      })
    );
    return;
  }

  // API requests: network-only (no caching)
  if (isApiRequest(url)) {
    e.respondWith(fetch(e.request));
    return;
  }

  // Page requests: network-first, fallback to cache, then offline page
  e.respondWith(
    fetch(e.request).then(function(response) {
      if (response && response.ok) {
        var copy = response.clone();
        caches.open(CACHE).then(function(cache) { cache.put(e.request, copy); });
      }
      return response;
    }).catch(function() {
      return caches.match(e.request).then(function(cached) {
        return cached || caches.match('/offline');
      });
    })
  );
});

// Listen for badge updates from the app
self.addEventListener('message', function(e) {
  if (e.data && e.data.type === 'SET_BADGE') {
    if (self.navigator.setAppBadge) {
      self.navigator.setAppBadge(e.data.count);
    } else if (self.navigator.setExperimentalAppBadge) {
      self.navigator.setExperimentalAppBadge(e.data.count);
    }
  }
  if (e.data && e.data.type === 'CLEAR_BADGE') {
    if (self.navigator.clearAppBadge) {
      self.navigator.clearAppBadge();
    } else if (self.navigator.clearExperimentalAppBadge) {
      self.navigator.clearExperimentalAppBadge();
    }
  }
});