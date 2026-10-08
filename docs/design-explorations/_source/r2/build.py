import html, math
# ---------------- data (same orders in every direction)
ORD=[("#2609","Mehdi","mixeur","129","High",89,"Confirm address","Waiting",[("r",5),("r",4),("r",3)]),
     ("#2601","Sami","casque bluetooth","220","High",87,"Confirm address","Needs you",[("r",5),("r",4),("r",3),("r",1)]),
     ("#2604","Hedi","tablette","450","High",85,"Ask prepayment","Waiting",[("r",5),("r",4),("r",2)]),
     ("#2603","سارة","crème visage","35","Medium",42,"Quick check","Waiting",[("r",3),("r",2),("l",1)]),
     ("#2608","كريم","montre connectée","149","Low",14,"Ship","Ready",[("l",4),("l",3),("r",1)]),
     ("#2606","Yassine","jean slim","59","Low",9,"Ship","Ready",[("l",4),("l",3),("l",2)])]
REASONS=[("3 warning signs: “9rib el jemaa”","+17","r"),("rural delivery zone","+13","r"),("vague address (“Douar Ouled Ali”)","+12","r"),("new customer","+7","r")]
MSG=[("Douar Ouled Ali, ","9rib el jemaa"),("ama ","ghali chwaya"),]
def esc(s): return html.escape(s)
def shape(t):  # tier shape: never colour alone
    return {"High":"●","Medium":"◆","Low":"▲"}[t]

# ---------------- logos (built to the direction's own grammar)
def logo_khatem(px=56, c1="#123f93", c2="#12958f"):
    return f'<svg viewBox="0 0 120 120" width="{px}" height="{px}" aria-hidden="true"><rect x="26" y="26" width="68" height="68" fill="{c1}"/><rect x="26" y="26" width="68" height="68" fill="{c2}" stroke="#fff" stroke-width="5" transform="rotate(45 60 60)"/><rect x="26" y="26" width="68" height="68" fill="none" stroke="#fff" stroke-width="5"/><rect x="48" y="48" width="24" height="24" fill="#fff" transform="rotate(45 60 60)"/></svg>'
def logo_roundel(px=56, ink="#1d36a3"):
    return f'<svg viewBox="0 0 138 120" width="{px*138/120:.0f}" height="{px}" aria-hidden="true"><circle cx="58" cy="60" r="46" fill="none" stroke="{ink}" stroke-width="7"/><circle cx="58" cy="60" r="37" fill="none" stroke="{ink}" stroke-width="2.5"/><path d="M38 86 V58 A20 20 0 0 1 78 58 V86 Z" fill="{ink}"/><rect x="50" y="66" width="16" height="20" fill="#fff"/><path d="M96 38 q6 -6 12 0 t12 0 M96 52 q6 -6 12 0 t12 0 M96 66 q6 -6 12 0 t12 0" fill="none" stroke="{ink}" stroke-width="3.5" stroke-linecap="round" transform="translate(2 0)"/></svg>'
def logo_line(px=56, ink="#0d1b3d", acc="#d63a2f"):
    return f'<svg viewBox="0 0 120 120" width="{px}" height="{px}" aria-hidden="true"><path d="M14 98 H44 L70 72 V46" fill="none" stroke="{acc}" stroke-width="13" stroke-linejoin="miter" stroke-linecap="butt"/><circle cx="44" cy="98" r="11" fill="#fff" stroke="{ink}" stroke-width="7"/><circle cx="70" cy="72" r="11" fill="#fff" stroke="{ink}" stroke-width="7"/><path d="M48 46 V28 A22 22 0 0 1 92 28 V46 Z" transform="translate(0 0)" fill="{ink}"/><rect x="62" y="30" width="16" height="16" fill="#fff"/></svg>'
def logo_cells(px=56, ink="#101010", plane="#ff4a1c"):
    cells=[(2,0),(3,0),(1,1),(2,1),(3,1),(4,1),(0,2),(1,2),(2,2),(3,2),(4,2),(5,2),(0,3),(1,3),(4,3),(5,3),(0,4),(1,4),(4,4),(5,4),(0,5),(1,5),(4,5),(5,5)]
    s=''.join(f'<rect x="{12+x*16}" y="{14+y*16}" width="14" height="14" fill="{ink}"/>' for x,y in cells)
    door=''.join(f'<rect x="{12+x*16}" y="{14+y*16}" width="14" height="14" fill="{plane}"/>' for x,y in [(2,4),(3,4),(2,5),(3,5)])
    return f'<svg viewBox="0 0 120 120" width="{px}" height="{px}" aria-hidden="true">{s}{door}</svg>'

