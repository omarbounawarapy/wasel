"use client"

import { useEffect } from "react"

/** Registers /sw.js (app shell only, never /api) so an installed Wasel opens to an offline page instead of a browser error. */
export default function ServiceWorker() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production" || !("serviceWorker" in navigator)) return
    navigator.serviceWorker.register("/sw.js").catch(() => { /* private mode or blocked: the site works without it */ })
  }, [])
  return null
}
