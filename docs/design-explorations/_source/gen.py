import html
N="#12386b"; T="#00abab"; I="#0b1d33"; G="#2f9e6e"; A="#f2a900"; R="#d6453d"; W="#ffffff"
S=lambda w,c,extra="": f'fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" {extra}'
C=[]
def add(name,idea,brief,svg,sizes_bg=None): C.append((name,idea,brief,svg))

add("Waw route","Arabic و (first letter of واصل) drawn as one route that ends at a stop.",
 "Brief: Geometric circle bowl + a single tail stroke curling left, ending in a teal dot. One idea, flat, two colours, readable at 16px.",
 f'<circle cx="64" cy="46" r="20" {S(13,N)}/><path d="M82 58 C90 92 72 110 34 104" {S(13,N)}/><circle cx="24" cy="102" r="8" fill="{T}"/>')
add("Square waw","Waw whose bowl is a parcel: the letter and the box are one shape.",
 "Brief: Replace the round bowl with a rounded square (the parcel), keep the same tail and dot. Reads as و first, box second.",
 f'<rect x="42" y="22" width="44" height="44" rx="10" {S(13,N)}/><path d="M82 62 C92 96 74 112 34 106" {S(13,N)}/><circle cx="24" cy="104" r="8" fill="{T}"/>')
add("Route W","One continuous line forms a W and arrives at a teal end point.",
 "Brief: Single stroke W, last leg teal with a terminal dot. Works as the Latin initial; the simplest mark in the set.",
 f'<path d="M16 30 L36 92 L60 42 L84 92" {S(13,N)}/><path d="M84 92 L104 30" {S(13,T)}/><circle cx="104" cy="30" r="7" fill="{T}"/>')
add("Parcel pin","A map pin with a taped parcel as its centre.",
 "Brief: Solid navy pin, white rounded square with a teal tape band. Says parcel + address instantly; strong favicon silhouette.",
 f'<path d="M60 114 C60 114 18 74 18 48 A42 42 0 0 1 102 48 C102 74 60 114 60 114Z" fill="{N}"/><rect x="40" y="28" width="40" height="40" rx="7" fill="{W}"/><rect x="40" y="43" width="40" height="9" fill="{T}"/>')
add("Delivered box","A box outline with a check that breaks out through the corner.",
 "Brief: Rounded square outline in navy; a teal check starts inside and exits past the corner = the parcel got out the door.",
 f'<rect x="20" y="30" width="72" height="72" rx="12" {S(12,N)}/><path d="M44 66 L60 82 L106 24" {S(13,T)}/>')
add("Doorstep","An arched door with the parcel waiting on the step.",
 "Brief: Navy arch (the customer's door), small teal square at its base. Ties directly to the COD refusal moment at the door.",
 f'<path d="M24 108 V54 A30 30 0 0 1 84 54 V108 Z" fill="{N}"/><rect x="72" y="76" width="34" height="32" rx="5" fill="{T}"/><rect x="72" y="88" width="34" height="6" fill="{W}"/>')
add("Split parcel","A square cut into accept / refuse halves by a diagonal gap.",
 "Brief: Two triangles, navy and teal, separated by a thin gap. Expresses a binary decision (ship or not) without a literal box.",
 f'<path d="M20 20 L88 20 L20 88 Z" fill="{N}"/><path d="M100 32 L100 100 L32 100 Z" fill="{T}"/>')
add("Tier arc","A semicircle gauge in the three real tier colours with a hub dot.",
 "Brief: Pure risk dial, no box. Green/amber/red arcs match the app's tiers so the logo and product share one language.",
 f'<path d="M18 84 A42 42 0 0 1 36 49" {S(14,G)}/><path d="M43 44 A42 42 0 0 1 77 44" {S(14,A)}/><path d="M84 49 A42 42 0 0 1 102 84" {S(14,R)}/><circle cx="60" cy="84" r="8" fill="{I}"/><path d="M60 84 L78 58" {S(7,I)}/>')
add("Chat parcel","A speech bubble whose body is a taped parcel.",
 "Brief: Navy rounded bubble with a tail bottom-left and a teal tape band. Speaks to orders placed in chat (WhatsApp).",
 f'<path d="M20 22 H100 a8 8 0 0 1 8 8 V78 a8 8 0 0 1 -8 8 H52 L28 106 V86 H20 a8 8 0 0 1 -8 -8 V30 a8 8 0 0 1 8 -8Z" fill="{N}"/><rect x="12" y="44" width="96" height="12" fill="{T}"/>')
