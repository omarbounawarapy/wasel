from d import *
from p_a import spark
import math
# ---------------- 6 Incident console
def p6():
    def grp(title,items,cls):
        r=''.join(f'<div class="inc {"on" if o[0]=="#2601" else ""}"><span class="sv {o[4][0].lower()}">{ {"High":"P1","Medium":"P2","Low":"P3"}[o[4]] }</span><div><b>{bdi(o[1])} · {o[0]}</b><span>{o[7]} · {fmt_age(o[8])}</span></div><em>{o[5]}</em></div>' for o in items)
        return f'<div class="gr {cls}"><h4>{title} <i>{len(items)}</i></h4>{r}</div>'
    trig=[O[0],O[1],O[2]]; ack=[O[3]]; res=[O[7],O[8]]
    tl=''.join(f'<li><time>{t}</time><span>{m}</span></li>' for t,m in [("12:36","Triggered: score 87, three warning signs"),("12:49","Wasel drafted a question; waiting for you"),("13:05","Assistant sent the question"),("14:15","No reply after 70 min"),("14:32","Escalated to you")])
    return f'''<div class="p p6"><div class="hd"><b>Wasel Incidents</b><nav><a class="on">Incidents</a><a>On-call</a><a>Analytics</a><a>Runbooks</a></nav><span class="oc">On call: <b>You</b> until 18:00 · then Assistant</span></div>
<div class="bd"><aside>{grp("Triggered",trig,"t")}{grp("Acknowledged",ack,"a")}{grp("Resolved today",res,"s")}</aside>
<main><div class="mh"><span class="sv h">P1</span><div><h2>Sami · #2601 · address unresolved</h2><p>Triggered 190 min ago · rural · 220 TND</p></div></div><div class="btn"><a class="ack">Acknowledge</a><a>Escalate to owner</a><a>Snooze 30 min</a><a class="rs">Resolve</a></div><h5>Timeline</h5><ul class="tl">{tl}</ul><h5>Runbook</h5><ol class="rb"><li>Ask for street, number and phone.</li><li>If no reply in 60 min, call.</li><li>If still none, hold the courier.</li></ol></main></div></div>'''
# ---------------- 7 CAD dispatch
def p7():
    inc=''.join(f'<tr class="{"sel" if o[0]=="#2601" else ""}"><td class="pr {o[4][0].lower()}">{ {"High":"P1","Medium":"P2","Low":"P3"}[o[4]] }</td><td>{o[0][1:]}</td><td>{bdi(o[1])}</td><td>{o[7].upper()}</td><td>{o[6].upper()}</td><td class="r">{fmt_age(o[8])}</td><td>{ {"Question sent":"WAIT","Scored":"NEW","Ready":"DONE"}[o[9]] }</td></tr>' for o in O)
    units=[("OWNER","AVAILABLE","a"),("ASSISTANT","SENT 3","b"),("COURIER A","EN ROUTE","c"),("COURIER B","AVAILABLE","a"),("LLM","LIVE","a")]
    ut=''.join(f'<div class="un {c}"><b>{n}</b><span>{s}</span></div>' for n,s,c in units)
    log=''.join(f'<p><time>{t}</time> {m}</p>' for t,m in [("14:32","#2601 ESCALATED TO OWNER"),("14:15","#2604 NO REPLY 130 MIN"),("13:50","#2609 QUESTION SENT BY ASSISTANT"),("13:21","#2603 SCORED MEDIUM 42"),("13:05","#2601 QUESTION SENT")])
    return f'''<div class="p p7"><div class="st"><b>WASEL CAD</b><span>14:32:08</span><span class="al">1 ESCALATION</span><span>SHIFT: OWNER</span></div>
<div class="gd"><section class="il"><h4>INCIDENTS</h4><table><thead><tr><th>PRI</th><th>NO</th><th>CUSTOMER</th><th>ZONE</th><th>ACTION</th><th>AGE</th><th>STAT</th></tr></thead>{inc}</table></section>
<section class="ut"><h4>UNITS</h4>{ut}</section>
<section class="lg"><h4>EVENT LOG</h4>{log}</section>
<section class="cm"><h4>COMMAND</h4><div class="in">&gt; ASSIGN 2601 ASSISTANT_</div><p>F1 ASSIGN  F2 CLOSE  F3 NOTE  F4 ESCALATE</p></section></div></div>'''
# ---------------- 8 Clinical central station
def ecg(score,w=260,h=44,final=None):
    pts=[]
    import random
    r=random.Random(score)
    n=40; base=h*0.5
    for i in range(n):
        x=i*w/(n-1)
        amp=score/100*(h*0.45)
        y=base-(amp*(1 if i%8==3 else -0.4 if i%8==4 else 0.15 if i%8==2 else 0))+r.uniform(-1.2,1.2)
        pts.append((x,y))
    d='M'+' L'.join(f'{x:.1f} {y:.1f}' for x,y in pts)
    return f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}"><path d="{d}" fill="none" stroke="#5be37a" stroke-width="2"/></svg>'
