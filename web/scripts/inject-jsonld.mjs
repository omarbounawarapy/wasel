// Runs after `next build` (npm "postbuild"): puts the SoftwareApplication JSON-LD into dist/index.html.
// Values come from the same env and constants as the page metadata. Only facts that are true: no rating, no price.
import { readFileSync, writeFileSync } from "node:fs"

const site = (process.env.NEXT_PUBLIC_SITE_URL || "").replace(/\/+$/, "")
if (!site) {
  console.error("inject-jsonld: NEXT_PUBLIC_SITE_URL is not set")
  process.exit(1)
}
const data = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "Wasel",
  description:
    "Wasel reads what your cash-on-delivery customers write, scores the refusal risk and drafts the confirmation message.",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  url: `${site}/`,
  image: `${site}/wasel-mark.png`,
}
const file = new URL("../dist/index.html", import.meta.url)
let html = readFileSync(file, "utf8")
if (html.includes("application/ld+json")) process.exit(0)
const tag = `<script type="application/ld+json">${JSON.stringify(data).replace(/</g, "\\u003c")}</script>`
if (!html.includes("</head>")) {
  console.error("inject-jsonld: no </head> in dist/index.html")
  process.exit(1)
}
html = html.replace("</head>", `${tag}</head>`)
writeFileSync(file, html)
console.log("inject-jsonld: added SoftwareApplication to dist/index.html")
