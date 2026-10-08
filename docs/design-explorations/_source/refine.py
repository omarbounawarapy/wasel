import html
N="#12386b"; T="#00abab"; I="#0b1d33"; W="#ffffff"
S=lambda w,c: f'fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"'
V=[]  # (family, id, name, design idea, svg, tile?)
def add(f,i,n,idea,svg,tile=False): V.append((f,i,n,idea,svg,tile))

# ---- A: waw family (fix "reads as 9")
add("A · Waw","A1","Kashida tail","Design: stretch the tail into a long flat kashida that runs under the whole mark, so it reads as an Arabic letter sitting on a baseline, not a numeral. Bowl navy, tail teal.",
 f'<circle cx="70" cy="42" r="18" {S(12,N)}/><path d="M86 54 C92 84 72 98 16 96" {S(12,T)}/>')
add("A · Waw","A2","Open loop","Design: break the bowl at the upper right like a calligraphic loop. An open counter is how real waw is written and kills the closed-circle 9 shape.",
 f'<path d="M78.4 33 A20 20 0 1 0 79 58 C92 92 70 106 24 100" {S(12,N)}/><circle cx="18" cy="100" r="7" fill="{T}"/>')
add("A · Waw","A3","Tile, tail breaks out","Design: white waw on a navy tile, with the teal tail leaving the tile edge. The tile gives the app icon a fixed silhouette; the breakout is the parcel leaving.",
 f'<rect x="14" y="10" width="92" height="92" rx="24" fill="{N}"/><circle cx="64" cy="42" r="15" {S(11,W)}/><path d="M77 52 C82 76 66 88 40 86" {S(11,W)}/><path d="M40 86 L8 106" {S(11,T)}/>',True)
add("A · Waw","A4","Taped bowl","Design: square parcel bowl with a teal tape band, navy tail. Keeps the box idea from concept 2 and makes the bowl obviously a package.",
 f'<rect x="40" y="18" width="46" height="46" rx="10" {S(12,N)}/><path d="M40 41 H86" {S(10,T)}/><path d="M80 60 C92 94 72 110 28 104" {S(12,N)}/>')
# ---- B: doorstep
add("B · Doorstep","B1","Big parcel","Design: scale the parcel up so it overlaps the arch base and survives at 16px. Teal parcel with no tape, so no thin detail.",
 f'<path d="M20 108 V52 A30 30 0 0 1 80 52 V108 Z" fill="{N}"/><rect x="58" y="62" width="48" height="46" rx="8" fill="{T}"/>')
add("B · Doorstep","B2","Parcel in the doorway","Design: the parcel is a notch cut out of the arch, so the door and the box share one silhouette. One colour plus a teal ground line.",
 f'<path d="M24 100 V54 A36 36 0 0 1 96 54 V100 Z" fill="{N}"/><rect x="46" y="68" width="28" height="32" rx="5" fill="{W}"/><path d="M12 108 H108" {S(8,T)}/>')
add("B · Doorstep","B3","Outline door","Design: arch drawn as a heavy outline with a solid teal parcel inside. Lighter and friendlier; the parcel is the only filled shape.",
 f'<path d="M24 106 V54 A34 34 0 0 1 92 54 V106" {S(12,N)}/><rect x="44" y="72" width="30" height="34" rx="6" fill="{T}"/><path d="M14 106 H106" {S(10,N)}/>')
add("B · Doorstep","B4","Horseshoe arch","Design: a horseshoe arch (Maghrebi) in place of the round arch, so the mark is recognisably Tunisian. Parcel centred in the doorway.",
 f'<path d="M34 108 V74 C16 68 12 30 60 12 C108 30 104 68 86 74 V108Z" fill="{N}"/><rect x="46" y="76" width="28" height="32" rx="5" fill="{T}"/>')
# ---- C: target
add("C · Target","C1","Ring and square","Design: one heavy navy ring and a solid teal square. Two shapes only, so nothing fragments at 16px.",
 f'<circle cx="60" cy="60" r="44" {S(16,N)}/><rect x="40" y="40" width="40" height="40" rx="8" fill="{T}"/>')
add("C · Target","C2","Framed target","Design: a rounded-square frame (the parcel) with a solid teal circle (the address) inside. The parcel contains the target.",
 f'<rect x="16" y="16" width="88" height="88" rx="22" {S(14,N)}/><circle cx="60" cy="60" r="18" fill="{T}"/>')
add("C · Target","C3","Target tile","Design: navy tile, heavy white ring, teal centre square. App-icon form of C1.",
 f'<rect x="8" y="8" width="104" height="104" rx="26" fill="{N}"/><circle cx="60" cy="60" r="30" {S(12,W)}/><rect x="48" y="48" width="24" height="24" rx="5" fill="{T}"/>',True)
# ---- D: w
add("D · w","D1","Heavy w tile","Design: rounder, heavier w than concept 19 with a teal full stop. The period reads as arrived and doubles as the dot over a stamp.",
 f'<rect x="8" y="8" width="104" height="104" rx="26" fill="{N}"/><path d="M24 40 L40 82 L58 52 L76 82 L92 40" {S(13,W)}/><circle cx="98" cy="90" r="8" fill="{T}"/>',True)
