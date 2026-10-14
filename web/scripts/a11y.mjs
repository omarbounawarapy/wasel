// Accessibility run over every route of a running Wasel (the API serving web/dist): axe-core rules WCAG 2.2 AA,
// in light and dark colour schemes, at phone and desktop width, plus the skip-link keyboard check.
// Usage: BASE_URL=http://localhost:8000 npm run a11y     (CHROME_PATH overrides the browser binary)
import { readFileSync } from "node:fs"
import puppeteer from "puppeteer-core"

const BASE = (process.env.BASE_URL || "http://localhost:8000").replace(/\/$/, "")
const CHROME = process.env.CHROME_PATH || "/usr/bin/google-chrome"
const axeSource = readFileSync(new URL("../node_modules/axe-core/axe.min.js", import.meta.url), "utf8")

const ROUTES = ["/", "/dashboard/", "/dashboard/inbox/", "/dashboard/paste/", "/dashboard/impact/", "/dashboard/activity/",
  "/dashboard/quality/", "/dashboard/monitor/", "/dashboard/traces/", "/dashboard/failures/", "/privacy/", "/no-such-page/"]
const VIEWS = [{ name: "phone", width: 390, height: 844 }, { name: "desktop", width: 1440, height: 900 }]
const SCHEMES = ["light", "dark"]

const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ["--no-sandbox"] })
let failures = 0
try {
  const list = await fetch(`${BASE}/api/orders?limit=1`, { headers: { "X-Visitor-Id": "00000000-0000-4000-8000-0000000000a1" } }).then(r => r.json()).catch(() => null)
  const first = list?.orders?.[0]?.order_id
  const routes = first ? [...ROUTES, `/dashboard/order/?id=${first}`] : ROUTES

  for (const scheme of SCHEMES) {
    for (const view of VIEWS) {
      const page = await browser.newPage()
      await page.setViewport({ width: view.width, height: view.height })
      await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: scheme }])
      for (const route of routes) {
        await page.goto(BASE + route, { waitUntil: "networkidle2", timeout: 60000 }).catch(() => {})
        await new Promise(r => setTimeout(r, 1200))
        await page.evaluate(axeSource)
        const res = await page.evaluate(() => axe.run(document, {
          runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] },
        }))
        for (const v of res.violations) {
          failures++
          console.log(`FAIL ${scheme}/${view.name} ${route}: ${v.id} (${v.impact}) x${v.nodes.length}: ${v.help}`)
          for (const n of v.nodes.slice(0, 2)) console.log(`     ${n.target.join(" ")}  ${(n.any[0]?.message || n.failureSummary || "").split("\n")[0]}`)
        }
      }
      // keyboard: the first Tab stop is the skip link and it moves focus to <main>
      await page.goto(BASE + "/dashboard/", { waitUntil: "networkidle2", timeout: 60000 }).catch(() => {})
      await page.keyboard.press("Tab")
      const skip = await page.evaluate(() => ({ cls: document.activeElement?.className || "", href: document.activeElement?.getAttribute("href") }))
      if (!String(skip.cls).includes("skip-link")) { failures++; console.log(`FAIL ${scheme}/${view.name}: first Tab stop is not the skip link`) }
      await page.keyboard.press("Enter")
      const landed = await page.evaluate(() => document.activeElement?.id)
      if (landed !== "main") { failures++; console.log(`FAIL ${scheme}/${view.name}: skip link did not focus #main (got "${landed}")`) }
      await page.close()
    }
  }
} finally {
  await browser.close()
}
console.log(failures ? `a11y: ${failures} problem(s)` : `a11y: ${routes_label()} ok`)
function routes_label() { return "all routes, light+dark, phone+desktop" }
process.exit(failures ? 1 : 0)
