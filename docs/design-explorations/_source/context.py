N="#12386b"; T="#00abab"; I="#0b1d33"; W="#ffffff"
S=lambda w,c: f'fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"'
F={
 "A1":("A1 · Kashida waw","Arabic-first, letter reads next to واصل",
   f'<circle cx="70" cy="42" r="18" {S(12,N)}/><path d="M86 54 C92 84 72 98 16 96" {S(12,T)}/>',
   f'<circle cx="70" cy="42" r="18" {S(12,W)}/><path d="M86 54 C92 84 72 98 16 96" {S(12,T)}/>',False),
 "B2":("B2 · Doorway","Parcel at the customer's door",
   f'<path d="M24 100 V54 A36 36 0 0 1 96 54 V100 Z" fill="{N}"/><rect x="46" y="68" width="28" height="32" rx="5" fill="{W}"/><path d="M12 108 H108" {S(8,T)}/>',
   f'<path d="M24 100 V54 A36 36 0 0 1 96 54 V100 Z" fill="{W}"/><rect x="46" y="68" width="28" height="32" rx="5" fill="{N}"/><path d="M12 108 H108" {S(8,T)}/>',False),
 "C1":("C1 · Ring and square","Address precision, assessment",
   f'<circle cx="60" cy="60" r="44" {S(16,N)}/><rect x="40" y="40" width="40" height="40" rx="8" fill="{T}"/>',
   f'<circle cx="60" cy="60" r="44" {S(16,W)}/><rect x="40" y="40" width="40" height="40" rx="8" fill="{T}"/>',False),
 "D1":("D1 · Heavy w tile","Wordmark-led, strongest tiny",
   f'<rect x="8" y="8" width="104" height="104" rx="26" fill="{N}"/><path d="M24 40 L40 82 L58 52 L76 82 L92 40" {S(13,W)}/><circle cx="98" cy="90" r="8" fill="{T}"/>',
   f'<rect x="8" y="8" width="104" height="104" rx="26" fill="{N}"/><path d="M24 40 L40 82 L58 52 L76 82 L92 40" {S(13,W)}/><circle cx="98" cy="90" r="8" fill="{T}"/>',True),
}
def sv(s,px): return f'<svg viewBox="0 0 120 120" width="{px}" height="{px}" aria-hidden="true">{s}</svg>'
def lock(s,px,ar=True):
    return f'<div class="lk">{sv(s,px)}<div class="wm" style="font-size:{px*0.42:.0f}px"><b>Wasel</b>{"<span lang=ar>واصل</span>" if ar else ""}</div></div>'
def tile(rev,isT,px,r):  # navy rounded tile with reversed mark
    if isT: return f'<div class="tile" style="width:{px}px;height:{px}px;border-radius:{r}">{sv(rev,px)}</div>'
    return f'<div class="tile" style="width:{px}px;height:{px}px;border-radius:{r};background:{N}">{sv(rev,px*0.7)}</div>'
