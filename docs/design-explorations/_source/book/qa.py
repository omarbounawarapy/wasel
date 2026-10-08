"""T0.8: static QA harness. Run from the repo root:
    python3 docs/design-explorations/_source/book/qa.py [direction-id ...]

Checks (per built file): size budget, offline (no external fetches), fonts embedded, registry tokens used,
forbidden shared vocabulary absent, tier name + glyph present, Arabic present with dir attributes, contrast of key pairs.
Browser-level checks (tap targets, overflow, screenshots) are run separately in Chrome.
"""
import os, re, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from kit import *
from kit import _lum

BUDGET = 3 * 1024 * 1024
FORBIDDEN = [r"\bHigh\b", r"\bMedium\b", r"\bLow\b"]  # the primitives the owner asked not to reuse

def visible_text(page):
    p = re.sub(r"<style.*?</style>", "", page, flags=re.S)
    p = re.sub(r"<script.*?</script>", "", p, flags=re.S)
    return re.sub(r"<[^>]+>", " ", p)

def check(did):
    d = direction(did)
    path = ROOT + f"book/{did}.html"
    out = []
    if not os.path.exists(path): return [("FAIL", "file", "not built")]
    page = open(path).read()
    size = len(page.encode())
    out.append(("PASS" if size <= BUDGET else "FAIL", "size", f"{size/1024:.0f} KB (budget {BUDGET//1024} KB)"))
    ext = [u for u in re.findall(r'(?:src|href)="(https?://[^"]+)"|url\((https?://[^)]+)\)', page) if any(u)]
    ext = [a or b for a, b in ext]
    hrefs_ok = all(not re.search(r"<(link|script|img)[^>]+(src|href)=[\"']https?://", page) for _ in [0])
    out.append(("PASS" if hrefs_ok and not any("url(http" in x for x in ext) else "FAIL", "offline", "no external stylesheet, script, image or font"))
    n_ff = page.count("@font-face")
    out.append(("PASS" if n_ff >= 4 else "FAIL", "fonts", f"{n_ff} embedded faces"))
    n = did.split("-")[0]
    out.append(("PASS" if all(f"d{n}-{r}" in page for r in ("ui", "data", "arabic")) else "FAIL", "font roles", f"d{n}-ui/data/arabic referenced"))
    low = page.lower()
    miss = [v for k, v in {**d["pal"], "t0": d["tiers"]["colors"][0], "t1": d["tiers"]["colors"][1], "t2": d["tiers"]["colors"][2]}.items() if v.lower() not in low]
    out.append(("PASS" if not miss else "WARN", "tokens used", "all registry colours appear" if not miss else f"unused: {miss}"))
    txt = visible_text(page)
    bad = [pat for pat in FORBIDDEN if re.search(pat, txt)]
    out.append(("PASS" if not bad else "FAIL", "no shared primitives", "no High/Medium/Low as tier words" if not bad else f"found {bad}"))
    names = d["tiers"]["names"]
    out.append(("PASS" if all(nm in txt for nm in names) else "FAIL", "tier vocabulary", "all three tier names visible"))
    out.append(("PASS" if re.search(r"[؀-ۿ]", txt) and 'dir="auto"' in page else "FAIL", "arabic", "Arabic text present with dir=auto"))
    out.append(("PASS" if "Synthetic" in txt or "synthetic" in txt else "FAIL", "synthetic note", "visible"))
    # contrast
    p = d["pal"]; pairs = [("ink on ground", p["ink"], p["ground"], 4.5), ("ink on surface", p["ink"], p["surface"], 4.5), ("mute on surface", p["mute"], p["surface"], 4.5), ("mute on ground", p["mute"], p["ground"], 4.5)]
    dark = _lum(p["ground"]) < 0.2
    for i, c in enumerate(d["tiers"]["colors"]):
        pairs.append((f"tier {names[i]} on surface", c, p["surface"], 4.5 if not dark else 4.5))
    for label, fg, bg, need in pairs:
        r = contrast(fg, bg)
        out.append(("PASS" if r >= need else "FAIL", "contrast", f"{label}: {r:.2f}:1 (need {need})"))
    return out

if __name__ == "__main__":
    ids = sys.argv[1:] or [f[:-5] for f in sorted(os.listdir(ROOT + "book")) if f.endswith(".html") and f != "index.html"]
    worst = 0
    for did in ids:
        print(f"\n== {did}")
        for status, rule, msg in check(did):
            print(f"  {status:4s} {rule:20s} {msg}")
            worst = max(worst, {"PASS": 0, "WARN": 1, "FAIL": 2}[status])
    sys.exit(worst)
