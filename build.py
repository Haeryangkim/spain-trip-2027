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
out = os.path.join(ROOT, "index.html")
with open(out, "w", encoding="utf-8") as f: f.write(html)
print(f"wrote {out} ({os.path.getsize(out)//1024} KB), days={len(trip.get('days',[]))}, restaurants={len(trip.get('restaurants',[]))}")
