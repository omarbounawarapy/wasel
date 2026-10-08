from data import *
def bdi(s): return f'<bdi dir="auto">{esc(s)}</bdi>'
HIGH=[o for o in O if o[4]=="High"]; MED=[o for o in O if o[4]=="Medium"]; LOW=[o for o in O if o[4]=="Low"]
# ---- 1 Bauhaus
def m1():
    def band(cls,shape,title,items):
        chips=''.join(f'<div class="chip"><b>{bdi(o[1])}</b><span>{o[0]} · {o[3]}</span><i>{o[5]}</i></div>' for o in items)
        return f'<div class="band {cls}"><div class="form {shape}"></div><h3>{title}</h3><div class="chips">{chips}</div></div>'
    return f'''<div class="m m1"><aside><div class="wm">wasel</div><nav><a class="on">orders</a><a>messages</a><a>add</a><a>results</a></nav><div class="diag"></div></aside>
<main>{band("r","sq","confirm first",HIGH)}{band("y","tri","check quickly",MED)}{band("b","ci","ship",LOW)}</main></div>'''
# ---- 2 Constructivism
def m2():
    groups=[("CONFIRM","the address",[o for o in O if o[6]=="Confirm the address"]),("PREPAY","first",[o for o in O if o[6]=="Ask for prepayment"]),("CHECK","quickly",[o for o in O if o[6]=="Quick check"]),("SHIP","now",[o for o in O if o[6]=="Ship"])]
    rows=''
    for i,(v,r,items) in enumerate(groups):
        names=' · '.join(f'{bdi(o[1])} {o[5]}' for o in items)
        rows+=f'<div class="cmd c{i}"><b>{len(items)}</b><div><h3>{v}<small>{r}</small></h3><p>{names}</p></div></div>'
    return f'''<div class="m m2"><div class="wedge"></div><header><span>WASEL</span><nav><a class="on">ORDERS</a><a>MESSAGES</a><a>RESULTS</a></nav></header><main>{rows}</main><div class="circ">87</div></div>'''
# ---- 3 Wabi-sabi / kintsugi
import random
def crack(seed,n,gold=False,w=120,h=90):
    r=random.Random(seed); d=''; x,y=r.randint(10,30),0
    for _ in range(n):
        pts=[(x,y)]
        for _ in range(4):
            x=max(4,min(w-4,x+r.randint(-22,22))); y=min(h,y+r.randint(10,24)); pts.append((x,y))
        d+='M'+' L'.join(f'{a} {b}' for a,b in pts)
        x,y=r.randint(10,w-10),r.randint(0,10)
    col="#b8923a" if gold else "#2c2824"
    return f'<svg viewBox="0 0 {w} {h}" class="cr"><path d="{d}" fill="none" stroke="{col}" stroke-width="{2.4 if gold else 1.4}" stroke-linecap="round"/></svg>'
def m3():
    cards=''
    wait={"#2609":"3 h","#2601":"3 h","#2604":"2 h","#2605":"1 h","#2603":"40 min"}
    for i,o in enumerate(O):
        n={"High":3,"Medium":2,"Low":0}[o[4]]
        mended = o[0]=="#2601"
        cr=crack(i,n,False)+(crack(i,n,True) if mended else '')
        tone={"High":"#b9a798","Medium":"#cbbfaa","Low":"#d8d3c8"}[o[4]]
        cards+=f'<div class="cup" style="background:{tone};transform:rotate({(i%3-1)*1.2}deg);height:{150+o[5]*0.5}px">{cr}<b>{bdi(o[1])}</b><span>{o[2]} · {o[3]}</span><em>{("waiting "+wait[o[0]]) if o[0] in wait else "ready"}</em></div>'
    return f'''<div class="m m3"><header><span>wasel</span><nav><a class="on">shelf</a><a>messages</a><a>results</a></nav></header><p class="note">The longer an order waits, the more it weathers. When the customer answers, the break is mended in gold and stays visible.</p><div class="shelf">{cards}</div></div>'''
# ---- 4 Saul Bass
def m4():
    strips=''
    for o in O[:5]:
        col={"High":"#e8501e","Medium":"#f2a900","Low":"#1a1a1a"}[o[4]]
        act={"Confirm the address":"↗ ASK","Ask for prepayment":"→ PREPAY","Quick check":"↘ CHECK","Ship":"↓ SHIP"}[o[6]]
        strips+=f'<div class="strip"><i class="sp"></i><div class="fr f1"><b>{bdi(o[1])}</b><span>{o[2]}</span></div><div class="fr f2" style="background:{col}"><em>{o[5]}</em></div><div class="fr f3"><strong>{act}</strong></div><i class="sp"></i></div>'
    return f'''<div class="m m4"><header><span>WASEL</span><nav><a class="on">STORYBOARD</a><a>MESSAGES</a><a>RESULTS</a></nav></header><p class="cap">Every order is three frames: what they said, how it will end, what you do.</p><div class="reel">{strips}</div><div class="more">+ 4 more orders, all ready to ship</div></div>'''