boards=[]
for k,(name,why,mk,rev,isT) in F.items():
    nav=''.join(f'<li class="{"on" if i==0 else ""}"><i></i>{t}</li>' for i,t in enumerate(["Orders to check","WhatsApp messages","Add an order","Money saved"]))
    rows=''.join(f'<tr><td><b>#26{n}</b> {c}</td><td><span class="p {cl}">{t}</span></td><td>Confirm with the customer</td></tr>' for n,c,cl,t in [("09","Mehdi","h","High 89"),("01","Sami","h","High 87"),("03","سارة","m","Medium 42"),("06","Yassine","l","Low 9")])
    favtab=f'<div class="tabs"><div class="tab on">{sv(mk if not isT else mk,16)}<span>Orders · Wasel</span></div><div class="tab"><span>inbox</span></div></div>'
    boards.append(f'''<section class="board"><header><h2>{name}</h2><p>{why}</p></header>
<div class="row">
 <div class="frame desk"><div class="side">{lock(mk,34)}<ul>{nav}</ul></div>
  <div class="main"><div class="status">AI scoring live · WhatsApp off</div><h4>Orders to check</h4><table>{rows}</table></div></div>
 <div class="col">
  <div class="frame mob"><div class="mh">{lock(mk,26,False)}</div><div class="mb"><b>Orders to check</b><div class="line"></div><div class="line s"></div></div></div>
  <div class="frame small"><div class="cap">Browser tab</div>{favtab}<div class="fav"><span>{sv(mk,16)}</span><span>{sv(mk,24)}</span><span>{sv(mk,32)}</span></div></div>
 </div>
 <div class="col">
  <div class="frame phone"><div class="cap">Home screen</div><div class="icons">{tile(rev,isT,44,"11px")}<div class="g"></div><div class="g"></div><div class="g"></div><div class="g"></div><div class="g"></div><div class="g"></div><div class="g"></div></div></div>
  <div class="frame wa"><div class="cap">WhatsApp avatar</div><div class="chat"><div class="av">{tile(rev,isT,44,"50%")}</div><div><b>Wasel</b><span>Please confirm your address…</span></div></div></div>
 </div>
 <div class="frame social"><div class="cap">Social card</div><div class="sc">{lock(rev if False else mk,0 or 1,False) if False else ''}<div class="scc"><div class="sl"><div class="whitecard">{lock(mk,44)}</div></div><b>COD order risk</b><span>Cash-on-delivery refusal risk, read from the customer's own messages.</span></div></div>
  <div class="cap" style="margin-top:12px">One colour, on stamp / invoice</div><div class="mono">{sv(mk.replace(T,N).replace(W,"#fff") if not isT else mk,56)}<span style="display:inline-block;width:12px"></span>{sv(mk.replace(T,"#000").replace(N,"#000"),56) if not isT else sv(mk.replace(N,"#000").replace(T,"#000"),56)}</div></div>
</div></section>''')
css='''
:root{--bg:#eef1f6;--ink:#0b1d33;--muted:#4b5563;--line:#d6dde8;--card:#fff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,"Noto Sans",sans-serif;line-height:1.45}
header.top,main{max-width:1380px;margin:0 auto;padding:0 20px}header.top{padding-top:28px}
h1{margin:0 0 6px;font-size:28px}.lead{color:var(--muted);max-width:80ch;font-size:15px;margin:0}
.board{background:#fff;border:1px solid var(--line);border-radius:18px;padding:20px;margin:20px 0}
.board header h2{margin:0;font-size:20px}.board header p{margin:2px 0 14px;color:var(--muted);font-size:14px}
.row{display:grid;grid-template-columns:minmax(420px,1.6fr) minmax(220px,.8fr) minmax(220px,.8fr) minmax(240px,.9fr);gap:14px;align-items:start}
.col{display:flex;flex-direction:column;gap:14px}
.frame{border:1px solid var(--line);border-radius:12px;background:#f4f6f9;overflow:hidden}
.cap{font-size:11px;color:var(--muted);padding:8px 12px 0;text-transform:uppercase;letter-spacing:.06em}
.lk{display:flex;align-items:center;gap:8px}.wm b{display:block;font-weight:800;color:#0b1d33;line-height:1;letter-spacing:-.4px}
.wm span{display:block;color:#00777a;font-size:.55em;margin-top:2px}
.desk{display:grid;grid-template-columns:200px 1fr;min-height:300px}
.side{background:#e6ecf4;border-right:1px solid #cfd8e6;padding:16px 12px}.side ul{list-style:none;margin:16px 0 0;padding:0;font-size:12px;color:#4b5563}
.side li{display:flex;gap:8px;align-items:center;padding:8px 8px;border-radius:9px}.side li i{width:12px;height:12px;border-radius:3px;background:#9aa8bd}
.side li.on{background:#fff;color:#12386b;font-weight:600}.side li.on i{background:#12386b}
.main{padding:14px}.status{background:#fff;border:1px solid var(--line);border-radius:9px;padding:5px 10px;font-size:11px;color:#374151}
.main h4{margin:12px 0 8px;font-size:17px;color:#0b1d33}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;font-size:11px}td{padding:9px 8px;border-top:1px solid #eef1f6}
.p{padding:2px 8px;border-radius:99px;color:#fff;font-weight:700;white-space:nowrap}.h{background:#dc2626}.m{background:#f59e0b;color:#451a03}.l{background:#047857}
.mob{padding:0}.mh{padding:10px 12px;background:#f4f6f9}.mb{padding:10px 12px;background:#f4f6f9}.mb b{font-size:15px}.line{height:10px;background:#fff;border-radius:6px;margin-top:8px}.line.s{width:60%}
.small .tabs{display:flex;gap:4px;padding:8px 10px 0}.tab{display:flex;gap:6px;align-items:center;font-size:11px;background:#dfe5ef;padding:7px 10px;border-radius:8px 8px 0 0;color:#374151}.tab.on{background:#fff}
.fav{display:flex;gap:18px;align-items:center;padding:12px;background:#fff}.fav span{display:inline-flex;align-items:center}
.phone .icons{display:grid;grid-template-columns:repeat(4,44px);gap:10px;padding:12px;justify-content:center;background:linear-gradient(#cfd9ea,#e9eef7)}
.g{width:44px;height:44px;border-radius:11px;background:rgba(255,255,255,.7)}.tile{display:flex;align-items:center;justify-content:center;overflow:hidden}
.wa .chat{display:flex;gap:10px;align-items:center;padding:12px;background:#fff;font-size:12px}.wa .chat b{display:block}.wa .chat span{color:#6b7280}
.social .sc{padding:12px}.scc{background:linear-gradient(135deg,#0b1d33,#12386b);border-radius:10px;padding:14px;color:#fff;font-size:12px}
.scc b{display:block;font-size:15px;margin:10px 0 2px;color:#7fd6d6;letter-spacing:.05em}.scc span{color:#dbe7f5}.whitecard{background:#fff;border-radius:10px;padding:8px 10px;display:inline-block}
.mono{padding:10px 12px;display:flex;align-items:center}
.scc .wm b{color:#0b1d33;font-size:inherit;margin:0;letter-spacing:-.4px}.scc .wm span{color:#00777a;font-size:.55em;margin:2px 0 0}
.notes{background:#fff;border:1px solid var(--line);border-radius:18px;padding:20px;margin:20px 0}.notes h2{margin-top:0}
@media(max-width:1100px){.row{grid-template-columns:1fr 1fr}.desk{grid-column:1/-1}}
'''
notes='''<section class="notes"><h2>What to look at</h2><ul>
<li><b>Sidebar:</b> does the mark hold its own next to the wordmark at real size, and does it look like it belongs to the UI colours?</li>
<li><b>Tab and 16px:</b> is the silhouette still recognisable?</li>
<li><b>Home screen and WhatsApp avatar:</b> the mark sits in a navy tile or circle. Is it centred and readable, and does it look different from the icons around it?</li>
<li><b>One colour:</b> the last row on each board is the stamp and invoice test, navy and black.</li></ul></section>'''
open('context.html','w').write(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Wasel Logo In Context</title><style>{css}</style></head><body><header class="top"><h1>Wasel: finalists in context</h1><p class="lead">Each finalist shown in the dashboard sidebar and mobile header, a browser tab, a phone home screen, a WhatsApp avatar, a social card and in one colour. Wordmark is a stand-in font.</p></header><main>{"".join(boards)}{notes}</main></body></html>')
print('ok')
