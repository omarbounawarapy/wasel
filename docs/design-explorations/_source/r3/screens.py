from data import *
# ---------------------------------------------------------------- 1 SWISS
def swiss():
    rows=''
    for o in O:
        fs=14+o[5]/100*17
        wk=800 if o[5]>=70 else 600 if o[5]>=40 else 400
        tone='r' if o[4]=="High" else 'g'
        rows+=f'<div class="ln {tone}"><span class="rf">{o[0]}</span><span class="nm" style="font-size:{fs:.1f}px;font-weight:{wk}"><bdi dir="auto">{esc(o[1])}</bdi><small>{o[2]} · {o[3]} TND</small></span><span class="tr">{SHAPE[o[4]]} {o[4]}</span><span class="sc2" style="font-size:{fs:.1f}px;font-weight:{wk}">{o[5]}</span></div>'
    nav=''.join(f'<li class="{"on" if i==0 else ""}"><b>{i+1}</b>{t}</li>' for i,t in enumerate(["Orders to check","Messages","Add an order","Results","Quality"]))
    why=''.join(f'<li><b>+{p}</b>{esc(t)}</li>' for t,p in REASONS[:3])
    return f'''<div class="sc swiss"><aside><div class="wm">Wasel<i>.</i></div><ol class="idx">{nav}</ol><p class="dt">Tuesday<br>7 October<br><span>Synthetic data</span></p></aside>
<section class="list"><h2>Orders</h2>{rows}</section>
<section class="spread"><div class="top"></div><p class="rf">#2601 · Sami · casque bluetooth · 220 TND</p><div class="big">87</div><p class="tier">● High risk</p>
<p class="quote" dir="auto">Douar Ouled Ali, <em>9rib el jemaa</em> ama <em>ghali chwaya</em>.</p><ul class="why">{why}</ul>
<p class="acts"><a class="pri">Send the question →</a><a>Approve</a><a class="far">Cancel order</a></p></section></div>'''
# ---------------------------------------------------------------- 2 DE STIJL
def destijl():
    W,H=700,560
    pos=squarify([o[3] for o in O],0,0,W,H)
    cells=''
    for i,o in enumerate(O):
        x,y,w,h=pos[i]
        cl={"High":"red","Medium":"yel","Low":"blu"}[o[4]]
        sel=" sel" if o[0]=="#2601" else ""
        small=w*h<9000
        cells+=f'<div class="cell {cl}{sel}" style="left:{x:.1f}px;top:{y:.1f}px;width:{w:.1f}px;height:{h:.1f}px"><b dir="auto">{esc(o[1])}</b><span>{o[0]} · {o[3]} TND</span>{"" if small else "<em>"+SHAPE[o[4]]+" "+o[4]+" "+str(o[5])+"</em>"}{"<em>"+SHAPE[o[4]]+str(o[5])+"</em>" if small else ""}</div>'
    nav=''.join(f'<li class="{"on" if i==0 else ""}">{t}</li>' for i,t in enumerate(["Orders","Messages","Add","Results","Quality"]))
    return f'''<div class="sc destijl"><aside><div class="wm">WASEL</div><ul>{nav}</ul><div class="key"><i class="red"></i>High<i class="yel"></i>Medium<i class="blu"></i>Low<p>Area = order value in TND. The black lines are the grid.</p></div></aside>
<main class="mapw"><div class="map" style="width:{W}px;height:{H}px">{cells}</div></main>
<section class="det"><h3>Sami</h3><p class="rf">#2601 · casque bluetooth · 220 TND</p><p class="rk">● High 87</p><p class="q" dir="auto">Douar Ouled Ali, <mark>9rib el jemaa</mark> ama <mark>ghali chwaya</mark></p><ul>{''.join(f"<li><b>+{p}</b> {esc(t)}</li>" for t,p in REASONS[:3])}</ul><div class="btns"><a class="pri">Send the question</a><a>Approve</a></div></section></div>'''
# ---------------------------------------------------------------- 3 ISOTYPE
def parcel(c,size=58,x=False):
    cross=f'<path d="M6 6 L52 52 M52 6 L6 52" stroke="#fff" stroke-width="5"/>' if x else ''
    return f'<svg viewBox="0 0 58 58" width="{size}" height="{size}" aria-hidden="true"><rect x="3" y="12" width="52" height="42" fill="{c}"/><path d="M3 12 L14 3 H44 L55 12 Z" fill="{c}"/><rect x="26" y="3" width="6" height="51" fill="#fff"/>{cross}</svg>'
