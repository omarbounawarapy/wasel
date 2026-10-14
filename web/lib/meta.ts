import type { Metadata } from "next"
import { INDEXABLE, PAGES, SITE_NAME, type PagePath } from "@/lib/site"

/** Metadata for one route: its own title, description, canonical URL and share card (served from the PAGES table). */
export function pageMeta(path: PagePath): Metadata {
  const { title, description } = PAGES[path]
  const url = path === "/" ? "/" : `${path}/`
  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: { title, description, url, siteName: SITE_NAME, type: "website", images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "Wasel: High 87 before the customer's reply, Low 16 after" }] },
    twitter: { card: "summary_large_image", title, description, images: ["/og-image.png"] },
    robots: INDEXABLE ? undefined : { index: false, follow: false },
  }
}