def p8():
    ico={"High":("!!!","#ff2d2d"),"Medium":("!!","#ffd400"),"Low":("!","#22d3ee")}
    rows=''
    for o in O:
        s,c=ico[o[4]] if o[4]!="Low" else ("","#22d3ee")
        alarm=f'<span class="al" style="background:{c};color:{"#000" if o[4]!="High" else "#fff"}">{s}</span>' if o[4]!="Low" else '<span class="al off"></span>'
        rows+=f'<div class="ch"><div class="bed">{o[0][1:]}</div><div class="nm"><b>{bdi(o[1])}</b><span>{o[2]}</span></div>{ecg(o[5])}<div class="num">{o[5]}</div>{alarm}</div>'
    return f'''<div class="p p8"><div class="ban"><b>HIGH PRIORITY</b> #2601 Sami: address unresolved 190 min · score 87<a>Silence 2 min</a></div><div class="hd"><span>WASEL CENTRAL STATION</span><span class="k"><i style="background:#ff2d2d"></i>High <i style="background:#ffd400"></i>Medium <i style="background:#22d3ee"></i>Low</span><span>14:32</span></div><div class="chs">{rows}</div></div>'''
# ---------------- 9 ISA-101 HP-HMI
def ind(label,val,unit,lo,hi,span,state="n"):
    pct=(val-span[0])/(span[1]-span[0])*100
    zl=(lo-span[0])/(span[1]-span[0])*100 if lo else 0; zh=(hi-span[0])/(span[1]-span[0])*100 if hi else 100
    return f'<div class="in"><div class="lb">{label}</div><div class="bar"><i class="z lo" style="width:{zl}%"></i><i class="z hi" style="left:{zh}%;width:{100-zh}%"></i><i class="mk {state}" style="left:{pct}%"></i></div><div class="vl {state}">{val}<small>{unit}</small></div></div>'
def p9():
    return f'''<div class="p p9"><div class="l1"><b>Wasel AI pipeline</b><nav><span>L1 Overview</span><span class="on">L2 Pipeline</span><span>L3 Unit</span><span>L4 Detail</span></nav><span class="al">1 abnormal · 0 critical</span></div>
<div class="flow"><div class="eq"><h5>Ingest</h5><span>WhatsApp off · paste on</span>{ind("Queue",3,"msgs",None,8,(0,10))}</div><i class="pipe"></i>
<div class="eq"><h5>Extract (LLM)</h5><span>Primary: Groq</span>{ind("Latency",2.1,"s",None,5,(0,8))}{ind("Quotes verified",99.2,"%",95,None,(90,100))}</div><i class="pipe"></i>
<div class="eq warn"><h5>Fallback</h5><span class="ab">ACTIVE since 13:40</span>{ind("Calls today",412,"",None,480,(0,600),"a")}</div><i class="pipe"></i>
<div class="eq"><h5>Score (code)</h5><span>Model v3 · rules</span>{ind("Drift",0.08,"",None,0.2,(0,0.4))}</div><i class="pipe"></i>
<div class="eq"><h5>Draft + checks</h5><span>3 gates</span>{ind("Blocked",0,"unsafe",None,1,(0,3))}{ind("Judge agree",100,"%",95,None,(90,100))}</div></div>
<div class="note"><b>Abnormal:</b> LLM fallback active since 13:40. Daily call budget 86% used. Everything else is within range. Grey means normal.</div></div>'''
# ---------------- 10 ATC data blocks
def p10():
    pos={"#2609":(300,130),"#2601":(220,230),"#2604":(150,330),"#2605":(340,280),"#2603":(520,110),"#2608":(640,200),"#2606":(700,140),"#2602":(740,260),"#2607":(600,310)}
    tr=''
    for o in O:
        x,y=pos[o[0]]; hi=o[4]=="High"
        c="#ff5a4d" if hi else "#e6b800" if o[4]=="Medium" else "#4be2a0"
        dx,dy=(46,-34) if y>150 else (46,26)
        sym=f'<polygon points="{x},{y-8} {x+8},{y+6} {x-8},{y+6}" fill="none" stroke="{c}" stroke-width="2"/>' if hi else f'<circle cx="{x}" cy="{y}" r="6" fill="none" stroke="{c}" stroke-width="2"/>'
        tr+=f'{sym}<line x1="{x+8}" y1="{y-4}" x2="{x+dx-4}" y2="{y+dy-8}" stroke="{c}" stroke-width="1"/><text x="{x+dx}" y="{y+dy-8}" font-size="12" fill="{c}" font-family="Roboto Mono">{o[1][:9]} {o[5]}</text><text x="{x+dx}" y="{y+dy+5}" font-size="11" fill="{c}" opacity=".8" font-family="Roboto Mono">{o[3]}T {o[6][:7].upper()}</text>'
    strips=''.join(f'<div class="fs {o[4][0].lower()}"><b>{o[0][1:]}</b><span>{bdi(o[1])}</span><em>{o[5]}</em></div>' for o in O[:6])
    rings=''.join(f'<circle cx="420" cy="230" r="{r}" fill="none" stroke="#1b3a2e" stroke-width="1"/>' for r in (80,160,240))
    return f'''<div class="p p10"><aside><h5>STRIP BAY · CONFIRM</h5>{strips}</aside><main><svg viewBox="0 0 840 460" width="100%" height="100%"><rect width="840" height="460" fill="#06100c"/>{rings}<line x1="0" y1="230" x2="840" y2="230" stroke="#1b3a2e"/><line x1="420" y1="0" x2="420" y2="460" stroke="#1b3a2e"/>{tr}<text x="20" y="440" font-size="11" fill="#4a7c66" font-family="Roboto Mono">X waiting time · Y order value · sector 1 · schematic</text></svg><div class="alert">ALERT: 4 HIGH TRACKS WAITING OVER 60 MIN</div></main></div>'''
