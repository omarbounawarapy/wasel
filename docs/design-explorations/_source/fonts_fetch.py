"""T0.4: downloads every registry font as woff2 (latin + arabic subsets) into docs/design-explorations/_fonts.

Run from the repo root: python3 docs/design-explorations/_source/fonts_fetch.py
Writes _fonts/manifest.json: family -> [{weight, subset, file, bytes, range}] and a report of any family that failed.
Uses the public Google Fonts CSS endpoint with a modern browser user agent so it serves woff2.
"""
import json, os, re, urllib.request, urllib.parse, hashlib

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
OUT = "docs/design-explorations/_fonts"
os.makedirs(OUT, exist_ok=True)
R = json.load(open("docs/design-explorations/registry.json"))

need = {}  # family -> set(roles)
for r in R:
    for role, fam in r["fonts"].items():
        need.setdefault(fam, set()).add(role)

def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return data if binary else data.decode("utf-8")

def css_for(fam, weights):
    q = urllib.parse.quote(fam).replace("%20", "+")
    url = f"https://fonts.googleapis.com/css2?family={q}:wght@{';'.join(map(str, weights))}&display=swap"
    return get(url)

manifest, failed = {}, []
for fam, roles in sorted(need.items()):
    css = None
    for weights in ([400, 600, 700], [400, 700], [400], [700]):
        try:
            css = css_for(fam, weights)
            used = weights
            break
        except Exception:
            continue
    if css is None:
        failed.append(fam)
        continue
    want = {"latin", "arabic"} if "arabic" in roles else {"latin"}
    # latin-ext covers accents such as the ones French uses beyond latin-1; keep it small: not needed for the mockups
    blocks = re.findall(r"/\* ([\w-]+) \*/\s*@font-face \{(.*?)\}", css, flags=re.S)
    seen, entries = {}, []
    for subset, body in blocks:
        if subset not in want:
            continue
        weight = re.search(r"font-weight:\s*(\d+)", body).group(1)
        um = re.search(r"url\((https:[^)]+\.woff2)\)", body)
        if not um: continue
        url = um.group(1)
        rng = re.search(r"unicode-range:\s*([^;]+);", body).group(1)
        if url not in seen:
            slug = re.sub(r"[^a-z0-9]+", "-", fam.lower()).strip("-")
            os.makedirs(f"{OUT}/{slug}", exist_ok=True)
            fn = f"{slug}/{subset}-{hashlib.md5(url.encode()).hexdigest()[:6]}.woff2"
            open(f"{OUT}/{fn}", "wb").write(get(url, True))
            seen[url] = fn
        entries.append(dict(weight=int(weight), subset=subset, file=seen[url], bytes=os.path.getsize(f"{OUT}/{seen[url]}"), range=rng,
                            variable=sum(1 for e in blocks if re.search(re.escape(url), e[1])) > 1))
    manifest[fam] = dict(roles=sorted(roles), weights_available=used, faces=entries)
    print(f"{fam:30s} weights {used}  files {len(set(e['file'] for e in entries))}  bytes {sum(os.path.getsize(f'{OUT}/{f}') for f in set(e['file'] for e in entries))}")

json.dump(dict(fonts=manifest, failed=failed), open(f"{OUT}/manifest.json", "w"), indent=1)
print("FAILED:", failed)