add("D · w","D2","Two-tone w","Design: no tile. A w whose middle stroke is teal, so the letter reads as navy plus one highlighted step.",
 f'<path d="M14 36 L34 90 L52 52" {S(14,N)}/><path d="M52 52 L70 90 L106 36" {S(14,N)}/><path d="M34 90 L52 52 L70 90" {S(14,T)}/>')
add("D · w","D3","w and stop","Design: plain navy w with a large teal full stop, no tile. The lightest form; the stop carries the brand colour.",
 f'<path d="M12 38 L32 90 L52 52 L72 90 L92 38" {S(14,N)}/><circle cx="106" cy="88" r="9" fill="{T}"/>')

def mono(svg,tile):
    return svg.replace(T, W if tile else N)
def rev(svg,tile):
    return svg.replace(N,W).replace(T,W) if not tile else svg.replace(N,W).replace(W+'"',W+'"')
def sv(svg,px): return f'<svg viewBox="0 0 120 120" width="{px}" height="{px}">{svg}</svg>'

cards=[];last=None
for f,i,n,idea,svg,tile in V:
    head='' 
    if f!=last: head=f'<h2 class="fam">{f}</h2>'; last=f
    isw=f.startswith("A")
    ninetest=f'<div class="nine"><span class="lbl">9-test</span>{sv(svg,36)}<b lang="en">2026</b><span class="sep"></span>{sv(svg,36)}<b lang="ar">واصل</b></div>' if isw else ''
    cards.append((head,f'''<article class="card"><div class="no">{i}</div><h3>{html.escape(n)}</h3>
<div class="lock">{sv(svg,92)}<div class="wm"><b>Wasel</b><span lang="ar">واصل</span></div></div>
{ninetest}
<div class="sizes"><span>{sv(svg,48)}</span><span>{sv(svg,32)}</span><span>{sv(svg,16)}</span><span class="dk">{sv(rev(svg,tile) if not tile else svg,32)}</span><span class="mono">{sv(mono(svg,tile),32)}</span></div>
<div class="cap"><span>48</span><span>32</span><span>16</span><span>on navy</span><span>1-colour</span></div>
<p class="idea">{html.escape(idea)}</p></article>'''))
body=''
cur=[]
for head,c in cards:
    if head:
        if cur: body+='<div class="grid">'+''.join(cur)+'</div>'; cur=[]
        body+=head
    cur.append(c)
body+='<div class="grid">'+''.join(cur)+'</div>'
page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Wasel Logo Refinement</title>
<style>
:root{{--bg:#f4f6f9;--card:#fff;--ink:#0b1d33;--muted:#4b5563;--line:#dbe2ec;--teal:#00777a}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0b1522;--card:#13233a;--ink:#e8eef7;--muted:#a9b8cc;--line:#25395a;--teal:#4fd1d1}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,"Noto Sans",sans-serif;line-height:1.5}}
header,main{{max-width:1320px;margin:0 auto;padding:0 16px}}header{{padding-top:32px}}main{{padding-bottom:48px}}
h1{{font-size:28px;margin:0 0 6px}}.fam{{font-size:20px;margin:28px 0 4px}}.lead{{color:var(--muted);max-width:75ch;font-size:15px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;margin:12px 0}}
.card{{position:relative;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px}}
.no{{position:absolute;top:12px;right:14px;font-weight:700;color:var(--muted);font-size:13px}}
h3{{margin:0 0 10px;font-size:16px}}
.lock{{display:flex;align-items:center;gap:14px;background:#fff;border-radius:12px;padding:12px;border:1px solid var(--line)}}
.wm b{{display:block;font-size:34px;line-height:1;color:#0b1d33;font-weight:800;letter-spacing:-.5px}}
.wm span{{display:block;color:#00777a;font-size:20px;margin-top:4px}}
.nine{{display:flex;align-items:center;gap:8px;background:#fff;border:1px dashed var(--line);border-radius:10px;padding:6px 10px;margin-top:8px;color:#0b1d33}}
.nine b{{font-size:22px}}.nine .lbl{{font-size:11px;color:#4b5563;margin-right:4px}}.sep{{width:1px;height:24px;background:#dbe2ec;margin:0 6px}}
.sizes{{display:flex;align-items:center;gap:12px;margin:12px 0 0;flex-wrap:wrap}}
.sizes span{{display:inline-flex}}.dk{{background:#0b1d33;border-radius:8px;padding:6px}}.mono{{background:#fff;border-radius:8px;padding:6px;border:1px solid var(--line)}}
.cap{{display:flex;gap:12px;font-size:11px;color:var(--muted);margin-top:2px}}.cap span{{min-width:32px}}
.idea{{font-size:13px;color:var(--muted);margin-top:10px}}
</style></head><body>
<header><h1>Wasel: logo refinement round</h1>
<p class="lead">14 variations of the four shortlisted directions. Each card shows the lockup, then the mark at 48, 32 and 16px, reversed on navy, and in one colour. The waw family also has a "9-test": the mark next to Latin digits and next to the Arabic name, to see how it reads in each context. Wordmark is a stand-in font.</p></header>
<main>{body}</main></body></html>'''
open('refine.html','w').write(page); print(len(V))
