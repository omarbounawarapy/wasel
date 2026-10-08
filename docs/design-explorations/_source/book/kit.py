"""Neutral helpers shared by every direction. They carry NO styling: each direction supplies its own CSS.

Rule (BRIEF-AND-PLAN.md, T0.6): no two directions may share a CSS class prefix or token name, so every
direction namespaces its classes with its own prefix (e.g. d04-) and its own CSS custom properties.
"""
import html, json, re, base64, os

ROOT = "docs/design-explorations/"
REG = json.load(open(ROOT + "registry.json"))
DATA = json.load(open(ROOT + "dataset.json"))
CONTENT = json.load(open(ROOT + "content.json"))
FONTS = json.load(open(ROOT + "_fonts/manifest.json"))["fonts"]

def esc(s): return html.escape("" if s is None else str(s))
def bdi(s): return f'<bdi dir="auto">{esc(s)}</bdi>'
def direction(did): return next(r for r in REG if r["id"] == did)

def age(m):
    return f"{m // 60} h {m % 60:02d}" if m >= 60 else f"{m} min"

def tier_index(raw):  # raw tier from the API -> 0 highest, 1 middle, 2 lowest
    return {"high": 0, "medium": 1, "low": 2}[raw]

def orders(): return DATA["orders"]
def hero(): return DATA["hero"]
def waiting(o): return DATA["waiting_minutes"][o["ref"]]

def hl(text, phrases, cls):
    """wrap each phrase found in text with <mark class=cls>; text is escaped first"""
    out = esc(text)
    for p in phrases:
        out = out.replace(esc(p), f'<mark class="{cls}">{esc(p)}</mark>')
    return out

# ----- SVG helpers (colours are passed in by the direction, never defaulted here)
def sparkline(vals, w, h, stroke, fill=None, sw=2):
    mx, mn, n = max(vals), min(vals), len(vals)
    pts = [(i * w / (n - 1), h - (v - mn) / ((mx - mn) or 1) * (h - 8) - 4) for i, v in enumerate(vals)]
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    area = f'<path d="{d} L{w} {h} L0 {h} Z" fill="{fill}"/>' if fill else ""
    return f'<svg viewBox="0 0 {w} {h}" width="100%" height="{h}" preserveAspectRatio="none" aria-hidden="true">{area}<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/></svg>'

def bar(pct, w, h, fg, bg, r=0):
    return f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" aria-hidden="true"><rect width="{w}" height="{h}" rx="{r}" fill="{bg}"/><rect width="{max(0, min(1, pct)) * w:.1f}" height="{h}" rx="{r}" fill="{fg}"/></svg>'

# ----- fonts (T0.4 output): embed as base64 under direction-unique aliases
def font_css(did):
    d = direction(did)
    n = did.split("-")[0]
    css, seen = [], set()
    for role, fam in d["fonts"].items():
        alias = f"d{n}-{role}"
        info = FONTS[fam]
        for face in info["faces"]:
            key = (alias, face["weight"], face["subset"])
            if key in seen: continue
            seen.add(key)
            b64 = base64.b64encode(open(ROOT + "_fonts/" + face["file"], "rb").read()).decode()
            css.append(f"@font-face{{font-family:'{alias}';font-weight:{face['weight']};font-style:normal;font-display:swap;"
                       f"src:url(data:font/woff2;base64,{b64}) format('woff2');unicode-range:{face['range']}}}")
    return "\n".join(css)

def stacks(did):
    n = did.split("-")[0]
    return dict(ui=f"'d{n}-ui','d{n}-arabic',system-ui,sans-serif",
                data=f"'d{n}-data','d{n}-arabic',ui-monospace,monospace",
                arabic=f"'d{n}-arabic',system-ui,sans-serif")

# ----- contrast
def _lum(hexc):
    h = hexc.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

def tint(hexc, amount, base="#FFFFFF"):
    """mix hexc toward base by amount (0..1 of base); used for tier background tints"""
    h = hexc.lstrip("#"); b = base.lstrip("#")
    mix = lambda i: round(int(h[i:i + 2], 16) * (1 - amount) + int(b[i:i + 2], 16) * amount)
    return "#%02X%02X%02X" % (mix(0), mix(2), mix(4))

# ----- neutral frames (structure only)
def phone(inner, w=390, h=844):
    return f'<div class="frame-phone" style="width:{w}px;height:{h}px">{inner}</div>'
def desktop(inner, w=1280, h=800):
    return f'<div class="frame-desktop" style="width:{w}px;height:{h}px">{inner}</div>'

FRAME_CSS = """
.frame-phone{position:relative;overflow:hidden;border-radius:42px;box-shadow:0 0 0 9px #101114,0 0 0 11px #3a3d44,0 18px 40px rgba(0,0,0,.28);flex:none}
.frame-desktop{position:relative;overflow:hidden;border-radius:8px;box-shadow:0 0 0 1px rgba(0,0,0,.18),0 12px 30px rgba(0,0,0,.18);flex:none}
"""
