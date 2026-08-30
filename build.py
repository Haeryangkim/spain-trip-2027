#!/usr/bin/env python3
"""Build index.html from data/itinerary.json + site/template.html + assets/ (single self-contained file)."""
import base64, json, os, datetime, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
def read(p, mode="r"):
    with open(os.path.join(ROOT, p), mode) as f: return f.read()
src = sys.argv[1] if len(sys.argv) > 1 else "data/itinerary.json"
trip = json.load(open(os.path.join(ROOT, src), encoding="utf-8"))
import re as _re
def _norm(n): return _re.sub(r"\s+", " ", _re.sub(r"\(.*?\)", "", n)).strip().lower()
_seen = {}
for r in trip.get("restaurants", []):
    k = _norm(r["name"])
    if k in _seen:
        if not _seen[k].get("used_on_day") and r.get("used_on_day"): _seen[k].update(r)
        continue
    _seen[k] = r
trip["restaurants"] = list(_seen.values())
# ---- representative photos (Wikipedia / Wikimedia Commons) ----
imap = json.loads(read("data/image_map.json"))
credits_all = json.loads(read("assets/image_credits.json"))
import re as _re2
def _img_for_block(b):
    if b.get("type") == "sight":
        s = imap["sights"].get(b.get("name_en") or "") or imap["sights"].get(b.get("name") or "")
        if s: return s
    if b.get("type") == "meal":
        for rn, slug in imap["restaurants"].items():
            if rn.lower() in b.get("name", "").lower(): return slug
    for rule in imap["keywords"]:
        pat, slug = rule[0], rule[1]
        types = rule[2] if len(rule) > 2 else None
        if types and b.get("type") not in types: continue
        if _re2.search(pat, b.get("name", ""), _re2.I): return slug
    return None
used_slugs = set()
for d in trip.get("days", []):
    for b in d.get("blocks", []):
        s = _img_for_block(b)
        if s: b["img"] = s; used_slugs.add(s)
for r in trip.get("restaurants", []):
    s = imap["restaurants"].get(r["name"])
    if not s:
        for rn, slug in imap["restaurants"].items():
            if rn.lower() in r["name"].lower(): s = slug; break
    if s: r["img"] = s; used_slugs.add(s)
trip["city_hero"] = imap["city_hero"]
used_slugs |= set(imap["city_hero"].values())
images, img_bytes = {}, 0
for slug in sorted(used_slugs):
    p = f"assets/img/{slug}.jpg"
    if not os.path.exists(os.path.join(ROOT, p)):
        print(f"  ! missing image {p}"); continue
    raw = read(p, "rb"); img_bytes += len(raw)
    images[slug] = "data:image/jpeg;base64," + base64.b64encode(raw).decode()
credits = [dict(slug=s, **{k: v for k, v in credits_all.get(s, {}).items() if k in ("author", "license", "url", "article")})
           for s in sorted(images)]

metas = json.loads(read("assets/base_meta.json"))
bases = []
for m in metas:
    b64 = base64.b64encode(read(f"assets/base_{m['name']}.jpg", "rb")).decode()
    bases.append({"name": m["name"], "bounds": m["bounds"], "zoom": m["zoom"], "dataUri": f"data:image/jpeg;base64,{b64}"})
def js(obj):  # safe for inline <script>
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")
html = read("site/template.html")
html = html.replace("/*__LEAFLET_CSS__*/", read("assets/leaflet.min.css"))
html = html.replace("/*__TRIP__*/{}", js(trip))
html = html.replace("/*__BASES__*/[]", js(bases))
html = html.replace('/*__BUILT__*/""', js(datetime.date.today().isoformat()))
html = html.replace("/*__IMAGES__*/{}", js(images))
html = html.replace("/*__CREDITS__*/[]", js(credits))
out = os.path.join(ROOT, "index.html")
with open(out, "w", encoding="utf-8") as f: f.write(html)
blocks_with_img = sum(1 for d in trip.get("days", []) for b in d.get("blocks", []) if b.get("img"))
rest_with_img = sum(1 for r in trip.get("restaurants", []) if r.get("img"))
print(f"wrote {out} ({os.path.getsize(out)//1024} KB), days={len(trip.get('days',[]))}, "
      f"restaurants={len(trip.get('restaurants',[]))}, images={len(images)} ({img_bytes//1024} KB) "
      f"→ blocks {blocks_with_img}, cards {rest_with_img}")
