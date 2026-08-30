#!/usr/bin/env python3
"""plan_v2/ 조각들을 data/itinerary.json 으로 병합.
  days: days_01_04.json + days_05_10.json + days_11_13.json
  restaurants: rest_madrid_out.json + rest_05_10_out.json + rest_11_13_out.json (이름 기준 중복 제거, used_on_day 우선)
  static: static_rewritten.json (safety, general_tips, weather, alternatives) + global_v2.json (summary, flights, booking_checklist, budget)
"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(ROOT, "data", "plan_v2")
def load(name, default=None):
    p = os.path.join(P, name)
    if not os.path.exists(p):
        print(f"  ! missing {name}"); return default
    return json.load(open(p, encoding="utf-8"))
def norm(n): return re.sub(r"\s+", " ", re.sub(r"\(.*?\)", "", n)).strip().lower()

days = []
for part in ("days_01_04.json", "days_05_10.json", "days_11_13.json"):
    days += load(part, [])
days.sort(key=lambda d: d["day_no"])
for d in days:  # 빌드 시 추가되는 파생 필드 제거
    for b in d["blocks"]:
        b.pop("img", None); b.pop("gmap", None)

static = load("static_rewritten.json", {})
text_rest = {norm(r["name"]): r for r in static.get("restaurants", [])}
rests = {}
for part in ("rest_madrid_out.json", "rest_05_10_out.json", "rest_11_13_out.json"):
    for r in load(part, []):
        r.pop("img", None); r.pop("gmap", None)
        k = norm(r["name"])
        t = text_rest.get(k)
        if t:  # 교정된 텍스트 필드 적용
            for f in ("must_try", "hours_note", "reservation_note"):
                if t.get(f): r[f] = t[f]
        if k in rests and rests[k].get("used_on_day") and not r.get("used_on_day"):
            continue
        rests[k] = r
# 교정 파일에만 있고 플래너 출력에 없는 식당(예비)은 used_on_day 0 으로 보존
for k, t in text_rest.items():
    if k not in rests:
        t = dict(t); t["used_on_day"] = 0; rests[k] = t
# 실제 식사 블록과 used_on_day 동기화
used = {}
for d in days:
    for b in d["blocks"]:
        if b.get("type") == "meal":
            for k in rests:
                if k and k in b["name"].lower(): used.setdefault(k, d["day_no"])
for k, r in rests.items():
    r["used_on_day"] = used.get(k, 0)

G = load("global_v2.json", {})
final = {
    "summary": G.get("summary") or static.get("summary"),
    "flights": G.get("flights") or static.get("flights"),
    "days": days,
    "alternatives": static.get("alternatives", []),
    "restaurants": sorted(rests.values(), key=lambda r: (r.get("used_on_day") or 99, r["name"])),
    "safety": static.get("safety", []),
    "booking_checklist": G.get("booking_checklist") or static.get("booking_checklist"),
    "budget": G.get("budget") or static.get("budget"),
    "weather": static.get("weather", []),
    "general_tips": static.get("general_tips", []),
}
out = os.path.join(ROOT, "data", "itinerary.json")
json.dump(final, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"merged → {out}: days={len(days)} blocks={sum(len(d['blocks']) for d in days)} restaurants={len(final['restaurants'])} (used {sum(1 for r in final['restaurants'] if r['used_on_day'])})")
