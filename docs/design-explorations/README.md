# Wasel design explorations

Static HTML mockups made while choosing a logo, brand world and dashboard structure for Wasel. Open any `index.html` in a browser (fonts load from Google Fonts). Nothing here is applied to `web/` and none of it is committed. All order data is synthetic.

| Folder | What it is |
|---|---|
| `01-logo-sketches` | 20 logo ideas (`grid.html`), 14 refinements of the shortlist (`refine.html`), the first 4 sketches |
| `02-logo-in-context` | Four finalist logos in a sidebar, tab, phone icon, avatar, social card and one colour |
| `03-premium-directions-v1` | Six "premium" directions. Rejected: they were one dashboard repainted |
| `04-worlds-from-tunisia` | Four brand worlds from the seller's own culture (tile geometry, waybills, rail diagram, grid) |
| `05-six-philosophies` | Swiss, De Stijl, Isotype, Ma and Rams, Tufte, Beck: six different product structures |
| `06-twenty-schools` | Twenty schools, each researched, each a different structure (Bauhaus to Marey's timetable) |
| `07-ops-dashboard-families` | Sixteen real operations-dashboard families (Bloomberg, observability, blotter, review queue, control tower, incident console, CAD, clinical station, ISA-101, ATC, support inbox, Polaris, Fiori, Carbon, wallboard, Linear) with a fit verdict for Wasel |
| `_source` | Python generators and CSS that produce the pages |

Owner's stated preferences: directions must differ in structure and philosophy, not just colour; each school or family researched individually and the design idea written before drawing; now a serious, professional operations-dashboard look. See `PRODUCT.md` for product truth.

## Planning files (added for the brand-book project)

| File | What it is |
|---|---|
| `BRIEF-AND-PLAN.md` | The request, rules, saved assets, real project content, phases and tasks, risks and open decisions |
| `registry.json` | 16 unique brand identities, built by `_source/registry_build.py` (which checks for reuse) |
| `_data/` | Real API responses from the running app (synthetic seed data) |
| `book/` | The standalone brand book: one offline file per direction plus `index.html` (built by `_source/book/assemble.py`). Built so far: `04-review-queue.html`, `01-terminal.html` |
| `dataset.json`, `content.json` | The synthetic data and the real project copy every screen reads |
| `_fonts/` | The 48 woff2 font families embedded into the book |
