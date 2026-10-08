from d import *
# ---------------- 11 Support inbox with SLA
def p11():
    sla={"#2609":"−0:15","#2601":"−0:10","#2604":"0:20","#2605":"0:50","#2603":"1:20","#2608":"–","#2606":"–","#2602":"–","#2607":"–"}
    conv=''.join(f'<div class="cv {"on" if o[0]=="#2601" else ""}"><div class="av">{esc(o[1][0])}</div><div class="tx"><b>{bdi(o[1])} <i>{o[0]}</i></b><span>{o[2]} · {o[6]}</span></div><span class="sla {"br" if sla[o[0]].startswith("−") else "ok"}">{sla[o[0]]}</span></div>' for o in O[:6])
    views=[("Needs reply",3,True),("SLA at risk",2,False),("Waiting on customer",1,False),("Ready to ship",4,False),("All open",9,False)]
    vv=''.join(f'<a class="{"on" if on else ""}">{t}<em>{n}</em></a>' for t,n,on in views)
    return f'''<div class="p p11"><div class="top"><b>Wasel Inbox</b><span class="pres">● You · available</span><span class="srch">Search conversations</span></div><div class="bd"><nav class="vw">{vv}</nav><section class="lst">{conv}</section>
<main><div class="mh"><b>Sami · casque bluetooth · 220 TND</b><span class="rk">High 87</span><span class="sl br">SLA −0:10</span></div>
<div class="th"><div class="m in2">Douar Ouled Ali, 9rib el jemaa <time>12:36</time></div><div class="m in2">ama ghali chwaya <time>12:47</time></div><div class="m out">Wasel draft · Bonjour Sami, pouvez-vous nous donner la rue, le numéro et un téléphone ? <time>13:05 sent</time></div><div class="m note">Internal: no reply in 3 h. Escalated.</div></div>
<div class="cmp"><div class="mac"><a>Ask for address</a><a>Ask prepayment</a><a>Call instead</a></div><div class="box">Reply to Sami, or use a macro…</div><div class="sd"><a class="pri">Send</a><a>Send and next</a></div></div></main></div></div>'''
# ---------------- 12 Polaris admin
def p12():
    tone={"High":"crit","Medium":"warn","Low":"ok"}
    rows=''.join(f'<tr><td><i class="cb"></i></td><td><b>{o[0]}</b></td><td>{bdi(o[1])}</td><td>{o[2]}</td><td class="r">{o[3]} TND</td><td><span class="bg {tone[o[4]]}">{o[4]} {o[5]}</span></td><td><span class="bg {"info" if o[9]=="Question sent" else "gr"}">{o[9]}</span></td><td>{o[6]}</td></tr>' for o in O)
    return f'''<div class="p p12"><div class="gb"><b>Wasel</b><span class="srch">Search orders, customers</span><span class="us">Owner</span></div><div class="bd"><nav class="sn"><a class="on">Orders</a><a>Messages</a><a>Add an order</a><a>Results</a><a>Quality</a></nav>
<main><div class="ph"><h2>Orders</h2><a class="pri">Add order</a></div><div class="cd"><div class="tabs"><a class="on">All</a><a>Needs review <em>4</em></a><a>Awaiting reply <em>3</em></a><a>Ready <em>4</em></a></div><div class="fl"><span class="in">Filter orders</span><span class="pill">Risk: High ×</span><span class="pill">+ Add filter</span><span class="so">Sort ▾</span></div>
<table><thead><tr><th></th><th>Order</th><th>Customer</th><th>Item</th><th>Total</th><th>Risk</th><th>Status</th><th>Next step</th></tr></thead>{rows}</table></div></main></div></div>'''
# ---------------- 13 SAP Fiori
def p13():
    wl=''.join(f'<tr class="{"sel" if o[0]=="#2601" else ""}"><td><b>{o[0]}</b><span>{bdi(o[1])}</span></td><td class="r">{o[5]}</td><td><span class="sg {o[4][0].lower()}">{o[4]}</span></td></tr>' for o in O[:7])
    return f'''<div class="p p13"><div class="sb"><b>Wasel</b><span>Order Review</span><i class="av">OW</i></div><div class="fcl">
<section class="wk"><div class="kp"><span class="kt r"><b>4</b>High</span><span class="kt"><b>1</b>Medium</span><span class="kt g"><b>4</b>Low</span></div><div class="tb2"><span>Work list (9)</span><span class="se">Search</span></div><table><thead><tr><th>Order</th><th>Score</th><th>Risk</th></tr></thead>{wl}</table></section>
<section class="ob"><div class="hd"><h2>#2601 · Sami</h2><p>casque bluetooth · 220 TND</p><div class="fc"><div><span>Score</span><b>87</b></div><div><span>Zone</span><b>Rural</b></div><div><span>Waiting</span><b>3 h 10</b></div><div><span>Customer</span><b>New</b></div></div></div>
<div class="an"><a class="on">General</a><a>Evidence</a><a>Messages</a><a>History</a></div><div class="sec"><h4>Evidence</h4><div class="g"><span>Quote</span><b>“9rib el jemaa”</b><span>Address</span><b>Landmark only</b><span>Rule</span><b>Vague address +12</b></div></div></section></div>
<div class="ft"><span class="m">Message (1)</span><a class="pri">Ask for address</a><a>Approve</a><a>Cancel order</a></div></div>'''
# ---------------- 14 Carbon data table
def p14():
    rows=''.join(f'<tr class="{"sel" if o[0] in ("#2609","#2601") else ""}"><td><i class="cb {"ck" if o[0] in ("#2609","#2601") else ""}"></i></td><td>{o[0]}</td><td>{bdi(o[1])}</td><td>{o[2]}</td><td class="r">{o[3]}</td><td><span class="tg {o[4][0].lower()}">{o[4]}</span> {o[5]}</td><td>{o[6]}</td><td class="r">{fmt_age(o[8])}</td></tr>' for o in O)
    return f'''<div class="p p14"><div class="sh"><span class="mn">☰</span><b>Wasel</b> <span>Order desk</span><span class="r2">?</span></div><div class="bd"><nav class="sd"><a class="on">Orders</a><a>Messages</a><a>Add an order</a><a>Results</a><a>Quality</a></nav>
<main><h2>Orders</h2><div class="bat"><span>2 items selected</span><a>Ask for address</a><a>Ask prepayment</a><a>Cancel</a><span class="x">Cancel selection</span></div><div class="tbr"><span class="se">Search</span><span class="fi">Filter</span><span class="dn">Density ▾</span></div>
<table><thead><tr><th></th><th>Order</th><th>Customer</th><th>Item</th><th>TND</th><th>Risk</th><th>Next step</th><th>Waiting</th></tr></thead>{rows}</table><div class="pg"><span>Items per page: 10</span><span>1–9 of 9</span><span>‹ ›</span></div></main></div></div>'''
# ---------------- 15 NOC wall
def p15():
    cells=[("Orders today","247","g"),("High risk waiting","4","r"),("Refused at door","24%","y"),("Avg time to confirm","24 min","g"),("AI pipeline","FALLBACK","y"),("Escalations","1","r")]
    tl=''.join(f'<div class="wc {c}"><span>{t}</span><b>{v}</b></div>' for t,v,c in cells)
    return f'''<div class="p p15"><div class="hd"><b>WASEL OPERATIONS</b><span class="clk">14:32</span></div><div class="gr">{tl}</div><div class="tk"><span>ESCALATED</span> #2601 SAMI 87 · NO REPLY 3 H 10 &nbsp;&nbsp;·&nbsp;&nbsp; #2604 HEDI 85 · 2 H 10 &nbsp;&nbsp;·&nbsp;&nbsp; #2609 MEHDI 89 · 3 H 15</div></div>'''
