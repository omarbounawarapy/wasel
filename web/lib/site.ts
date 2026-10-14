// Build-time site facts shared by the metadata, robots, sitemap and structured data.
// NEXT_PUBLIC_SITE_URL is the public origin. `npm run dev` falls back to localhost; a production build refuses to
// run without it, so a canonical URL or share card can never point at the wrong host.
const fromEnv = process.env.NEXT_PUBLIC_SITE_URL?.trim().replace(/\/+$/, "")

if (!fromEnv && process.env.NODE_ENV === "production") {
  throw new Error("NEXT_PUBLIC_SITE_URL is not set. Set it to the public origin (https://wasel.runs-on.dev) before `npm run build`.")
}

export const SITE_URL = fromEnv || "http://localhost:5173"

// The demo shows synthetic data under the product name, so it is kept out of search results unless this is "1".
export const INDEXABLE = process.env.NEXT_PUBLIC_INDEXABLE === "1"

export const SITE_NAME = "Wasel"
export const SITE_TITLE = "Wasel · COD order risk"
export const SITE_DESCRIPTION =
  "Wasel reads what your cash-on-delivery customers write, scores the refusal risk and drafts the confirmation message."
export const CONTACT_EMAIL = "contact@wasel.runs-on.dev"

// Every public route of the export, with its title and one-sentence description (at most 160 characters).
// The route layouts, the sitemap and the checks all read this one table.
export const PAGES = {
  "/": {
    title: "Wasel · COD order risk",
    description: SITE_DESCRIPTION,
  },
  "/dashboard": {
    title: "Orders to check · Wasel",
    description: "Every cash-on-delivery order sorted by refusal risk, with the next step to take for each one.",
  },
  "/dashboard/inbox": {
    title: "WhatsApp messages · Wasel",
    description: "The customer conversations behind your orders, with Wasel's drafted reply ready for you to review and send.",
  },
  "/dashboard/paste": {
    title: "Add an order · Wasel",
    description: "Paste a customer's message in Darija, Arabizi, Arabic or French and get a refusal-risk score in seconds.",
  },
  "/dashboard/order": {
    title: "Order · Wasel",
    description: "One order in detail: the customer's messages, what Wasel understood, the risk score and the reply to send.",
  },
  "/dashboard/impact": {
    title: "Money saved · Wasel",
    description: "How many refused deliveries Wasel is expected to prevent and what that is worth, from the demo data.",
  },
  "/dashboard/activity": {
    title: "Activity log · Wasel",
    description: "A time-ordered record of orders received, messages scored and replies sent on this server.",
  },
  "/dashboard/quality": {
    title: "Quality checks · Wasel",
    description: "How accurate Wasel's reading and scoring are on the test sets, and where it still gets things wrong.",
  },
  "/dashboard/monitor": {
    title: "Live monitor · Wasel",
    description: "Whether the AI models are answering, how fast, and how much of today's AI budget is left.",
  },
  "/dashboard/traces": {
    title: "AI call log · Wasel",
    description: "Every call Wasel made to an AI model: what was asked, what came back and how long it took.",
  },
  "/dashboard/failures": {
    title: "Silent failures · Wasel",
    description: "Orders where the AI read the message wrongly without any error, found by comparing it to the rules.",
  },
  "/privacy": {
    title: "Privacy · Wasel",
    description: "What the Wasel demo stores, for how long, which providers receive message text and who to contact.",
  },
} as const

export type PagePath = keyof typeof PAGES
