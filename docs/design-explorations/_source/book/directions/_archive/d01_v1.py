"""Direction 01: Terminal Desk (Bloomberg Terminal family).
Own identity: Archivo Narrow + Red Hat Mono, Readex Pro for Arabic, amber and cyan on black, tiers ACT / WATCH / CLEAR.
Structure: command line, mnemonic panels, function-key bar. Everything is one keystroke away.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from kit import *

PREFIX = "tm"
D = direction("01-terminal")
pal, T = D["pal"], D["tiers"]
NAMES, COLS = T["names"], T["colors"]
H = hero()
OR = orders()
SELECTED = "#2601"
CY = pal["secondary"]

# ------------------------------------------------------------------ data helpers
def status(o):
    if o["tier_raw"] == "low": return "READY"
    if waiting(o) >= 120: return "WAITING"
    if o["tier_raw"] == "medium": return "NEW"
    return "ASKED"

def nextstep(o):
    return {"high": {"confirm": "CONFIRM", "prepay": "PREPAY"}, "medium": {"confirm": "QUICK CHECK"}, "low": {"ship": "SHIP"}}[o["tier_raw"]][o["action_raw"]]

def hms(m): return f"{m // 60}H{m % 60:02d}" if m >= 60 else f"{m}M"

# ------------------------------------------------------------------ marks
SHAPES = {
    0: '<path d="M6 1 11 11H1z" fill="{c}"/>',
    1: '<path d="M6 1 11 6 6 11 1 6z" fill="{c}"/>',
    2: '<rect x="1.5" y="1.5" width="9" height="9" fill="{c}"/>',
}
def glyph(i, size=12):
    return f'<svg class="tm-gl" width="{size}" height="{size}" viewBox="0 0 12 12" aria-hidden="true">{SHAPES[i].format(c=COLS[i])}</svg>'

def mark(variant="color", size=48):
    a, k, w = pal["primary"], "#000000", "#FFFFFF"
    if variant == "favicon":
        return (f'<svg width="{size}" height="{size}" viewBox="0 0 32 32" aria-label="Wasel favicon"><rect width="32" height="32" fill="{k}"/><rect x="2" y="2" width="28" height="28" fill="{a}"/>'
                f'<path d="M7 8l3 12 3-9 3 9 3-12" fill="none" stroke="{k}" stroke-width="2.4" stroke-linejoin="round"/><path d="M22 28v-8a3 3 0 0 1 6 0v8z" fill="{k}"/></svg>')
    if variant == "app":
        return (f'<svg width="{size}" height="{size}" viewBox="0 0 120 120" aria-label="Wasel app icon"><rect width="120" height="120" rx="22" fill="{k}"/><rect x="8" y="8" width="104" height="104" rx="16" fill="none" stroke="{pal["line"]}" stroke-width="2"/>'
                f'<g transform="translate(17 38) scale(.78)">{_block(a, k)}</g></svg>')
    fg, ink, bg = {"color": (a, k, None), "mono": (w, k, None), "reversed": (k, a, a)}[variant]
    back = f'<rect width="120" height="120" fill="{bg}"/>' if bg else ""
    if variant == "mono": back = f'<rect width="120" height="120" fill="#101010"/>'
    return f'<svg width="{size}" height="{size}" viewBox="0 0 120 120" aria-label="Wasel mark">{back}<g transform="translate(6 18)">{_block(fg, ink)}</g></svg>'

def _block(fg, ink):
    # amber block carrying the command WSL; the cursor gap on the right is cut as a door arch
    return (f'<path d="M0 0H108V84H0z" fill="{fg}"/><text x="7" y="58" font-family="var(--ui)" font-weight="700" font-size="42" fill="{ink}" letter-spacing="0">WSL</text>'
            f'<path d="M82 84V52a11 11 0 0 1 22 0v32z" fill="#000000"/>')

def wordmark(variant="color", size=44):
    col = {"color": pal["primary"], "mono": "#FFFFFF", "reversed": "#000000"}[variant]
    return f'<span class="tm-wm" style="color:{col}"><b style="font-size:{size * .6:.0f}px">WASEL</b><span lang="ar" class="tm-wm-ar">واصل</span></span>'

def lockup(variant="color", size=44):
    return f'<span class="tm-lock">{mark(variant, size)}{wordmark(variant, size)}</span>'

CODES = ["ORD", "MSG", "ADD", "RES", "LOG", "QLT", "FAIL", "MON", "AIC", "SRCH", "SND", "CXL"]
CODE_NAMES = {"ORD": "Orders", "MSG": "Messages", "ADD": "Add an order", "RES": "Money saved", "LOG": "Activity log", "QLT": "Quality checks", "FAIL": "Silent failures", "MON": "Live monitor", "AIC": "AI call log", "SRCH": "Search", "SND": "Send", "CXL": "Cancel"}
def code(c, on=False):
    return f'<span class="tm-code {"on" if on else ""}">{c}</span>'

# ------------------------------------------------------------------ shared pieces
def tchip(o, score=True):
    i = tier_index(o["tier_raw"])
    s = f' <b>{o["score"]}</b>' if score else ""
    return f'<span class="tm-t tm-t{i}">{glyph(i)}{NAMES[i]}{s}</span>'

def cmdbar(cmd="ORD", sub=""):
    return (f'<header class="tm-cmd"><span class="tm-logo">{mark("favicon", 26)}</span><span class="tm-prompt">WASEL</span><span class="tm-in">{esc(cmd)} <u>&lt;GO&gt;</u><i class="tm-cur"></i></span>'
            f'<span class="tm-sub">{esc(sub)}</span><span class="tm-r"><span>AI SCORING LIVE</span><span>WA OFF (DEMO)</span><span class="tm-syn">SYNTHETIC DATA</span><span>TUE 07 OCT 14:32 CET</span></span></header>')

FKEYS = [("F1", "ORD"), ("F2", "MSG"), ("F3", "ADD"), ("F4", "RES"), ("F5", "LOG"), ("F6", "QLT"), ("F7", "FAIL"), ("F8", "MON"), ("F9", "AIC"), ("F10", "HELP")]
def fbar(active=None):
    k = "".join(f'<span class="tm-fk {"on" if n == active else ""}"><i>{f}</i>{n}</span>' for f, n in FKEYS)
    return f'<footer class="tm-fb">{k}<span class="tm-esc">ESC CANCEL</span><span class="tm-go">ENTER GO</span></footer>'

def helpline(text):
    return f'<div class="tm-help"><b>HELP</b> {esc(text)}</div>'

def panel(c, title, body, cls=""):
    return f'<section class="tm-p {cls}"><h3><em>{c}</em>{esc(title)}</h3><div class="tm-pb">{body}</div></section>'

def blotter(rows=None, cols=8):
    rows = rows or OR
    h = '<tr><th>ID</th><th>CUSTOMER</th><th>ITEM</th><th class="r">TND</th><th>RISK</th><th>NEXT</th><th>STATUS</th><th class="r">AGE</th></tr>'
    b = "".join(f'<tr class="{"sel" if o["ref"] == SELECTED else ""}"><td>{o["ref"][1:]}</td><td>{bdi(o["customer"])}</td><td>{esc(o["product"]).upper()}</td><td class="r">{o["price_tnd"]:.0f}</td><td>{tchip(o)}</td><td>{nextstep(o)}</td><td class="tm-s">{status(o)}</td><td class="r">{hms(waiting(o))}</td></tr>' for o in rows)
    leg = f'<p class="tm-leg">9 ORDERS · 4 {NAMES[0]} · 1 {NAMES[1]} · 4 {NAMES[2]} &nbsp;&nbsp; {glyph(0)} {NAMES[0]} ACT NOW &nbsp; {glyph(1)} {NAMES[1]} CONFIRM &nbsp; {glyph(2)} {NAMES[2]} SHIP · AGE = TIME SINCE FIRST MESSAGE</p>'
    return f'<table class="tm-tab">{h}{b}</table>{leg}'

def reasons(compact=False):
    r = f'<tr><td>BASE FOR A FIRST ORDER</td><td class="r">{H["base"]}</td></tr>' + "".join(f'<tr><td>{esc(f["label"]).upper()}</td><td class="r tm-up">+{f["points"]}</td></tr>' for f in H["factors"])
    return f'<table class="tm-tab tm-kv">{r}<tr class="tm-tot"><td>SCORE</td><td class="r">87</td></tr></table>'

def tape(phone=False):
    phr = [f["quote"] for f in H["flags"]]
    ts = ["12:09", "12:36", "12:47"]
    lines = "".join(f'<p class="tm-cl" dir="auto"><time>{t}</time><b>SAMI</b> {hl(m["text"], phr, "tm-hl")}</p>' for m, t in zip(H["messages"], ts))
    sysl = ('<p class="tm-sl"><time>12:48</time><b>WASEL</b> SCORE V1 87 · ACT</p><p class="tm-sl"><time>12:49</time><b>WASEL</b> DRAFT READY: ASK FOR STREET, NUMBER, PHONE</p>')
    return f'<div class="tm-tape">{lines}{sysl}</div>'

def actions():
    return '<div class="tm-act"><span><i>1</i>ASK ADDRESS</span><span><i>2</i>APPROVE</span><span class="tm-cx"><i>3</i>CANCEL ORDER</span></div>'

def mon_desk():
    return ('<table class="tm-tab tm-kv"><tr><td>NEEDS DECISION</td><td class="r">0</td></tr><tr><td>WAITING FOR CUSTOMER</td><td class="r tm-w">5</td></tr><tr><td>READY TO SHIP</td><td class="r tm-g">4</td></tr>'
            f'<tr><td>{NAMES[0]} / {NAMES[1]} / {NAMES[2]}</td><td class="r">4 / 1 / 4</td></tr><tr><td>AT RISK TND</td><td class="r">1,148</td></tr><tr><td>AI SCORING</td><td class="r tm-g">LIVE</td></tr></table>')

# ------------------------------------------------------------------ brand sheet
def swatch(name, hexv, note=""):
    cr = contrast(hexv, "#000000"); tc = "#000" if cr >= 7 else "#fff"
    return f'<div class="tm-sw" style="background:{hexv};color:{tc}"><b>{name}</b><span>{hexv}</span><em>{note}</em></div>'

def brand():
    L = lambda t: f'<h3 class="tm-bh"><em>{t[:3].upper()}</em>{t}</h3>'
    logos = (f'<div class="tm-logos"><div class="tm-lg">{lockup("color", 64)}<span>LOCKUP</span></div><div class="tm-lg">{mark("color", 64)}<span>MARK</span></div><div class="tm-lg">{mark("mono", 64)}<span>ONE COLOUR</span></div>'
             f'<div class="tm-lg tm-inv">{mark("reversed", 64)}<span>REVERSED</span></div><div class="tm-lg">{mark("favicon", 32)}{mark("favicon", 16)}<span>FAVICON 32, 16</span></div><div class="tm-lg">{mark("app", 64)}<span>APP ICON</span></div></div>')
    sws = "".join([swatch("GROUND", pal["ground"], "page"), swatch("SURFACE", pal["surface"], "panels"), swatch("AMBER", pal["primary"], "text, keys"), swatch("MUTE", pal["mute"], "labels"), swatch("CYAN", CY, "customer, links"), swatch("LINE", pal["line"], "rules"),
                   swatch(NAMES[0], COLS[0], "tier"), swatch(NAMES[1], COLS[1], "tier"), swatch(NAMES[2], COLS[2], "tier"), swatch("FOCUS", pal["focus"], "cursor")])
    contr = "".join(f'<tr><td>{a}</td><td class="r">{contrast(f, b):.1f}:1</td><td class="r">{"AA" if contrast(f, b) >= 4.5 else "LARGE ONLY"}</td></tr>' for a, f, b in
                    [("AMBER ON GROUND", pal["primary"], pal["ground"]), ("MUTE ON SURFACE", pal["mute"], pal["surface"]), ("CYAN ON GROUND", CY, pal["ground"]), (f"{NAMES[0]} ON SURFACE", COLS[0], pal["surface"]), (f"{NAMES[1]} ON SURFACE", COLS[1], pal["surface"]), (f"{NAMES[2]} ON SURFACE", COLS[2], pal["surface"]), ("BLACK ON AMBER", "#000000", pal["primary"])])
    tiers = "".join(f'<div class="tm-tr">{tchip(dict(tier_raw=r, score=s))}<p>{t}</p></div>' for r, s, t in
                    [("high", 87, "ACT NOW. LIKELY REFUSED AT THE DOOR. RESOLVE BEFORE A COURIER GOES."), ("medium", 42, "WATCH. SOME DOUBT. A QUICK CONFIRMATION HELPS."), ("low", 9, "CLEAR. LOOKS SAFE. SHIP NORMALLY.")])
    stat = "".join(f'<span class="tm-st">{s}</span>' for s in D["status"])
    icons = "".join(f'<div class="tm-icon">{code(c)}<span>{CODE_NAMES[c]}</span></div>' for c in CODES)
    voice = [("PAGE", "ORD  ORDERS TO CHECK"), ("EVIDENCE", "MSG  WHAT THE CUSTOMER SAID"), ("REASON", "RSN  WHY THIS SCORE"), ("PRIMARY ACTION", "1 ASK ADDRESS"), ("EMPTY", "NO ORDERS TO REVIEW. ADD ONE: F3."),
             ("ERROR", "COULD NOT LOAD. CHECK THAT THE WASEL SERVER IS RUNNING. REFRESH."), ("ARABIC", "الطلبات التي تحتاج مراجعة"), ("TIER HELP", "ACT: LIKELY REFUSED AT THE DOOR.")]
    vtab = "".join(f'<tr><td>{k}</td><td dir="auto">{v}</td></tr>' for k, v in voice)
    spec = (f'<div class="tm-type"><div class="tm-sp1">AA ARCHIVO NARROW</div><p class="tm-spp">ORDERS TO CHECK. LABELS, KEYS AND PANEL TITLES ARE SET CONDENSED, UPPERCASE.</p>'
            f'<div class="tm-sp2">0123456789 RED HAT MONO</div><p class="tm-spp tm-mono">12:36 SAMI  DOUAR OULED ALI, 9RIB EL JEMAA   87   +17   1,148 TND</p>'
            f'<div class="tm-sp3" lang="ar" dir="rtl">دوار أولاد علي، قريب من الجامع</div><p class="tm-spp">READEX PRO FOR ARABIC. FIGURES ARE MONOSPACED SO COLUMNS ALIGN.</p></div>')
    comps = (f'<div class="tm-comps"><span class="tm-key tm-keygo">ENTER GO</span><span class="tm-key tm-keyesc">ESC CANCEL</span><span class="tm-key">F1 ORD</span><span class="tm-cmdsample">ORD 2601 &lt;GO&gt;<i class="tm-cur"></i></span>'
             f'{tchip(OR[1])}{tchip(OR[4])}{tchip(OR[7])}<table class="tm-tab" style="width:420px"><tr class="sel"><td>2601</td><td>SAMI</td><td class="r">220</td><td>{tchip(OR[1])}</td></tr></table></div>')
    return (f'<div class="tm-brand"><section><p class="tm-pos"><b>TERMINAL DESK.</b> THE PRODUCT AS A TRADER’S TERMINAL: A COMMAND LINE, MNEMONIC PANELS, A KEY ROW. DENSITY IS NOT CRAMMING, IT IS VALUE PER SECOND. '
            f'IT BORROWS THE TERMINAL’S CONSISTENCY AND KEYBOARD, NOT ITS NOSTALGIA.</p></section>'
            f'<section>{L("LOGO SUITE")}{logos}<p class="tm-note">IDEA: AN AMBER BLOCK CARRYING THE COMMAND WSL, WITH THE CURSOR GAP CUT AS A DOOR ARCH.</p></section>'
            f'<section>{L("COLOUR")}<div class="tm-sws">{sws}</div><table class="tm-tab">{contr}</table></section>'
            f'<section>{L("TYPE")}{spec}</section>'
            f'<section>{L("TIER VOCABULARY")}<div class="tm-trs">{tiers}</div>{L("STATUS VOCABULARY")}<div class="tm-sts">{stat}</div></section>'
            f'<section>{L("MNEMONICS")}<div class="tm-icons">{icons}</div></section>'
            f'<section>{L("VOICE")}<table class="tm-tab">{vtab}</table></section><section>{L("COMPONENTS")}{comps}</section></div>')

# ------------------------------------------------------------------ desktop screens
def app(inner, cmd="ORD", sub="", help_=None, active="ORD"):
    h = helpline(help_) if help_ else ""
    return f'<div class="tm-app">{cmdbar(cmd, sub)}{h}<div class="tm-main">{inner}</div>{fbar(active)}</div>'

def D1():
    g = (panel("ORD", "ORDERS TO CHECK", blotter(), "tm-a") + panel("RSN", "WHY THIS SCORE · #2601 SAMI", reasons() + actions(), "tm-b") + panel("MSG", "WHAT THE CUSTOMER SAID", tape(), "tm-c") + panel("MON", "DESK", mon_desk(), "tm-d"))
    return app(f'<div class="tm-grid1">{g}</div>', "ORD 2601", "SAMI · CASQUE BLUETOOTH · 220 TND · RURAL", CONTENT["pages"]["orders"]["subtitle"], "ORD")

def D2():
    head = (f'<table class="tm-tab tm-kv tm-hd"><tr><td>CUSTOMER</td><td>{bdi(H["customer"])}</td><td>ITEM</td><td>{esc(H["product"]).upper()}</td><td>PRICE</td><td>220 TND</td><td>ZONE</td><td>RURAL</td><td>SCORE</td><td>{tchip(OR[1])}</td></tr></table>')
    draft = (f'<div class="tm-tag">ARABIZI · STANDARD MESSAGE</div><p class="tm-dr" dir="auto">{esc(H["draft"]["text"])}</p><div class="tm-act"><span><i>F1</i>SEND THE QUESTION</span><span><i>F2</i>EDIT</span></div>')
    hist = ('<table class="tm-tab"><tr><th>V</th><th>WHEN</th><th>RISK</th><th>NOTE</th></tr><tr><td>1</td><td>FIRST SCORE</td><td>' + tchip(OR[1]) + '</td><td>3 WARNING SIGNS, RURAL, VAGUE ADDRESS</td></tr>'
            f'<tr class="sel"><td>2</td><td>AFTER REPLY</td><td><span class="tm-t tm-t2">{glyph(2)}{NAMES[2]} <b>16</b></span></td><td>FULL ADDRESS GIVEN −32</td></tr></table>')
    g = panel("MSG", "WHAT THE CUSTOMER SAID", f'<p class="tm-hint">{esc(CONTENT["pages"]["order"]["hints"][0]).upper()}</p>{tape()}', "tm-m1") + panel("SND", "MESSAGE TO THE CUSTOMER", draft, "tm-m2") + panel("RSN", "WHY THIS SCORE", reasons() + actions(), "tm-m3") + panel("HST", "SCORE HISTORY", hist, "tm-m4")
    return app(head + f'<div class="tm-grid2">{g}</div>', "ORD 2601 DETAIL", "WAITING FOR CUSTOMER", CONTENT["pages"]["order"]["verdict_line"], "ORD")

def D3():
    rows = "".join(f'<tr class="{"sel" if o["ref"] == SELECTED else ""}"><td>{o["ref"][1:]}</td><td>{bdi(o["customer"])}</td><td dir="auto" class="tm-pv">{esc(o["preview"] or "")}</td><td>{tchip(o, False)}</td><td class="r">{hms(waiting(o))}</td></tr>' for o in OR)
    conv = f'<table class="tm-tab"><tr><th>ID</th><th>CUSTOMER</th><th>LAST MESSAGE</th><th>RISK</th><th class="r">AGE</th></tr>{rows}</table>'
    thread = f'<div class="tm-warn">WA OFF (DEMO MODE): REPLIES ARE RECORDED, NOT SENT.</div>{tape()}<div class="tm-in2">REPLY TO SAMI_<i class="tm-cur"></i></div>'
    g = panel("MSG", "WHATSAPP MESSAGES · 9 CONVERSATIONS", conv, "tm-v1") + panel("THR", "SAMI #2601", thread, "tm-v2") + panel("RSN", "WHY", reasons() + actions(), "tm-v3")
    return app(f'<div class="tm-grid3">{g}</div>', "MSG", "9 CONVERSATIONS · 0 NEED DECISION · 5 WAITING", CONTENT["pages"]["messages"]["subtitle"], "MSG")

def D4():
    ex = "".join(f'<tr><td class="tm-n">{i}</td><td>{esc(e).upper()}</td></tr>' for i, e in enumerate(CONTENT["pages"]["add"]["examples"], 1))
    form = ('<p class="tm-lab">CUSTOMER MESSAGE</p><div class="tm-ta" dir="auto">Douar Ouled Ali, 9rib el jemaa. ama ghali chwaya, mouch dima fi dar<i class="tm-cur"></i></div><p class="tm-lab tm-r">0 / 2,000</p>'
            '<table class="tm-tab tm-kv"><tr><td>CUSTOMER NAME</td><td>SAMI</td></tr><tr><td>PRODUCT</td><td>CASQUE BLUETOOTH</td></tr><tr><td>PRICE (TND)</td><td>220</td></tr><tr><td>DELIVERY ZONE</td><td>RURAL</td></tr></table>'
            '<div class="tm-act"><span><i>F1</i>SCORE THIS ORDER</span><span><i>ESC</i>CLEAR</span></div>')
    side = (f'<p class="tm-hint">PICK AN EXAMPLE</p><table class="tm-tab">{ex}</table><p class="tm-hint tm-mt">WHAT WILL BE CHECKED</p><ol class="tm-ol"><li>READ: ADDRESS, ZONE AND WARNING SIGNS IN THE CUSTOMER’S OWN WORDS.</li>'
            f'<li>SCORE: A MODEL AND FIXED RULES, 0 TO 100. THE AI NEVER PICKS THE NUMBER.</li><li>ASK: ONE QUESTION THAT WOULD REDUCE THE RISK. YOU SEND IT.</li></ol>')
    return app(f'<div class="tm-grid4">{panel("ADD", "ADD AN ORDER", form, "tm-f1")}{panel("HLP", "EXAMPLES AND CHECKS", side, "tm-f2")}</div>', "ADD", "PASTE A MESSAGE EXACTLY AS WRITTEN", CONTENT["pages"]["add"]["subtitle"], "ADD")

def D5():
    I = DATA["impact"]
    res = (f'<table class="tm-tab tm-kv"><tr><td>ESTIMATED WASTED-TRIP COST AVOIDED</td><td class="r tm-big">{I["tnd_saved"]:.0f} TND</td></tr><tr><td>STATUS</td><td class="r tm-w">SIMULATED</td></tr>'
           f'<tr><td>REFUSED DELIVERIES AVOIDED</td><td class="r">{I["trips_avoided"]:.0f} OF {I["n_orders"]:,}</td></tr><tr><td>REFUSED AT THE DOOR TODAY</td><td class="r">{I["baseline"] * 100:.0f}%</td></tr>'
           f'<tr><td>REFUSED WITH WASEL</td><td class="r tm-g">{I["projected"] * 100:.0f}%</td></tr><tr><td>CHANGE</td><td class="r tm-g">−{(I["baseline"] - I["projected"]) * 100:.1f} PTS</td></tr></table>')
    ass = "".join(f'<tr><td>{esc(a).upper()}</td><td class="r">{esc(b)}</td></tr>' for a, b in I["assumptions_plain"])
    log = '<table class="tm-tab"><tr><th>TIME</th><th>EVENT</th><th>CUSTOMER</th><th>ID</th></tr>' + "".join(f'<tr><td>{e["ts"]}</td><td>{esc(e["title"]).upper()}{(" " + e["detail"]) if e.get("detail") else ""}</td><td>{bdi(e["who"])}</td><td>{e["ref"][1:]}</td></tr>' for e in DATA["activity"][:11]) + '</table>'
    counts = ('<table class="tm-tab tm-kv"><tr><td>MESSAGES RECEIVED</td><td class="r">9</td></tr><tr><td>ORDERS SCORED</td><td class="r">9</td></tr><tr><td>REPLIES DRAFTED</td><td class="r">5</td></tr><tr><td>TRICKS BLOCKED</td><td class="r">0</td></tr></table>')
    g = panel("RES", "MONEY SAVED", res, "tm-r1") + panel("ASM", "HOW THIS WAS ESTIMATED", f'<table class="tm-tab">{ass}</table>', "tm-r2") + panel("LOG", "ACTIVITY LOG", counts + log, "tm-r3")
    return app(f'<div class="tm-grid5">{g}</div>', "RES", "SIMULATION ON SYNTHETIC ORDERS, NOT REAL SALES", CONTENT["pages"]["impact"]["subtitle"], "RES")

def D6():
    mon = DATA["monitor"]; q = DATA["quality"]
    drift = '<table class="tm-tab"><tr><th>FEATURE</th><th>STATE</th><th class="r">PSI</th></tr>' + "".join(f'<tr><td>{esc(d["name"]).upper()}</td><td class="tm-g">AS EXPECTED</td><td class="r">{d["psi"]:.2f}</td></tr>' for d in mon["drift"]) + '</table>'
    safe = '<table class="tm-tab"><tr><th>CHECK</th><th class="r">RATE</th></tr>' + "".join(f'<tr><td>{esc(n).upper()}</td><td class="r">{v * 100:.0f}%</td></tr>' for n, v in mon["safety"]) + '</table>'
    qrows = "".join(f'<tr><td>{esc(s["suite"]).upper()}</td><td class="r">{s["n"]}</td>' + "".join(f'<td class="r tm-g">{v * 100:.1f}</td>' for _, v in s["metrics"]) + '</tr>' for s in q)
    qt = f'<table class="tm-tab"><tr><th>SUITE</th><th class="r">CASES</th><th class="r">A</th><th class="r">B</th><th class="r">C</th></tr>{qrows}</table><p class="tm-hint">A, B, C ARE THE THREE HEADLINE CHECKS OF EACH SUITE. ALL RELEASE CHECKS PASSED.</p>'
    fl = DATA["failures"]
    ft = f'<table class="tm-tab tm-kv"><tr><td>TEST CONVERSATIONS CHECKED</td><td class="r">{fl["sessions"]}</td></tr><tr><td>FINDINGS</td><td class="r">{fl["findings"]}</td></tr><tr><td>SOURCE</td><td class="r tm-w">SYNTHETIC, NOT REAL</td></tr></table>'
    ai = '<table class="tm-tab tm-kv"><tr><td>AI CALLS</td><td class="r">0</td></tr><tr><td>TYPICAL ANSWER TIME</td><td class="r">–</td></tr><tr><td>BACKUP MODEL USED</td><td class="r">0</td></tr></table><p class="tm-hint">NO AI CALLS YET. OFFLINE MODE.</p>'
    g = panel("MON", "LIVE MONITOR · ARE CUSTOMERS WRITING DIFFERENTLY?", drift, "tm-h1") + panel("MON", "IS THE AI BEHAVING?", safe, "tm-h2") + panel("QLT", "QUALITY CHECKS", qt, "tm-h3") + panel("FAIL", "SILENT FAILURES", ft, "tm-h4") + panel("AIC", "AI CALL LOG", ai, "tm-h5")
    return app(f'<div class="tm-ok">RELEASE CHECKS: ALL CHECKS PASSED · EVERYTHING LOOKS NORMAL</div><div class="tm-grid6">{g}</div>', "MON", "ALL CLEAR", "Quality checks, live monitor, silent failures and the AI call log in one place.", "MON")

def D7():
    t = lambda c, title, body: panel(c, title, body, "tm-sx")
    empty = '<p class="tm-big2">NO ORDERS TO REVIEW</p><p class="tm-hint">ADD ONE WITH F3, OR WAIT FOR THE NEXT WHATSAPP MESSAGE.</p><div class="tm-act"><span><i>F3</i>ADD AN ORDER</span></div>'
    load = '<p class="tm-load">SCORING <i>████████░░░░░░░░</i> 50%</p><table class="tm-tab"><tr class="tm-skel"><td>…</td><td>…</td><td>…</td></tr><tr class="tm-skel"><td>…</td><td>…</td><td>…</td></tr></table>'
    err = f'<div class="tm-err">{esc(CONTENT["states"]["error"]).upper()}</div><div class="tm-act"><span><i>F1</i>RETRY</span></div>'
    off = f'<div class="tm-off">{esc(CONTENT["states"]["offline"]).upper()}</div><table class="tm-tab"><tr class="sel"><td>2601</td><td>SAMI</td><td>{tchip(OR[1])}</td><td>LAST DATA 14:28</td></tr></table>'
    g = t("ORD", "EMPTY", empty) + t("SCR", "LOADING", load) + t("ERR", "ERROR", err) + t("NET", "OFFLINE", off)
    return app(f'<div class="tm-grid7">{g}</div>', "ORD", "SYSTEM STATES", "How each state looks in the terminal.", "ORD")

def desktop():
    return [("D1 Orders to check", D1()), ("D2 Order detail with messages", D2()), ("D3 WhatsApp messages", D3()), ("D4 Add an order", D4()), ("D5 Metrics: money saved and activity", D5()), ("D6 AI health", D6()), ("D7 System states", D7())]

# ------------------------------------------------------------------ phone screens
def pbar(title, code_="ORD"):
    return f'<div class="tm-sb"><span>14:32</span><span>5G ▮▮▮</span></div><div class="tm-pbar"><span class="tm-plogo">{mark("favicon", 28)}</span><b>{code(code_, True)} {esc(title)}</b></div>'

def pkeys(active="ORD"):
    ks = [("ORD", "ORD"), ("MSG", "MSG"), ("ADD", "ADD"), ("RES", "RES"), ("MORE", "MORE")]
    return '<nav class="tm-keys">' + "".join(f'<a class="{"on" if n == active else ""}">{n}</a>' for n, _ in ks) + "</nav>"

def pcmd(text="ORD 2601 <GO>"):
    return f'<div class="tm-pcmd"><span>&gt;</span>{esc(text)}<i class="tm-cur"></i></div>'

def M1():
    rows = "".join(f'<div class="tm-pr"><div><b>{o["ref"][1:]} {bdi(o["customer"])}</b><span>{esc(o["product"]).upper()} · {o["price_tnd"]:.0f} TND · {nextstep(o)}</span></div><div class="tm-pr-r">{tchip(o)}<em>{status(o)} {hms(waiting(o))}</em></div></div>' for o in OR)
    cnt = f'<div class="tm-pf"><a><i>{NAMES[0]}</i> 4</a><a><i>{NAMES[1]}</i> 1</a><a><i>{NAMES[2]}</i> 4</a></div>'
    return f'<div class="tm-ph">{pbar("ORDERS TO CHECK")}{cnt}<div class="tm-pl">{rows}</div>{pcmd("ORD")}{pkeys("ORD")}</div>'

def M2():
    ev = (f'<div class="tm-card"><h4>WHAT THE CUSTOMER SAID</h4>{tape(True)}</div><div class="tm-card"><h4>ADDRESS CHECK</h4><table class="tm-tab tm-kv"><tr><td>STREET</td><td class="r">NOT GIVEN</td></tr><tr><td>LANDMARK</td><td class="r">“9RIB EL JEMAA”</td></tr><tr><td>ZONE</td><td class="r">RURAL</td></tr></table></div>'
          f'<div class="tm-card"><h4>WHY THIS SCORE</h4>{reasons()}</div>')
    return (f'<div class="tm-ph">{pbar("2601 SAMI", "ORD")}<div class="tm-ps"><div class="tm-ph1">{tchip(OR[1])}<span>CASQUE BLUETOOTH · 220 TND · RURAL</span></div>{ev}</div>'
            f'<div class="tm-pact"><a class="tm-k1"><i>1</i>ASK ADDRESS</a><div class="tm-row2"><a><i>2</i>APPROVE</a><a class="tm-kc"><i>3</i>CANCEL</a></div></div>{pkeys("ORD")}</div>')

def M3():
    d = f'<div class="tm-card"><h4>WASEL DRAFT · ARABIZI</h4><p class="tm-dr" dir="auto">{esc(H["draft"]["text"])}</p><a class="tm-k1 tm-kw"><i>F1</i>SEND THE QUESTION</a></div>'
    return f'<div class="tm-ph">{pbar("SAMI", "MSG")}<div class="tm-ps">{tape(True)}{d}</div>{pcmd("REPLY TO SAMI")}{pkeys("MSG")}</div>'

def M4():
    ex = "".join(f'<div class="tm-ex"><i>{n}</i>{esc(e).upper()}</div>' for n, e in enumerate(CONTENT["pages"]["add"]["examples"], 1))
    return (f'<div class="tm-ph">{pbar("ADD AN ORDER", "ADD")}<div class="tm-ps"><p class="tm-hint">{esc(CONTENT["pages"]["add"]["subtitle"]).upper()}</p>{ex}<p class="tm-lab">CUSTOMER MESSAGE</p>'
            f'<div class="tm-ta" dir="auto">Douar Ouled Ali, 9rib el jemaa. ama ghali chwaya<i class="tm-cur"></i></div><p class="tm-hint">ORDER DETAILS (OPTIONAL) ▸</p></div>'
            f'<div class="tm-pact"><a class="tm-k1"><i>F1</i>SCORE THIS ORDER</a></div>{pkeys("ADD")}</div>')

def M5():
    I = DATA["impact"]
    return (f'<div class="tm-ph">{pbar("MONEY SAVED", "RES")}<div class="tm-ps"><div class="tm-card"><h4>ESTIMATED WASTED-TRIP COST AVOIDED</h4><p class="tm-bigp">{I["tnd_saved"]:.0f} <small>TND</small></p><p class="tm-w">SIMULATED</p></div>'
            f'<div class="tm-card"><table class="tm-tab tm-kv"><tr><td>REFUSED AT THE DOOR TODAY</td><td class="r">{I["baseline"] * 100:.0f}%</td></tr><tr><td>REFUSED WITH WASEL</td><td class="r tm-g">{I["projected"] * 100:.0f}%</td></tr><tr><td>DELIVERIES AVOIDED</td><td class="r">{I["trips_avoided"]:.0f}</td></tr></table></div>'
            f'<div class="tm-card"><h4>TODAY</h4><table class="tm-tab">' + "".join(f'<tr><td>{e["ts"]}</td><td>{esc(e["title"]).upper()} {bdi(e["who"])}</td></tr>' for e in DATA["activity"][:4]) + f'</table></div></div>{pkeys("RES")}</div>')

def M6():
    more = [("LOG", "ACTIVITY LOG"), ("QLT", "QUALITY CHECKS"), ("FAIL", "SILENT FAILURES"), ("MON", "LIVE MONITOR"), ("AIC", "AI CALL LOG")]
    rows = "".join(f'<div class="tm-more">{code(c)}<b>{n}</b><span>›</span></div>' for c, n in more)
    return f'<div class="tm-ph">{pbar("MORE", "ORD")}<div class="tm-ps">{rows}<p class="tm-hint tm-mt">AI SCORING LIVE · WA OFF (DEMO) · SYNTHETIC DATA</p></div>{pkeys("MORE")}</div>'

def phone():
    return [("M1 Orders list", M1()), ("M2 Case with action keys", M2()), ("M3 Messages thread", M3()), ("M4 Add an order", M4()), ("M5 Metrics glance", M5()), ("M6 More", M6())]

def notes():
    return ('<div class="tm-notes"><h3>HOW THIS MAPS TO THE REAL PROJECT</h3><ul>'
            '<li><b>Same pages, same data.</b> Orders to check, WhatsApp messages, Add an order, Money saved, Activity log and the AI-health pages each become one or more mnemonic panels with their real copy.</li>'
            '<li><b>What changes.</b> A command line replaces menu navigation; the order table, reasons and conversation share one screen; the sidebar becomes a function-key row.</li>'
            '<li><b>Codebase impact.</b> A panel grid with a global command parser (ORD, MSG, ADD, RES…), keyboard-first actions (1, 2, 3, F-keys), monospaced tables. The API is unchanged.</li>'
            '<li><b>Honest cost.</b> It rewards daily users and punishes first-timers: every code must be learned or discoverable (the key row does that). Amber on black is tiring in bright rooms, and the phone version must drop most of the density.</li></ul></div>')

# ------------------------------------------------------------------ stylesheet
CSS = f"""
:root{{--tm-g:{pal['ground']};--tm-s:{pal['surface']};--tm-a:{pal['primary']};--tm-m:{pal['mute']};--tm-c:{CY};--tm-l:{pal['line']};--tm-f:{pal['focus']};--tm-t0:{COLS[0]};--tm-t1:{COLS[1]};--tm-t2:{COLS[2]}}}
body.tm{{background:#000;color:var(--tm-a);font:13px/1.4 var(--data)}}
.tm-top{{background:#000;border-bottom:1px solid var(--tm-l);font-family:var(--ui);text-transform:uppercase;letter-spacing:.04em}}.tm-top span{{color:var(--tm-m)}}.tm-top nav a{{color:var(--tm-a);padding:4px 10px;text-decoration:none;font-weight:700}}
.bb-sec>h2{{font:700 20px var(--ui);text-transform:uppercase;letter-spacing:.06em;color:var(--tm-a)}}.tm-lock{{display:inline-flex;align-items:center;gap:12px}}.tm-wm{{display:inline-flex;align-items:baseline;gap:10px;font-family:var(--ui)}}.tm-wm b{{font-weight:700;letter-spacing:.08em}}.tm-wm-ar{{font:600 1.1em var(--ar)}}
.tm-app{{width:1280px;height:800px;background:#000;color:var(--tm-a);display:flex;flex-direction:column;font:12.5px/1.4 var(--data)}}.tm-app *{{box-sizing:border-box}}
.tm-cmd{{display:flex;align-items:center;gap:14px;height:42px;padding:0 12px;background:var(--tm-s);border-bottom:1px solid var(--tm-l);flex:none}}.tm-prompt{{font:700 14px var(--ui);background:var(--tm-a);color:#000;padding:2px 10px;letter-spacing:.08em}}
.tm-in{{border:1px solid var(--tm-a);padding:4px 12px;color:#fff;min-width:210px}}.tm-in u{{text-decoration:none;color:var(--tm-t2)}}.tm-cur{{display:inline-block;width:8px;height:14px;background:var(--tm-f);margin-left:3px;vertical-align:-2px}}.tm-sub{{color:var(--tm-m);font:13px var(--ui);letter-spacing:.05em;text-transform:uppercase}}
.tm-r{{margin-left:auto;display:flex;gap:18px;color:var(--tm-m);font:12px var(--ui);letter-spacing:.06em}}.tm-syn{{color:var(--tm-c)}}
.tm-help{{padding:4px 12px;background:#000;border-bottom:1px solid var(--tm-l);color:var(--tm-m);font:12px var(--data);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:none}}.tm-help b{{background:var(--tm-m);color:#000;padding:0 6px;margin-right:8px;font-family:var(--ui)}}
.tm-main{{flex:1;min-height:0;padding:2px;background:var(--tm-l);display:flex;flex-direction:column;gap:2px}}
.tm-p{{background:#000;padding:6px 10px 8px;overflow:hidden;min-width:0;display:flex;flex-direction:column}}.tm-p h3{{margin:0 0 6px;font:700 12.5px var(--ui);letter-spacing:.08em;color:#FFD470;border-bottom:1px solid var(--tm-l);padding-bottom:4px}}.tm-p h3 em{{font-style:normal;background:var(--tm-a);color:#000;padding:0 7px;margin-right:9px}}.tm-pb{{min-height:0;overflow:hidden}}
.tm-grid1{{flex:1;display:grid;grid-template-columns:1.7fr 1fr;grid-template-rows:1.3fr 1fr .85fr;gap:2px;background:var(--tm-l);min-height:0}}.tm-a{{grid-row:1/4}}.tm-b{{grid-column:2}}.tm-c{{grid-column:2}}.tm-d{{grid-column:2}}
.tm-grid2{{flex:1;display:grid;grid-template-columns:1.3fr 1fr;grid-template-rows:1.25fr 1fr;gap:2px;background:var(--tm-l);min-height:0}}.tm-hd{{margin:0 0 2px}}.tm-hd td:first-child{{padding-left:10px}}
.tm-grid3{{flex:1;display:grid;grid-template-columns:1.4fr 1fr .7fr;gap:2px;background:var(--tm-l);min-height:0}}.tm-grid4{{flex:1;display:grid;grid-template-columns:1.2fr 1fr;gap:2px;background:var(--tm-l);min-height:0}}
.tm-grid5{{flex:1;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:2px;background:var(--tm-l);min-height:0}}.tm-r3{{grid-row:1/3;grid-column:2}}
.tm-grid6{{flex:1;display:grid;grid-template-columns:1fr 1fr 1.35fr;grid-template-rows:1fr 1fr;gap:2px;background:var(--tm-l);min-height:0}}.tm-h3 .tm-tab td:first-child{{max-width:150px}}.tm-h3{{grid-row:1/3;grid-column:3}}.tm-grid7{{flex:1;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:2px;background:var(--tm-l);min-height:0}}
.tm-tab{{width:100%;border-collapse:collapse}}.tm-tab th{{text-align:left;color:var(--tm-m);font:600 11.5px var(--ui);letter-spacing:.08em;padding:3px 8px 3px 0;border-bottom:1px solid var(--tm-l);white-space:nowrap}}.tm-tab td{{padding:4px 8px 4px 0;color:var(--tm-a);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:260px}}.tm-tab .r{{text-align:right;padding-right:0}}.tm-tab .r+th,.tm-tab .r+td{{padding-left:16px}}.tm-tab tr.sel td{{background:#1D1500;color:#fff}}.tm-tab .tm-kv td:first-child{{color:var(--tm-m)}}
.tm-kv td:first-child{{color:var(--tm-m)}}.tm-tot td{{border-top:1px solid var(--tm-l);color:#fff;font-weight:700}}.tm-up{{color:var(--tm-t0)}}.tm-g{{color:var(--tm-t2)}}.tm-w{{color:#FFD470}}.tm-s{{color:var(--tm-c)}}.tm-big{{font:700 22px var(--ui);color:#fff}}.tm-pv{{color:var(--tm-m);max-width:250px}}
.tm-t{{display:inline-flex;align-items:center;gap:5px;font:700 12px var(--ui);letter-spacing:.06em}}.tm-t b{{font-family:var(--data);font-weight:700}}.tm-t0{{color:var(--tm-t0)}}.tm-t1{{color:var(--tm-t1)}}.tm-t2{{color:var(--tm-t2)}}.tm-gl{{flex:none}}
.tm-tape p{{margin:0 0 3px;color:#E8D9B0}}.tm-tape time{{color:var(--tm-m);margin-right:10px}}.tm-tape b{{color:var(--tm-c);margin-right:8px;font-weight:600}}.tm-tape .tm-sl b{{color:var(--tm-a)}}.tm-tape .tm-cl{{color:var(--tm-c)}}mark.tm-hl{{background:var(--tm-a);color:#000;padding:0 2px}}
.tm-act{{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}}.tm-act span{{background:#141414;border:1px solid #555;color:#fff;padding:3px 10px;font:600 12px var(--ui);letter-spacing:.05em}}.tm-act i{{font-style:normal;background:var(--tm-a);color:#000;padding:0 5px;margin-right:7px}}.tm-act .tm-cx i{{background:var(--tm-t0);color:#000}}
.tm-fb{{display:flex;gap:2px;padding:2px;background:#111;flex:none}}.tm-fk{{background:#1A1A1A;color:#fff;font:600 12px var(--ui);letter-spacing:.06em;padding:4px 12px}}.tm-fk i{{font-style:normal;background:var(--tm-a);color:#000;padding:0 5px;margin-right:6px}}.tm-fk.on{{background:var(--tm-a);color:#000}}.tm-fk.on i{{background:#000;color:var(--tm-a)}}.tm-esc,.tm-go{{font:700 12px var(--ui);letter-spacing:.06em;padding:4px 12px;color:#000}}.tm-esc{{margin-left:auto;background:var(--tm-t0)}}.tm-go{{background:var(--tm-t2)}}
.tm-leg{{margin:10px 0 0;padding-top:8px;border-top:1px solid var(--tm-l);color:var(--tm-m);font:12px var(--data)}}.tm-leg svg{{vertical-align:-2px}}.tm-hint{{color:var(--tm-m);font:12px var(--data);margin:0 0 5px}}.tm-mt{{margin-top:12px}}.tm-hd td{{padding:6px 14px 6px 0}}.tm-hd{{background:#000;border-bottom:2px solid var(--tm-l)}}.tm-tag{{display:inline-block;background:var(--tm-c);color:#000;font:700 11.5px var(--ui);padding:0 8px;margin-bottom:6px;letter-spacing:.06em}}.tm-dr{{margin:0 0 6px;color:#fff;border:1px solid var(--tm-l);padding:8px 10px;line-height:1.55}}
.tm-warn,.tm-ok,.tm-err,.tm-off{{padding:5px 10px;font:700 12px var(--ui);letter-spacing:.06em}}.tm-warn{{background:var(--tm-a);color:#000;margin-bottom:6px}}.tm-ok{{background:#0C2A1A;color:var(--tm-t2);border:1px solid var(--tm-t2);margin:2px 0}}.tm-err{{background:var(--tm-t0);color:#000;margin-bottom:6px}}.tm-off{{background:var(--tm-a);color:#000;margin-bottom:6px}}.tm-in2{{margin-top:auto;border:1px solid var(--tm-a);padding:6px 10px;color:var(--tm-m)}}
.tm-lab{{font:600 11.5px var(--ui);letter-spacing:.08em;color:var(--tm-m);margin:6px 0 3px}}.tm-ta{{border:1px solid var(--tm-a);padding:9px 12px;min-height:120px;color:#fff;font-size:14px;line-height:1.6}}.tm-ol{{margin:0;padding-left:20px;color:#E8D9B0}}.tm-ol li{{margin-bottom:6px}}.tm-n{{width:24px;color:var(--tm-c)}}.tm-big2{{font:700 20px var(--ui);letter-spacing:.06em;color:#fff;margin:14px 0 4px}}.tm-load{{color:#fff}}.tm-load i{{font-style:normal;color:var(--tm-a);letter-spacing:-1px}}.tm-skel td{{color:var(--tm-m)}}
/* brand */
.tm-brand{{display:grid;grid-template-columns:repeat(2,minmax(480px,1fr));gap:2px;width:100%;max-width:1180px;background:var(--tm-l);border:2px solid var(--tm-l)}}.tm-brand>section{{background:#000;padding:16px}}.tm-brand>section:first-child{{grid-column:1/-1}}.tm-bh{{margin:0 0 10px;font:700 14px var(--ui);letter-spacing:.08em;color:#FFD470}}.tm-bh em{{font-style:normal;background:var(--tm-a);color:#000;padding:0 7px;margin-right:9px}}.tm-pos{{margin:0;max-width:90ch;font-size:14px;color:#E8D9B0}}.tm-note{{color:var(--tm-m);margin:10px 0 0;font-size:12px}}
.tm-logos{{display:grid;grid-template-columns:repeat(3,1fr);gap:2px;background:var(--tm-l)}}.tm-lg{{display:flex;flex-direction:column;gap:8px;align-items:center;justify-content:center;background:#050505;padding:14px;min-height:110px}}.tm-lg span{{font:600 11px var(--ui);color:var(--tm-m);letter-spacing:.08em}}.tm-inv{{background:var(--tm-a)}}.tm-inv span{{color:#000}}.tm-lg:nth-child(5){{flex-direction:row;flex-wrap:wrap}}
.tm-sws{{display:grid;grid-template-columns:repeat(5,1fr);gap:4px;margin-bottom:12px}}.tm-sw{{padding:9px 8px;min-height:80px;display:flex;flex-direction:column;justify-content:flex-end;font:12px var(--data);border:1px solid #333}}.tm-sw b{{font:700 12px var(--ui);letter-spacing:.06em}}.tm-sw em{{font-style:normal;opacity:.8}}
.tm-type{{display:flex;flex-direction:column;gap:6px}}.tm-sp1{{font:700 34px var(--ui);letter-spacing:.04em;color:#fff}}.tm-sp2{{font:600 22px var(--data);color:#fff}}.tm-sp3{{font:32px var(--ar);color:#fff}}.tm-spp{{margin:0;color:var(--tm-m);font-size:12px}}.tm-mono{{color:var(--tm-a)}}
.tm-trs{{display:flex;flex-direction:column;gap:8px;margin-bottom:12px}}.tm-tr{{display:flex;gap:14px;align-items:center}}.tm-tr .tm-t{{min-width:110px}}.tm-tr p{{margin:0;color:var(--tm-m);font-size:12px}}.tm-sts{{display:flex;flex-wrap:wrap;gap:6px}}.tm-st{{border:1px solid var(--tm-a);padding:2px 12px;font:700 12px var(--ui);letter-spacing:.08em}}
.tm-icons{{display:grid;grid-template-columns:repeat(6,1fr);gap:4px}}.tm-icon{{display:flex;flex-direction:column;align-items:center;gap:6px;border:1px solid var(--tm-l);padding:12px 4px;font:11px var(--ui);color:var(--tm-m)}}.tm-code{{display:inline-block;border:1px solid var(--tm-a);color:var(--tm-a);padding:1px 6px;font:700 12px var(--ui);letter-spacing:.08em}}.tm-code.on{{background:var(--tm-a);color:#000}}
.tm-comps{{display:flex;gap:10px;flex-wrap:wrap;align-items:center}}.tm-key{{background:#1A1A1A;color:#fff;font:700 12px var(--ui);padding:5px 12px;letter-spacing:.06em}}.tm-keygo{{background:var(--tm-t2);color:#000}}.tm-keyesc{{background:var(--tm-t0);color:#000}}.tm-cmdsample{{border:1px solid var(--tm-a);padding:4px 12px;color:#fff}}
.tm-notes{{max-width:900px;background:#050505;border:1px solid var(--tm-l);padding:6px 20px 14px;color:#E8D9B0;font:13px/1.5 var(--data)}}.tm-notes h3{{font:700 14px var(--ui);letter-spacing:.08em;color:#FFD470}}.tm-notes li{{margin:6px 0}}
/* phone */
.tm-ph{{width:390px;height:844px;background:#000;color:var(--tm-a);display:flex;flex-direction:column;font:13px/1.45 var(--data)}}.tm-ph *{{box-sizing:border-box}}.tm-sb{{display:flex;justify-content:space-between;padding:12px 24px 4px;font:700 13px var(--ui);background:var(--tm-s)}}.tm-pbar{{display:flex;align-items:center;gap:12px;padding:8px 14px;background:var(--tm-s);border-bottom:1px solid var(--tm-l)}}.tm-pbar b{{font:700 15px var(--ui);letter-spacing:.06em;color:#fff}}
.tm-pf{{display:flex;gap:2px;padding:2px;background:var(--tm-l)}}.tm-pf a{{flex:1;background:#000;padding:12px 4px;text-align:center;font:700 12px var(--ui);letter-spacing:.06em;color:#fff;min-height:44px;display:flex;align-items:center;justify-content:center;gap:6px}}.tm-pf i{{font-style:normal;color:var(--tm-m)}}
.tm-pl{{flex:1;overflow:hidden}}.tm-pr{{display:flex;justify-content:space-between;gap:8px;padding:10px 14px;border-bottom:1px solid var(--tm-l);min-height:60px}}.tm-pr b{{display:block;color:#fff}}.tm-pr span{{display:block;color:var(--tm-m);font-size:11.5px}}.tm-pr-r{{text-align:right}}.tm-pr-r em{{display:block;font-style:normal;color:var(--tm-c);font:11.5px var(--data);margin-top:3px}}
.tm-ps{{flex:1;overflow:hidden;padding:10px 12px;display:flex;flex-direction:column;gap:10px}}.tm-ph1{{display:flex;flex-direction:column;gap:4px}}.tm-ph1 span{{color:var(--tm-m)}}.tm-card{{border:1px solid var(--tm-l);padding:9px 11px}}.tm-card h4{{margin:0 0 6px;font:700 11.5px var(--ui);letter-spacing:.08em;color:#FFD470}}
.tm-pact{{padding:10px 12px;border-top:1px solid var(--tm-l);display:flex;flex-direction:column;gap:8px;background:var(--tm-s)}}.tm-pact a{{display:flex;align-items:center;justify-content:center;min-height:48px;font:700 14px var(--ui);letter-spacing:.06em;border:1px solid #666;color:#fff}}.tm-pact a i{{font-style:normal;background:var(--tm-a);color:#000;padding:0 6px;margin-right:8px}}.tm-k1{{background:var(--tm-a);color:#000!important;border-color:var(--tm-a)!important}}.tm-k1 i{{background:#000!important;color:var(--tm-a)!important}}.tm-kc{{color:var(--tm-t0)!important;border-color:var(--tm-t0)!important}}.tm-row2{{display:flex;gap:8px}}.tm-row2 a{{flex:1}}.tm-kw{{margin-top:8px}}
.tm-card .tm-k1{{display:flex;align-items:center;justify-content:center;min-height:48px;font:700 14px var(--ui);letter-spacing:.06em}}.tm-card .tm-k1 i{{font-style:normal;padding:0 6px;margin-right:8px}}.tm-pcmd{{margin:6px 12px;border:1px solid var(--tm-a);padding:12px 12px;color:var(--tm-m);min-height:46px}}.tm-pcmd span{{color:var(--tm-a);margin-right:8px}}.tm-keys{{display:flex;gap:2px;padding:2px 2px 22px;background:#111}}.tm-keys a{{flex:1;text-align:center;padding:14px 0;background:#1A1A1A;color:#fff;font:700 13px var(--ui);letter-spacing:.08em;min-height:48px}}.tm-keys a.on{{background:var(--tm-a);color:#000}}
.tm-ex{{border:1px solid var(--tm-l);padding:12px;color:#E8D9B0;min-height:46px;display:flex;align-items:center}}.tm-ex i{{font-style:normal;background:var(--tm-c);color:#000;padding:0 6px;margin-right:10px;font-weight:700}}.tm-bigp{{margin:0;font:700 48px var(--ui);color:#fff}}.tm-bigp small{{font-size:18px}}.tm-more{{display:flex;align-items:center;gap:14px;border:1px solid var(--tm-l);padding:14px 12px;min-height:54px}}.tm-more b{{flex:1;font:600 14px var(--ui);letter-spacing:.06em;color:#fff}}.tm-more span{{color:var(--tm-m)}}
"""
