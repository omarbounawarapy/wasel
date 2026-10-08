from d import *
import math
# ---------------- 1 Bloomberg
def p1():
    rows=''.join(f'<tr class="{"sel" if o[0]=="#2601" else ""}"><td>{o[0][1:]}</td><td>{bdi(o[1])}</td><td class="r">{o[3]}</td><td class="{o[4][0].lower()}">{SH[o[4]]} {o[5]}</td><td>{o[6].upper()}</td><td class="r">{fmt_age(o[8])}</td></tr>' for o in O)
    feed=''.join(f'<p><b>{t}</b> {m}</p>' for t,m in [("12:36","SAMI  Douar Ouled Ali, 9rib el jemaa"),("12:47","SAMI  ama ghali chwaya"),("12:48","WASEL SCORE v1 87 HIGH"),("12:49","WASEL DRAFT: ask for street, number, phone"),("13:05","HEDI  no reply, 2h10 since question")])
    reas=''.join(f'<tr><td>{esc(t.upper())}</td><td class="r up">+{p}</td></tr>' for t,p in REAS)
    return f'''<div class="p p1"><div class="cmd"><span class="y">WASEL</span><span class="in">ORD 2601 &lt;GO&gt;</span><span class="mut">Sami · casque bluetooth · 220 TND</span><span class="clk">TUE 07 OCT 14:32 CET</span></div>
<div class="grid"><section class="pn a"><h3><em>ORD</em> Order blotter</h3><table><thead><tr><th>ID</th><th>CUSTOMER</th><th>TND</th><th>RISK</th><th>NEXT</th><th>AGE</th></tr></thead>{rows}</table></section>
<section class="pn b"><h3><em>RSN</em> Reasons · #2601</h3><table>{reas}<tr class="tot"><td>SCORE</td><td class="r h">87</td></tr></table><p class="act"><span>1 SEND QUESTION</span><span>2 APPROVE</span><span>3 CANCEL</span></p></section>
<section class="pn c"><h3><em>MSG</em> Conversation</h3>{feed}</section>
<section class="pn d"><h3><em>MON</em> Desk</h3><table><tr><td>HIGH</td><td class="r h">4</td></tr><tr><td>MEDIUM</td><td class="r a2">1</td></tr><tr><td>LOW</td><td class="r g">4</td></tr><tr><td>AT RISK TND</td><td class="r">1,148</td></tr><tr><td>LLM</td><td class="r g">LIVE</td></tr></table></section></div>
<div class="fk"><span>1 Orders</span><span>2 Msgs</span><span>3 Add</span><span>4 Results</span><span>5 Quality</span><span class="r2">ESC Cancel</span></div></div>'''
# ---------------- 2 Observability
def spark(vals,w=300,h=70,color="#73bf69",fill=True):
    mx=max(vals); mn=min(vals); n=len(vals)
    pts=[(i*w/(n-1), h-(v-mn)/(mx-mn+1e-9)*(h-8)-4) for i,v in enumerate(vals)]
    d='M'+' L'.join(f'{x:.1f} {y:.1f}' for x,y in pts)
    a=d+f' L{w} {h} L0 {h} Z'
    return f'<svg viewBox="0 0 {w} {h}" width="100%" height="{h}" preserveAspectRatio="none">'+(f'<path d="{a}" fill="{color}" opacity=".15"/>' if fill else '')+f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"/></svg>'