add("Lens on box","A magnifier over a square: inspection of an order.",
 "Brief: Teal ring lens with a navy square inside and a short handle. Says assessment; avoids the 'safe' shield.",
 f'<circle cx="54" cy="54" r="34" {S(12,T)}/><rect x="38" y="38" width="32" height="32" rx="6" fill="{N}"/><path d="M80 80 L106 106" {S(14,T)}/>')
add("Chevron forward","Two chevrons pointing forward inside a rounded square.",
 "Brief: Navy tile, a white and a teal chevron. Motion and progress; tile makes it app-icon ready.",
 f'<rect x="12" y="12" width="96" height="96" rx="24" fill="{N}"/><path d="M38 36 L62 60 L38 84" {S(13,W)}/><path d="M64 36 L88 60 L64 84" {S(13,T)}/>')
add("Target square","Concentric rings with a square at the centre.",
 "Brief: Navy ring, teal ring, solid navy square = the parcel landing on the exact address. Precision and address quality.",
 f'<circle cx="60" cy="60" r="46" {S(9,N)}/><circle cx="60" cy="60" r="28" {S(9,T)}/><rect x="48" y="48" width="24" height="24" rx="4" fill="{N}"/>')
add("Waw app tile","White waw with a teal dot on a navy rounded square.",
 "Brief: The app-icon form of concept 1. Strongest at small sizes because the tile gives it a fixed silhouette.",
 f'<rect x="8" y="8" width="104" height="104" rx="26" fill="{N}"/><circle cx="62" cy="48" r="17" {S(11,W)}/><path d="M77 58 C84 86 70 100 40 96" {S(11,W)}/><circle cx="32" cy="94" r="7" fill="{T}"/>')
add("Double V","Two offset V shapes make a W: one navy, one teal.",
 "Brief: Two chunky chevrons overlapping by a third. The teal V is the 'next step' leaning on the navy one.",
 f'<path d="M12 30 L38 96 L64 30" {S(14,N)}/><path d="M52 30 L78 96 L104 30" {S(14,T)}/>')
add("Hex seal","A hexagon with a box outline and teal dot: a stamp.",
 "Brief: Solid navy hexagon, white square outline, teal dot at centre. Reads as an inspected-and-sealed parcel.",
 f'<path d="M60 8 L106 34 L106 86 L60 112 L14 86 L14 34 Z" fill="{N}"/><rect x="38" y="38" width="44" height="44" rx="8" {S(8,W)}/><circle cx="60" cy="60" r="7" fill="{T}"/>')
add("Round seal","A circle stamp with a tilted taped parcel.",
 "Brief: Navy disc, tilted white square with a teal band. Friendly, badge-like; good for stickers on parcels.",
 f'<circle cx="60" cy="60" r="52" fill="{N}"/><g transform="rotate(-12 60 60)"><rect x="36" y="36" width="48" height="48" rx="9" fill="{W}"/><rect x="36" y="54" width="48" height="11" fill="{T}"/></g>')
add("Two ends","Seller and customer as two dots joined by a curve with a parcel on it.",
 "Brief: Navy dot, teal dot, a curved link, small square on the curve. 'Wasel' as connect; the product sits between two people.",
 f'<path d="M24 86 C32 20 88 20 96 86" {S(8,N)}/><circle cx="24" cy="90" r="12" fill="{N}"/><circle cx="96" cy="90" r="12" fill="{T}"/><rect x="48" y="28" width="24" height="24" rx="5" fill="{I}"/>')
add("Home tick","A house outline with a teal check as its door.",
 "Brief: Navy house outline, teal check in the doorway. Delivery to a home; the check means 'accepted at the door'.",
 f'<path d="M16 58 L60 18 L104 58 V104 H16 Z" {S(11,N)}/><path d="M42 68 L56 82 L80 52" {S(12,T)}/>')
add("Lower-case w","A heavy rounded w in a tile, with a teal full stop.",
 "Brief: Wordmark-led: a bold geometric w and a teal period (arrived). Cheapest to build and easy to lock up with the name.",
 f'<rect x="8" y="8" width="104" height="104" rx="26" fill="{N}"/><path d="M26 44 L40 82 L56 56 L72 82 L86 44" {S(12,W)}/><circle cx="96" cy="86" r="7" fill="{T}"/>')
add("Tri-tone cube","A flat isometric cube in three tones, the safe baseline.",
 "Brief: Three faces in navy, teal and light blue. The most conventional option; included as a control to judge the others against.",
 f'<path d="M60 10 L104 34 L60 58 L16 34 Z" fill="{T}"/><path d="M16 34 L60 58 L60 110 L16 86 Z" fill="{N}"/><path d="M104 34 L60 58 L60 110 L104 86 Z" fill="#5b86bd"/>')

