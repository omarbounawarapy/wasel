// Wasel service worker: caches the app shell so an installed app opens offline to a clear page.
// It never stores /api responses (they hold customer text) and never answers a non-GET request.
const SHELL = "wasel-shell-v1"
const ASSETS = ["/offline.html", "/wasel-logo-compact.png", "/icon-192.png"]

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(SHELL).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()))
})

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== SHELL).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener("fetch", (event) => {
  const req = event.request
  const url = new URL(req.url)
  if (req.method !== "GET" || url.origin !== self.location.origin) return
  if (url.pathname.startsWith("/api")) return // network only, nothing kept

  if (req.mode === "navigate") {
    // Pages: network first, the offline page when the network is down.
    event.respondWith(fetch(req).catch(() => caches.match("/offline.html")))
    return
  }
  if (url.pathname.startsWith("/_next/static/")) {
    // Hashed build files never change under the same name: cache first.
    event.respondWith(
      caches.match(req).then((hit) => hit || fetch(req).then((res) => {
        const copy = res.clone()
        caches.open(SHELL).then((c) => c.put(req, copy))
        return res
      })),
    )
  }
})
