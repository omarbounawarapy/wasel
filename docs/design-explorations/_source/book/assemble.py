"""T0.5: assembles one standalone, offline HTML file per direction, and the index page.

A direction module (directions/dNN.py) exposes:
    CSS            the direction's own stylesheet (uses only its own tokens)
    brand()        -> html for the brand sheet
    desktop()      -> list of (label, html) for D1..D7, each html is the inner content of a 1280x800 frame
    phone()        -> list of (label, html) for M1..M6, each html is the inner content of a 390x844 frame
    notes()        -> html for the "how this maps to the real project" section
The wrapper below is deliberately plain so the direction's tokens carry the whole look.
"""
import os, sys, importlib, json
sys.path.insert(0, os.path.dirname(__file__))
from kit import *

WRAP_CSS = """
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0}
.bb-top{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:22px;padding:10px 24px}
.bb-top nav{display:flex;gap:6px;margin-left:auto;flex-wrap:wrap}
.bb-sec{padding:26px 24px 8px}.bb-sec>h2{margin:0 0 4px}.bb-sec>p.lead{margin:0 0 16px;max-width:90ch}
.bb-row{display:flex;gap:28px;flex-wrap:wrap;align-items:flex-start}
.bb-fig{display:flex;flex-direction:column;gap:8px}.bb-fig>figcaption{font-size:13px}.bb-fig{margin:0}
.bb-zt{display:none}.bb-zb{cursor:pointer;font-size:12px;padding:2px 10px;border-radius:99px;border:1px solid currentColor;opacity:.75;align-self:flex-start}
.bb-cap{display:flex;gap:10px;align-items:center}
.bb-d .zm{zoom:.74}.bb-p .zm{zoom:.8}
.bb-fig:has(.bb-zt:checked) .zm{zoom:1}.bb-fig:has(.bb-zt:checked){flex-basis:100%}
@media print{.bb-top{position:static}}
"""

ONLY_JS = """<script>(function(){var q=new URLSearchParams(location.search).get('only');if(!q)return;
document.addEventListener('DOMContentLoaded',function(){document.querySelector('.bb-top').style.display='none';
var st=document.createElement('style');st.textContent='.bb-cap{display:none}.zm{zoom:1!important}.bb-sec{padding:0!important}.bb-sec>h2{display:none}body{background:#888!important}';document.head.appendChild(st);
document.querySelectorAll('.bb-sec').forEach(function(s){if(q==='brand'){if(s.id!=='brand')s.style.display='none';return}
var kind=q[0]==='d'?'desktop':q[0]==='p'?'phone':'';if(s.id!==kind){s.style.display='none';return}
var figs=s.querySelectorAll('.bb-fig');figs.forEach(function(f,i){if(i!==parseInt(q.slice(1))-1)f.style.display='none'})})})})();</script>"""

def fig(label, body, kind, idx):
    z = f"z-{kind}{idx}"
    return (f'<figure class="bb-fig bb-{kind}"><div class="bb-cap"><figcaption>{esc(label)}</figcaption>'
            f'<input type="checkbox" id="{z}" class="bb-zt"><label for="{z}" class="bb-zb">Enlarge</label></div>'
            f'<div class="zm">{body}</div></figure>')

def build_direction(did):
    d = direction(did)
    mod = importlib.import_module("directions." + "d" + did.split("-")[0])
    n = did.split("-")[0]
    desk = mod.desktop(); ph = mod.phone()
    secs = []
    secs.append(("brand", "Brand", f'<div class="bb-row">{mod.brand()}</div>'))
    secs.append(("desktop", "Desktop screens", f'<div class="bb-row">{"".join(fig(l, desktop(h), "d", i) for i, (l, h) in enumerate(desk))}</div>'))
    secs.append(("phone", "Phone screens", f'<div class="bb-row">{"".join(fig(l, phone(h), "p", i) for i, (l, h) in enumerate(ph))}</div>'))
    secs.append(("notes", "On the real project", mod.notes()))
    nav = "".join(f'<a href="#{i}">{t}</a>' for i, t, _ in secs)
    body = "".join(f'<section class="bb-sec" id="{i}"><h2>{t}</h2>{h}</section>' for i, t, h in secs)
    st = stacks(did)
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wasel · {esc(d["name"])}</title><style>{font_css(did)}{FRAME_CSS}{WRAP_CSS}:root{{--ui:{st["ui"]};--data:{st["data"]};--ar:{st["arabic"]}}}
{mod.CSS}</style>{ONLY_JS}</head><body class="{mod.PREFIX}"><header class="bb-top {mod.PREFIX}-top"><b>Wasel · {esc(d["name"])}</b><span>{esc(d["family"])} · synthetic data</span><nav>{nav}</nav></header>{body}</body></html>'''
    out = ROOT + f"book/{did}.html"
    os.makedirs(ROOT + "book", exist_ok=True)
    open(out, "w").write(page)
    return out, len(page.encode())

def build_index(built):
    rows = ""
    for r in REG:
        did = r["id"]; ok = did in built
        sw = "".join(f'<i style="background:{c}" title="{c}"></i>' for c in (r["pal"]["ground"], r["pal"]["primary"], r["pal"]["secondary"], *r["tiers"]["colors"]))
        link = f'<a href="{did}.html">Open</a>' if ok else '<span class="soon">not built yet</span>'
        rows += (f'<tr><td>{did.split("-")[0]}</td><td><b>{esc(r["name"])}</b><span>{esc(r["family"])}</span></td><td>{esc(r["fonts"]["ui"])} + {esc(r["fonts"]["data"])}<span>{esc(r["fonts"]["arabic"])}</span></td>'
                 f'<td class="sw">{sw}</td><td>{" / ".join(esc(t) for t in r["tiers"]["names"])}</td><td>{esc(r["fit"])}</td><td>{link}</td></tr>')
    html_ = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Wasel brand book</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{margin:0;font:14px/1.5 system-ui,sans-serif;background:#f3f4f6;color:#15171c}}main{{max-width:1180px;margin:0 auto;padding:28px 20px}}h1{{margin:0 0 6px}}p{{max-width:80ch;color:#444}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #d6d9df}}th,td{{text-align:left;padding:9px 12px;border-top:1px solid #e7e9ee;vertical-align:top}}th{{font-size:12px;color:#555;border-top:0}}td span{{display:block;color:#666;font-size:12px}}
.sw i{{display:inline-block;width:18px;height:18px;border-radius:3px;border:1px solid rgba(0,0,0,.15);margin-right:3px}}.soon{{color:#999}}a{{color:#0b3d91;font-weight:600}}</style></head>
<body><main><h1>Wasel brand book</h1><p>One standalone, offline file per direction: brand sheet, seven desktop screens, six phone screens and notes on how it applies to the real project. Every direction has its own fonts, palette, tier vocabulary, logo and icons. Synthetic data throughout.</p>
<table><thead><tr><th>#</th><th>Direction</th><th>Fonts</th><th>Colours</th><th>Tier vocabulary</th><th>Fit</th><th></th></tr></thead><tbody>{rows}</tbody></table></main></body></html>'''
    open(ROOT + "book/index.html", "w").write(html_)

if __name__ == "__main__":
    ids = sys.argv[1:] or [r["id"] for r in REG]
    built = {}
    for did in ids:
        try:
            out, size = build_direction(did); built[did] = size; print(f"built {did}: {size/1024:.0f} KB")
        except ModuleNotFoundError as e:
            print(f"skip {did}: {e}")
    prior = [f[:-5] for f in os.listdir(ROOT + "book") if f.endswith(".html") and f != "index.html"]
    build_index(set(prior) | set(built))