def p2():
    orders=[12,18,22,31,36,28,19,24,33,38,29,21]
    refus=[31,30,32,29,28,27,28,26,25,25,24,24]
    conf=[44,40,38,41,36,33,30,28,27,26,25,24]
    back=[2,3,3,4,6,5,4,5,7,8,7,5]
    tab=''.join(f'<tr><td>{o[0]}</td><td>{bdi(o[1])}</td><td><span class="b {o[4][0].lower()}">{o[5]}</span></td><td>{o[7]}</td><td>{fmt_age(o[8])}</td></tr>' for o in O[:5])
    stat=lambda t,v,u,c,sub: f'<div class="st"><span>{t}</span><b class="{c}">{v}<small>{u}</small></b><i>{sub}</i></div>'
    return f'''<div class="p p2"><div class="tb"><b>Wasel / Operations</b><span class="vr">zone: <i>All</i></span><span class="vr">tier: <i>High, Medium</i></span><span class="rng">Last 12 hours ▾</span><span class="rf">Refresh 10s</span></div>
<div class="row sts">{stat("Orders (traffic)","247","/day","g","+12% vs yesterday")}{stat("Refused at door (errors)","24","%","y","threshold 25%")}{stat("Time to confirm (latency)","24","min","g","p90 · goal 30")}{stat("Backlog (saturation)","5","orders","r","limit 4 · 2 over 2 h")}</div>
<div class="row mid"><div class="pnl"><h4>Orders per hour</h4>{spark(orders,420,120,"#73bf69")}</div><div class="pnl"><h4>Refusal rate %</h4>{spark(refus,420,120,"#f2cc0c")}</div></div>
<div class="row mid"><div class="pnl"><h4>Highest risk right now</h4><table><thead><tr><th>Order</th><th>Customer</th><th>Risk</th><th>Zone</th><th>Waiting</th></tr></thead>{tab}</table></div><div class="pnl sm"><h4>Time to confirm, p90 (min)</h4>{spark(conf,260,100,"#5794f2")}<h4 style="margin-top:8px">Backlog</h4>{spark(back,260,60,"#f2495c")}</div></div></div>'''
# ---------------- 3 OMS blotter
def p3():
    stcol={"Scored":"#e8e8e8","Question sent":"#bcd6f5","Awaiting reply":"#d9c8ee","Ready":"#c6efc1"}
    rows=''.join(f'<tr class="{"sel" if o[0]=="#2601" else ""}" style="background:{stcol.get(o[9] if o[0]!="#2604" else "Awaiting reply")}"><td>{o[0]}</td><td>{bdi(o[1])}</td><td>{o[2]}</td><td class="r">{o[3]}</td><td><b class="t{o[4][0]}">{SH[o[4]]} {o[4]}</b></td><td class="r">{o[5]}</td><td>{o[9] if o[0]!="#2604" else "Awaiting reply"}</td><td>{o[6]}</td><td class="r">{fmt_age(o[8])}</td></tr>' for o in O)
    leg=''.join(f'<span><i style="background:{c}"></i>{t}</span>' for t,c in [("Scored","#e8e8e8"),("Question sent","#bcd6f5"),("Awaiting reply","#d9c8ee"),("Ready","#c6efc1"),("Cancel pending","#f5b6ea"),("Cancelled","#f2a3a3")])
    return f'''<div class="p p3"><div class="menu"><span>File</span><span>Edit</span><span>Orders</span><span>Messages</span><span>Results</span><span class="r2">Wasel Desk · Synthetic</span></div>
<div class="tbar"><b>Order blotter</b><span>Filter: All tiers ▾</span><span>Sort: Risk ▾</span><span class="rr">9 orders · 4 need action</span></div>
<table class="bl"><thead><tr><th>Order</th><th>Customer</th><th>Item</th><th>TND</th><th>Risk</th><th>Score</th><th>Status</th><th>Next action</th><th>Age</th></tr></thead>{rows}</table>
<div class="leg">{leg}</div>
<div class="tkt"><div class="th">Order ticket · #2601 Sami</div><div class="tb2"><div><span>Score</span><b>87</b></div><div><span>Item</span><b>casque bluetooth</b></div><div><span>Value</span><b>220 TND</b></div><div><span>Zone</span><b>Rural</b></div><div><span>Next</span><b>Ask for address</b></div><div class="btns"><a class="send">SEND QUESTION</a><a>APPROVE</a><a class="cx">CANCEL</a></div></div></div></div>'''
# ---------------- 4 Fraud review
def p4():
    q=''.join(f'<div class="qi {"on" if o[0]=="#2601" else ""}"><div><b>{bdi(o[1])}</b><span>{o[2]} · {o[3]} TND</span></div><em class="{o[4][0].lower()}">{o[5]}</em></div>' for o in O[:6])
    ev=lambda t,items: f'<div class="ev"><h5>{t}</h5>'+''.join(f'<div><span>{a}</span><b>{b}</b></div>' for a,b in items)+'</div>'
    return f'''<div class="p p4"><div class="top"><b>Wasel</b><nav><a>Home</a><a class="on">Reviews <em>4</em></a><a>Orders</a><a>Rules</a><a>Reports</a></nav><span class="srch">Search</span></div>
<div class="body"><aside><div class="ah"><b>Open reviews</b><span>4 high · 1 medium</span></div>{q}</aside>
<main><div class="mh"><div><h2>Sami · casque bluetooth · 220 TND</h2><p>#2601 · opened 190 min ago · WhatsApp</p></div><span class="rk">High risk 87</span></div>
<div class="cols">{ev("Customer's words",[("12:36","“Douar Ouled Ali, 9rib el jemaa”"),("12:47","“ama ghali chwaya”")])}{ev("Address check",[("Street","Not given"),("Landmark","“near the mosque”"),("Zone","Rural")])}{ev("History",[("Orders before","None"),("Delivered","–"),("Refused","–")])}</div>
<div class="why"><h5>Why 87</h5>{''.join(f'<div class="wr"><span>{esc(t)}</span><div class="bar"><i style="width:{p*4}px"></i></div><b>+{p}</b></div>' for t,p in REAS)}</div>
<div class="dec"><span>J / K previous, next</span><a class="pri">Ask for the address</a><a>Approve</a><a class="rej">Cancel order</a></div></main></div></div>'''
# ---------------- 5 Control tower (map)
def p5():
    pts={"#2609":(250,200),"#2601":(220,255),"#2604":(180,360),"#2605":(280,300),"#2603":(330,120),"#2608":(380,145),"#2606":(340,175),"#2602":(395,175),"#2607":(300,150)}
    col={"High":"#d63a2f","Medium":"#e39b12","Low":"#1f8a5b"}
    mk=''.join(f'<g><circle cx="{pts[o[0]][0]}" cy="{pts[o[0]][1]}" r="{11 if o[0]=="#2601" else 8}" fill="{col[o[4]]}" stroke="#fff" stroke-width="3"/>{"<circle cx=%d cy=%d r=18 fill=none stroke=#d63a2f stroke-width=2 />"%pts[o[0]] if o[0]=="#2601" else ""}</g>' for o in O)
    land="M210 40 C280 30 380 70 400 120 C420 170 400 230 360 270 C340 320 320 380 290 430 C260 470 210 470 190 420 C170 360 150 290 175 230 C185 180 170 100 210 40 Z"
    ex=''.join(f'<div class="ex {o[4][0].lower()}"><b>{bdi(o[1])} · {o[0]}</b><span>{o[7]} · {fmt_age(o[8])} waiting · {o[6]}</span></div>' for o in O[:4])
    return f'''<div class="p p5"><div class="tp"><b>Wasel Control Tower</b><span class="f">Region: All Tunisia ▾</span><span class="f">Window: Today ▾</span><div class="kp"><span><b>247</b> orders</span><span><b class="r">4</b> at risk</span><span><b>24%</b> refusal</span></div></div>
<div class="bd"><aside><h4>Exceptions <em>4</em></h4>{ex}</aside><main><svg viewBox="0 0 600 500" width="100%" height="100%"><rect width="600" height="500" fill="#dfe8ee"/><path d="{land}" fill="#f4f2ec" stroke="#aab4bd" stroke-width="2"/><path d="M200 120 Q260 150 300 140 M180 300 Q250 330 330 290" stroke="#d3d8dc" fill="none"/>{mk}<text x="470" y="470" font-size="11" fill="#6b7782">Schematic map, not to scale</text></svg></main>
<section class="dt"><h4>Sami · #2601</h4><p class="r">High 87 · Rural</p><div class="e"><span>Question sent</span><b>190 min ago</b></div><div class="e"><span>Next</span><b>Confirm address</b></div><div class="e"><span>If answered</span><b>87 → 16</b></div><a>Open order</a></section></div></div>'''