# ---------------- shared screen shell
NAV=["Orders","Messages","Add an order","Results","Quality"]
def tabs(): return '<div class="tabs" role="tablist"><button class="on">Needs you <b>1</b></button><button>Waiting <b>3</b></button><button>Ready <b>2</b></button></div>'
def nav(logo, name="Wasel"):
    return f'<aside class="rail"><div class="brand"><span class="lgb">{logo}</span><span class="bn">{name}<i lang="ar">واصل</i></span></div><nav>'+''.join(f'<a class="{"on" if i==0 else ""}" href="#">{n}</a>' for i,n in enumerate(NAV))+'</nav><div class="rfoot">Synthetic data</div></aside>'
def topbar(): return f'<div class="bar"><h3>Orders</h3>{tabs()}<div class="srch">Search orders</div></div>'
def rows(tilefn):
    out=''
    for i,o in enumerate(ORD):
        sel=" sel" if o[0]=="#2601" else ""
        out+=f'<tr class="{sel}"><td class="id">{o[0]}</td><td><b dir="auto">{esc(o[1])}</b><span>{o[2]} · {o[3]} TND</span></td><td><span class="rk {o[4].lower()}"><i>{shape(o[4])}</i>{o[4]} {o[5]}</span></td><td class="sig">{tilefn(o)}</td><td>{o[6]}</td></tr>'
    return out
def table(tilefn,sighead="Why"):
    return f'<table><thead><tr><th>Order</th><th>Customer</th><th>Risk ▾</th><th>{sighead}</th><th>Next step</th></tr></thead><tbody>{rows(tilefn)}</tbody></table>'
def quote():
    return '<p class="q" dir="auto">Douar Ouled Ali, <mark>9rib el jemaa</mark><br>ama <mark>ghali chwaya</mark>. mouch dima fi dar</p>'
def actions(): return '<div class="acts"><button class="pri">Send question</button><button>Approve</button><span class="gap"></span><button class="dng">Cancel order</button></div>'

# =============== A: Zellige / Mosaique ===============
def tiles(o,size=13):
    t=''
    for k,n in o[8]:
        t+=''.join(f'<i class="t {k}"></i>' for _ in range(n))
    return f'<span class="strip">{t}</span>'
def mosaic(counts,cols=8):
    cells=[]
    for k,n in counts: cells+= [k]*n
    return '<div class="mos">'+''.join(f'<i class="t {c}"></i>' for c in cells)+'</div>'
def screenA():
    detail=f'''<section class="det"><header><h4>#2601 · Sami</h4><p>casque bluetooth · 220 TND · rural zone · new customer</p></header>
<div class="score"><span class="rk high"><i>●</i>High 87</span><span class="next">Next: confirm the address</span></div>
{quote()}
<h5>Why this score: every tile is about 3 points</h5>
<div class="mrow"><span class="lab">Now</span>{mosaic([("r",13),("n",3)])}<b>87</b></div>
<div class="mrow"><span class="lab">If they give a full address</span>{mosaic([("r",3),("l",8),("n",5)])}<b>16</b></div>
<ul class="why">{''.join(f'<li><span class="sw {c}"></span>{esc(t)}<b>{p}</b></li>' for t,p,c in REASONS[:3])}</ul>{actions()}</section>'''
    return f'<div class="scr A">{nav(logo_khatem(34))}<main>{topbar()}<div class="split"><div class="lst">{table(tiles,"Reasons")}</div>{detail}</div></main></div>'
# =============== B: Waybill / bordereau ===============
def stampchip(o): return f'<span class="mini">{o[7]}</span>'
def screenB():
    detail=f'''<section class="det"><header><h4>#2601 · Sami</h4><p>casque bluetooth · 220 TND · rural zone · new customer</p></header>
<div class="verdict"><div class="stamp" aria-label="Verdict: confirm the address">CONFIRMER<br>L’ADRESSE</div><div><span class="rk high"><i>●</i>High 87</span><p>Ask for the missing address before a courier is sent.</p></div></div>
{quote()}
<h5>Versions</h5>
<div class="copies"><div class="cp w"><b>v1 · 12:45</b><span>High 87</span><em>3 warning signs, rural zone, vague address</em></div><div class="cp p"><b>v2 · after reply</b><span>Low 16</span><em>full address given −32</em></div></div>
{actions()}</section>'''
    return f'<div class="scr B">{nav(logo_roundel(34))}<main>{topbar()}<div class="split"><div class="lst">{table(lambda o: "<span class=mini>"+o[7]+"</span>","State")}</div>{detail}</div></main></div>'
