from data import *
import math
def bdi(s): return f'<bdi dir="auto">{esc(s)}</bdi>'
# ---- 17 Aviation checklist
def m17():
    items=[("Customer message read","DONE","ok"),("Address complete","NOT COMPLETE","nk"),("Order value under 300 TND","NO: 220 is fine, limit 300","ok"),("Prior delivered orders","NONE","nk"),("Phone number given","YES","ok")]
    li=''.join(f'<li class="{c}"><i>{"■" if c=="ok" else "□"}</i><span>{t}</span><b>{r}</b></li>' for t,r,c in items)
    return f'''<div class="m m17"><header><span>WASEL</span><nav><a class="on">Checklist</a><a>Orders</a><a>Results</a></nav></header><div class="card"><h2>BEFORE SHIPPING <small>#2601 · Sami · 220 TND</small></h2><ul>{li}</ul>
<div class="pause"><b>PAUSE</b> Do not hand to the courier until ADDRESS COMPLETE.</div><div class="acts"><a class="pri">SEND ADDRESS QUESTION</a><a>ABORT: CANCEL ORDER</a></div><p class="foot">Checklist 2 of 5 items open · read, do, confirm</p></div></div>'''
# ---- 18 Chiaroscuro
def m18():
    rows=''
    for o in O:
        b=0.55+o[5]/100*0.45
        rows+=f'<div class="ro" style="--b:{b:.2f}"><span>{o[0]}</span><b>{bdi(o[1])}</b><em>{o[2]} · {o[3]} TND</em><strong>{o[5]}</strong></div>'
    return f'''<div class="m m18"><div class="beam"></div><header><span>wasel</span><nav><a class="on">orders</a><a>messages</a><a>results</a></nav></header><div class="rows">{rows}</div><aside><b>Sami</b><p>Douar Ouled Ali, <mark>9rib el jemaa</mark> ama <mark>ghali chwaya</mark></p><a>Ask for the address</a></aside></div>'''
# ---- 19 Zellige completion
def m19():
    cx=[150,300,450]; cy=[110,250,390]
    tiles=''
    done={"#2608","#2606","#2602","#2607"}
    for i,o in enumerate(O):
        x=cx[i%3]+60; y=cy[i//3]-10
        r=62; pts=' '.join(f'{x+r*math.cos(math.radians(22.5+45*k)):.1f},{y+r*math.sin(math.radians(22.5+45*k)):.1f}' for k in range(8))
        glaze=o[0] in done
        fill={"Low":"#12958f","Medium":"#dca017","High":"#b8442c"}[o[4]] if glaze else "#d9cfc3"
        stroke="#123f93" if o[0]!="#2601" else "#111"
        tiles+=f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{6 if o[0]=="#2601" else 3}"/><text x="{x}" y="{y-2}" text-anchor="middle" font-size="15" font-weight="700" fill="{"#fff" if glaze and o[4]!="Medium" else "#2b2118"}">{esc(o[1])}</text><text x="{x}" y="{y+16}" text-anchor="middle" font-size="12" fill="{"#fff" if glaze and o[4]!="Medium" else "#4a3f35"}">{o[5]} · {"decided" if glaze else "to do"}</text>'
    for i in range(2):
        for j in range(2):
            x=cx[i]+60+75; y=cy[j]-10+95-85*0
            x=cx[i]+135; y=cy[j]+60
            tiles+=f'<rect x="{x-9}" y="{y-9}" width="18" height="18" fill="#123f93" transform="rotate(45 {x} {y})"/>'
    return f'''<div class="m m19"><header><span>WASEL</span><nav><a class="on">Today's panel</a><a>Messages</a><a>Results</a></nav><p>4 of 9 tiles glazed. Each decision fires a tile; the panel is finished when none are left bare.</p></header><svg viewBox="0 0 700 470" width="100%">{tiles}</svg><aside><b>Next bare tile</b><p>Sami · 87 · ask for the address</p><a>Decide</a></aside></div>'''
# ---- 20 Marey timetable
def m20():
    stages=["Scored","Question asked","Reply","Rescored","Shipped"]
    Y0,Y1=60,330; X0,X1=120,900
    ys=[Y0+i*(Y1-Y0)/4 for i in range(5)]
    hr=lambda h: X0+(h-8)*(X1-X0)/7.2
    grid=''.join(f'<line x1="{hr(h)}" y1="{Y0}" x2="{hr(h)}" y2="{Y1}" stroke="#e1e5ec"/><text x="{hr(h)}" y="{Y1+22}" text-anchor="middle" font-size="12" fill="#586178">{h:02d}:00</text>' for h in range(8,16))
    rows=''.join(f'<line x1="{X0}" y1="{y}" x2="{X1}" y2="{y}" stroke="#cfd5df"/><text x="{X0-10}" y="{y+4}" text-anchor="end" font-size="13" fill="#10182e">{s}</text>' for y,s in zip(ys,stages))
    # order paths: list of (hour, stage idx)
    P={"Sami":[(9.8,0),(9.9,1),(12.5,1)],"Mehdi":[(9.2,0),(9.3,1),(12.2,1)],"Hedi":[(10.5,0),(10.6,1),(12.9,1)],"Nour":[(11.0,0),(11.1,1),(13.1,1)],
       "Yassine":[(8.4,0),(8.5,3),(8.9,4)],"Leila":[(8.7,0),(8.8,3),(9.3,4)],"Rim":[(9.0,0),(9.1,3),(9.6,4)],"Karim":[(9.4,0),(9.5,3),(10.1,4)],"Sarah":[(13.0,0),(13.1,1),(14.2,1)]}
    NOW=14.5
    lines=''
    for n,p in P.items():
        stalled = n in ("Sami","Mehdi","Hedi","Nour","Sarah")
        col="#d63a2f" if stalled else "#1f8a5b"
        pts=' '.join(f'{hr(h):.1f},{ys[s]:.1f}' for h,s in p)
        end=p[-1]
        ext=''
        if stalled: ext=f'<line x1="{hr(end[0]):.1f}" y1="{ys[end[1]]:.1f}" x2="{hr(NOW):.1f}" y2="{ys[end[1]]:.1f}" stroke="{col}" stroke-width="3" stroke-dasharray="3 5"/>'
        lines+=f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="3" stroke-linejoin="round"/>{ext}<circle cx="{hr(end[0] if not stalled else NOW):.1f}" cy="{ys[end[1]]:.1f}" r="4" fill="{col}"/><text x="{hr(p[0][0])+4:.1f}" y="{ys[0]-8-(12 if n in ('Mehdi','Hedi','Yassine','Karim') else 0):.1f}" text-anchor="start" font-size="11" fill="#10182e">{n}</text>'
    now=f'<line x1="{hr(NOW):.1f}" y1="{Y0-10}" x2="{hr(NOW):.1f}" y2="{Y1}" stroke="#10182e" stroke-width="2"/><text x="{hr(NOW):.1f}" y="{Y0-16}" text-anchor="middle" font-size="12" font-weight="700" fill="#10182e">now 14:30</text>'
    return f'''<div class="m m20"><header><span>WASEL</span><nav><a class="on">Timetable</a><a>Orders</a><a>Results</a></nav><p>A steep line is a fast order. A flat line is an order waiting on a customer.</p></header><svg viewBox="0 0 960 380" width="100%">{grid}{rows}{lines}{now}</svg><aside><b>Stalled for 2 h or more</b><p>Mehdi, Sami, Hedi, Nour. Each is high risk and waiting for an answer.</p></aside></div>'''
