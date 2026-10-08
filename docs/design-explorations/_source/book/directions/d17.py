"""Direction 17: Clear Desk (hybrid). Terminal Desk's rigid panel grid and key row, with a light, welcoming palette.
Built from the persona rounds: light surface (dark as a switch), plain sentences, a search bar instead of a command line,
the queue on the left beside the case, tier words that name the action (Hold, Ask, Ship), one primary button per screen,
the synthetic-data notice shown once, shortcuts shown as hints on desktop only.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from kit import *

PREFIX = "hx"
D = direction("17-clear-desk")
pal, T = D["pal"], D["tiers"]
NAMES, COLS = T["names"], T["colors"]
H = hero()
OR = orders()
SELECTED = "#2601"
NEXT = CONTENT["pages"]["orders"]["next_steps"]
STAT = CONTENT["pages"]["orders"]["statuses"]
PGS = CONTENT["pages"]

# ------------------------------------------------------------------ language strings (list screens only)
L = {
 "en": dict(dir="ltr", title="Orders to check", tiers=NAMES, next=dict(confirm=NEXT["confirm"], prepay=NEXT["prepay"], check=NEXT["review"], ship=NEXT["ship"]),
            status=dict(WAITING=STAT["awaiting_reply"], NEW=STAT["needs_review"], READY=STAT["ready_to_ship"]),
            keys=["Orders", "Messages", "Add", "Money", "More"], banner="{r} to hold · {u} to ask · {s} to ship. Nothing needs your decision.",
            filters=["Needs your decision", "Waiting for customer", "Ready to ship"], unit="min", hour="h", search="Search an order or a customer"),
 "fr": dict(dir="ltr", title="Commandes à vérifier", tiers=["Attendre", "Demander", "Expédier"], next=dict(confirm="Confirmer avec le client", prepay="Demander un prépaiement", check="Vérifier vous-même", ship="Expédier normalement"),
            status=dict(WAITING="En attente du client", NEW="Votre décision", READY="Prêt à expédier"),
            keys=["Commandes", "Messages", "Ajouter", "Argent", "Plus"], banner="{r} à retenir · {u} à interroger · {s} à expédier. Aucune décision requise.",
            filters=["Votre décision", "En attente du client", "Prêt à expédier"], unit="min", hour="h", search="Chercher une commande ou un client"),
 "ar": dict(dir="rtl", title="الطلبات التي تحتاج مراجعة", tiers=["أوقف", "اسأل", "اشحن"], next=dict(confirm="أكّد مع الزبون", prepay="اطلب دفعاً مسبقاً", check="تحقق بنفسك", ship="اشحن عادياً"),
            status=dict(WAITING="في انتظار الزبون", NEW="قرارك", READY="جاهز للشحن"),
            keys=["الطلبات", "الرسائل", "إضافة", "المال", "المزيد"], banner="{r} للإيقاف · {u} للسؤال · {s} للشحن. لا قرار مطلوب منك.",
            filters=["قرارك", "في انتظار الزبون", "جاهز للشحن"], unit="د", hour="س", search="ابحث عن طلب أو زبون"),
}

# ------------------------------------------------------------------ data helpers
def status(o):
    if o["tier_raw"] == "low": return "READY"
    if waiting(o) >= 120: return "WAITING"
    if o["tier_raw"] == "medium": return "NEW"
    return "WAITING"

def nextkey(o):
    if o["tier_raw"] == "medium": return "check"
    return o["action_raw"]

def nextstep(o, lang="en"): return L[lang]["next"][nextkey(o)]

def wait(m, lang="en"):
    u, h = L[lang]["unit"], L[lang]["hour"]
    return f"{m // 60} {h} {m % 60:02d} {u}" if m >= 60 else f"{m} {u}"

# ------------------------------------------------------------------ marks
def glyph(i, size=14):
    c = f"var(--t{i})"
    shapes = {
        0: f'<path d="M5 1.5h4L12.5 5v4L9 12.5H5L1.5 9V5z" fill="{c}"/><path d="M4.5 7h5" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/>',
        1: f'<path d="M7 1 13 7 7 13 1 7z" fill="{c}"/><path d="M7 4.2v3.4" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/><circle cx="7" cy="9.6" r="1" fill="#fff"/>',
        2: f'<circle cx="7" cy="7" r="6" fill="{c}"/><path d="M4.2 7.2 6.2 9.2 9.9 5.2" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    }
    return f'<svg class="hx-gl" width="{size}" height="{size}" viewBox="0 0 14 14" aria-hidden="true">{shapes[i]}</svg>'

def mark(variant="color", size=48):
    p, ink, w = pal["primary"], pal["ink"], "#FFFFFF"
    if variant == "favicon":
        return (f'<svg width="{size}" height="{size}" viewBox="0 0 32 32" aria-label="Wasel favicon"><rect width="32" height="32" fill="{p}"/>'
                f'<path d="M6 8l3.2 12L13 11l3.8 9L20 8" fill="none" stroke="{w}" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/><path d="M20 28v-7a3.5 3.5 0 0 1 7 0v7z" fill="{w}"/></svg>')
    if variant == "app":
        return (f'<svg width="{size}" height="{size}" viewBox="0 0 120 120" aria-label="Wasel app icon"><rect width="120" height="120" rx="26" fill="{p}"/><g transform="translate(18 18) scale(2.6)">'
                f'<path d="M6 8l3.2 12L13 11l3.8 9L20 8" fill="none" stroke="{w}" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/><path d="M20 28v-7a3.5 3.5 0 0 1 7 0v7z" fill="{w}" transform="translate(-1 -3)"/></g></svg>')
    fg, ic, bg = {"color": (p, w, None), "mono": (ink, w, None), "reversed": (w, p, p)}[variant]
    back = f'<rect width="32" height="32" fill="{bg}"/>' if bg else ""
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 32 32" aria-label="Wasel mark">{back}<rect x="2" y="2" width="28" height="28" fill="{fg}"/>'
            f'<path d="M6.5 8.5l3 11 3.5-8.5 3.5 8.5 3-11" fill="none" stroke="{ic}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/><path d="M21 28v-6.5a3 3 0 0 1 6 0V28z" fill="{ic}"/></svg>')

def wordmark(variant="color"):
    col = {"color": pal["ink"], "mono": pal["ink"], "reversed": "#FFFFFF"}[variant]
    return f'<span class="hx-wm" style="color:{col}"><b>Wasel</b><span lang="ar" class="hx-wm-ar">واصل</span></span>'

def lockup(variant="color", size=44):
    return f'<span class="hx-lock">{mark(variant, size)}{wordmark(variant)}</span>'

# ------------------------------------------------------------------ shared pieces
def chip(o, score=True, lang="en"):
    i = tier_index(o["tier_raw"])
    s = f'<b>{o["score"]}</b>' if score else ""
    return f'<span class="hx-t hx-t{i}">{glyph(i, 13)}<span>{L[lang]["tiers"][i]}</span>{s}</span>'

def chip_plain(i, label=None, score=None):
    s = f'<b>{score}</b>' if score is not None else ""
    return f'<span class="hx-t hx-t{i}">{glyph(i, 13)}<span>{label or NAMES[i]}</span>{s}</span>'

def topbar(search="Search an order or a customer", tab="Orders", dark=False):
    nav = "".join(f'<a class="{"on" if n == tab else ""}">{n}</a>' for n in ["Orders", "Messages", "Add an order", "Money saved", "More"])
    return (f'<header class="hx-bar"><span class="hx-logo">{mark("favicon", 28)}</span><b class="hx-bn">Wasel</b><nav>{nav}</nav>'
            f'<span class="hx-search">{esc(search)}</span><span class="hx-lang"><b>EN</b> FR AR</span><span class="hx-theme"><i class="{"" if dark else "on"}">Light</i><i class="{"on" if dark else ""}">Dark</i></span></header>')

def notice():
    return '<div class="hx-note"><b>Synthetic data.</b> Everything on these screens is test data, not real customers or real sales.</div>'

def pills(lang="en", active=None):
    f = L[lang]["filters"]; counts = [0, 5, 4]
    return '<div class="hx-pills">' + "".join(f'<span class="hx-pill {"on" if i == active else ""}">{f[i]} <b>{counts[i]}</b></span>' for i in range(3)) + '</div>'

def summary(lang="en"):
    return f'<div class="hx-sum">{glyph(0, 15)}<span>{L[lang]["banner"].format(r=4, u=1, s=4)}</span></div>'

def keyrow(active="Orders"):
    ks = [("1", "Orders"), ("2", "Messages"), ("3", "Add an order"), ("4", "Money saved"), ("5", "Activity"), ("6", "Quality"), ("7", "Failures"), ("8", "Monitor"), ("9", "AI calls")]
    k = "".join(f'<span class="hx-k {"on" if n == active else ""}"><i>{a}</i>{n}</span>' for a, n in ks)
    return f'<footer class="hx-keys"><span class="hx-kl">Keyboard shortcuts</span>{k}<span class="hx-kr"><i>/</i>Search</span></footer>'

def panel(title, body, cls="", tag=None):
    t = f'<em>{tag}</em>' if tag else ""
    return f'<section class="hx-p {cls}"><h3>{esc(title)}{t}</h3><div class="hx-pb">{body}</div></section>'

def app(inner, tab="Orders", sub=None, strip=True, active="Orders", dark=False, search="Search an order or a customer"):
    cls = "hx-app hx-dark" if dark else "hx-app"
    s = f'<div class="hx-sub">{esc(sub)}</div>' if sub else ""
    return f'<div class="{cls}">{topbar(search, tab, dark)}{notice() if strip else ""}{s}<div class="hx-main">{inner}</div>{keyrow(active)}</div>'

def queue(rows=None, compact=False):
    rows = rows or OR
    out = ""
    for o in rows:
        cur = " cur" if o["ref"] == SELECTED else ""
        out += (f'<div class="hx-q{cur}"><div class="hx-q1"><b>{bdi(o["customer"])}</b><span class="hx-n">{o["ref"]}</span>{chip(o)}</div>'
                f'<div class="hx-q2"><span>{nextstep(o)}</span><span class="hx-n">{o["price_tnd"]:.0f} TND · {wait(waiting(o))}</span></div></div>')
    return f'<div class="hx-ql">{out}</div>'

def why_rows():
    rows = f'<tr><td>First order from this customer</td><td class="r">{H["base"]}</td><td class="hx-bc"><i style="width:{H["base"]}%"></i></td></tr>'
    rows += "".join(f'<tr><td>{esc(f["label"][0].upper() + f["label"][1:])}</td><td class="r hx-up">+{f["points"]}</td><td class="hx-bc"><i style="width:{f["points"] * 3}%"></i></td></tr>' for f in H["factors"])
    return f'<table class="hx-tab hx-why">{rows}<tr class="hx-tot"><td>Score</td><td class="r">87</td><td></td></tr></table>'

def customer_line():
    return f'<p class="hx-cl"><b>{bdi(H["customer"])}</b> · {esc(H["product"]).capitalize()} · 220 TND · Rural delivery zone · {chip(OR[1])}</p>'

def quotes():
    phr = [f["quote"] for f in H["flags"]]
    ts = ["12:09", "12:36", "12:47"]
    lines = "".join(f'<div class="hx-bub" dir="auto"><time>{t}</time><p>{hl(m["text"], phr, "hx-hl")}</p></div>' for m, t in zip(H["messages"], ts))
    why = "".join(f'<li><mark class="hx-hl">{esc(f["quote"])}</mark> {esc(w)}</li>' for f, w in zip(H["flags"], ["is a landmark, not a street address.", "means the customer may not be home when the courier comes.", "means the customer finds the price high."]))
    return f'<div class="hx-qt">{lines}</div><p class="hx-lab">Why these words are highlighted</p><ul class="hx-ul">{why}</ul>'

def primary(text, key=None):
    k = f'<i>{key}</i>' if key else ""
    return f'<a class="hx-btn">{k}{esc(text)}</a>'

def actions():
    return f'<div class="hx-act">{primary("Send the question to Sami", "Enter")}<a class="hx-lnk">Approve the order</a><a class="hx-lnk hx-danger">Cancel the order</a></div>'

def desk_panel():
    f = PGS["orders"]["counters"]
    rows = (f'<tr><td>Money at risk</td><td class="r">1,148 TND</td></tr><tr><td>AI scoring</td><td class="r hx-ok">Live</td></tr>'
            f'')
    return f'<table class="hx-tab hx-kv">{rows}</table>'

AR_DRAFT = "من فضلك ابعثلي العنوان الكامل: اسم الشارع ورقم الدار ونمرة تليفون. تنجم تبعثهم؟"

# ------------------------------------------------------------------ brand sheet
def swatch(name, hexv, note="", on=None):
    cr = contrast(hexv, "#FFFFFF"); tc = "#fff" if cr >= 4.5 else "#17212B"
    return f'<div class="hx-sw" style="background:{hexv};color:{tc}"><b>{name}</b><span>{hexv}</span><em>{note}</em></div>'

DARK = dict(ground="#14191F", surface="#1C232B", ink="#E8EDF2", mute="#9AA7B4", primary="#4FD1C5", line="#2B3540", t0="#FF8A80", t1="#FFC857", t2="#6FD39B")

def brand():
    Hd = lambda t: f'<h3 class="hx-bh">{t}</h3>'
    logos = (f'<div class="hx-logos"><div class="hx-lg">{lockup("color", 64)}<span>Lockup</span></div><div class="hx-lg">{mark("color", 64)}<span>Mark</span></div><div class="hx-lg">{mark("mono", 64)}<span>One colour</span></div>'
             f'<div class="hx-lg hx-inv">{mark("reversed", 64)}<span>Reversed</span></div><div class="hx-lg">{mark("favicon", 32)}{mark("favicon", 16)}<span>Favicon 32, 16</span></div><div class="hx-lg">{mark("app", 64)}<span>App icon</span></div></div>')
    sws = "".join([swatch("Ground", pal["ground"], "page"), swatch("Surface", pal["surface"], "panels"), swatch("Ink", pal["ink"], "text"), swatch("Mute", pal["mute"], "secondary text"), swatch("Teal", pal["primary"], "buttons, links"), swatch("Blue", pal["secondary"], "customer words"), swatch("Line", pal["line"], "rules"),
                   swatch(NAMES[0], COLS[0], "tier"), swatch(NAMES[1], COLS[1], "tier"), swatch(NAMES[2], COLS[2], "tier")])
    dk = "".join(f'<div class="hx-sw" style="background:{v};color:{"#fff" if k in ("ground", "surface", "line") else "#14191F"};border:1px solid #333"><b>{k}</b><span>{v}</span></div>' for k, v in DARK.items())
    contr = "".join(f'<tr><td>{a}</td><td class="r">{contrast(f, b):.1f}:1</td><td class="r">{"AA" if contrast(f, b) >= 4.5 else "Large text only"}</td></tr>' for a, f, b in
                    [("Ink on ground", pal["ink"], pal["ground"]), ("Mute on ground", pal["mute"], pal["ground"]), ("White on teal", "#FFFFFF", pal["primary"]), (f"{NAMES[0]} on white", COLS[0], "#FFFFFF"), (f"{NAMES[1]} on white", COLS[1], "#FFFFFF"), (f"{NAMES[2]} on white", COLS[2], "#FFFFFF"),
                     ("Dark: ink on ground", DARK["ink"], DARK["ground"]), ("Dark: teal on ground", DARK["primary"], DARK["ground"])])
    gloss = [("high", 87, "Likely to be refused at the door. Hold the parcel and ask first.", "Attendre · أوقف"), ("medium", 42, "Some doubt. Ask the customer a quick question.", "Demander · اسأل"), ("low", 9, "Looks fine. Ship it normally.", "Expédier · اشحن")]
    tiers = "".join(f'<div class="hx-tr">{chip(dict(tier_raw=r, score=s))}<p>{t}<br><i dir="auto">{g}</i></p></div>' for r, s, t, g in gloss)
    stat = "".join(f'<span class="hx-st">{s}</span>' for s in D["status"])
    voice = [("Page title", "Orders to check"), ("Evidence", "What the customer said"), ("Reason", "Why this score"), ("Primary action", "Send the question to Sami"), ("Empty", "Nothing here yet. Add an order or wait for the next WhatsApp message."),
             ("Error", CONTENT["states"]["error"]), ("Arabic", "الطلبات التي تحتاج مراجعة"), ("French", "Commandes à vérifier"), ("Tier help", "Hold: likely to be refused at the door.")]
    vtab = "".join(f'<tr><td>{k}</td><td dir="auto">{v}</td></tr>' for k, v in voice)
    spec = (f'<div class="hx-type"><div class="hx-sp1">DM Sans, for words</div><p class="hx-spp">Orders to check. Sentences in sentence case, 14 to 16 px on phones, 13 to 14 px on desktop.</p>'
            f'<div class="hx-sp2">0123456789 IBM Plex Mono</div><p class="hx-spp hx-mono">2601  Sami   Hold 87   +17   1,148 TND   3 h 10 min</p>'
            f'<div class="hx-sp3" lang="ar" dir="rtl">دوار أولاد علي، قريب من الجامع</div><p class="hx-spp">IBM Plex Sans Arabic. Numbers and prices are monospaced so columns line up.</p></div>')
    comps = (f'<div class="hx-comps">{primary("Send the question to Sami", "Enter")}<a class="hx-lnk">Approve the order</a><a class="hx-lnk hx-danger">Cancel the order</a>{chip(OR[1])}{chip(OR[4])}{chip(OR[7])}'
             f'<span class="hx-search" style="min-width:260px">Search an order or a customer</span><span class="hx-pill on">Needs your decision <b>0</b></span><span class="hx-pill">Waiting for customer <b>5</b></span></div>')
    return (f'<div class="hx-brand"><section class="hx-wide"><p class="hx-pos"><b>Clear Desk.</b> The rigid, ordered panel grid of a professional desk, in a light and friendly palette. Same structure the owner liked, with plain sentences, buttons that look like buttons, and one primary action per screen. A dark theme is a switch, not a different product.</p></section>'
            f'<section>{Hd("Logo suite")}{logos}<p class="hx-note2">Idea: a teal square on the same grid as the panels, carrying a W whose last stroke becomes a door arch.</p></section>'
            f'<section>{Hd("Colour, light theme")}<div class="hx-sws">{sws}</div><table class="hx-tab">{contr}</table></section>'
            f'<section>{Hd("Colour, dark theme (switch)")}<div class="hx-sws">{dk}</div><p class="hx-note2">Soft charcoal-navy with pale text and a mint teal. No amber, no glow.</p></section>'
            f'<section>{Hd("Type")}{spec}</section>'
            f'<section>{Hd("Tier vocabulary: words that name the action")}<div class="hx-trs">{tiers}</div>{Hd("Status vocabulary")}<div class="hx-sts">{stat}</div></section>'
            f'<section>{Hd("Voice")}<table class="hx-tab">{vtab}</table></section><section>{Hd("Components")}{comps}</section></div>')

# ------------------------------------------------------------------ desktop screens
def D1(dark=False):
    case = customer_line() + why_rows() + actions()
    left = panel("Orders to check", pills(active=None) + queue(), "hx-a", "9 orders")
    g = left + panel("Why this score · #2601 Sami", case, "hx-b") + panel("What the customer said", quotes(), "hx-c") + panel("Today at a glance", desk_panel(), "hx-d")
    return app(f'{summary()}<div class="hx-grid1">{g}</div>', "Orders", PGS["orders"]["subtitle"], True, "Orders", dark)

def D8(): return D1(True)

def hist():
    rows = [("14:32", "Escalated to you", "No reply after 90 minutes", "–"), ("13:05", "Question sent", "By the assistant, in Arabizi", "–"), ("12:49", "Message drafted", "Address question", "–"),
            ("12:48", "Scored 87", "First score, three warning signs", "“9rib el jemaa”"), ("12:47", "Message received", "“ghali chwaya”", "Price hesitation"), ("12:36", "Message received", "“Douar Ouled Ali…”", "Vague location"), ("12:09", "Order opened", "First message", "–")]
    tr = "".join(f'<tr><td class="hx-n">{t}</td><td>{a}</td><td>{b}</td><td>{c}</td></tr>' for t, a, b, c in rows)
    after = f'<tr class="cur"><td>Next</td><td>If he answers</td><td colspan="2">{chip_plain(2, score=16)} Full address given, −32</td></tr>'
    return f'<table class="hx-tab"><tr><th>Time</th><th>What happened</th><th>Detail</th><th>Signal</th></tr>{after}{tr}</table><p class="hx-hint">Every event for this order. All orders: Activity log.</p>'

def D2():
    draft = (f'<div class="hx-tabs"><span class="on">Arabizi (sent to customer)</span><span>Français</span><span>العربية</span></div><p class="hx-dr" dir="auto">{esc(H["draft"]["text"])}</p>'
             f'<p class="hx-tr2"><b>FR</b> {esc(H["french_draft"])}</p><p class="hx-tr2" dir="rtl"><b>AR</b> {AR_DRAFT}</p><p class="hx-hint">Arabizi is Darija written in Latin letters, the way customers type it on WhatsApp.</p>'
             f'<div class="hx-act">{primary("Send the question to Sami", "Enter")}<a class="hx-lnk">Edit the message</a></div>')
    g = (panel("What the customer said", quotes(), "hx-m1") + panel("Message to the customer", draft, "hx-m2") + panel("Why this score", why_rows() + '<div class="hx-act"><a class="hx-lnk">Approve the order</a><a class="hx-lnk hx-danger">Cancel the order</a></div>', "hx-m3") + panel("Audit trail for this order", hist(), "hx-m4"))
    return app(f'{customer_line()}<div class="hx-grid2">{g}</div>', "Orders", PGS["order"]["verdict_line"], True, "Orders")

def D3():
    rows = "".join(f'<tr class="{"cur" if o["ref"] == SELECTED else ""}"><td class="hx-n">{o["ref"][1:]}</td><td>{bdi(o["customer"])}</td><td dir="auto" class="hx-pv">{esc(o["preview"] or "")}</td><td>{chip(o, False)}</td><td class="r hx-n">{wait(waiting(o))}</td></tr>' for o in OR)
    conv = f'<table class="hx-tab"><tr><th>ID</th><th>Customer</th><th>Last message</th><th>Risk</th><th class="r">Waiting</th></tr>{rows}</table>'
    thread = (f'<div class="hx-warn">WhatsApp is off in demo mode. Replies are recorded, not sent.</div>{quotes()}'
              f'<div class="hx-reply"><b>Your reply, ready to send</b><p dir="auto">{esc(H["draft"]["text"])}</p></div><div class="hx-act">{primary("Send the question to Sami", "Enter")}<a class="hx-lnk">Edit the reply</a></div>')
    g = panel("WhatsApp messages", pills(active=None) + conv, "hx-v1", "9 conversations") + panel("Sami · #2601", thread, "hx-v2") + panel("Why", why_rows(), "hx-v3")
    return app(f'<div class="hx-grid3">{g}</div>', "Messages", PGS["messages"]["subtitle"], True, "Messages")

def D4():
    ex = "".join(f'<div class="hx-ex"><i>{i}</i>{esc(e)}</div>' for i, e in enumerate(PGS["add"]["examples"], 1))
    form = ('<p class="hx-lab">Customer message</p><div class="hx-ta" dir="auto">Douar Ouled Ali, 9rib el jemaa. ama ghali chwaya, mouch dima fi dar<i class="hx-cur"></i></div><p class="hx-lab hx-r">0 / 2,000</p>'
            '<table class="hx-tab hx-kv"><tr><td>Customer name</td><td>Sami</td></tr><tr><td>Product</td><td>Casque Bluetooth</td></tr><tr><td>Price (TND)</td><td>220</td></tr><tr><td>Delivery zone</td><td>Rural</td></tr></table>'
            f'<div class="hx-act">{primary("Score this order", "Enter")}<a class="hx-lnk">Clear the form</a></div>')
    side = (f'<p class="hx-lab">Try an example</p>{ex}<p class="hx-lab hx-mt">What happens next</p><ol class="hx-ol"><li>Wasel reads the address, the zone and any warning signs in the customer’s own words.</li>'
            f'<li>It scores the risk from 0 to 100 with a model and fixed rules. The AI never picks the number.</li><li>It drafts one question that would reduce the risk. You decide whether to send it.</li></ol>')
    return app(f'<div class="hx-grid4">{panel("Add an order", form, "hx-f1")}{panel("Examples and what happens next", side, "hx-f2")}</div>', "Add an order", PGS["add"]["subtitle"], True, "Add an order")

def D5():
    I = DATA["impact"]
    res = (f'<p class="hx-big">{I["tnd_saved"]:.0f} <small>TND</small></p><p class="hx-lab">Estimated cost of wasted trips avoided. Simulated on test orders, not real sales.</p>'
           f'<table class="hx-tab hx-kv"><tr><td>Refused deliveries avoided</td><td class="r">{I["trips_avoided"]:.0f} of {I["n_orders"]:,}</td></tr><tr><td>Refused at the door today</td><td class="r">{I["baseline"] * 100:.0f}%</td></tr>'
           f'<tr><td>Refused with Wasel</td><td class="r hx-ok">{I["projected"] * 100:.0f}%</td></tr><tr><td>Change</td><td class="r hx-ok">−{(I["baseline"] - I["projected"]) * 100:.1f} points</td></tr></table>')
    ass = "".join(f'<tr><td>{esc(a)}</td><td class="r">{esc(b)}</td></tr>' for a, b in I["assumptions_plain"])
    log = '<table class="hx-tab"><tr><th>Time</th><th>What happened</th><th>Customer</th><th>ID</th></tr>' + "".join(f'<tr><td class="hx-n">{e["ts"]}</td><td>{esc(e["title"])}{(" · " + esc(e["detail"])) if e.get("detail") else ""}</td><td>{bdi(e["who"])}</td><td class="hx-n">{e["ref"][1:]}</td></tr>' for e in DATA["activity"][:11]) + '</table>'
    g = panel("Money saved", res, "hx-r1") + panel("How this was estimated", f'<table class="hx-tab">{ass}</table>', "hx-r2") + panel("Activity log", log, "hx-r3")
    return app(f'<div class="hx-grid5">{g}</div>', "Money saved", PGS["impact"]["subtitle"], True, "Money saved")

def D6():
    mon = DATA["monitor"]; q = DATA["quality"]
    drift = '<table class="hx-tab"><tr><th>What we watch</th><th>State</th><th class="r">Change</th></tr>' + "".join(f'<tr><td>{esc(d["name"])}</td><td class="hx-ok">As expected</td><td class="r hx-n">{d["psi"]:.2f}</td></tr>' for d in mon["drift"]) + '</table>'
    safe = '<table class="hx-tab"><tr><th>Check</th><th class="r">Rate</th></tr>' + "".join(f'<tr><td>{esc(n)}</td><td class="r hx-n">{v * 100:.0f}%</td></tr>' for n, v in mon["safety"]) + '</table>'
    qrows = "".join(f'<tr><td>{esc(s["suite"])}</td><td class="r hx-n">{s["n"]}</td>' + "".join(f'<td class="r hx-n hx-ok">{v * 100:.1f}</td>' for _, v in s["metrics"]) + '</tr>' for s in q)
    qt = f'<table class="hx-tab"><tr><th>Test</th><th class="r">Cases</th><th class="r">Score 1</th><th class="r">Score 2</th><th class="r">Score 3</th></tr>{qrows}</table><p class="hx-hint">Each test reports its three main scores. All release checks passed.</p>'
    fl = DATA["failures"]
    ft = f'<table class="hx-tab hx-kv"><tr><td>Test conversations checked</td><td class="r hx-n">{fl["sessions"]}</td></tr><tr><td>Findings</td><td class="r hx-n">{fl["findings"]}</td></tr><tr><td>Source</td><td class="r">Synthetic, not real</td></tr></table>'
    ai = '<table class="hx-tab hx-kv"><tr><td>AI calls</td><td class="r hx-n">0</td></tr><tr><td>Typical answer time</td><td class="r">–</td></tr><tr><td>Backup model used</td><td class="r hx-n">0</td></tr></table><p class="hx-hint">No AI calls yet. Offline mode.</p>'
    g = panel("Are customers writing differently?", drift, "hx-h1") + panel("Is the AI behaving?", safe, "hx-h2") + panel("Quality tests", qt, "hx-h3") + panel("Silent failures", ft, "hx-h4") + panel("AI call log", ai, "hx-h5")
    top = '<div class="hx-okb"><b>Nothing is wrong.</b> 0 alerts, all release checks passed. The panels below are details for the technical team.</div>'
    return app(top + f'<div class="hx-grid6">{g}</div>', "More", "Quality checks, live monitor, silent failures and the AI call log in one place.", True, "Monitor")

def D7():
    t = lambda title, body: panel(title, body, "hx-sx")
    empty = f'<p class="hx-big2">{esc(CONTENT["states"]["empty"])}</p><p class="hx-hint">Add an order, or wait for the next WhatsApp message.</p><div class="hx-act">{primary("Add an order", "3")}</div>'
    load = f'<p class="hx-load">{esc(CONTENT["states"]["scoring"])}… <span class="hx-prog"><i></i></span> 50%</p><div class="hx-skel"></div><div class="hx-skel"></div>'
    err = f'<div class="hx-err">{esc(CONTENT["states"]["error"])}</div><div class="hx-act">{primary("Try again", "R")}</div>'
    off = f'<div class="hx-warn">{esc(CONTENT["states"]["offline"])}</div><table class="hx-tab"><tr class="cur"><td class="hx-n">2601</td><td>Sami</td><td>{chip(OR[1])}</td><td>Last data 14:28</td></tr></table>'
    g = t("Empty", empty) + t("Loading", load) + t("Error", err) + t("Offline", off)
    return app(f'<div class="hx-grid7">{g}</div>', "Orders", "How each state looks.", True, "Orders")

def desktop():
    return [("D1 Orders to check", D1()), ("D2 Order detail with messages", D2()), ("D3 WhatsApp messages", D3()), ("D4 Add an order", D4()), ("D5 Metrics: money saved and activity", D5()), ("D6 AI health", D6()), ("D7 System states", D7()), ("D8 Orders to check, dark theme", D8())]

# ------------------------------------------------------------------ phone screens
def pbar(title, back=False, lang="en"):
    b = '<span class="hx-back">‹</span>' if back else f'<span class="hx-plogo">{mark("favicon", 30)}</span>'
    return f'<div class="hx-sb"><span>14:32</span><span>5G ▮▮▮</span></div><div class="hx-pbar">{b}<b>{esc(title)}</b><span class="hx-pl2"><b>EN</b> FR AR</span></div>'

def pnav(active=0, lang="en"):
    return '<nav class="hx-nav">' + "".join(f'<a class="{"on" if i == active else ""}"><i></i>{k}</a>' for i, k in enumerate(L[lang]["keys"])) + "</nav>"

def pcards(lang):
    out = ""
    for o in OR:
        out += (f'<div class="hx-card"><div class="hx-c1"><b>{o["ref"][1:]} {bdi(o["customer"])}</b>{chip(o, True, lang)}</div>'
                f'<div class="hx-c2">{nextstep(o, lang)}</div><div class="hx-c3"><span>{esc(o["product"]).capitalize()} · {o["price_tnd"]:.0f} TND</span><span>{wait(waiting(o), lang)}</span></div></div>')
    return out

def M1(lang="en", dark=False):
    d = ' dir="rtl"' if L[lang]["dir"] == "rtl" else ""
    cls = "hx-ph hx-dark" if dark else "hx-ph"
    f = L[lang]["filters"]
    pl = "".join(f'<span class="hx-pill {"on" if i == 0 else ""}">{f[i]} <b>{[0, 5, 4][i]}</b></span>' for i in range(3))
    return (f'<div class="{cls}"{d}>{pbar(L[lang]["title"], False, lang)}{summary(lang)}<div class="hx-pillrow">{pl}</div>'
            f'<div class="hx-cards">{pcards(lang)}</div>{pnav(0, lang)}</div>')

def addr_check():
    rows = [("Street", "Not given", "bad", "Ask for it"), ("Landmark", "“9rib el jemaa”", "mid", "Not enough alone"), ("Zone", "Rural", "mid", "Check the courier covers it"), ("Phone", "Not given", "bad", "Ask for it")]
    r = "".join(f'<div class="hx-ac hx-ac-{c}"><span class="hx-dot"></span><b>{a}</b><span>{b}</span><em>{h}</em></div>' for a, b, c, h in rows)
    return f'<div class="hx-cd"><h4>Address check</h4>{r}<p class="hx-verdict"><b>Ask before you ship.</b> The question below covers all four.</p></div>'

def M2(dark=False):
    cls = "hx-ph hx-dark" if dark else "hx-ph"
    prev = (f'<div class="hx-cd hx-ready"><h4>Your message, ready to send</h4><p class="hx-dr" dir="auto">{esc(H["draft"]["text"])}</p><p class="hx-tr2"><b>FR</b> {esc(H["french_draft"])}</p><p class="hx-hint">Arabizi: Darija in Latin letters.</p></div>')
    cd = f'<div class="hx-cd"><h4>What the customer said</h4>{quotes()}</div><div class="hx-cd"><h4>Why this score</h4>{why_rows()}</div>'
    return (f'<div class="{cls}">{pbar("Order 2601 · Sami", True)}<div class="hx-ps"><div class="hx-ph1">{chip(OR[1])}<span>Casque Bluetooth · 220 TND · Rural zone</span></div>{addr_check()}{prev}{cd}</div>'
            f'<div class="hx-pact">{primary("Send to Sami")}<div class="hx-row2"><a class="hx-lnk">Approve the order</a><a class="hx-lnk hx-danger">Cancel the order</a></div></div></div>')

def M3():
    d = f'<div class="hx-cd hx-ready"><h4>Your reply, ready to send</h4><p class="hx-dr" dir="auto">{esc(H["draft"]["text"])}</p><p class="hx-tr2"><b>FR</b> {esc(H["french_draft"])}</p></div>'
    return f'<div class="hx-ph">{pbar("Sami · WhatsApp", True)}<div class="hx-ps">{quotes()}</div>{d}<div class="hx-pact">{primary("Send to Sami")}<div class="hx-row2"><a class="hx-lnk">Edit the reply</a></div></div></div>'

def M4():
    ex = "".join(f'<div class="hx-ex"><i>{n}</i>{esc(e)}</div>' for n, e in enumerate(PGS["add"]["examples"], 1))
    return (f'<div class="hx-ph">{pbar("Add an order")}<div class="hx-ps"><p class="hx-hint">{esc(PGS["add"]["subtitle"])}</p>{ex}<p class="hx-lab">Customer message</p>'
            f'<div class="hx-ta" dir="auto">Douar Ouled Ali, 9rib el jemaa. ama ghali chwaya<i class="hx-cur"></i></div><p class="hx-hint">Order details (optional) ▸</p></div>'
            f'<div class="hx-pact">{primary("Score this order")}</div>{pnav(2)}</div>')

def M5():
    I = DATA["impact"]
    return (f'<div class="hx-ph">{pbar("Money saved")}<div class="hx-ps"><div class="hx-cd"><h4>Estimated cost of wasted trips avoided</h4><p class="hx-big">{I["tnd_saved"]:.0f} <small>TND</small></p><p class="hx-warnline">Simulated on test orders, not real sales.</p></div>'
            f'<div class="hx-cd"><table class="hx-tab hx-kv"><tr><td>Refused at the door today</td><td class="r">{I["baseline"] * 100:.0f}%</td></tr><tr><td>Refused with Wasel</td><td class="r hx-ok">{I["projected"] * 100:.0f}%</td></tr><tr><td>Deliveries avoided</td><td class="r">{I["trips_avoided"]:.0f}</td></tr></table></div>'
            f'<div class="hx-cd"><h4>Today</h4><table class="hx-tab">' + "".join(f'<tr><td class="hx-n">{e["ts"]}</td><td>{esc(e["title"])} {bdi(e["who"])}</td></tr>' for e in DATA["activity"][:4]) + f'</table></div></div>{pnav(3)}</div>')

def M6():
    more = ["Activity log", "Quality checks", "Silent failures", "Live monitor", "AI call log"]
    rows = "".join(f'<div class="hx-more"><b>{n}</b><span>›</span></div>' for n in more)
    return f'<div class="hx-ph">{pbar("More")}<div class="hx-ps">{rows}<p class="hx-hint hx-mt">AI scoring is live. WhatsApp is off in demo mode. All data on these screens is synthetic.</p></div>{pnav(4)}</div>'

def phone():
    return [("M1 Orders list", M1()), ("M2 Case with one primary button", M2()), ("M3 Messages thread", M3()), ("M4 Add an order", M4()), ("M5 Metrics glance", M5()), ("M6 More", M6()),
            ("M7 Orders list in French", M1("fr")), ("M8 Orders list in Arabic (right to left)", M1("ar")), ("M9 Orders list, dark theme", M1("en", True)), ("M10 Case, dark theme", M2(True))]

def notes():
    return ('<div class="hx-notes"><h3>How this maps to the real project</h3><ul>'
            '<li><b>Same pages, same data.</b> Orders to check, WhatsApp messages, Add an order, Money saved, Activity log and the AI-health pages keep their real copy and their real data.</li>'
            '<li><b>What it keeps from Terminal Desk.</b> The rigid panel grid with hairline rules, dense tables, monospaced numbers, the counts strip, the shortcut row on desktop and the one-keystroke actions.</li>'
            '<li><b>What it takes from Review Desk.</b> A light, calm surface, the queue on the left beside the case, filter pills and cards that separate the evidence from the score.</li>'
            '<li><b>What changed after the client rounds.</b> No codes on screen, tier words that name the action (Hold, Ask, Ship), sentences instead of abbreviations, a highlighted word always explained, one primary button per screen, the synthetic-data notice shown once, dark as a switch.</li>'
            '<li><b>Codebase impact.</b> A panel grid component, a tier chip, theme tokens for light and dark, i18n with right-to-left layout, and a global search. The API is unchanged.</li>'
            '<li><b>Honest cost.</b> Less distinctive than the pure terminal, and it needs more width for sentences. French and Arabic cover the list screens only.</li></ul></div>')

# ------------------------------------------------------------------ stylesheet
CSS = f"""
body.hx,.hx-app,.hx-ph{{--g:{pal['ground']};--s:{pal['surface']};--ink:{pal['ink']};--mute:{pal['mute']};--p:{pal['primary']};--c:{pal['secondary']};--l:{pal['line']};--f:{pal['focus']};--t0:{COLS[0]};--t1:{COLS[1]};--t2:{COLS[2]};--t0b:{tint(COLS[0], .92)};--t1b:{tint(COLS[1], .90)};--t2b:{tint(COLS[2], .90)};--pb:{tint(pal['primary'], .90)};--hl:#FFE9A8;--hlt:#17212B;--onp:#FFFFFF;--bar:{tint(pal['primary'], .80)}}}
.hx-dark{{--g:{DARK['ground']};--s:{DARK['surface']};--ink:{DARK['ink']};--mute:{DARK['mute']};--p:{DARK['primary']};--c:#8FB4FF;--l:{DARK['line']};--f:{DARK['primary']};--t0:{DARK['t0']};--t1:{DARK['t1']};--t2:{DARK['t2']};--t0b:#3A2124;--t1b:#3A3020;--t2b:#1F3629;--pb:#173A38;--hl:#5A4A12;--hlt:#FFF1C2;--onp:#0B1F1E;--bar:#245A56}}
body.hx{{background:#ECEFEC;color:var(--ink);font:14px/1.45 var(--ui)}}
.bb-top{{background:#fff;border-bottom:1px solid var(--l);color:var(--ink);font-family:var(--ui)}}.bb-top span{{color:var(--mute)}}.bb-top nav a{{color:var(--p);padding:4px 10px;text-decoration:none;font-weight:600}}
.bb-sec>h2{{font:700 22px var(--ui);color:var(--ink)}}
.hx-lock{{display:inline-flex;align-items:center;gap:12px}}.hx-wm{{display:inline-flex;align-items:baseline;gap:10px;font-family:var(--ui)}}.hx-wm b{{font-weight:700;font-size:26px}}.hx-wm-ar{{font:600 26px var(--ar)}}
.hx-app{{width:1280px;height:800px;background:var(--g);color:var(--ink);display:flex;flex-direction:column;font:13.5px/1.45 var(--ui)}}.hx-app *,.hx-ph *{{box-sizing:border-box}}
.hx-bar{{display:flex;align-items:center;gap:16px;height:52px;padding:0 14px;background:var(--s);border-bottom:1px solid var(--l);flex:none}}.hx-bn{{font:700 17px var(--ui);color:var(--ink)}}.hx-bar nav{{display:flex;gap:2px;margin-left:8px}}.hx-bar nav a{{padding:15px 12px;font-weight:600;color:var(--mute);border-bottom:3px solid transparent}}.hx-bar nav a.on{{color:var(--p);border-bottom-color:var(--p)}}
.hx-search{{margin-left:auto;border:1px solid var(--l);background:var(--g);color:var(--mute);padding:8px 14px;min-width:300px}}.hx-lang{{font:600 12px var(--ui);color:var(--mute)}}.hx-lang b{{background:var(--p);color:var(--onp);padding:1px 6px}}.hx-theme{{display:flex;border:1px solid var(--l);font:600 12px var(--ui)}}.hx-theme i{{font-style:normal;padding:5px 10px;color:var(--mute)}}.hx-theme i.on{{background:var(--p);color:var(--onp)}}
.hx-note{{padding:5px 14px;background:var(--pb);color:var(--ink);border-bottom:1px solid var(--l);font-size:12.5px;flex:none}}.hx-note b{{color:var(--p)}}.hx-sub{{padding:6px 14px;color:var(--mute);border-bottom:1px solid var(--l);font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:none}}
.hx-main{{flex:1;min-height:0;padding:2px;background:var(--l);display:flex;flex-direction:column;gap:2px}}
.hx-sum{{display:flex;align-items:center;gap:10px;padding:8px 14px;background:var(--s);font:600 14px var(--ui);color:var(--ink);flex:none}}
.hx-p{{background:var(--s);padding:0;overflow:hidden;min-width:0;display:flex;flex-direction:column;border-top:3px solid var(--p)}}.hx-p h3{{margin:0;padding:9px 14px;font:700 14px var(--ui);color:var(--ink);border-bottom:1px solid var(--l);display:flex;justify-content:space-between;align-items:center}}.hx-p h3 em{{font:600 12px var(--ui);font-style:normal;color:var(--mute)}}.hx-pb{{padding:10px 14px;min-height:0;overflow:hidden}}
.hx-grid1{{flex:1;display:grid;grid-template-columns:420px 1fr;grid-template-rows:1.25fr 1fr .5fr;gap:2px;background:var(--l);min-height:0}}.hx-a{{grid-row:1/4}}.hx-b,.hx-c,.hx-d{{grid-column:2}}
.hx-grid2{{flex:1;display:grid;grid-template-columns:1.1fr 1fr;grid-template-rows:1fr 1.1fr;gap:2px;background:var(--l);min-height:0}}
.hx-grid3{{flex:1;display:grid;grid-template-columns:1.35fr 1fr .75fr;gap:2px;background:var(--l);min-height:0}}.hx-grid4{{flex:1;display:grid;grid-template-columns:1.2fr 1fr;gap:2px;background:var(--l);min-height:0}}
.hx-grid5{{flex:1;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:2px;background:var(--l);min-height:0}}.hx-r3{{grid-row:1/3;grid-column:2}}
.hx-grid6{{flex:1;display:grid;grid-template-columns:1fr 1fr 1.35fr;grid-template-rows:1fr 1fr;gap:2px;background:var(--l);min-height:0}}.hx-h3{{grid-row:1/3;grid-column:3}}.hx-grid7{{flex:1;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:2px;background:var(--l);min-height:0}}
.hx-pills{{display:flex;gap:6px;margin-bottom:8px;flex-wrap:wrap}}.hx-pill{{display:inline-flex;gap:5px;align-items:center;border:1px solid var(--l);background:var(--s);padding:5px 8px;font:600 12px var(--ui);color:var(--ink);white-space:nowrap}}.hx-pill b{{font-family:var(--data)}}.hx-pill.on{{background:var(--p);border-color:var(--p);color:var(--onp)}}
.hx-ql{{display:flex;flex-direction:column}}.hx-q{{padding:9px 10px;border-bottom:1px solid var(--l);border-left:3px solid transparent}}.hx-q.cur{{background:var(--pb);border-left-color:var(--p)}}.hx-q1{{display:flex;align-items:center;gap:8px}}.hx-q1 b{{font-size:14.5px;flex:1}}.hx-q2{{display:flex;justify-content:space-between;color:var(--mute);font-size:12.5px;margin-top:2px}}.hx-n{{font-family:var(--data);font-size:12.5px;color:var(--mute)}}
.hx-t{{display:inline-flex;align-items:center;gap:5px;padding:2px 8px;font:700 12.5px var(--ui);white-space:nowrap}}.hx-t b{{font-family:var(--data);font-weight:700}}.hx-t0{{color:var(--t0);background:var(--t0b)}}.hx-t1{{color:var(--t1);background:var(--t1b)}}.hx-t2{{color:var(--t2);background:var(--t2b)}}.hx-gl{{flex:none}}
.hx-tab{{width:100%;border-collapse:collapse}}.hx-tab th{{text-align:left;color:var(--mute);font:600 12px var(--ui);padding:4px 10px 4px 0;border-bottom:1px solid var(--l);white-space:nowrap}}.hx-tab td{{padding:6px 10px 6px 0;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:260px;border-bottom:1px solid var(--l)}}.hx-tab .r{{text-align:right;padding-right:0}}.hx-tab .r+th,.hx-tab .r+td{{padding-left:14px}}.hx-tab tr.cur td{{background:var(--pb)}}
.hx-kv td:first-child{{color:var(--mute)}}.hx-tot td{{font-weight:700;border-top:2px solid var(--l)}}.hx-up{{color:var(--t0);font-family:var(--data)}}.hx-ok{{color:var(--t2);font-weight:600}}.hx-pv{{color:var(--mute);max-width:230px}}.hx-why td{{border-bottom:0;padding:4px 10px 4px 0}}.hx-bc{{width:90px}}.hx-bc i{{display:block;height:6px;background:var(--bar)}}
.hx-cl{{margin:0 0 8px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 14px 0}}.hx-grid2 + .x{{}}
.hx-bub{{margin:0 0 6px;padding:6px 10px;background:var(--g);border-left:3px solid var(--c)}}.hx-bub time{{font:11.5px var(--data);color:var(--mute)}}.hx-bub p{{margin:2px 0 0;color:var(--ink)}}mark.hx-hl{{background:var(--hl);color:var(--hlt);padding:0 3px}}
.hx-lab{{font:600 12px var(--ui);color:var(--mute);margin:8px 0 3px}}.hx-ul{{margin:0;padding-left:18px;color:var(--ink);font-size:13px}}.hx-ul li{{margin-bottom:3px}}.hx-hint{{color:var(--mute);font:12.5px var(--ui);margin:4px 0}}
.hx-act{{display:flex;gap:14px;margin-top:10px;align-items:center;flex-wrap:wrap}}.hx-btn{{display:inline-flex;align-items:center;gap:9px;background:var(--p);color:var(--onp);padding:9px 18px;font:700 14px var(--ui);border:1px solid var(--p)}}.hx-btn i{{font:600 11px var(--data);font-style:normal;background:rgba(255,255,255,.22);padding:1px 6px}}.hx-lnk{{color:var(--p);font:600 13.5px var(--ui);text-decoration:underline;text-underline-offset:3px;padding:6px 2px}}.hx-danger{{color:var(--t0)}}
.hx-keys{{display:flex;gap:2px;padding:4px 8px;background:var(--s);border-top:1px solid var(--l);flex:none;align-items:center}}.hx-kl{{font:600 12px var(--ui);color:var(--mute);margin-right:8px}}.hx-k{{font:600 12px var(--ui);color:var(--ink);padding:3px 8px}}.hx-k i{{font:600 11px var(--data);font-style:normal;background:var(--g);border:1px solid var(--l);padding:0 5px;margin-right:5px}}.hx-k.on{{background:var(--pb);color:var(--p)}}.hx-kr{{margin-left:auto;font:600 12px var(--ui)}}.hx-kr i{{font:600 11px var(--data);font-style:normal;background:var(--g);border:1px solid var(--l);padding:0 5px;margin-right:5px}}
.hx-tabs{{display:flex;gap:2px;margin-bottom:6px}}.hx-tabs span{{padding:4px 12px;border:1px solid var(--l);font:600 12.5px var(--ui);color:var(--mute)}}.hx-tabs span.on{{background:var(--p);border-color:var(--p);color:var(--onp)}}.hx-dr{{margin:0 0 6px;border:1px solid var(--l);padding:8px 10px;line-height:1.55;background:var(--g)}}.hx-tr2{{margin:0 0 6px;color:var(--ink);font-size:12.5px;line-height:1.5}}.hx-tr2 b{{background:var(--c);color:#fff;padding:0 5px;margin-inline-end:6px;font-size:11.5px}}
.hx-warn,.hx-err,.hx-okb{{padding:8px 12px;font:600 13px var(--ui);margin-bottom:8px}}.hx-warn{{background:var(--t1b);color:var(--t1)}}.hx-err{{background:var(--t0b);color:var(--t0)}}.hx-okb{{background:var(--t2b);color:var(--t2);margin:0;flex:none}}.hx-reply{{margin-top:8px;border:1px solid var(--p);padding:8px 10px}}.hx-reply b{{font:700 12px var(--ui);color:var(--p)}}.hx-reply p{{margin:4px 0 0}}
.hx-ta{{border:1px solid var(--p);padding:9px 12px;min-height:120px;font-size:14px;line-height:1.6;background:var(--g)}}.hx-cur{{display:inline-block;width:2px;height:16px;background:var(--p);margin-left:2px;vertical-align:-3px}}.hx-ol{{margin:0;padding-left:20px}}.hx-ol li{{margin-bottom:6px}}.hx-ex{{border:1px solid var(--l);padding:8px 10px;margin-bottom:5px;background:var(--g)}}.hx-ex i{{font:600 11px var(--data);font-style:normal;background:var(--c);color:#fff;padding:1px 6px;margin-right:8px}}.hx-mt{{margin-top:12px}}
.hx-big{{margin:0 0 4px;font:700 44px var(--ui);color:var(--ink)}}.hx-big small{{font-size:18px;color:var(--mute)}}.hx-big2{{font:700 20px var(--ui);margin:14px 0 4px}}.hx-load{{margin:0 0 10px}}.hx-prog{{display:inline-block;width:160px;height:8px;background:var(--l);vertical-align:middle}}.hx-prog i{{display:block;width:50%;height:100%;background:var(--p)}}.hx-skel{{height:34px;background:var(--g);margin-bottom:6px;border:1px solid var(--l)}}.hx-warnline{{color:var(--t1);font-weight:600;margin:4px 0 0}}
/* brand sheet */
.hx-brand{{display:grid;grid-template-columns:repeat(2,minmax(480px,1fr));gap:2px;width:100%;max-width:1180px;background:var(--l);border:2px solid var(--l)}}.hx-brand>section{{background:var(--s);padding:18px}}.hx-wide{{grid-column:1/-1}}.hx-bh{{margin:0 0 10px;font:700 15px var(--ui);color:var(--ink);border-bottom:2px solid var(--p);padding-bottom:6px;display:inline-block}}.hx-pos{{margin:0;max-width:90ch;font-size:15px}}.hx-note2{{color:var(--mute);margin:10px 0 0;font-size:12.5px}}
.hx-logos{{display:grid;grid-template-columns:repeat(3,1fr);gap:2px;background:var(--l)}}.hx-lg{{display:flex;flex-direction:column;gap:8px;align-items:center;justify-content:center;background:var(--g);padding:14px;min-height:110px}}.hx-lg span{{font:600 11.5px var(--ui);color:var(--mute)}}.hx-inv{{background:var(--p)}}.hx-inv span{{color:#fff}}.hx-lg:nth-child(5){{flex-direction:row;flex-wrap:wrap}}
.hx-sws{{display:grid;grid-template-columns:repeat(5,1fr);gap:4px;margin-bottom:12px}}.hx-sw{{padding:9px 8px;min-height:80px;display:flex;flex-direction:column;justify-content:flex-end;font:12px var(--data);border:1px solid var(--l)}}.hx-sw b{{font:700 12.5px var(--ui)}}.hx-sw em{{font-style:normal;opacity:.85;font-family:var(--ui)}}
.hx-type{{display:flex;flex-direction:column;gap:6px}}.hx-sp1{{font:700 34px var(--ui)}}.hx-sp2{{font:600 22px var(--data)}}.hx-sp3{{font:32px var(--ar)}}.hx-spp{{margin:0;color:var(--mute);font-size:12.5px}}.hx-mono{{font-family:var(--data);color:var(--ink)}}
.hx-trs{{display:flex;flex-direction:column;gap:10px;margin-bottom:14px}}.hx-tr{{display:flex;gap:14px;align-items:flex-start}}.hx-tr .hx-t{{min-width:120px}}.hx-tr p{{margin:0;color:var(--mute);font-size:12.5px}}.hx-tr i{{font-style:normal;color:var(--ink)}}.hx-sts{{display:flex;flex-wrap:wrap;gap:6px}}.hx-st{{border:1px solid var(--p);color:var(--p);padding:3px 12px;font:600 12.5px var(--ui)}}
.hx-comps{{display:flex;gap:12px;flex-wrap:wrap;align-items:center}}
.hx-notes{{max-width:900px;background:var(--s);border:1px solid var(--l);padding:6px 22px 14px;color:var(--ink);font:14px/1.55 var(--ui)}}.hx-notes h3{{font:700 16px var(--ui)}}.hx-notes li{{margin:7px 0}}
/* phone */
.hx-ph{{width:390px;height:844px;background:var(--g);color:var(--ink);display:flex;flex-direction:column;font:15px/1.45 var(--ui)}}.hx-ph .hx-hint{{font-size:13.5px}}
.hx-sb{{display:flex;justify-content:space-between;padding:12px 24px 4px;font:700 13px var(--ui);background:var(--s)}}.hx-pbar{{display:flex;align-items:center;gap:10px;padding:8px 14px 10px;background:var(--s);border-bottom:1px solid var(--l)}}.hx-pbar>b{{flex:1;font:700 18px var(--ui)}}.hx-back{{font:400 30px var(--ui);color:var(--p);width:30px;line-height:1}}.hx-pl2{{font:600 11px var(--ui);color:var(--mute);white-space:nowrap}}.hx-pl2 b{{background:var(--p);color:var(--onp);padding:0 4px}}
.hx-ph .hx-sum{{font-size:13.5px;line-height:1.35;padding:10px 14px;border-bottom:1px solid var(--l)}}.hx-pillrow{{display:flex;gap:6px;padding:8px 12px;background:var(--s);border-bottom:1px solid var(--l);overflow:hidden}}.hx-pillrow .hx-pill{{flex:1;justify-content:center;white-space:normal;text-align:center;line-height:1.2;padding:6px 6px;min-height:48px;font-size:12.5px;flex-direction:column;gap:2px}}
.hx-cards{{flex:1;overflow:hidden;display:flex;flex-direction:column;gap:1px;background:var(--l)}}.hx-card{{background:var(--s);padding:10px 14px;min-height:76px}}.hx-c1{{display:flex;justify-content:space-between;align-items:center;gap:8px}}.hx-c1 b{{font-size:16px}}.hx-c2{{color:var(--ink);font-size:14px;margin:3px 0 2px}}.hx-c3{{display:flex;justify-content:space-between;color:var(--mute);font-size:13px}}
.hx-ps{{flex:1;overflow:hidden;padding:10px 12px;display:flex;flex-direction:column;gap:10px}}.hx-ph1{{display:flex;flex-direction:column;gap:4px;align-items:flex-start}}.hx-ph1>span:last-child{{color:var(--mute)}}.hx-cd{{background:var(--s);border:1px solid var(--l);border-top:3px solid var(--p);padding:9px 12px}}.hx-cd h4{{margin:0 0 6px;font:700 14px var(--ui)}}.hx-ready{{border-top-color:var(--c)}}
.hx-ac{{display:grid;grid-template-columns:12px 80px 1fr;gap:2px 8px;align-items:center;padding:5px 0;border-bottom:1px solid var(--l)}}.hx-ac b{{font-size:13.5px}}.hx-ac span:nth-child(3){{color:var(--ink);font-size:13.5px}}.hx-ac em{{grid-column:3;font-style:normal;font-size:12.5px;color:var(--mute)}}.hx-dot{{width:10px;height:10px;border-radius:50%}}.hx-ac-bad .hx-dot{{background:var(--t0)}}.hx-ac-mid .hx-dot{{background:var(--t1)}}.hx-ac-ok .hx-dot{{background:var(--t2)}}.hx-ac-bad em{{color:var(--t0)}}.hx-verdict{{margin:8px 0 0;font-size:13.5px}}.hx-verdict b{{color:var(--t0)}}
.hx-pact{{padding:10px 12px 22px;border-top:1px solid var(--l);display:flex;flex-direction:column;gap:6px;background:var(--s)}}.hx-pact .hx-btn{{justify-content:center;min-height:54px;font-size:16px;width:100%}}.hx-row2{{display:flex;justify-content:space-around}}.hx-row2 .hx-lnk{{min-height:44px;display:flex;align-items:center}}
.hx-nav{{display:flex;padding:4px 2px 22px;background:var(--s);border-top:1px solid var(--l)}}.hx-nav a{{flex:1;text-align:center;padding:6px 0 4px;color:var(--mute);font:600 12px var(--ui);min-height:52px;display:flex;flex-direction:column;align-items:center;gap:4px}}.hx-nav a i{{width:22px;height:22px;border:2px solid currentColor}}.hx-nav a.on{{color:var(--p)}}.hx-nav a.on i{{background:var(--p)}}
.hx-more{{display:flex;align-items:center;background:var(--s);border:1px solid var(--l);padding:14px 14px;min-height:56px}}.hx-more b{{flex:1;font:600 15.5px var(--ui)}}.hx-more span{{color:var(--mute)}}
.hx-qt .hx-bub{{font-size:14.5px}}
"""
