import html
ORD=[("#2609","Mehdi","mixeur · 129 TND","High",89,"Confirm the address","vague address (“Thala”) · rural zone"),
     ("#2601","Sami","casque bluetooth · 220 TND","High",87,"Confirm the address","3 warning signs · rural zone"),
     ("#2603","سارة","crème visage · 35 TND","Medium",42,"Quick check","vague address · 2 warning signs"),
     ("#2606","Yassine","jean slim · 59 TND","Low",9,"Ship","good order history · urban")]
def arch(fill,notch,line=None,stroke=None,sw=8,uid="a"):
    base=f'<path d="M24 100 V54 A36 36 0 0 1 96 54 V100 Z" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"' if stroke else '')+'/>'
    nt=f'<rect x="46" y="68" width="28" height="32" rx="5" fill="{notch}"/>'
    ln=f'<path d="M12 108 H108" fill="none" stroke="{line}" stroke-width="7" stroke-linecap="round"/>' if line else ''
    return base+nt+ln
def sv(inner,px,vb="0 0 120 120",extra=""): return f'<svg viewBox="{vb}" width="{px}" height="{px}" aria-hidden="true" {extra}>{inner}</svg>'

# ---------- logo marks per direction
def m_glass(px,uid):
    d=f'<defs><linearGradient id="g{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2a5da8"/><stop offset="1" stop-color="#0f2f5c"/></linearGradient><linearGradient id="h{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
    return sv(d+f'<rect x="4" y="4" width="112" height="112" rx="27" fill="url(#g{uid})"/><rect x="4" y="4" width="112" height="112" rx="27" fill="url(#h{uid})"/>'+f'<g transform="translate(16 12) scale(.8)">{arch("#fff","#1d4a8a","#5fe0e0")}</g>',px)
def m_graph(px,uid): return sv(f'<rect x="4" y="4" width="112" height="112" rx="26" fill="#0c0f14"/><rect x="4.5" y="4.5" width="111" height="111" rx="25.5" fill="none" stroke="#2a313d"/><g transform="translate(18 14) scale(.76)">{arch("none","#2dd4bf",None,"#2dd4bf",9)}</g>',px)
def m_paper(px,uid): return sv(f'<rect x="4" y="4" width="112" height="112" rx="14" fill="#f3ede1"/><g transform="translate(16 12) scale(.8)">{arch("#1b1915","#f3ede1","#a23b2a")}</g>',px)
def m_instr(px,uid):
    ticks=''.join(f'<line x1="60" y1="10" x2="60" y2="18" stroke="#8a93a3" stroke-width="3" stroke-linecap="round" transform="rotate({a} 60 60)"/>' for a in range(-120,121,30))
    return sv(f'<circle cx="60" cy="60" r="54" fill="#e9ecf1"/><circle cx="60" cy="60" r="54" fill="none" stroke="#c9cfd9" stroke-width="2"/>{ticks}<g transform="translate(33 32) scale(.46)">{arch("#12386b","#e9ecf1","#f26b21")}</g>',px)
def m_luxe(px,uid): return sv(f'<rect x="4" y="4" width="112" height="112" rx="28" fill="#0a1a33"/><rect x="4.5" y="4.5" width="111" height="111" rx="27.5" fill="none" stroke="#c9a96a" stroke-opacity=".55"/><g transform="translate(18 14) scale(.76)">{arch("none","#c9a96a",None,"#c9a96a",6)}</g>',px)
def m_swiss(px,uid): return sv(f'<rect x="4" y="4" width="112" height="112" rx="0" fill="#fff"/><g transform="translate(18 14) scale(.76)">{arch("#0a0a0a","#fff")}</g>',px)

def lock(mark,px,name_css,ar_css,extra=""):
    return f'<div class="lk">{mark}<div class="wm"><b style="{name_css}">Wasel</b><span lang="ar" style="{ar_css}">واصل</span></div></div>'

# ---------- screens (each its own look)
def rows_glass():
    t={"High":("#e5484d","#fdecec"),"Medium":("#d98200","#fff4e0"),"Low":("#2f9e6e","#e8f6ef")}
    return ''.join(f'<div class="r"><div class="av2">{o[1][0]}</div><div class="mid"><b>{o[0]} {o[1]}</b><span>{o[2]}</span></div><div class="why">{o[6]}</div><div class="chip" style="color:{t[o[3]][0]};background:{t[o[3]][1]}">{o[3]} {o[4]}</div></div>' for o in ORD)