# =============== C: Metro / ligne ===============
STAGES=["Message","Scored","Asked","Reply","Rescored","Shipped","Door"]
def minijourney(o):
    pos={"Waiting":2,"Needs you":1,"Ready":4}[o[7]]
    c={"High":"#d63a2f","Medium":"#e39b12","Low":"#1f8a5b"}[o[4]]
    s=''.join(f'<i class="st{" on" if i<=pos else ""}" style="--c:{c}"></i>' for i in range(7))
    return f'<span class="mj">{s}</span>'
def journey():
    xs=[30+i*52 for i in range(7)]
    col=lambda i: "#d63a2f" if i<=3 else "#1f8a5b"
    seg=''.join(f'<line x1="{xs[i]}" y1="40" x2="{xs[i+1]}" y2="40" stroke="{col(i)}" stroke-width="8" {"stroke-dasharray=\"2 9\"" if i>=3 else ""}/>' for i in range(6))
    dots=''.join(f'<circle cx="{xs[i]}" cy="40" r="9" fill="#fff" stroke="{"#0d1b3d"}" stroke-width="4"/>' for i in range(7))
    cur=f'<circle cx="{xs[2]}" cy="40" r="14" fill="none" stroke="#d63a2f" stroke-width="3"/>'
    lab=''.join(f'<text x="{xs[i]}" y="76" text-anchor="middle" font-size="10.5" fill="#33405c">{STAGES[i]}</text>' for i in range(7))
    ref=f'<path d="M{xs[5]} 40 L{xs[5]+26} 12" stroke="#8a93a8" stroke-width="3" stroke-dasharray="3 5"/><text x="{xs[5]+30}" y="12" font-size="10" fill="#8a93a8">Refused</text>'
    return f'<svg viewBox="0 0 400 92" width="100%" role="img" aria-label="Order journey: scored high, question asked, waiting for reply; after the reply the line turns green">{seg}{ref}{dots}{cur}{lab}</svg>'
def screenC():
    detail=f'''<section class="det"><header><h4>#2601 · Sami</h4><p>casque bluetooth · 220 TND · rural zone · new customer</p></header>
<div class="score"><span class="rk high"><i>●</i>High 87</span><span class="next">Waiting for the customer</span></div>
<div class="jr">{journey()}<p class="cap">Red until the reply. If they give a full address the line turns green: 87 to 16.</p></div>
{quote()}
<ul class="why">{''.join(f'<li>{esc(t)}<b>{p}</b></li>' for t,p,c in REASONS[:3])}</ul>{actions()}</section>'''
    return f'<div class="scr C">{nav(logo_line(34))}<main>{topbar()}<div class="split"><div class="lst">{table(minijourney,"Journey")}</div>{detail}</div></main></div>'
# =============== D: Crouwel grid ===============
def digits(n):
    # 3x5 cell digits for 0-9
    F={"0":"111101101101111","1":"010110010010111","2":"111001111100111","3":"111001111001111","4":"101101111001001","5":"111100111001111","6":"111100111101111","7":"111001001001001","8":"111101111101111","9":"111101111001111"}
    out='';x0=0
    for d in str(n):
        for r in range(5):
            for c in range(3):
                if F[d][r*3+c]=="1": out+=f'<rect x="{x0+c*17}" y="{r*17}" width="15" height="15"/>'
        x0+=3*17+10
    return f'<svg viewBox="0 0 {x0} 85" height="64" aria-label="{n}" role="img" fill="currentColor">{out}</svg>'
def screenD():
    detail=f'''<section class="det"><header><h4>#2601 · Sami</h4><p>casque bluetooth · 220 TND · rural zone · new customer</p></header>
<div class="plane"><div class="num">{digits(87)}</div><div><span class="rk high"><i>●</i>High</span><p>Confirm the address before a courier is sent.</p></div></div>
{quote()}
<ul class="why">{''.join(f'<li>{esc(t)}<b>{p}</b></li>' for t,p,c in REASONS[:3])}</ul>{actions()}</section>'''
    return f'<div class="scr D">{nav(logo_cells(34))}<main>{topbar()}<div class="split"><div class="lst">{table(lambda o: "<span class=pts>"+str(o[5])+"</span>","Points")}</div>{detail}</div></main></div>'

A,B,C,D=screenA(),screenB(),screenC(),screenD()
exec(open('page.py').read())
