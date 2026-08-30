#!/usr/bin/env python3
"""Sanity-check data/itinerary.json: dates, time order/overlap, coords, ratings, restaurant usage."""
import json, sys, datetime, math
p = sys.argv[1] if len(sys.argv) > 1 else "data/itinerary.json"
T = json.load(open(p, encoding="utf-8"))
errs, warns = [], []
def tm(s):
    try: h, m = s.split(":"); return int(h)*60+int(m)
    except Exception: return None
def region(lat, lng):
    if lat is None or lng is None: return None
    if lng > 60: return "korea"
    if lng < -2: return "madrid"
    if lat < 40.3 and lng > 1.2: return "mallorca"
    if lat >= 40.3: return "barcelona"
    return None
days = T.get("days", [])
start = datetime.date(2027, 4, 25)
EXPECTED_DAYS = 13          # 2027-04-25(울산 출발) ~ 2027-05-07(인천 도착)
if len(days) != EXPECTED_DAYS: errs.append(f"days={len(days)} (expected {EXPECTED_DAYS})")
for i, d in enumerate(days):
    exp = (start + datetime.timedelta(days=i)).isoformat()
    if d.get("day_no") != i+1: errs.append(f"day_no {d.get('day_no')} at index {i}")
    if d.get("date") != exp: errs.append(f"D{d.get('day_no')} date {d.get('date')} != {exp}")
    prev_end = -1; prev_name = ""
    first = next((b for b in d.get("blocks", []) if not (b.get("type") == "tip" and b.get("start") == "00:00")), None)
    if first and tm(first.get("start", "")) is not None and tm(first["start"]) < 9*60 and d.get("day_no") not in (1, 13):
        warns.append(f"D{d['day_no']} starts before 09:00: {first['start']} {first['name'][:40]}")
    for b in d.get("blocks", []):
        s, e = tm(b.get("start","")), tm(b.get("end",""))
        if s is None or e is None: errs.append(f"D{d['day_no']} bad time {b.get('start')}–{b.get('end')} {b.get('name')}"); continue
        if e < s and not (b.get("type") == "flight" and e < s): errs.append(f"D{d['day_no']} end<start {b['name']}")
        if s < prev_end - 5 and b.get("type") != "tip": warns.append(f"D{d['day_no']} overlap: {prev_name} ends {prev_end//60:02d}:{prev_end%60:02d} but {b['name']} starts {b['start']}")
        prev_end = max(prev_end, e if e >= s else s); prev_name = b["name"]
        if b.get("type") in ("sight", "meal") and (b.get("lat") is None or b.get("lng") is None): errs.append(f"D{d['day_no']} no coords: {b['name']}")
        r = region(b.get("lat"), b.get("lng"))
        if b.get("lat") is not None and r is None: errs.append(f"D{d['day_no']} coords off-map {b['name']} {b.get('lat')},{b.get('lng')}")
        if b.get("type") == "meal":
            g = b.get("google_rating")
            if g is None: warns.append(f"D{d['day_no']} meal without rating: {b['name']}")
            elif g < 3.5: errs.append(f"D{d['day_no']} rating {g} < 3.5: {b['name']}")
rests = T.get("restaurants", [])
names = {}
for r in rests:
    if r.get("google_rating", 0) < 3.5: errs.append(f"restaurant {r['name']} rating {r.get('google_rating')}")
    if region(r.get("lat"), r.get("lng")) is None: errs.append(f"restaurant coords off-map {r['name']}")
    names.setdefault(r["name"].strip().lower(), []).append(r.get("used_on_day"))
dups = {k: v for k, v in names.items() if len(v) > 1}
if dups: warns.append(f"duplicate restaurants: {dups}")
used = [r for r in rests if r.get("used_on_day")]
for s in T.get("safety", []):
    for a in s.get("avoid_areas", []):
        if region(a.get("lat"), a.get("lng")) is None: errs.append(f"avoid area coords off-map {a['area']}")
print(f"days={len(days)} blocks={sum(len(d.get('blocks',[])) for d in days)} sights={sum(1 for d in days for b in d.get('blocks',[]) if b.get('type')=='sight')} meals={sum(1 for d in days for b in d.get('blocks',[]) if b.get('type')=='meal')} restaurants={len(rests)} (used {len(used)}) safety_cities={len(T.get('safety',[]))} bookings={len(T.get('booking_checklist',[]))}")
print("ERRORS:", len(errs)); [print("  E", e) for e in errs]
print("WARNINGS:", len(warns)); [print("  W", w) for w in warns]
sys.exit(1 if errs else 0)