def screen_glass(m):
    return f'''<div class="s glass"><aside><div class="brand">{m}<b>Wasel</b></div><nav><a class="on">Orders</a><a>Messages</a><a>Add order</a><a>Results</a><a>Quality</a></nav><div class="foot">AI scoring live</div></aside>
<main><div class="top"><div class="seg"><span class="on">Needs you</span><span>Waiting</span><span>Ready</span></div><div class="search">Search ⌘K</div></div>
<h1>Four orders<br>need a second look.</h1><div class="list">{rows_glass()}</div></main></div>'''
def screen_graph(m):
    rows=''.join(f'<tr><td class="mono">{o[0]}</td><td>{o[1]}</td><td class="dim">{o[2]}</td><td><span class="dot {o[3].lower()}"></span>{o[3]} <span class="mono">{o[4]}</span></td><td class="dim">{o[5]}</td><td><kbd>↵</kbd></td></tr>' for o in ORD)
    return f'''<div class="s graph"><aside><div class="brand">{m}<b>Wasel</b></div><nav><a class="on"><i></i>Orders <em>9</em></a><a><i></i>Inbox</a><a><i></i>Add</a><a><i></i>Results</a><a><i></i>Quality</a></nav></aside>
<main><div class="bar"><span>Orders</span><span class="cmd">⌘K  Search or jump to…</span></div><div class="tabs2"><span class="on">All</span><span>High</span><span>Medium</span><span>Low</span></div>
<table><thead><tr><th>ID</th><th>Customer</th><th>Item</th><th>Risk</th><th>Next</th><th></th></tr></thead>{rows}</table><div class="hint"><kbd>J</kbd><kbd>K</kbd> move  <kbd>↵</kbd> open  <kbd>C</kbd> confirm</div></main></div>'''
def screen_paper(m):
    rows=''.join(f'<div class="pr"><span class="n">{i+1}</span><div><b>{o[1]}</b> <i>{o[0]}</i><p>{o[6]}.</p></div><div class="sc"><span>{o[4]}</span><em>{o[3].lower()}</em></div></div>' for i,o in enumerate(ORD))
    return f'''<div class="s paper"><header><div class="brand">{m}<b>Wasel</b></div><nav><a class="on">Today</a><a>Orders</a><a>Messages</a><a>Results</a></nav></header>
<main><p class="kick">Tuesday, 7 October</p><h1>Four orders deserve<br>a second look.</h1><p class="sub">Wasel read each customer's own words and ranked them by the risk of refusal at the door.</p><div class="ledger">{rows}</div></main></div>'''
def screen_instr(m):
    cards=''.join(f'<div class="ic"><div class="mini"><svg viewBox="0 0 60 34" width="60"><path d="M6 30 A24 24 0 0 1 54 30" fill="none" stroke="#d5dae3" stroke-width="5" stroke-linecap="round"/><path d="M6 30 A24 24 0 0 1 54 30" fill="none" stroke="{ {"High":"#e5484d","Medium":"#e89b0b","Low":"#2f9e6e"}[o[3]] }" stroke-width="5" stroke-linecap="round" stroke-dasharray="{o[4]*0.754:.0f} 80"/></svg><b>{o[4]}</b></div><div><b>{o[1]}</b><span>{o[0]} · {o[2]}</span></div></div>' for o in ORD)
    return f'''<div class="s instr"><aside><div class="brand">{m}</div><i class="on"></i><i></i><i></i><i></i></aside>
<main><div class="hero"><svg viewBox="0 0 200 118" width="230"><path d="M16 104 A84 84 0 0 1 184 104" fill="none" stroke="#d5dae3" stroke-width="14" stroke-linecap="round"/><path d="M16 104 A84 84 0 0 1 184 104" fill="none" stroke="#e5484d" stroke-width="14" stroke-linecap="round" stroke-dasharray="235 400"/><line x1="100" y1="104" x2="154" y2="46" stroke="#12161d" stroke-width="5" stroke-linecap="round"/><circle cx="100" cy="104" r="9" fill="#12161d"/></svg><div><small>HIGHEST RISK TODAY</small><h1>89</h1><p>#2609 Mehdi · mixeur<br>Vague address, rural zone</p><button>Confirm the address</button></div></div>
<div class="grid2">{cards}</div></main></div>'''
def screen_luxe(m):
    rows=''.join(f'<div class="lr"><div><b>{o[1]}</b><span>{o[0]} · {o[2]}</span></div><div class="lw">{o[6]}</div><div class="ls {o[3].lower()}">{o[4]}</div></div>' for o in ORD)
    return f'''<div class="s luxe"><header><div class="brand">{m}<b>WASEL</b></div><nav><a class="on">Orders</a><a>Messages</a><a>Results</a><a>Quality</a></nav><div class="pill">Professional</div></header>
<main><small>RISK DESK</small><h1>Orders to review</h1><div class="stats"><div><b>4</b><span>high risk</span></div><div><b>1</b><span>medium</span></div><div><b>4</b><span>ready</span></div></div><div class="lrows">{rows}</div></main></div>'''
def screen_swiss(m):
    rows=''.join(f'<div class="wr"><span>{o[0]}</span><b>{o[1]}</b><span>{o[2]}</span><span class="{o[3].lower()}">{o[3]}</span><strong>{o[4]}</strong></div>' for o in ORD)
    return f'''<div class="s swiss"><header><div class="brand">{m}<b>Wasel</b></div><nav><a class="on">Orders</a><a>Messages</a><a>Results</a></nav></header>
<main><div class="big"><strong>4</strong><span>orders at high risk.<br>Confirm before shipping.</span></div><div class="wrows">{rows}</div></main></div>'''