# ---- 5 Metro
def m5():
    return f'''<div class="m m5"><div class="pan"><div class="sec s1"><h1>orders</h1><div class="tl big r"><b>4</b><span>need you</span></div><div class="tl med o"><b>1</b><span>quick check</span></div><div class="tl med g"><b>4</b><span>ready to ship</span></div><div class="tl wide b"><span>Sami · #2601 · 87</span><em>“9rib el jemaa”<br>Confirm the address</em></div></div>
<div class="sec s2"><h1>messages</h1><div class="tl big d"><b>0</b><span>unread</span></div><div class="tl wide d2"><span>WhatsApp off in demo mode</span></div></div>
<div class="sec s3"><h1>results</h1><div class="tl big g"><b>128</b><span>refusals avoided</span></div><div class="tl med b"><b>24%</b><span>refused with Wasel</span></div></div></div><div class="bar"><span>●</span><span>◆</span><span>▲</span></div></div>'''
# ---- 6 Newsroom
def m6():
    lead=O[1]; briefs=[O[0],O[2],O[3]]
    bs=''.join(f'<article><h4>{bdi(o[1])}: {o[6].lower()}</h4><p>{o[2]}, {o[3]} TND. Score {o[5]}.</p></article>' for o in briefs)
    also=', '.join(f'{bdi(o[1])} {o[5]}' for o in LOW)
    return f'''<div class="m m6"><header><div class="mast">The Wasel Daily</div><nav><span>Tuesday 7 October</span><a>Orders</a><a>Messages</a><a>Results</a></nav></header>
<div class="front"><article class="lead"><h2>Sami's 220 TND headset is likely to be refused unless the address is confirmed</h2><p class="by">High risk 87 · rural zone · new customer</p><p>He gave “Douar Ouled Ali, <b>9rib el jemaa</b>” and said <b>ghali chwaya</b> when asked about the price. Wasel found three warning signs. If he sends a full address the score falls to 16.</p><p class="ed"><a class="run">Run it: send the question</a> <a>Hold</a> <a>Spike: cancel</a></p></article>
<div class="col">{bs}</div></div><footer><b>Also ready:</b> {also}</footer></div>'''
# ---- 7 Triage tags
def m7():
    def tag(o,cls):
        a="✓" if o[4]=="Low" else "✕"
        v="✓" if o[3]<300 else "✕"
        h="✓" if o[4]=="Low" and o[5]<15 else "✕"
        return f'<div class="tag {cls}"><i class="hole"></i><div class="hd">{o[0]}</div><b>{bdi(o[1])}</b><ul><li><span>Address</span><u>{a}</u></li><li><span>Value</span><u>{v}</u></li><li><span>History</span><u>{h}</u></li></ul><div class="tear">{o[6]}</div></div>'
    z=lambda cls,title,items: f'<section class="zone {cls}"><h3>{title} <em>{len(items)}</em></h3><div class="rail">{"".join(tag(o,cls) for o in items)}</div></section>'
    return f'''<div class="m m7"><header><span>WASEL</span><nav><a class="on">TRIAGE</a><a>MESSAGES</a><a>RESULTS</a></nav><p>Categorise, do not diagnose. Three checks, thirty seconds.</p></header><div class="zones">{z("red","IMMEDIATE",HIGH)}{z("yel","DELAYED",MED)}{z("grn","MINOR",LOW)}<section class="zone blk"><h3>HOLD <em>0</em></h3><p>Nothing cancelled.</p></section></div></div>'''
# ---- 8 Airport signage
def m8():
    arrow={"Confirm the address":"↖","Ask for prepayment":"→","Quick check":"↗","Ship":"↓"}
    rows=''
    for o in O:
        rows+=f'<div class="sg"><span class="pic">{ {"High":"●","Medium":"◆","Low":"▲"}[o[4]] }</span><span class="to">{bdi(o[1])}<small>{o[6]}</small></span><span class="code">{o[0]}</span><span class="ar">{arrow[o[6]]}</span></div>'
    return f'''<div class="m m8"><header><span class="logo">Wasel</span><nav><a class="on">Departures</a><a>Messages</a><a>Results</a></nav></header><div class="board"><div class="hd"><span></span><span>Order</span><span>No.</span><span>Go</span></div>{rows}</div><div class="legend">↖ confirm the address &nbsp; → ask for prepayment &nbsp; ↗ quick check &nbsp; ↓ ship</div></div>'''
# ---- 9 Pacioli ledger
def m9():
    deb=''.join(f'<tr><td>{esc(t)}</td><td class="n">{p}</td></tr>' for t,p in REASONS)
    return f'''<div class="m m9"><header><span>WASEL · Libro</span><nav><a class="on">Ledger</a><a>Messages</a><a>Results</a></nav></header><div class="page"><h2>#2601 · Sami · casque bluetooth · 220 TND</h2><div class="journal"><b>Journal</b><p>12:36 · Dr · “9rib el jemaa” · 17</p><p>12:36 · Dr · rural zone · 13</p><p>12:47 · Dr · “ghali chwaya” · 12</p><p class="cr">13:05 · Cr · full address given · 32 <em>(after reply)</em></p></div>
<div class="tacc"><div class="side"><h4>Raises the risk (debit)</h4><table>{deb}<tr><td>base for first orders</td><td class="n">45</td></tr></table></div><div class="side cr"><h4>Lowers the risk (credit)</h4><table><tr><td>full address given</td><td class="n">32</td></tr><tr><td>—</td><td></td></tr></table></div></div>
<div class="bal"><span>Balance: score</span><b>87 → 16</b><span class="dbl">after the credit entry</span></div></div></div>'''
# ---- 10 Cybersyn exception room
def m10():
    return f'''<div class="m m10"><header><span>WASEL</span><nav><a class="on">Operations</a><a>Messages</a><a>Results</a></nav></header><main><div class="ring"><i></i><b>7 of 9</b><span>within limits</span></div>
<div class="alerts"><div class="alg"><em>Escalated to you</em><b>Sami · #2601</b><p>High risk 87. Question sent 3 h ago, no reply. The assistant tried once.</p><a>Take over</a></div><div class="alg"><em>Escalated to you</em><b>Hedi · #2604</b><p>450 TND, vague address. Prepayment asked 2 h ago, no reply.</p><a>Take over</a></div></div></main><footer><span>Level 1 customer</span> › <span>Level 2 assistant</span> › <span class="on">Level 3 you</span><p>Quiet unless something leaves its limits.</p></footer></div>'''