# ---------------- 16 Linear-style
def p16():
    grp=lambda t,items,c: f'<div class="g"><h4><i class="{c}"></i>{t} <em>{len(items)}</em></h4>'+''.join(f'<div class="rw {"on" if o[0]=="#2601" else ""}"><span class="id">{o[0]}</span><i class="pr {o[4][0].lower()}"></i><b>{bdi(o[1])}</b><span class="sub">{o[2]}</span><span class="tg">{o[7]}</span><span class="sc">{o[5]}</span></div>' for o in items)+'</div>'
    return f'''<div class="p p16"><aside><div class="ws">Wasel</div><a class="on">Inbox</a><a>My orders</a><a>All orders</a><a>Messages</a><a>Results</a><div class="sp"></div><a>Quality</a></aside>
<main><div class="tp"><b>Inbox</b><span class="fl">Filter</span><span class="dp">Display</span><span class="kb">C new · G I inbox · . menu</span></div>
{grp("Needs you",[O[0],O[1],O[2]],"t")}{grp("Waiting for customer",[O[3],O[4]],"w")}{grp("Ready",[O[5],O[6]],"d")}</main>
<section class="pk"><h4>#2601 Sami</h4><p>High 87 · Rural · 3 h 10</p><div class="pe">“9rib el jemaa”</div><span>Status</span><b>Question sent</b><span>Next</span><b>Confirm address</b></section>
<div class="cmdk"><div class="ci">Ask for the address…</div><div class="co on">Ask for the address <kbd>A</kbd></div><div class="co">Approve for shipping <kbd>S</kbd></div><div class="co">Cancel order <kbd>⌫</kbd></div></div></div>'''
