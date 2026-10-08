"""Direction 04: Review Desk (fraud-review queue family). Pilot direction.
Own identity: Figtree + Spectral, Amiri for Arabic, navy on cool white, tiers Highest / Elevated / Normal.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from kit import *

PREFIX = "rd"
D = direction("04-review-queue")
pal, T = D["pal"], D["tiers"]
NAMES, COLS = T["names"], T["colors"]
TINTS = [tint(c, 0.90) for c in COLS]
STATUS = {"awaiting_reply": "Awaiting customer", "needs_review": "Needs decision", "ready_to_ship": "Cleared", "shipped": "Closed"}
NEXT = CONTENT["pages"]["orders"]["next_steps"]
H = hero()
OR = orders()
SELECTED = "#2601"

# ------------------------------------------------------------------ marks and glyphs
def glyph(i, size=14):
    c = COLS[i]
    if i == 0:
        return f'<svg class="rd-gl" width="{size}" height="{size}" viewBox="0 0 14 14" aria-hidden="true"><path d="M2 7.5 7 2.5l5 5M2 12 7 7l5 5" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    if i == 1:
        return f'<svg class="rd-gl" width="{size}" height="{size}" viewBox="0 0 14 14" aria-hidden="true"><path d="M2 9.5 7 4.5l5 5" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    return f'<svg class="rd-gl" width="{size}" height="{size}" viewBox="0 0 14 14" aria-hidden="true"><path d="M3 7h8" stroke="{c}" stroke-width="2" stroke-linecap="round"/></svg>'

def mark(variant="color", size=48):
    p, ink, white = pal["primary"], pal["ink"], "#FFFFFF"
    if variant == "favicon":
        return (f'<svg width="{size}" height="{size}" viewBox="0 0 32 32" aria-label="Wasel favicon"><rect width="32" height="32" rx="7" fill="{p}"/>'
                f'<circle cx="15" cy="15" r="8" fill="none" stroke="{white}" stroke-width="3"/><path d="M11.5 19v-4a3.5 3.5 0 0 1 7 0v4z" fill="{white}"/><path d="M21 21l5 5" stroke="{white}" stroke-width="3" stroke-linecap="round"/></svg>')
    if variant == "app":
        return (f'<svg width="{size}" height="{size}" viewBox="0 0 120 120" aria-label="Wasel app icon"><rect width="120" height="120" rx="27" fill="{p}"/>'
                f'<g transform="translate(14 16) scale(.8)">{_folder(white, p)}</g></svg>')
    fg, detail, bg = {"color": (p, white, None), "mono": (ink, white, None), "reversed": (white, p, p)}[variant]
    back = f'<rect width="120" height="120" rx="18" fill="{bg}"/>' if bg else ""
    return f'<svg width="{size}" height="{size}" viewBox="0 0 120 120" aria-label="Wasel mark">{back}<g transform="translate(6 12) scale(.9)">{_folder(fg, detail)}</g></svg>'

def _folder(fg, detail):
    return (f'<path d="M8 22a8 8 0 0 1 8-8h26l8 8h54a8 8 0 0 1 8 8v58a8 8 0 0 1-8 8H16a8 8 0 0 1-8-8z" fill="{fg}"/>'
            f'<circle cx="56" cy="60" r="26" fill="none" stroke="{detail}" stroke-width="7"/>'
            f'<path d="M46 74V58a10 10 0 0 1 20 0v16z" fill="{detail}"/><path d="M75 79l17 17" stroke="{detail}" stroke-width="8" stroke-linecap="round"/>')

def wordmark(variant="color", size=44, ar=True):
    col = {"color": pal["ink"], "mono": pal["ink"], "reversed": "#FFFFFF"}[variant]
    arc = {"color": pal["primary"], "mono": pal["ink"], "reversed": "#FFFFFF"}[variant]
    a = f'<span class="rd-wm-ar" lang="ar" style="color:{arc}">واصل</span>' if ar else ""
    return f'<span class="rd-wm" style="color:{col}"><b style="font-size:{size * .62:.0f}px">Wasel</b>{a}</span>'

def lockup(variant="color", size=44):
    return f'<span class="rd-lock">{mark(variant, size)}{wordmark(variant, size)}</span>'

# ------------------------------------------------------------------ icons (filled 20px, 2px outline when active)
ICONS = {
 "Orders": '<path d="M4 5h12v2H4zm0 4h12v2H4zm0 4h8v2H4z"/>',
 "Messages": '<path d="M3 4h14a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H8l-4 3v-3H3a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z"/>',
 "Add": '<path d="M9 4h2v5h5v2h-5v5H9v-5H4V9h5z"/>',
 "Results": '<path d="M4 16V9h3v7zm5 0V4h3v12zm5 0v-5h3v5z"/>',
 "Quality": '<path d="M10 2l7 3v5c0 4-3 7-7 8-4-1-7-4-7-8V5zm-1 11l5-5-1.4-1.4L9 10.2 7.4 8.6 6 10z"/>',
 "Monitor": '<path d="M10 3a8 8 0 0 0-8 8h2a6 6 0 0 1 12 0h2a8 8 0 0 0-8-8zm1 9.6V7h-2v5.6a1.8 1.8 0 1 0 2 0z"/>',
 "Log": '<path d="M5 3h10v14H5zm2 3v2h6V6zm0 4v2h6v-2zm0 4v2h4v-2z"/>',
 "Search": '<path d="M8.5 3a5.5 5.5 0 1 0 3.3 9.9l3.6 3.6 1.4-1.4-3.6-3.6A5.5 5.5 0 0 0 8.5 3zm0 2a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7z"/>',
 "Filter": '<path d="M3 4h14l-5.5 6.5V16l-3 1.5v-7z"/>',
 "Send": '<path d="M3 10 17 3l-3.5 14-3.2-4.6zm6.6 1.6L13 6.8z"/>',
 "Cancel": '<path d="M5.4 4 10 8.6 14.6 4 16 5.4 11.4 10 16 14.6 14.6 16 10 11.4 5.4 16 4 14.6 8.6 10 4 5.4z"/>',
 "Approve": '<path d="M4 10.5 8 14.5 16 5.5l1.4 1.4L8 17.3 2.6 11.9z"/>',
}
def icon(name, size=20, color="currentColor"):
    return f'<svg class="rd-ic" width="{size}" height="{size}" viewBox="0 0 20 20" fill="{color}" aria-hidden="true">{ICONS[name]}</svg>'

# ------------------------------------------------------------------ small parts
def chip(o, show_score=True):
    i = tier_index(o["tier_raw"])
    s = f' <b>{o["score"]}</b>' if show_score else ""
    return f'<span class="rd-chip rd-t{i}">{glyph(i)}{NAMES[i]}{s}</span>'

def facts(o):
    return f'{esc(o["product"])} · {o["price_tnd"]:.0f} TND'

def logo_lockup(size=32):
    return lockup("color", size)

def topbar(active="Orders to check"):
    items = [("Orders to check", "Orders"), ("WhatsApp messages", "Messages"), ("Add an order", "Add"), ("Money saved", "Results"), ("AI health", "Quality")]
    nav = "".join(f'<a class="{"on" if n == active else ""}">{icon(i, 18)}{n}</a>' for n, i in items)
    return (f'<header class="rd-bar">{logo_lockup(30)}<nav>{nav}</nav><div class="rd-bar-r"><span class="rd-live"><i></i>AI scoring live</span>'
            f'<span class="rd-syn">Synthetic data</span><span class="rd-search">{icon("Search", 16)}Search<kbd>/</kbd></span></div></header>')

def pagehead(title, sub, right=""):
    return f'<div class="rd-ph"><div><h1>{esc(title)}</h1><p>{esc(sub)}</p></div>{right}</div>'

def seg(counts, active=1):
    labels = ["Needs decision", "Awaiting customer", "Cleared"]
    return '<div class="rd-seg">' + "".join(f'<a class="{"on" if i == active else ""}">{l}<b>{c}</b></a>' for i, (l, c) in enumerate(zip(labels, counts))) + "</div>"

def queue(selected=SELECTED, compact=False):
    rows = ""
    for o in OR:
        i = tier_index(o["tier_raw"])
        rows += (f'<div class="rd-q {"on" if o["ref"] == selected else ""}"><div class="rd-q-main"><b>{bdi(o["customer"])}</b><span>{facts(o)}</span></div>'
                 f'<div class="rd-q-r">{chip(o)}<em>{age(waiting(o))}</em></div></div>')
    return (f'<aside class="rd-queue"><div class="rd-qh"><b>Open reviews</b><span>9 · 4 {NAMES[0].lower()}</span>{icon("Filter", 16)}</div>{rows}</aside>')

def reasons_block(small=False):
    rows = "".join(f'<div class="rd-r"><span>{esc(f["label"])}</span><i style="width:{f["points"] * 5}px"></i><b>+{f["points"]}</b></div>' for f in H["factors"])
    base = f'<div class="rd-r rd-r-b"><span>Base for a first order</span><i style="width:{H["base"] * 5 // 2}px;background:{pal["mute"]}"></i><b>{H["base"]}</b></div>'
    return f'<div class="rd-reasons"><h3>Why this score</h3>{base}{rows}<div class="rd-r rd-r-t"><span>Score</span><b>87</b></div></div>'

def evidence():
    m = H["messages"]
    words = [(m[1]["text"], "12:36"), (m[2]["text"], "12:47")]
    phr = [f["quote"] for f in H["flags"]]
    q = "".join(f'<p dir="auto"><time>{t}</time>{hl(tx, phr, "rd-hl")}</p>' for tx, t in words)
    return (f'<div class="rd-cards"><section class="rd-card"><h3>What the customer wrote</h3>{q}</section>'
            f'<section class="rd-card"><h3>Address check</h3><dl><dt>Street</dt><dd>Not given</dd><dt>Landmark</dt><dd dir="auto">“9rib el jemaa”</dd><dt>Zone</dt><dd>Rural</dd></dl></section>'
            f'<section class="rd-card"><h3>History</h3><dl><dt>Orders before</dt><dd>None</dd><dt>Delivered</dt><dd>–</dd><dt>Refused</dt><dd>–</dd></dl></section></div>')

def decisionbar(sticky=False):
    return (f'<div class="rd-decide {"rd-sticky" if sticky else ""}"><span><kbd>J</kbd><kbd>K</kbd> next, previous</span>'
            f'<a class="rd-btn rd-pri">{icon("Send", 16)}Send the question</a><a class="rd-btn">{icon("Approve", 16)}Approve for shipping</a><a class="rd-btn rd-danger">{icon("Cancel", 16)}Cancel order</a></div>')

def casehead(o_ref="#2601"):
    return (f'<div class="rd-ch"><div><h2>{bdi(H["customer"])} · {o_ref}</h2><p>{esc(H["product"])} · {H["price_tnd"]:.0f} TND · rural zone · new customer</p></div>'
            f'<span class="rd-chip rd-t0 rd-big">{glyph(0, 18)}{NAMES[0]} <b>87</b></span></div>'
            f'<p class="rd-verdict">{esc(CONTENT["pages"]["order"]["verdict_line"])}</p>')

def transcript(phone=False):
    phr = [f["quote"] for f in H["flags"]]
    out = ""
    ts = ["12:09", "12:36", "12:47"]
    for m, t in zip(H["messages"], ts):
        out += f'<div class="rd-msg rd-in" dir="auto"><p>{hl(m["text"], phr, "rd-hl")}</p><time>{t}</time></div>'
    return f'<div class="rd-thread">{out}</div>'

def draftcard():
    d = H["draft"]
    return (f'<section class="rd-card rd-draft"><h3>Message to the customer</h3><span class="rd-tag">Arabizi · standard message</span>'
            f'<p dir="auto" class="rd-dtext">{esc(d["text"])}</p><div class="rd-row"><a class="rd-btn">Edit</a><a class="rd-btn rd-pri">{icon("Send", 16)}Send the question</a></div></section>')

def history():
    return (f'<section class="rd-card"><h3>Score history</h3><div class="rd-hist"><div><b>1</b><span>First score</span><em class="rd-t0">{NAMES[0]} 87</em><p>3 warning signs, rural delivery zone, vague address</p></div>'
            f'<div class="rd-then"></div><div><b>2</b><span>After the reply</span><em class="rd-t2">{NAMES[2]} 16</em><p>full address given −32</p></div></div></section>')

# ------------------------------------------------------------------ brand sheet
def swatch(name, hexv, note=""):
    cr = contrast(hexv, "#FFFFFF"); tc = "#fff" if cr >= 4.5 else pal["ink"]
    return f'<div class="rd-sw" style="background:{hexv};color:{tc}"><b>{name}</b><span>{hexv}</span><em>{note}</em></div>'

def brand():
    L = lambda t: f'<h3 class="rd-bh">{t}</h3>'
    logos = (f'<div class="rd-logos"><div class="rd-lg">{lockup("color", 64)}<span>Lockup</span></div><div class="rd-lg">{mark("color", 64)}<span>Mark</span></div>'
             f'<div class="rd-lg">{mark("mono", 64)}<span>One colour</span></div><div class="rd-lg rd-inv">{mark("reversed", 64)}<span>Reversed</span></div>'
             f'<div class="rd-lg">{mark("favicon", 32)}{mark("favicon", 16)}<span>Favicon 32 and 16</span></div><div class="rd-lg">{mark("app", 64)}<span>App icon</span></div></div>')
    sws = "".join([swatch("Ground", pal["ground"], "page"), swatch("Surface", pal["surface"], "cards"), swatch("Ink", pal["ink"], "text"), swatch("Mute", pal["mute"], "secondary text"),
                   swatch("Primary", pal["primary"], "actions"), swatch("Secondary", pal["secondary"], "links"), swatch("Line", pal["line"], "dividers"),
                   swatch(NAMES[0], COLS[0], "tier"), swatch(NAMES[1], COLS[1], "tier"), swatch(NAMES[2], COLS[2], "tier")])
    contr = "".join(f'<tr><td>{a}</td><td>{contrast(f, b):.1f}:1</td><td>{"AA" if contrast(f, b) >= 4.5 else "large only"}</td></tr>' for a, f, b in
                    [("Ink on surface", pal["ink"], pal["surface"]), ("Mute on surface", pal["mute"], pal["surface"]), ("White on primary", "#FFFFFF", pal["primary"]),
                     (f"{NAMES[0]} on its tint", COLS[0], TINTS[0]), (f"{NAMES[1]} on its tint", COLS[1], TINTS[1]), (f"{NAMES[2]} on its tint", COLS[2], TINTS[2])])
    tiers = "".join(f'<div class="rd-tr"><span class="rd-chip rd-t{i}">{glyph(i)}{NAMES[i]} <b>{s}</b></span><p>{t}</p></div>' for i, (s, t) in enumerate(
        [(87, "Likely to be refused at the door. Resolve before a courier is sent."), (42, "Some doubt. A quick confirmation helps."), (9, "Looks safe. Ship normally.")]))
    stat = "".join(f'<span class="rd-st">{s}</span>' for s in ["Open", "Awaiting customer", "Needs decision", "Cleared", "Closed"])
    icons = "".join(f'<div class="rd-icon">{icon(n, 24)}<span>{n}</span></div>' for n in ICONS)
    voice = [("Page title", "Orders to check"), ("Evidence", "What the customer wrote"), ("Reason", "Why this score"), ("Primary action", "Send the question"), ("Empty", "No orders to review. Paste a message to start."),
             ("Error", "Could not load this. Check that the Wasel server is running, then refresh."), ("Arabic", "الطلبات التي تحتاج مراجعة"), ("Tier help", "Highest: likely refused at the door.")]
    vtab = "".join(f'<tr><td>{k}</td><td dir="auto">{v}</td></tr>' for k, v in voice)
    specimen = (f'<div class="rd-type"><div class="rd-sp1">Aa Figtree</div><p class="rd-sp-ui">Orders to check. Wasel reads what each customer wrote and scores how likely the order is to be refused at the door.</p>'
                f'<div class="rd-sp2">Aa Spectral</div><p class="rd-sp-data">“9rib el jemaa ama ghali chwaya.” Customer words and evidence are set in a book face.</p>'
                f'<div class="rd-sp3" lang="ar" dir="rtl">دوار أولاد علي، قريب من الجامع</div><p class="rd-sp-note">Amiri for Arabic text; tabular lining figures: 0123456789.</p></div>')
    comps = (f'<div class="rd-comps"><a class="rd-btn rd-pri">Send the question</a><a class="rd-btn">Approve for shipping</a><a class="rd-btn rd-danger">Cancel order</a>'
             f'<span class="rd-input">Search reviews</span>{chip(OR[1])}<div class="rd-q on" style="width:300px"><div class="rd-q-main"><b>Sami</b><span>casque bluetooth · 220 TND</span></div><div class="rd-q-r">{chip(OR[1])}<em>3 h 10</em></div></div></div>')
    return (f'<div class="rd-brand"><section><p class="rd-pos"><b>Review Desk.</b> The product as a fraud analyst’s desk: a queue of open reviews, a case with evidence, one clear decision. '
            f'It borrows the structure of payment-review tools and puts the customer’s own words at the centre.</p></section>'
            f'<section>{L("Logo suite")}{logos}<p class="rd-note">Idea: a case-file tab whose magnifier lens is a door. It says review, evidence and address in one mark.</p></section>'
            f'<section>{L("Colour")}<div class="rd-sws">{sws}</div><table class="rd-tab">{contr}</table></section>'
            f'<section>{L("Type")}{specimen}</section>'
            f'<section>{L("Tier vocabulary")}<div class="rd-trs">{tiers}</div>{L("Status vocabulary")}<div class="rd-sts">{stat}</div></section>'
            f'<section>{L("Icons")}<div class="rd-icons">{icons}</div></section>'
            f'<section>{L("Voice")}<table class="rd-tab">{vtab}</table></section><section>{L("Components")}{comps}</section></div>')

# ------------------------------------------------------------------ desktop screens
def D1():
    return (f'<div class="rd-app">{topbar()}<div class="rd-page">{pagehead("Orders to check", CONTENT["pages"]["orders"]["subtitle"], seg([0, 5, 4]))}'
            f'<div class="rd-split">{queue()}<main class="rd-case">{casehead()}{evidence()}{reasons_block()}{decisionbar()}</main></div></div></div>')

def D2():
    return (f'<div class="rd-app">{topbar()}<div class="rd-page"><a class="rd-back">← All orders</a>{casehead()}'
            f'<div class="rd-two"><div><section class="rd-card"><h3><span class="rd-n">1</span>What the customer said</h3><p class="rd-hint">{esc(CONTENT["pages"]["order"]["hints"][0])}</p>{transcript()}'
            f'<p class="rd-hint">How this message was checked ▸</p></section>{draftcard()}</div>'
            f'<div>{reasons_block()}{history()}{decisionbar()}</div></div></div></div>')

def D3():
    conv = ""
    for o in OR:
        conv += (f'<div class="rd-q {"on" if o["ref"] == SELECTED else ""}"><div class="rd-q-main"><b>{bdi(o["customer"])}</b><span dir="auto">{esc(o["preview"] or "")}</span></div><div class="rd-q-r">{chip(o, False)}<em>{age(waiting(o))}</em></div></div>')
    return (f'<div class="rd-app">{topbar("WhatsApp messages")}<div class="rd-page">{pagehead("WhatsApp messages", CONTENT["pages"]["messages"]["subtitle"], seg([0, 5, 4]))}'
            f'<div class="rd-split rd-split3"><aside class="rd-queue"><div class="rd-qh"><b>Conversations</b><span>9</span></div>{conv}</aside>'
            f'<main class="rd-case"><div class="rd-banner">WhatsApp is off in demo mode. Replies are recorded, not sent.</div><div class="rd-ch"><div><h2>{bdi(H["customer"])}</h2><p>#2601 · simulated channel</p></div>{chip(OR[1])}</div>'
            f'{transcript()}<section class="rd-card rd-draft"><h3>Wasel draft</h3><p dir="auto" class="rd-dtext">{esc(H["draft"]["text"])}</p><div class="rd-row"><a class="rd-btn rd-pri">{icon("Send", 16)}Send the question</a></div></section>'
            f'<div class="rd-composer">Reply to Sami<span>{icon("Send", 18)}</span></div></main>'
            f'<aside class="rd-side">{reasons_block()}</aside></div></div></div>')

def D4():
    ex = "".join(f'<span class="rd-pill">{e}</span>' for e in CONTENT["pages"]["add"]["examples"])
    return (f'<div class="rd-app">{topbar("Add an order")}<div class="rd-page">{pagehead("Add an order", CONTENT["pages"]["add"]["subtitle"])}'
            f'<div class="rd-two"><section class="rd-card"><h3>Customer message</h3><p class="rd-hint">Or try an example</p><div class="rd-pills">{ex}</div><label>What the customer wrote</label>'
            f'<div class="rd-ta" dir="auto">Douar Ouled Ali, 9rib el jemaa. ama ghali chwaya, mouch dima fi dar</div><div class="rd-count">0 / 2,000</div>'
            f'<h3 class="rd-mt">Order details (optional)</h3><div class="rd-form"><div><label>Customer name</label><span class="rd-input">Sami</span></div><div><label>Product</label><span class="rd-input">casque bluetooth</span></div>'
            f'<div><label>Price (TND)</label><span class="rd-input">220</span></div><div><label>Delivery zone</label><span class="rd-input">Rural ▾</span></div></div><a class="rd-btn rd-pri rd-wide">Score this order</a></section>'
            f'<section class="rd-card"><h3>What Wasel will check</h3><ol class="rd-steps"><li><b>Read.</b> Wasel finds the address, the zone and any warning signs in the customer’s own words.</li>'
            f'<li><b>Score.</b> A model and fixed rules give a score from 0 to 100. The AI never picks the number.</li><li><b>Ask.</b> Wasel drafts the one question that would reduce the risk. You send it.</li></ol>'
            f'<div class="rd-peek"><span class="rd-chip rd-t0">{glyph(0)}{NAMES[0]} <b>87</b></span><p>Example result: vague address, rural zone, price hesitation.</p></div></section></div></div></div>')

def D5():
    I = DATA["impact"]; ev = ""
    for e in DATA["activity"][:8]:
        ev += f'<div class="rd-ev"><time>{e["ts"]}</time><b>{esc(e["title"])} · {bdi(e["who"])}</b><span>{esc(e["ref"])}</span></div>'
    return (f'<div class="rd-app">{topbar("Money saved")}<div class="rd-page">{pagehead("Money saved", CONTENT["pages"]["impact"]["subtitle"])}'
            f'<div class="rd-grid4"><section class="rd-card rd-hero"><span class="rd-tag">Simulated</span><p>Estimated wasted-trip cost avoided</p><div class="rd-big-n">{I["tnd_saved"]:.0f} <small>TND</small></div>'
            f'<p>About {I["trips_avoided"]:.0f} refused deliveries avoided out of {I["n_orders"]:,}, if every recommendation is followed.</p></section>'
            f'<section class="rd-card"><h3>Refused at the door today</h3><div class="rd-n2">{I["baseline"] * 100:.0f}%</div><p class="rd-hint">Without Wasel (synthetic data)</p></section>'
            f'<section class="rd-card"><h3>Refused with Wasel</h3><div class="rd-n2 rd-ok">{I["projected"] * 100:.0f}%</div><p class="rd-hint">{(I["baseline"] - I["projected"]) * 100:.1f} points fewer refusals</p></section></div>'
            f'<div class="rd-two"><section class="rd-card"><h3>How this was estimated</h3><table class="rd-tab">{"".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td></tr>" for a, b in I["assumptions_plain"])}</table></section>'
            f'<section class="rd-card"><h3>Activity log</h3>{ev}</section></div></div></div>')

def D6():
    mon = DATA["monitor"]; q = DATA["quality"]
    drift = "".join(f'<div class="rd-dr"><span>{esc(d["name"])}</span><b class="rd-t2">As expected</b><em>{d["psi"]:.2f}</em></div>' for d in mon["drift"])
    safe = "".join(f'<div class="rd-dr"><span>{esc(n)}</span><b>{v * 100:.0f}%</b><em>lower is better</em></div>' for n, v in mon["safety"])
    qc = "".join(f'<section class="rd-card"><h3>{esc(s["suite"])}</h3><p class="rd-hint">Tested on {s["n"]} cases</p>' + "".join(f'<div class="rd-dr"><span>{esc(a)}</span><b>{v * 100:.1f}%</b></div>' for a, v in s["metrics"]) + "</section>" for s in q[:4])
    return (f'<div class="rd-app">{topbar("AI health")}<div class="rd-page">{pagehead("AI health", "Quality checks, live monitor, silent failures and the AI call log in one place.")}'
            f'<div class="rd-banner rd-ok2">{icon("Quality", 18)}Release checks: all checks passed. Everything looks normal.</div>'
            f'<div class="rd-grid4 rd-g2"><section class="rd-card"><h3>Are customers writing differently?</h3>{drift}</section><section class="rd-card"><h3>Is the AI behaving?</h3>{safe}</section></div>'
            f'<div class="rd-grid4 rd-g4">{qc}</div></div></div>')

def D7():
    def tile(t, body): return f'<section class="rd-card rd-st-tile"><h3>{t}</h3>{body}</section>'
    skel = "".join('<div class="rd-skel"></div>' for _ in range(4))
    return (f'<div class="rd-app">{topbar()}<div class="rd-page">{pagehead("System states", "How each state looks in Review Desk.")}<div class="rd-grid4 rd-g2">'
            + tile("Empty queue", f'<div class="rd-empty"><b>No orders to review</b><p>Paste a customer message, or wait for the next WhatsApp message.</p><a class="rd-btn rd-pri">Add an order</a></div>')
            + tile("Loading", f'<div class="rd-load">{skel}</div><p class="rd-hint">Scoring…</p>')
            + tile("Error", f'<div class="rd-banner rd-err">{CONTENT["states"]["error"]}</div><a class="rd-btn">Try again</a>')
            + tile("Offline", f'<div class="rd-banner rd-warn">{CONTENT["states"]["offline"]}</div><div class="rd-q on"><div class="rd-q-main"><b>Sami</b><span>last data 14:28</span></div><div class="rd-q-r">{chip(OR[1])}</div></div>')
            + '</div></div></div>')

def desktop():
    return [("D1 Orders to check", D1()), ("D2 Order detail with messages", D2()), ("D3 WhatsApp messages", D3()), ("D4 Add an order", D4()), ("D5 Metrics: money saved and activity", D5()), ("D6 AI health", D6()), ("D7 System states", D7())]

# ------------------------------------------------------------------ phone screens
def sbar(): return '<div class="rd-sb"><span>14:32</span><span>5G ▮▮▮</span></div>'
def tabbar(active="Orders"):
    items = [("Orders", "Orders"), ("WhatsApp", "Messages"), ("Add", "Add"), ("Money saved", "Results"), ("More", "Log")]
    return '<nav class="rd-tabs">' + "".join(f'<a class="{"on" if n == active else ""}">{icon(i, 22)}<span>{n}</span></a>' for n, i in items) + "</nav>"

def M1():
    rows = "".join(f'<div class="rd-pq"><div><b>{bdi(o["customer"])}</b><span>{facts(o)}</span></div><div class="rd-pq-r">{chip(o)}<em>{age(waiting(o))}</em></div></div>' for o in OR)
    return (f'<div class="rd-ph-app">{sbar()}<div class="rd-pbar">{mark("color", 30)}<b>Orders to check</b><span>{icon("Search", 22)}</span></div>'
            f'<div class="rd-pseg"><a>Needs decision <b>0</b></a><a class="on">Awaiting <b>5</b></a><a>Cleared <b>4</b></a></div><div class="rd-plist">{rows}</div>{tabbar("Orders")}</div>')

def M2():
    ev = evidence().replace("rd-cards", "rd-pcards")
    return (f'<div class="rd-ph-app">{sbar()}<div class="rd-pbar"><a>←</a><b>Sami · #2601</b><span>⋯</span></div><div class="rd-pscroll"><div class="rd-pch"><span class="rd-chip rd-t0 rd-big">{glyph(0, 18)}{NAMES[0]} <b>87</b></span>'
            f'<p>{esc(H["product"])} · 220 TND · rural zone</p></div>{ev}{reasons_block()}</div><div class="rd-pdec"><a class="rd-btn rd-pri rd-wide">Send the question</a><div class="rd-row"><a class="rd-btn">Approve for shipping</a><a class="rd-btn rd-danger">Cancel</a></div></div></div>')

def M3():
    return (f'<div class="rd-ph-app">{sbar()}<div class="rd-pbar"><a>←</a><b>Sami</b>{chip(OR[1])}</div><div class="rd-pscroll rd-pmsgs">{transcript(True)}'
            f'<div class="rd-draftp"><span class="rd-tag">Wasel draft · Arabizi</span><p dir="auto">{esc(H["draft"]["text"])}</p><a class="rd-btn rd-pri rd-wide">Send the question</a></div></div>'
            f'<div class="rd-pcomp">Reply to Sami<span>{icon("Send", 22)}</span></div></div>')

def M4():
    return (f'<div class="rd-ph-app">{sbar()}<div class="rd-pbar"><a>←</a><b>Add an order</b><span></span></div><div class="rd-pscroll"><p class="rd-hint">{esc(CONTENT["pages"]["add"]["subtitle"])}</p>'
            f'<div class="rd-pills rd-pills-s">{"".join(f"<span class=rd-pill>{e}</span>" for e in CONTENT["pages"]["add"]["examples"])}</div><label>What the customer wrote</label>'
            f'<div class="rd-ta rd-ta-p" dir="auto">Douar Ouled Ali, 9rib el jemaa. ama ghali chwaya</div><p class="rd-hint">Order details (optional) ▸</p></div><div class="rd-pdec"><a class="rd-btn rd-pri rd-wide">Score this order</a></div></div>')

def M5():
    I = DATA["impact"]
    return (f'<div class="rd-ph-app">{sbar()}<div class="rd-pbar">{mark("color", 30)}<b>Money saved</b><span></span></div><div class="rd-pscroll"><section class="rd-card rd-hero"><span class="rd-tag">Simulated</span><p>Wasted-trip cost avoided</p>'
            f'<div class="rd-big-n">{I["tnd_saved"]:.0f} <small>TND</small></div><p>About {I["trips_avoided"]:.0f} refused deliveries avoided</p></section>'
            f'<div class="rd-pstats"><section class="rd-card"><h3>Without Wasel</h3><div class="rd-n2">{I["baseline"] * 100:.0f}%</div></section><section class="rd-card"><h3>With Wasel</h3><div class="rd-n2 rd-ok">{I["projected"] * 100:.0f}%</div></section></div>'
            f'<section class="rd-card"><h3>Today</h3>' + "".join(f'<div class="rd-ev"><time>{e["ts"]}</time><b>{esc(e["title"])} · {bdi(e["who"])}</b></div>' for e in DATA["activity"][:4]) + f'</section></div>{tabbar("Money saved")}</div>')

def M6():
    more = ["Activity log", "Quality checks", "Silent failures", "Live monitor", "AI call log"]
    ic = ["Log", "Quality", "Quality", "Monitor", "Log"]
    rows = "".join(f'<div class="rd-more">{icon(i, 22)}<b>{n}</b><span>›</span></div>' for n, i in zip(more, ic))
    return (f'<div class="rd-ph-app">{sbar()}<div class="rd-pbar">{mark("color", 30)}<b>More</b><span></span></div><div class="rd-pscroll">{rows}<p class="rd-hint rd-mt">AI scoring live · WhatsApp off (demo mode) · Synthetic data</p></div>{tabbar("More")}</div>')

def phone():
    return [("M1 Orders list", M1()), ("M2 Case with decision bar", M2()), ("M3 Messages thread", M3()), ("M4 Add an order", M4()), ("M5 Metrics glance", M5()), ("M6 More", M6())]

def notes():
    return ('<div class="rd-notes"><h3>How this maps to the real project</h3><ul>'
            '<li><b>Same pages, same copy.</b> Orders to check, WhatsApp messages, Add an order, Money saved, Activity log and the AI-health pages keep their real titles and text.</li>'
            '<li><b>What changes.</b> The orders table becomes a queue plus a case view; the order page becomes an evidence page; the three stat cards become one segmented control.</li>'
            '<li><b>Codebase impact.</b> New queue and case components, evidence cards, a decision bar, J/K keyboard handling. The API is unchanged.</li>'
            '<li><b>Honest cost.</b> It looks like every payments dashboard; the distinctiveness rests on the evidence cards and the customer’s quoted words. Dense queues need the segmented filter to stay useful above about 50 orders.</li></ul></div>')

# ------------------------------------------------------------------ stylesheet (own tokens only)
CSS = f"""
:root{{--rd-ground:{pal['ground']};--rd-surface:{pal['surface']};--rd-ink:{pal['ink']};--rd-mute:{pal['mute']};--rd-primary:{pal['primary']};--rd-secondary:{pal['secondary']};--rd-line:{pal['line']};--rd-focus:{pal['focus']};
--rd-t0:{COLS[0]};--rd-t1:{COLS[1]};--rd-t2:{COLS[2]};--rd-t0b:{TINTS[0]};--rd-t1b:{TINTS[1]};--rd-t2b:{TINTS[2]};--rd-pt:{tint(pal['primary'], .92)}}}
body.rd{{background:var(--rd-ground);color:var(--rd-ink);font:14px/1.45 var(--ui);}}
.rd-top{{background:var(--rd-surface);border-bottom:1px solid var(--rd-line)}}.rd-top span{{color:var(--rd-mute)}}.rd-top nav a{{color:var(--rd-primary);padding:4px 10px;border-radius:6px;text-decoration:none;font-weight:600}}
.bb-sec>h2{{font:700 22px var(--ui)}}.rd-lock{{display:inline-flex;align-items:center;gap:10px}}.rd-wm{{display:inline-flex;align-items:baseline;gap:8px}}.rd-wm b{{font-weight:700;letter-spacing:-.01em}}.rd-wm-ar{{font:700 1.05em var(--ar)}}
.rd-app{{width:1280px;height:800px;background:var(--rd-ground);display:flex;flex-direction:column;font:14px/1.45 var(--ui);color:var(--rd-ink);overflow:hidden}}.rd-app *{{box-sizing:border-box}}
.rd-bar{{display:flex;align-items:center;gap:22px;height:58px;padding:0 24px;background:var(--rd-surface);border-bottom:1px solid var(--rd-line);flex:none}}.rd-bar nav{{display:flex;gap:4px}}
.rd-bar nav a{{display:flex;align-items:center;gap:7px;padding:7px 11px;white-space:nowrap;border-radius:8px;color:var(--rd-mute);font-weight:500}}.rd-bar nav a.on{{color:var(--rd-primary);background:var(--rd-pt);font-weight:700}}.rd-ic{{flex:none}}
.rd-bar-r{{margin-left:auto;display:flex;align-items:center;gap:16px;font-size:13px;color:var(--rd-mute)}}.rd-live i{{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--rd-t2);margin-right:6px}}
.rd-syn{{border:1px solid var(--rd-line);border-radius:99px;padding:2px 10px;white-space:nowrap}}.rd-live{{white-space:nowrap}}.rd-search{{display:flex;align-items:center;gap:6px;border:1px solid var(--rd-line);border-radius:8px;padding:6px 12px;background:var(--rd-ground)}}kbd{{font:600 11px var(--ui);border:1px solid var(--rd-line);border-bottom-width:2px;border-radius:5px;padding:0 6px;background:var(--rd-surface);color:var(--rd-mute);margin:0 2px}}
.rd-page{{flex:1;padding:18px 24px 0;min-height:0;display:flex;flex-direction:column;gap:14px;overflow:hidden}}.rd-ph{{display:flex;justify-content:space-between;align-items:flex-end;gap:30px}}.rd-ph h1{{margin:0;font:700 26px var(--ui);letter-spacing:-.01em}}.rd-ph p{{margin:2px 0 0;color:var(--rd-mute);max-width:760px}}
.rd-seg{{display:flex;background:var(--rd-surface);border:1px solid var(--rd-line);border-radius:10px;padding:3px;flex:none}}.rd-seg a{{padding:7px 14px;border-radius:8px;color:var(--rd-mute);font-weight:600;white-space:nowrap}}.rd-seg a.on{{background:var(--rd-primary);color:#fff}}.rd-seg b{{margin-left:8px;opacity:.85}}
.rd-split{{flex:1;display:grid;grid-template-columns:350px 1fr;gap:16px;min-height:0}}.rd-split3{{grid-template-columns:330px 1fr 300px}}
.rd-queue{{background:var(--rd-surface);border:1px solid var(--rd-line);border-radius:12px;overflow:hidden}}.rd-qh{{display:flex;gap:10px;align-items:center;padding:12px 16px;border-bottom:1px solid var(--rd-line)}}.rd-qh span{{color:var(--rd-mute);flex:1;font-size:13px}}
.rd-q{{display:flex;justify-content:space-between;gap:10px;padding:8px 16px;border-bottom:1px solid #EEF1F6}}.rd-q.on{{background:var(--rd-pt);box-shadow:inset 3px 0 0 var(--rd-primary)}}.rd-q-main{{min-width:0}}.rd-q-main b{{display:block;font-weight:600}}.rd-q-main span{{display:block;color:var(--rd-mute);font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:190px}}
.rd-q-r{{text-align:right;flex:none}}.rd-q-r em{{display:block;font-style:normal;font-size:12px;color:var(--rd-mute);margin-top:3px}}
.rd-chip{{display:inline-flex;align-items:center;gap:5px;padding:2px 9px 2px 6px;border-radius:7px;font-weight:700;font-size:12.5px;white-space:nowrap}}.rd-chip b{{font-variant-numeric:tabular-nums}}.rd-t0{{color:var(--rd-t0);background:var(--rd-t0b)}}.rd-t1{{color:var(--rd-t1);background:var(--rd-t1b)}}.rd-t2{{color:var(--rd-t2);background:var(--rd-t2b)}}em.rd-t0,em.rd-t1,em.rd-t2{{background:none!important;font-style:normal;font-weight:700}}.rd-big{{font-size:16px;padding:5px 14px 5px 10px}}
.rd-case{{background:var(--rd-surface);border:1px solid var(--rd-line);border-radius:12px;padding:18px 22px;overflow:hidden;display:flex;flex-direction:column;gap:12px;min-width:0}}.rd-ch{{display:flex;justify-content:space-between;align-items:flex-start}}.rd-ch h2{{margin:0;font:700 22px var(--ui)}}.rd-ch p{{margin:2px 0 0;color:var(--rd-mute)}}.rd-verdict{{margin:0;color:var(--rd-mute)}}
.rd-cards{{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:12px}}.rd-card{{background:var(--rd-surface);border:1px solid var(--rd-line);border-radius:10px;padding:12px 14px}}.rd-card h3,.rd-reasons h3{{margin:0 0 8px;font:700 12.5px var(--ui);color:var(--rd-mute);text-transform:none;letter-spacing:.01em}}.rd-card p{{margin:0 0 6px;font:16px/1.5 var(--data)}}.rd-card p time{{display:block;font:12px var(--ui);color:var(--rd-mute)}}
.rd-card dl{{margin:0;display:grid;grid-template-columns:auto 1fr;gap:5px 14px}}.rd-card dt{{color:var(--rd-mute)}}.rd-card dd{{margin:0;font-weight:600;text-align:right}}mark.rd-hl{{background:{tint(COLS[1], .78)};color:var(--rd-ink);padding:0 2px;border-radius:3px;border-bottom:2px solid var(--rd-t1)}}
.rd-reasons{{border:1px solid var(--rd-line);border-radius:10px;padding:12px 14px;background:var(--rd-surface)}}.rd-r{{display:grid;grid-template-columns:300px 1fr 40px;gap:12px;align-items:center;padding:4px 0}}.rd-r i{{display:block;height:8px;border-radius:99px;background:var(--rd-t0)}}.rd-r b{{text-align:right;font-variant-numeric:tabular-nums}}.rd-r-t{{border-top:1px solid var(--rd-line);margin-top:4px;padding-top:8px;font-weight:700}}
.rd-decide{{display:flex;gap:10px;align-items:center;margin-top:auto}}.rd-decide>span{{margin-right:auto;color:var(--rd-mute);font-size:13px}}.rd-two .rd-decide>span{{display:none}}.rd-two .rd-decide{{flex-wrap:wrap;gap:8px}}.rd-two .rd-decide .rd-btn{{padding:8px 11px}}.rd-btn{{white-space:nowrap;display:inline-flex;align-items:center;gap:7px;padding:9px 16px;border-radius:9px;border:1px solid var(--rd-line);background:var(--rd-surface);font-weight:600;color:var(--rd-ink)}}.rd-pri{{background:var(--rd-primary);border-color:var(--rd-primary);color:#fff}}.rd-danger{{color:var(--rd-t0)}}.rd-wide{{width:100%;justify-content:center}}
.rd-back{{color:var(--rd-primary);font-weight:600}}.rd-two{{flex:1;display:grid;grid-template-columns:1.25fr 1fr;gap:16px;min-height:0}}.rd-two>div{{display:flex;flex-direction:column;gap:14px;min-height:0}}.rd-n{{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--rd-pt);color:var(--rd-primary);margin-right:8px;font-size:12px}}.rd-hint{{color:var(--rd-mute);font-size:13px;margin:0 0 6px}}
.rd-thread{{display:flex;flex-direction:column;gap:8px;padding:10px;background:var(--rd-ground);border-radius:10px}}.rd-msg{{max-width:78%;background:var(--rd-surface);border:1px solid var(--rd-line);border-radius:12px;padding:8px 12px}}.rd-msg p{{margin:0;font:16px/1.45 var(--data)}}.rd-msg time{{display:block;font:11.5px var(--ui);color:var(--rd-mute);margin-top:2px}}
.rd-draft .rd-tag,.rd-tag{{display:inline-block;font:700 11.5px var(--ui);color:var(--rd-primary);background:var(--rd-pt);border-radius:99px;padding:2px 10px;margin-bottom:6px}}.rd-dtext{{background:var(--rd-ground);border:1px solid var(--rd-line);border-radius:8px;padding:10px 12px}}.rd-row{{display:flex;gap:8px;justify-content:flex-end}}
.rd-hist{{display:flex;gap:12px;align-items:stretch}}.rd-hist>div:not(.rd-then){{flex:1;border:1px solid var(--rd-line);border-radius:8px;padding:8px 10px}}.rd-hist b{{display:inline-block;width:20px;height:20px;border-radius:50%;background:var(--rd-ink);color:#fff;text-align:center;font-size:12px;margin-right:6px}}.rd-hist span{{color:var(--rd-mute)}}.rd-hist em{{display:block;font:700 20px var(--ui);margin:4px 0}}.rd-hist p{{font:13px/1.4 var(--ui);color:var(--rd-mute)}}.rd-then{{width:24px;align-self:center;height:2px;background:var(--rd-line)}}
.rd-banner{{border-radius:8px;padding:9px 14px;background:var(--rd-pt);color:var(--rd-primary);font-weight:600;display:flex;gap:8px;align-items:center}}.rd-ok2{{background:var(--rd-t2b);color:var(--rd-t2)}}.rd-err{{background:var(--rd-t0b);color:var(--rd-t0)}}.rd-warn{{background:var(--rd-t1b);color:var(--rd-t1)}}
.rd-composer{{margin-top:auto;border:1px solid var(--rd-line);border-radius:10px;padding:11px 14px;color:var(--rd-mute);display:flex;justify-content:space-between}}.rd-side{{background:var(--rd-surface);border:1px solid var(--rd-line);border-radius:12px;padding:14px;overflow:hidden}}.rd-side .rd-r{{grid-template-columns:1fr 40px;}}.rd-side .rd-r i{{display:none}}
.rd-pills{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}}.rd-pill{{border:1px solid var(--rd-line);border-radius:99px;padding:5px 12px;background:var(--rd-surface);font-size:13px}}label{{display:block;font:600 13px var(--ui);margin:8px 0 4px}}.rd-ta{{min-height:110px;border:1px solid var(--rd-line);border-radius:9px;padding:10px 12px;font:16px/1.5 var(--data);background:var(--rd-surface)}}.rd-count{{text-align:right;color:var(--rd-mute);font-size:12px}}.rd-mt{{margin-top:14px!important}}
.rd-form{{display:grid;grid-template-columns:1fr 1fr;gap:6px 12px;margin-bottom:12px}}.rd-input{{display:block;border:1px solid var(--rd-line);border-radius:8px;padding:8px 12px;background:var(--rd-surface);color:var(--rd-mute)}}.rd-steps{{margin:0;padding-left:18px}}.rd-steps li{{margin-bottom:8px}}.rd-peek{{margin-top:12px;display:flex;gap:10px;align-items:center;background:var(--rd-ground);border-radius:10px;padding:10px}}.rd-peek p{{margin:0;font:13px var(--ui);color:var(--rd-mute)}}
.rd-grid4{{display:grid;grid-template-columns:1.6fr 1fr 1fr;gap:14px}}.rd-g2{{grid-template-columns:1fr 1fr}}.rd-g4{{grid-template-columns:repeat(4,1fr)}}.rd-hero{{background:var(--rd-primary);border-color:var(--rd-primary);color:#fff}}.rd-hero .rd-tag{{background:rgba(255,255,255,.18);color:#fff}}.rd-hero p{{font:14px var(--ui);color:#E6EEFA}}.rd-big-n{{font:700 52px/1.1 var(--ui);letter-spacing:-.02em}}.rd-big-n small{{font-size:20px;font-weight:600}}
.rd-n2{{font:700 38px var(--ui);color:var(--rd-ink)}}.rd-ok{{color:var(--rd-t2)}}.rd-tab{{width:100%;border-collapse:collapse;font-size:13px}}.rd-tab td{{padding:7px 4px;border-bottom:1px solid #EEF1F6}}.rd-tab td:last-child{{text-align:right;color:var(--rd-mute)}}.rd-ev{{display:grid;grid-template-columns:48px 1fr auto;gap:8px;padding:6px 0;border-bottom:1px solid #EEF1F6;font-size:13px}}.rd-ev time{{color:var(--rd-mute)}}.rd-ev span{{color:var(--rd-mute)}}
.rd-dr{{display:grid;grid-template-columns:1fr auto 90px;gap:10px;padding:7px 0;border-bottom:1px solid #EEF1F6;font-size:13.5px}}.rd-dr em{{font-style:normal;color:var(--rd-mute);text-align:right;font-size:12px}}.rd-empty{{text-align:center;padding:20px}}.rd-skel{{height:34px;border-radius:8px;background:linear-gradient(90deg,#EEF1F6,#E2E8F2,#EEF1F6);margin-bottom:8px}}.rd-st-tile{{min-height:210px}}
/* brand sheet */
.rd-brand{{display:grid;grid-template-columns:repeat(2,minmax(480px,1fr));gap:16px;width:100%;max-width:1180px}}.rd-brand>section{{background:var(--rd-surface);border:1px solid var(--rd-line);border-radius:12px;padding:18px}}.rd-brand>section:first-child{{grid-column:1/-1}}.rd-bh{{margin:0 0 10px;font:700 15px var(--ui)}}.rd-pos{{margin:0;font-size:16px;max-width:90ch}}.rd-note{{color:var(--rd-mute);margin:10px 0 0}}
.rd-logos{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}.rd-lg{{display:flex;flex-direction:column;gap:8px;align-items:center;justify-content:center;border:1px solid var(--rd-line);border-radius:10px;padding:14px;min-height:112px;background:var(--rd-ground)}}.rd-lg span{{font-size:12px;color:var(--rd-mute)}}.rd-inv{{background:var(--rd-primary)}}.rd-inv span{{color:#fff}}.rd-lg:nth-child(5){{flex-direction:row;flex-wrap:wrap}}
.rd-sws{{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-bottom:12px}}.rd-sw{{border-radius:8px;padding:10px 8px;min-height:84px;display:flex;flex-direction:column;justify-content:flex-end;font-size:12px;border:1px solid rgba(0,0,0,.08)}}.rd-sw b{{font-size:13px}}.rd-sw em{{font-style:normal;opacity:.85}}
.rd-type{{display:flex;flex-direction:column;gap:6px}}.rd-sp1{{font:700 36px var(--ui)}}.rd-sp2{{font:600 30px var(--data)}}.rd-sp3{{font:34px var(--ar)}}.rd-sp-ui,.rd-sp-data,.rd-sp-note{{margin:0;color:var(--rd-mute)}}.rd-sp-data{{font:15px var(--data)}}
.rd-trs{{display:flex;flex-direction:column;gap:8px;margin-bottom:12px}}.rd-tr{{display:flex;gap:12px;align-items:center}}.rd-tr p{{margin:0;color:var(--rd-mute)}}.rd-sts{{display:flex;flex-wrap:wrap;gap:6px}}.rd-st{{border:1px solid var(--rd-line);border-radius:99px;padding:4px 12px;font-weight:600;background:var(--rd-ground)}}
.rd-icons{{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}}.rd-icon{{display:flex;flex-direction:column;align-items:center;gap:6px;border:1px solid var(--rd-line);border-radius:8px;padding:12px 6px;color:var(--rd-primary);font-size:12px}}.rd-icon span{{color:var(--rd-mute)}}.rd-comps{{display:flex;gap:10px;flex-wrap:wrap;align-items:center}}
.rd-notes{{max-width:900px;background:var(--rd-surface);border:1px solid var(--rd-line);border-radius:12px;padding:6px 20px 14px}}.rd-notes li{{margin:6px 0}}
/* phone */
.rd-ph-app{{width:390px;height:844px;background:var(--rd-ground);display:flex;flex-direction:column;font:15px/1.45 var(--ui);color:var(--rd-ink);position:relative}}.rd-ph-app *{{box-sizing:border-box}}.rd-sb{{display:flex;justify-content:space-between;padding:12px 26px 4px;font-weight:700;font-size:13px;background:var(--rd-surface)}}
.rd-pbar{{display:flex;align-items:center;gap:12px;padding:10px 16px;background:var(--rd-surface);border-bottom:1px solid var(--rd-line)}}.rd-pbar b{{flex:1;font-size:18px}}.rd-pbar a{{font-size:22px;color:var(--rd-primary);padding:6px}}.rd-pseg{{display:flex;gap:6px;padding:10px 14px;background:var(--rd-surface)}}.rd-pseg a{{flex:1;text-align:center;padding:10px 4px;border-radius:10px;border:1px solid var(--rd-line);font-weight:600;font-size:13px;min-height:44px;display:flex;align-items:center;justify-content:center;gap:5px;color:var(--rd-mute)}}.rd-pseg a.on{{background:var(--rd-primary);color:#fff;border-color:var(--rd-primary)}}
.rd-plist{{flex:1;overflow:hidden;padding:6px 12px}}.rd-pq{{display:flex;justify-content:space-between;gap:8px;padding:12px;margin-bottom:8px;background:var(--rd-surface);border:1px solid var(--rd-line);border-radius:12px;min-height:60px}}.rd-pq b{{display:block}}.rd-pq span{{font-size:13px;color:var(--rd-mute)}}.rd-pq-r{{text-align:right}}.rd-pq-r em{{display:block;font-style:normal;font-size:12px;color:var(--rd-mute);margin-top:3px}}
.rd-pscroll{{flex:1;overflow:hidden;padding:14px;display:flex;flex-direction:column;gap:12px}}.rd-pch p{{margin:6px 0 0;color:var(--rd-mute)}}.rd-pcards{{display:flex;flex-direction:column;gap:10px}}.rd-ph-app .rd-r{{grid-template-columns:1fr 70px 30px}}.rd-ph-app .rd-r i{{max-width:70px}}.rd-pdec{{padding:12px 14px 22px;background:var(--rd-surface);border-top:1px solid var(--rd-line);display:flex;flex-direction:column;gap:8px}}.rd-pdec .rd-btn{{min-height:48px}}.rd-pdec .rd-row .rd-btn{{flex:1;justify-content:center}}
.rd-pmsgs .rd-thread{{background:transparent;padding:0}}.rd-draftp{{background:var(--rd-surface);border:1px solid var(--rd-line);border-radius:12px;padding:12px}}.rd-draftp p{{margin:4px 0 10px;font:15px/1.5 var(--data)}}.rd-pcomp{{margin:8px 14px 22px;border:1px solid var(--rd-line);border-radius:24px;padding:12px 16px;display:flex;justify-content:space-between;color:var(--rd-mute);background:var(--rd-surface);min-height:48px}}
.rd-ta-p{{min-height:130px}}.rd-pills-s{{margin-bottom:2px}}.rd-pstats{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}.rd-tabs{{display:flex;background:var(--rd-surface);border-top:1px solid var(--rd-line);padding:6px 4px 22px}}.rd-tabs a{{flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;font-size:11.5px;color:var(--rd-mute);min-height:48px;justify-content:center}}.rd-tabs a.on{{color:var(--rd-primary);font-weight:700}}
.rd-ph-app .rd-btn{{min-height:44px}}.rd-ph-app .rd-pill{{min-height:44px;display:inline-flex;align-items:center}}.rd-more{{display:flex;align-items:center;gap:14px;padding:14px;background:var(--rd-surface);border:1px solid var(--rd-line);border-radius:12px;min-height:56px;color:var(--rd-primary)}}.rd-more b{{flex:1;color:var(--rd-ink);font-weight:600}}.rd-more span{{color:var(--rd-mute)}}
"""
