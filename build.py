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
        # 느슨한 매칭: name_en 과 매핑 키가 서로 포함 관계면 가장 긴 키 채택
        ne = (b.get("name_en") or "").lower()
        best = None
        for key, slug in imap["sights"].items():
            k = key.lower().split(" (")[0]
            if len(k) >= 6 and (k in ne or ne in k):
                if best is None or len(k) > len(best[0]): best = (k, slug)
        if best: return best[1]
    if b.get("type") == "meal":
        for rn, slug in imap["restaurants"].items():
            if rn.lower() in b.get("name", "").lower(): return slug
    for rule in imap["keywords"]:
        pat, slug = rule[0], rule[1]
        types = rule[2] if len(rule) > 2 else None
        if types and b.get("type") not in types: continue
        if _re2.search(pat, b.get("name", ""), _re2.I): return slug
    return None
def _gmaps(name, area="", lat=None, lng=None):
    """구글맵 검색 URL (좌표로 지도 중심을 잡고 상호로 검색)."""
    import urllib.parse
    q = _re2.sub(r"\(.*?\)", "", f"{name} {area}").strip()
    url = "https://www.google.com/maps/search/" + urllib.parse.quote(q)
    if lat is not None and lng is not None:
        url += f"/@{lat},{lng},17z"
    return url

rest_by_name = {}
for r in trip.get("restaurants", []):
    r["gmap"] = _gmaps(r["name"], r.get("area", ""), r.get("lat"), r.get("lng"))
    rest_by_name[r["name"].strip().lower()] = r

used_slugs = set()
for d in trip.get("days", []):
    for b in d.get("blocks", []):
        s = _img_for_block(b)
        if s: b["img"] = s; used_slugs.add(s)
        if b.get("type") == "meal":
            hit = next((r for n, r in rest_by_name.items() if n and n in b.get("name", "").lower()), None)
            if hit:
                b["gmap"] = hit["gmap"]
            elif b.get("lat") is not None:
                b["gmap"] = _gmaps(b.get("name_en") or b.get("name", ""), "", b.get("lat"), b.get("lng"))
        elif b.get("type") in ("sight", "hotel", "free") and b.get("lat") is not None:
            b["gmap"] = _gmaps(b.get("name_en") or b.get("name", ""), "", b.get("lat"), b.get("lng"))

def _travel_mode(mode):
    m = (mode or "").lower()
    if any(k in m for k in ("walk", "도보", "foot")): return "walking"
    if any(k in m for k in ("taxi", "car", "택시", "렌터", "drive", "driving")): return "driving"
    if any(k in m for k in ("bus", "metro", "train", "tram", "subway", "rail", "cercan", "ktx", "arex", "버스", "지하철", "열차", "기차", "트램", "boat", "ferry")): return "transit"
    return None

def _nav_url(o, d, mode):
    import urllib.parse
    q = {"api": "1", "destination": f"{d[0]},{d[1]}"}
    if o: q["origin"] = f"{o[0]},{o[1]}"
    if mode: q["travelmode"] = mode
    return "https://www.google.com/maps/dir/?" + urllib.parse.urlencode(q)

def _km(a, b):
    import math
    R = 6371; dl = math.radians(b[0]-a[0]); dg = math.radians(b[1]-a[1])
    x = math.sin(dl/2)**2 + math.cos(math.radians(a[0]))*math.cos(math.radians(b[0]))*math.sin(dg/2)**2
    return 2*R*math.asin(math.sqrt(x))

# 이동 블록: 직전 지점 → 이 블록 좌표로 길안내 · 머무는 블록: 현재 위치 → 지점 길안내
for d in trip.get("days", []):
    prev = None
    for b in d.get("blocks", []):
        here = (b["lat"], b["lng"]) if b.get("lat") is not None and b.get("lng") is not None else None
        if b.get("type") == "transport" and here and prev and _km(prev, here) < 400:
            mode = _travel_mode(b.get("transport_mode")) or _travel_mode(b.get("transport_detail")) or "transit"
            b["nav"] = _nav_url(prev, here, mode)
        elif b.get("type") in ("sight", "meal", "hotel", "free") and here:
            b["nav"] = _nav_url(None, here, "walking")
        if here: prev = here
for r in trip.get("restaurants", []):
    s = imap["restaurants"].get(r["name"])  # 대표 요리 사진
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
# Streamlit Community Cloud 정적 서빙용 사본 (<앱주소>/app/static/index.html)
static_dir = os.path.join(ROOT, "static")
os.makedirs(static_dir, exist_ok=True)
with open(os.path.join(static_dir, "index.html"), "w", encoding="utf-8") as f: f.write(html)

print(f"wrote {out} ({os.path.getsize(out)//1024} KB), days={len(trip.get('days',[]))}, "
      f"restaurants={len(trip.get('restaurants',[]))}, images={len(images)} ({img_bytes//1024} KB) "
      f"→ blocks {blocks_with_img}, cards {rest_with_img}; static/index.html 동기화")