def isotype():
    col={"High":"#e0401a","Medium":"#e69a00","Low":"#161616"}
    groups={"Confirm the address":[], "Ask for prepayment":[], "Quick check":[], "Ship":[]}
    for o in O: groups[o[6]].append(o)
    cols=''
    for g,items in groups.items():
        pics=''.join(f'<div class="pk{" sel" if o[0]=="#2601" else ""}">{parcel(col[o[4]])}<b dir="auto">{esc(o[1])}</b><span>{SHAPE[o[4]]} {o[5]} · {o[3]}</span></div>' for o in items)
        cols+=f'<div class="colm"><h4>{g}</h4><p class="cnt">{"".join(parcel("#161616",14) for _ in items)} <b>{len(items)}</b></p><div class="pks">{pics}</div></div>'
    v1=''.join(parcel("#e0401a",26) for _ in range(9)); v2=''.join(parcel("#e0401a",26) for _ in range(2))+''.join(parcel("#d8d8d8",26) for _ in range(7))
    saved=''.join(parcel("#161616",22) for _ in range(13))
    return f'''<div class="sc isotype"><header><div class="wm">{parcel("#161616",26)} Wasel</div><nav><a class="on">Orders</a><a>Messages</a><a>Add</a><a>Results</a><a>Quality</a></nav></header>
<div class="boardw"><div class="board">{cols}</div>
<div class="below"><div class="v"><h5>Sami, #2601: one parcel = 10 points</h5><div class="rowp"><span>Now</span>{v1}<b>87</b></div><div class="rowp"><span>If he gives a full address</span>{v2}<b>16</b></div></div>
<div class="v"><h5>Results: one parcel = 10 refused deliveries avoided</h5><div class="rowp">{saved}<b>128</b></div><p>Each parcel is the same size. More parcels, not bigger parcels.</p></div></div></div></div>'''
# ---------------------------------------------------------------- 4 MA / HARA / RAMS
def ma():
    ticks=''.join(f'<i class="{"on" if o[0]=="#2601" else "dn" if o[4]=="Low" else ""}"></i>' for o in O)
    return f'''<div class="sc ma"><div class="tl">Wasel</div><div class="tr">9 orders · 4 need you</div>
<main><p class="s1">Sami wants a Bluetooth headset for 220 TND.</p>
<p class="s2">He wrote <u>“9rib el jemaa”</u> and <u>“ghali chwaya”</u>.<br>We do not know where to deliver.</p>
<p class="s3">Wasel is 87 out of 100 sure this will be refused at the door.</p>
<div class="ch"><a class="pri">Ask for the address</a><a>Ship anyway</a></div></main>
<div class="bt"><div class="ticks">{ticks}</div><span>Space to choose · → next · Esc to list</span></div></div>'''
# ---------------------------------------------------------------- 5 TUFTE
MULT={"#2609":[("vague address “Thala”",17),("rural zone",13),("high value",8),("first order",7)],
      "#2601":[("“9rib el jemaa”",17),("rural zone",13),("vague address",12),("new customer",7)],
      "#2604":[("order value 450 TND",24),("vague address “douar…”",15),("rural zone",9),("asked twice about price",6)],
      "#2605":[("vague address “Kairouan”",14),("order value 349 TND",13),("no phone given",5)],
      "#2603":[("vague address “7ay Nasr”",11),("2 warning signs",9),("repeat customer",-8)],
      "#2608":[("full address given",-18),("urban zone",-9),("first order",5)],
      "#2606":[("6 delivered before",-24),("urban zone",-9)],
      "#2602":[("full address given",-30),("3 delivered before",-12)],
      "#2607":[("full address given",-22),("urban zone",-8)]}