D=[
 dict(n="01",name="Quiet Glass",tag="Apple-direction: calm, spacious, translucent",
  idea="Design idea: treat Wasel like a macOS app. A frosted sidebar, one big sentence as the page title, rows with room to breathe, and colour only where meaning lives (the risk chips). The logo becomes an app-icon tile with a soft gradient and a glass highlight, so it feels like software you install, not a website.",
  mark=m_glass,screen=screen_glass,font="Inter, SF Pro",pal=["#f5f5f7","#1d1d1f","#0f2f5c","#5fe0e0","#e5484d"],
  lock=("font-family:Inter;font-weight:650;letter-spacing:-.02em;color:#1d1d1f","color:#0a7f86;font-family:'Noto Sans Arabic'"),
  why=["Big headline replaces the three stat cards","Frosted sidebar, one accent, generous padding","App-icon tile with gradient and highlight"]),
 dict(n="02",dark="dark",name="Graphite Pro",tag="Dense, dark, keyboard-first tool for daily operators",
  idea="Design idea: the tool a professional lives in all day. Near-black canvas, hairline borders, tabular numbers, a command bar and visible keyboard shortcuts. Teal is the single signal colour. The mark is an outline arch with a lit parcel, drawn like a pro-app glyph.",
  mark=m_graph,screen=screen_graph,font="Inter, JetBrains Mono",pal=["#0c0f14","#161b23","#2a313d","#2dd4bf","#e8ecf2"],
  lock=("font-family:Inter;font-weight:600;letter-spacing:-.01em;color:#e8ecf2","color:#2dd4bf;font-family:'Noto Sans Arabic'"),
  why=["Table-first, ⌘K and J/K navigation","Hairlines, no shadows, tabular numerals","One accent: teal"]),
 dict(n="03",name="Paper & Ink",tag="Editorial and calm, like a quality newspaper brief",
  idea="Design idea: a daily briefing, not a dashboard. Warm paper, a serif headline written as a sentence, a numbered ledger with hairlines, and one oxblood accent for the stamp line. It signals care and judgement, which is what a risk adviser sells. The mark is a printed-ink arch with a red ground rule.",
  mark=m_paper,screen=screen_paper,font="Newsreader, Inter",pal=["#f3ede1","#1b1915","#a23b2a","#6b6354","#d8cfbd"],
  lock=("font-family:Newsreader,Georgia,serif;font-weight:600;letter-spacing:-.01em;color:#1b1915","color:#a23b2a;font-family:'Noto Sans Arabic'"),
  why=["Today's briefing as a written headline","Numbered ledger, hairline rules","Serif for judgement, sans for data"]),
 dict(n="04",name="Instrument",tag="Tactile and precise, like a well-made measuring device",
  idea="Design idea: lean into the fact that Wasel is a measuring instrument. A real dial reads the highest-risk order, small dials replace pills, a slim icon rail replaces the sidebar. Warm grey hardware tones, one signal orange. The mark is the arch on a dial face with tick marks.",
  mark=m_instr,screen=screen_instr,font="Instrument Sans, IBM Plex Mono",pal=["#e9ecf1","#12161d","#12386b","#f26b21","#e5484d"],
  lock=("font-family:'Instrument Sans';font-weight:700;letter-spacing:-.02em;color:#12161d","color:#12386b;font-family:'Noto Sans Arabic'"),
  why=["Dial hero for the riskiest order","Mini dials instead of text pills","Icon rail, hardware-grey surfaces"]),
 dict(n="05",dark="dark",name="Midnight Luxe",tag="Private-bank feel: dark navy, gold hairlines",
  idea="Design idea: price the product like a professional service. Deep navy canvas, fine gold hairlines, wide-tracked caps, three large numbers up front and a quiet table below. The mark is a gold line-drawn arch in a navy tile, like an engraved seal.",
  mark=m_luxe,screen=screen_luxe,font="Cormorant Garamond, Inter",pal=["#0a1a33","#102446","#c9a96a","#e9eef7","#6f87ab"],
  lock=("font-family:Inter;font-weight:600;letter-spacing:.2em;color:#f2ead8;font-size:.8em","color:#c9a96a;font-family:'Noto Sans Arabic'"),
  why=["Three big numbers lead the page","Gold hairlines, wide-tracked caps","Looks priced, not free"]),
 dict(n="06",name="Swiss Mono",tag="Ultra-minimal, black and white, risk as the only colour",
  idea="Design idea: remove everything that is not information. A huge number states the situation, rows are a strict grid, and the only colour in the whole product is the risk. The mark is a single solid black arch with a cut-out parcel: one shape, no gradient, works on a stamp.",
  mark=m_swiss,screen=screen_swiss,font="Inter Tight, Helvetica",pal=["#ffffff","#0a0a0a","#e5e5e5","#d92d20","#2f9e6e"],
  lock=("font-family:'Inter Tight',Inter;font-weight:700;letter-spacing:-.03em;color:#0a0a0a","color:#0a0a0a;font-family:'Noto Sans Arabic'"),
  why=["One giant number as the headline","Strict grid, no cards, no shadows","Colour appears only for risk"]),
]
cards=[]
for d in D:
    d.setdefault('dark','')
    m=d["mark"]
    cards.append(f'''<article class="dir" id="d{d["n"]}"><header><span class="no">{d["n"]}</span><div><h2>{d["name"]}</h2><p>{d["tag"]}</p></div></header>
<p class="idea">{html.escape(d["idea"])}</p>
<div class="frame">{d["screen"](m(30,d["n"]+"s"))}</div>
<div class="kit"><div class="kk"><h4>Logo</h4><div class="lkrow {d['dark']}">{lock(m(56,d["n"]+"l"),56,*d["lock"])}{m(48,d["n"]+"t")}<span class="circ">{m(44,d["n"]+"c")}</span>{m(16,d["n"]+"f")}</div></div>
<div class="kk"><h4>Palette</h4><div class="sw">{''.join(f'<i style="background:{c}"><b>{c}</b></i>' for c in d["pal"])}</div></div>
<div class="kk"><h4>Type</h4><p class="ty">{d["font"]}</p><ul>{''.join(f"<li>{html.escape(w)}</li>" for w in d["why"])}</ul></div></div></article>''')
css=open('directions.css').read()
open('directions.html','w').write(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Wasel Product Directions</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Inter+Tight:wght@500;700&family=Instrument+Sans:wght@500;700&family=Newsreader:ital,wght@0,500;0,600;1,400&family=Cormorant+Garamond:wght@500;600&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+Arabic:wght@500;700&display=swap" rel="stylesheet">
<style>{css}</style></head><body><header class="top"><h1>Wasel: six premium directions</h1><p>Each direction changes the whole product feel (layout, type, colour, logo), not just the paint. Same four orders in every screen so you can compare. Not final art: fonts load from Google Fonts, the wordmark is set in the direction's type.</p>
<nav class="jump">{''.join(f'<a href="#d{d["n"]}">{d["n"]} {d["name"]}</a>' for d in D)}</nav></header><main>{"".join(cards)}</main></body></html>''')
print('ok')