cards=[]
for i,(n,idea,brief,svg) in enumerate(C,1):
    small=lambda px: f'<svg viewBox="0 0 120 120" width="{px}" height="{px}">{svg}</svg>'
    cards.append(f'''<article class="card"><div class="no">{i:02d}</div><h3>{html.escape(n)}</h3>
<div class="lock"><svg viewBox="0 0 120 120" width="96" height="96">{svg}</svg><div class="wm"><b>Wasel</b><span lang="ar">واصل</span></div></div>
<div class="sizes">{small(32)}{small(16)}<span class="dk">{small(32)}</span></div>
<p class="idea">{html.escape(idea)}</p><p class="brief">{html.escape(brief)}</p></article>''')
page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Wasel Logo Ideas</title>
<style>
:root{{--bg:#f4f6f9;--card:#fff;--ink:#0b1d33;--muted:#4b5563;--line:#dbe2ec;--teal:#00777a}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#0b1522;--card:#13233a;--ink:#e8eef7;--muted:#a9b8cc;--line:#25395a;--teal:#4fd1d1}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,"Noto Sans",sans-serif;line-height:1.5}}
header,main,footer{{max-width:1320px;margin:0 auto;padding:0 16px}}header{{padding-top:32px}}
h1{{font-size:28px;margin:0 0 6px}}h2{{font-size:18px;margin:24px 0 8px}}p{{margin:0}}
.lead{{color:var(--muted);max-width:70ch}}
.princ{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin:16px 0 8px}}
.princ div{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;font-size:14px}}
.princ b{{display:block;margin-bottom:4px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;margin:16px 0 40px}}
.card{{position:relative;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px}}
.no{{position:absolute;top:12px;right:14px;font-weight:700;color:var(--muted);font-size:13px}}
h3{{margin:0 0 10px;font-size:16px}}
.lock{{display:flex;align-items:center;gap:14px;background:#fff;border-radius:12px;padding:12px;border:1px solid var(--line)}}
.wm b{{display:block;font-size:34px;line-height:1;color:#0b1d33;font-weight:800;letter-spacing:-.5px}}
.wm span{{display:block;color:#00777a;font-size:20px;margin-top:4px}}
.sizes{{display:flex;align-items:center;gap:12px;margin:10px 0}}
.dk{{background:#0b1d33;border-radius:8px;padding:6px;display:inline-flex}}
.idea{{font-size:14px;font-weight:600;margin-top:6px}}.brief{{font-size:13px;color:var(--muted);margin-top:6px}}
footer{{padding-bottom:40px;font-size:13px;color:var(--muted)}}a{{color:var(--teal)}}
</style></head><body>
<header><h1>Wasel: 20 logo directions</h1>
<p class="lead">Rough vector sketches, not final art. Each card shows the idea, the lockup with the Arabic name <span lang="ar">واصل</span>, then the mark at 32px, 16px and 32px on navy to test small-size and reversed legibility. The wordmark is a stand-in font.</p>
<h2>What the research said</h2>
<div class="princ">
<div><b>Build a system, not one file</b>Brands now ship a full logo, stacked, icon and monogram. So every idea here has to work as a mark alone.</div>
<div><b>Favicon test</b>Clear silhouette, minimal inner detail, strong contrast, no thin strokes. Look at the 16px column.</div>
<div><b>Arabic and Latin balance</b>Latin letters take vertical space, Arabic connects horizontally. Keep each script independent in the lockup.</div>
<div><b>Delivery job</b>Speed, reliability and professionalism at a glance. Wasel adds one more: a risk judgement, so it should not promise "safe".</div>
</div></header>
<main><div class="grid">{"".join(cards)}</div></main>
<footer>Sources: <a href="https://www.manypixels.co/blog/brand-design/logo-design-trends">ManyPixels, logo design trends 2026</a> · <a href="https://www.zenind.com/help/post/how-to-create-a-delivery-logo-practical-design-tips-for-a-fast-trustworthy-brand">Zenind, delivery logo tips</a> · <a href="https://phable.io/blog/fintech-logo-design-guide">Phable, fintech logo design</a> · <a href="https://kaina.nuxt.dev/showcase/zas-chaumet-logo-arabization">Arabization case study</a></footer>
</body></html>'''
open('grid.html','w').write(page)
print(len(C))
