// Fails when an exported page is missing what a shared link or a search result needs:
// a unique non-empty <title> (not the bare root title), a meta description of at most 160 characters, a canonical URL.
// Run after `npm run build`: `npm run check:pages` (also run by CI, and by `make check` when web/dist exists).
import { readdirSync, readFileSync, statSync } from "node:fs"
import { join, relative } from "node:path"

const dist = new URL("../dist", import.meta.url).pathname
const ROOT_TITLE = "Wasel · COD order risk"

function pages(dir) {
  const out = []
  for (const name of readdirSync(dir)) {
    const p = join(dir, name)
    if (name === "_next" || name === "_not-found" || name === ".well-known") continue
    if (statSync(p).isDirectory()) out.push(...pages(p))
    else if (name === "index.html") out.push(p)
  }
  return out
}

const files = pages(dist)
if (!files.length) {
  console.error("check-pages: no index.html under web/dist; run `npm run build` first")
  process.exit(2)
}
const problems = []
const titles = new Map()
const pick = (html, re) => (html.match(re) || [])[1]?.trim() ?? ""

const isNotFound = (rel) => rel === "/404.html" || rel === "/404/"

for (const f of files.concat(join(dist, "404.html"))) {
  let html
  try { html = readFileSync(f, "utf8") } catch { continue }
  const rel = "/" + relative(dist, f).replace(/index\.html$/, "")
  const title = pick(html, /<title>([^<]*)<\/title>/)
  const desc = pick(html, /<meta name="description" content="([^"]*)"/)
  const canon = pick(html, /<link rel="canonical" href="([^"]*)"/)
  if (!title) problems.push(`${rel}: empty <title>`)
  else if (rel !== "/" && title === ROOT_TITLE) problems.push(`${rel}: has only the root title`)
  else if (!isNotFound(rel) && !/ · Wasel$/.test(title) && title !== ROOT_TITLE) problems.push(`${rel}: title "${title}" is not "Page · Wasel"`)
  if (titles.has(title) && !isNotFound(rel) && !isNotFound(titles.get(title))) problems.push(`${rel}: same title as ${titles.get(title)}`)
  titles.set(title, rel)
  if (!desc) problems.push(`${rel}: no meta description`)
  else if (desc.length > 160) problems.push(`${rel}: description is ${desc.length} characters (max 160)`)
  if (!canon && !isNotFound(rel)) problems.push(`${rel}: no canonical URL`)
  if (canon && !/^https?:\/\//.test(canon)) problems.push(`${rel}: canonical is not absolute: ${canon}`)
}
if (problems.length) {
  console.error("check-pages: FAIL\n  " + problems.join("\n  "))
  process.exit(1)
}
console.log(`check-pages: ${files.length} pages ok (titles, descriptions, canonical)`)
