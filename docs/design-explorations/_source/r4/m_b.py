from data import *
import math
def bdi(s): return f'<bdi dir="auto">{esc(s)}</bdi>'
# ---- 11 Macintosh desktop
def icon(c="#111"):
    px=["0011111100","0100000010","0100000010","0100110010","0100110010","0100000010","0100000010","0100000010","0111111110","0000000000"]
    r=''.join(f'<rect x="{x*3}" y="{y*3}" width="3" height="3" fill="{c}"/>' for y,row in enumerate(px) for x,ch in enumerate(row) if ch=="1")
    return f'<svg viewBox="0 0 30 30" width="38" height="38" style="image-rendering:pixelated">{r}</svg>'
def folder():
    px=["0111100000","1000011110","1000000001","1000000001","1000000001","1000000001","1000000001","1111111111"]
    r=''.join(f'<rect x="{x*3.6}" y="{y*3.6}" width="3.6" height="3.6" fill="#111"/>' for y,row in enumerate(px) for x,ch in enumerate(row) if ch=="1")
    return f'<svg viewBox="0 0 36 30" width="44" height="36">{r}</svg>'
def m11():
    ic=''.join(f'<div class="ic{" sel" if o[0]=="#2601" else ""}">{icon()}<span>{bdi(o[1])} {o[5]}</span></div>' for o in O if o[7]==2)
    win=lambda t,items,cls="": f'<div class="win {cls}"><div class="tb"><i></i><b>{t}</b><i></i></div><div class="bd">{items}</div></div>'
    ready=''.join(f'<div class="ic">{icon()}<span>{bdi(o[1])} {o[5]}</span></div>' for o in O if o[6]=="Ship")
    return f'''<div class="m m11"><div class="menu"><b>●</b><span>File</span><span>Edit</span><span>Order</span><span>View</span><span class="r">Wasel</span></div>
<div class="desk"><div class="inbox">{win("Orders to decide",ic)}</div>
<div class="trays">{win("Ask for the address",'<div class="drop">drop here</div>')}{win("Ask for prepayment",'<div class="drop">drop here</div>')}{win("Ship",ready,"w3")}</div>
<div class="trash">{folder()}<span>Cancel</span></div></div><div class="hint">Drag an order onto what you want to do. Double-click to read it.</div></div>'''
# ---- 12 Hashiya
def m12():
    return f'''<div class="m m12"><header><span>WASEL · حاشية</span><nav><a class="on">Reading</a><a>Orders</a><a>Results</a></nav></header><div class="leaf"><div class="frame2">
<div class="main2"><p class="ar" dir="rtl">دوار أولاد علي، <mark>قريب من الجامع</mark><br>غالي <mark>شوية</mark>. مش دايما في الدار</p><p class="lat" dir="ltr">Douar Ouled Ali, <mark>9rib el jemaa</mark> ama <mark>ghali chwaya</mark>. mouch dima fi dar</p></div>
<div class="g g1"><b>9rib el jemaa</b>“near the mosque”: a landmark, not an address. <em>+17</em></div>
<div class="g g2"><b>ghali chwaya</b>“a bit expensive”: hesitates on price. <em>+9</em></div>
<div class="g g3"><b>mouch dima fi dar</b>“not always home”: may not be there at delivery. <em>+8</em></div>
<div class="g g4"><b>Douar Ouled Ali</b>a rural hamlet: delivery zone. <em>+13</em></div>
<div class="g g5"><b>Score 87.</b> Ask for a street, a number and a phone.</div></div></div></div>'''
# ---- 13 Hurufiyya
def m13():
    seals=''.join(f'<div class="sl"><svg viewBox="0 0 60 60" width="52" height="52"><circle cx="30" cy="30" r="26" fill="none" stroke="#a31621" stroke-width="3"/><text x="30" y="37" text-anchor="middle" font-size="22" font-weight="700" fill="#a31621" font-family="Archivo">{o[5]}</text></svg><span>{bdi(o[1])}</span></div>' for o in O)
    return f'''<div class="m m13"><aside><div class="wm">واصل<small>wasel</small></div><div class="seals">{seals}</div></aside><main><svg viewBox="0 0 700 460" width="100%"><defs><path id="p1" d="M30 360 C180 120 360 420 640 90" fill="none"/><path id="p2" d="M30 430 C220 300 420 440 660 250" fill="none"/></defs>
<text font-size="82" font-weight="800" fill="#14110f" font-family="Noto Kufi Arabic"><textPath href="#p1" startOffset="2%">غالي شوية</textPath></text>
<text font-size="46" font-weight="500" fill="#bdb6ad" font-family="Noto Kufi Arabic"><textPath href="#p2">دوار أولاد علي، قريب من الجامع</textPath></text>
<text x="30" y="40" font-size="14" fill="#6b645c" font-family="Archivo">Sami · casque bluetooth · 220 TND · the heavy strokes are what raised the risk</text></svg>
<div class="verdict"><svg viewBox="0 0 120 120" width="96" height="96"><circle cx="60" cy="60" r="54" fill="none" stroke="#a31621" stroke-width="5"/><circle cx="60" cy="60" r="44" fill="none" stroke="#a31621" stroke-width="2"/><text x="60" y="76" text-anchor="middle" font-size="46" font-weight="800" fill="#a31621" font-family="Archivo">87</text></svg><p>High risk.<br>Ask for the address.</p></div></main></div>'''
# ---- 14 Imhof
def m14():
    pts={"#2609":(0.20,0.55),"#2601":(0.18,0.72),"#2604":(0.30,0.95),"#2605":(0.28,0.78),"#2603":(0.50,0.12),"#2608":(0.82,0.33),"#2606":(0.88,0.13),"#2602":(0.84,0.33),"#2607":(0.91,0.22)}
    W,H=600,400
    cont=''
    for i,r in enumerate([40,85,135,190,250]):
        cont+=f'<ellipse cx="95" cy="70" rx="{r*1.1}" ry="{r*0.9}" fill="none" stroke="#7a4b2a" stroke-width="{2 if i in(1,3) else 1}" opacity=".8"/>'
    spots=''
    for o in O:
        x,y=pts[o[0]]; X=40+x*W; Y=20+(1-y)*H*0.88
        spots+=f'<g><circle cx="{X}" cy="{Y}" r="4" fill="#111"/><text x="{X+8}" y="{Y+4}" font-size="12" fill="#111">{esc(o[1])} {o[5]}</text></g>'
    labels=''.join(f'<text x="{95+int(r*1.1)*0.7}" y="{70+int(r*0.9)*0.7}" font-size="10" fill="#7a4b2a">{v}</text>' for r,v in [(85,"40"),(135,"60"),(190,"80")])
    return f'''<div class="m m14"><header><span>WASEL · Survey</span><nav><a class="on">Terrain</a><a>Orders</a><a>Results</a></nav></header><div class="mapbox"><svg viewBox="0 0 680 440" width="100%"><defs><radialGradient id="rg" cx="14%" cy="16%" r="90%"><stop offset="0" stop-color="#d98a6a"/><stop offset=".35" stop-color="#ecc59a"/><stop offset=".7" stop-color="#cfe0c4"/><stop offset="1" stop-color="#a9cfcf"/></radialGradient></defs>
<rect x="40" y="20" width="{W}" height="352" fill="url(#rg)" stroke="#333"/>{cont}{labels}{spots}
<text x="40" y="400" font-size="12" fill="#333">← vague address · address clarity · full address →</text><text x="12" y="200" font-size="12" fill="#333" transform="rotate(-90 12 200)">order value in TND →</text></svg>
<aside><b>Reading the terrain</b><p>Height is risk. The summit sits where a vague address meets a high value. Contours every 20 points.</p><p><b>Sami, 87 m</b><br>On the northern slope. A full address moves him east, down to 16.</p></aside></div></div>'''
# ---- 15 IKEA manual
def line(inner,w=84): return f'<svg viewBox="0 0 90 70" width="{w}" height="{int(w*.78)}" fill="none" stroke="#111" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round">{inner}</svg>'
def m15():
    s1=line('<rect x="10" y="8" width="52" height="34" rx="6"/><path d="M18 52 L30 42"/><path d="M20 20 H52 M20 28 H46 M20 35 H38"/><circle cx="74" cy="20" r="8"/><path d="M62 52 Q74 34 86 52"/>')
    s2=line('<path d="M15 60 V30 L40 10 L65 30 V60 Z"/><rect x="32" y="40" width="16" height="20"/><path d="M72 18 L72 34 M72 40 V42" stroke="#e0a800" stroke-width="4"/><circle cx="72" cy="40" r="1" />')
    s3=line('<rect x="8" y="14" width="46" height="30" rx="6"/><path d="M16 50 L28 44"/><path d="M60 30 H84 M76 22 L84 30 L76 38"/>')
    return f'''<div class="m m15"><header><span>WASEL</span><nav><a class="on">Handle an order</a><a>Orders</a><a>Results</a></nav><span class="pg">Sami · #2601 · step 2 of 3</span></header><div class="steps">
<div class="stp"><b>1</b>{s1}<p>Read what he wrote.</p></div>
<div class="stp now"><b>2</b>{s2}<p>One part is missing: a full address.</p><div class="parts"><span>street</span><span>number</span><span>phone</span></div></div>
<div class="stp"><b>3</b>{s3}<p>Send the question. Wait for the answer.</p><a>Send</a></div></div><div class="ok">✓ When the part arrives, Wasel checks it again for you.</div></div>'''
# ---- 16 Ranganathan
def m16():
    fac=lambda t,items: f'<div class="fc"><h4>{t}</h4>'+''.join(f'<label><input type="checkbox" {"checked" if c else ""}> {i} <em>{n}</em></label>' for i,n,c in items)+'</div>'
    rows=''
    mark={"#2609":"N:H:C:R:3h","#2601":"N:H:C:R:3h","#2604":"N:H:P:R:2h","#2605":"R:H:P:R:1h","#2603":"R:M:Q:U:40m","#2608":"R:L:S:U:0","#2606":"R:L:S:U:0","#2602":"R:L:S:U:0","#2607":"R:L:S:U:0"}
    for o in O: rows+=f'<tr class="{"hit" if o[0] in("#2609","#2601") else ""}"><td class="cm">{mark[o[0]]}</td><td>{bdi(o[1])}<span>{o[2]} · {o[3]} TND</span></td><td>{o[4]} {o[5]}</td></tr>'
    return f'''<div class="m m16"><header><span>WASEL</span><nav><a class="on">Browse</a><a>Messages</a><a>Results</a></nav><div class="crumb"><i>Customer: new</i> : <i>Risk: high</i> : <i>Action: confirm</i> : <i>Zone: rural</i> <a>clear</a></div></header><div class="fb"><aside>{fac("Personality · the customer",[("New","3",True),("Returning","6",False)])}{fac("Matter · the goods",[("under 100 TND","3",False),("100 to 300","4",False),("over 300","2",False)])}{fac("Energy · what to do",[("Confirm","2",True),("Prepay","2",False),("Ship","4",False)])}{fac("Space · the zone",[("Rural","5",True),("Urban","4",False)])}{fac("Time · waiting",[("under 1 h","2",False),("1 to 3 h","3",False)])}</aside>
<section><p class="cnt">2 orders match</p><table><thead><tr><th>Class mark</th><th>Order</th><th>Risk</th></tr></thead>{rows}</table></section></div></div>'''