def tufte():
    cells=''
    for o in O:
        rs=MULT[o[0]]
        bars=''
        for t,p in rs:
            w=abs(p)*3.2
            if p>=0: b=f'<span class="bz"><i class="up" style="width:{w:.0f}px"></i></span>'
            else: b=f'<span class="bz neg"><i class="dn" style="width:{w:.0f}px"></i></span>'
            bars+=f'<div class="br"><span class="bl">{esc(t)}</span>{b}<span class="bv">{"+" if p>0 else "−"}{abs(p)}</span></div>'
        hist=f'<span class="hist">v1 87 → v2 16</span>' if o[0]=="#2601" else ''
        cells+=f'<article><header><b dir="auto">{esc(o[1])}</b> <span>{o[0]} · {o[2]} · {o[3]} TND</span><em>{o[5]}</em></header>{bars}{hist}</article>'
    return f'''<div class="sc tufte"><header class="th"><b>Wasel</b><nav><a>Orders</a> <a>Messages</a> <a>Add an order</a> <a>Results</a> <a>Quality</a></nav><span class="sort">Sorted by risk · by value · by age</span></header>
<div class="wall">{cells}</div><aside class="note"><p><b>How to read this.</b> Each bar is one reason. Right of the line raises the risk, left lowers it, at the same scale for every order. The number is the score.</p><p>Look for the order whose bars point away from the others.</p></aside></div>'''
# ---------------------------------------------------------------- 6 BECK
def beck():
    Y={"Confirm the address":130,"Ask for prepayment":280,"Ship":430}
    COL={"Confirm the address":"#d63a2f","Ask for prepayment":"#e39b12","Ship":"#1f8a5b"}
    X=[120,250,380,510,640]; ST=["Scored","Question asked","Reply","Rescored","Shipped"]
    paths=''
    for k,y in Y.items():
        if y<280: d=f"M{X[0]-50} {y} H690 L840 {y+150} H900"
        elif y==280: d=f"M{X[0]-50} {y} H900"
        else: d=f"M{X[0]-50} {y} H690 L840 {y-150} H900"
        paths+=f'<path d="{d}" fill="none" stroke="{COL[k]}" stroke-width="11" stroke-linejoin="miter"/>'
    stat=''
    for k,y in Y.items():
        for i,x in enumerate(X): stat+=f'<circle cx="{x}" cy="{y}" r="8" fill="#fff" stroke="#10182e" stroke-width="4"/>'
    for i,s in enumerate(ST): stat+=f'<text x="{X[i]}" y="70" text-anchor="middle" font-size="12" fill="#586178">{s}</text>'
    for k,y in Y.items(): stat+=f'<text x="{X[0]-62}" y="{y-20}" font-size="14" font-weight="700" fill="{COL[k]}">{k}</text>'
    door=f'<g transform="translate(900 280)"><rect x="-17" y="-17" width="34" height="34" fill="#fff" stroke="#10182e" stroke-width="5" transform="rotate(45)"/><text x="30" y="5" font-size="14" font-weight="700" fill="#10182e">Door</text></g><path d="M905 330 L960 372" stroke="#8a93a8" stroke-width="3" stroke-dasharray="4 6"/><text x="965" y="380" font-size="12" fill="#8a93a8">Refused</text>'
    pl={"#2609":(250,"Confirm the address",-1),"#2601":(380,"Confirm the address",1),"#2603":(120,"Confirm the address",1),"#2604":(250,"Ask for prepayment",-1),"#2605":(250,"Ask for prepayment",1),"#2608":(510,"Ship",-1),"#2606":(510,"Ship",1),"#2602":(640,"Ship",-1),"#2607":(640,"Ship",1)}
    mk=''
    tc={"High":"#d63a2f","Medium":"#e39b12","Low":"#1f8a5b"}
    for o in O:
        x,k,s=pl[o[0]]; y=Y[k]
        sel=o[0]=="#2601"
        mk+=f'<g><circle cx="{x}" cy="{y}" r="{18 if sel else 13}" fill="{tc[o[4]]}" stroke="#10182e" stroke-width="{5 if sel else 3}"/><text x="{x}" y="{y+(-30 if s<0 else 42)}" text-anchor="middle" font-size="13" font-weight="{700 if sel else 600}" fill="#10182e" direction="rtl">{esc(o[1])} {o[5]}</text></g>'
    return f'''<div class="sc beck"><header><div class="wm"><svg viewBox="0 0 120 120" width="26" height="26"><path d="M8 100 H48 L78 70 V44" fill="none" stroke="#d63a2f" stroke-width="14"/><circle cx="48" cy="100" r="11" fill="#fff" stroke="#10182e" stroke-width="7"/></svg> Wasel</div><nav><a class="on">Today</a><a>Messages</a><a>Add</a><a>Results</a><a>Quality</a></nav><span class="honest">Schematic: spacing is not time or distance.</span></header>
<svg viewBox="0 0 1060 520" width="100%" role="img" aria-label="Orders drawn as markers on three lines that converge at the Door">{paths}{stat}{door}{mk}</svg>
<aside class="selc"><b>Sami · #2601</b><span>● High 87 · waiting for the reply</span><a>Open</a></aside></div>'''
SCREENS=dict(swiss=swiss(),destijl=destijl(),isotype=isotype(),ma=ma(),tufte=tufte(),beck=beck())
