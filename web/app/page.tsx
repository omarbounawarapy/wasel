import Landing from "@/components/Landing"
import { pageMeta } from "@/lib/meta"

export const metadata = pageMeta("/")

// The SoftwareApplication JSON-LD is added to dist/index.html by scripts/inject-jsonld.mjs after the build:
// React would HTML-escape a JSON script child, and raw HTML injection is banned in this repo (hygiene.sh).
export default function Home() {
  return <Landing />
}
