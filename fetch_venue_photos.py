#!/usr/bin/env python3
"""각 맛집 공식 사이트의 대표 이미지(og:image 등)를 수집해 assets/venue/<slug>.jpg 로 저장."""
import json, os, re, subprocess, io, sys, html
from PIL import Image
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "assets", "venue")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"

def slugify(name):
    s = re.sub(r"\(.*?\)", "", name).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s.encode("ascii", "ignore").decode()).strip("-")
    return s or re.sub(r"[^0-9a-z]+", "-", name.lower())

def curl(url, binary=False, timeout=25):
    r = subprocess.run(["curl", "-sSL", "-m", str(timeout), "-A", UA, "--compressed", url],
                       capture_output=True)
    if r.returncode != 0: raise RuntimeError(r.stderr.decode()[:120])
    return r.stdout if binary else r.stdout.decode("utf-8", "ignore")

META_RE = [
    re.compile(r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image(?::secure_url)?["\']', re.I),
    re.compile(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']', re.I),
]

def find_image(url):
    page = curl(url)
    for rx in META_RE:
        m = rx.search(page)
        if m:
            u = html.unescape(m.group(1)).strip()
            if u.startswith("//"): u = "https:" + u
            if u.startswith("/"):
                from urllib.parse import urljoin
                u = urljoin(url, u)
            if not u.lower().endswith(".svg"): return u, "og:image"
    # fallback: 첫 대형 이미지 후보
    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+\.(?:jpe?g|png|webp)[^"\']*)["\']', page, re.I)
    from urllib.parse import urljoin
    for u in imgs:
        if any(k in u.lower() for k in ("logo", "icon", "sprite")): continue
        return urljoin(url, html.unescape(u)), "first-img"
    raise RuntimeError("no image tag")

def save(slug, img_url):
    data = curl(img_url, binary=True, timeout=40)
    im = Image.open(io.BytesIO(data)); im.load()
    if im.mode != "RGB": im = im.convert("RGB")
    w, h = im.size
    if w < 220 or h < 130: raise RuntimeError(f"too small {w}x{h}")
    tw, th = 360, 240
    sc = max(tw / w, th / h)
    im = im.resize((max(tw, int(w * sc + .5)), max(th, int(h * sc + .5))), Image.LANCZOS)
    w, h = im.size; l, t = (w - tw) // 2, int((h - th) * 0.4)
    im = im.crop((l, t, l + tw, t + th))
    p = os.path.join(OUT, slug + ".jpg"); im.save(p, "JPEG", quality=74, optimize=True, progressive=True)
    return os.path.getsize(p)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    T = json.load(open(os.path.join(ROOT, "data", "itinerary.json"), encoding="utf-8"))
    only = sys.argv[1:]
    credits = {}
    cpath = os.path.join(ROOT, "assets", "venue_credits.json")
    if os.path.exists(cpath): credits = json.load(open(cpath, encoding="utf-8"))
    for r in T["restaurants"]:
        slug = slugify(r["name"])
        if only and slug not in only: continue
        url = (r.get("url") or "").strip()
        if not url or "google.com" in url or "maps.google" in url or "guiarepsol" in url:
            print(f"  SKIP {slug:36s} (공식 사이트 없음)"); continue
        try:
            img, how = find_image(url)
            n = save(slug, img)
            credits[slug] = {"name": r["name"], "source": url, "img": img[:160], "how": how}
            print(f"  ok   {slug:36s} {n//1024:3d}KB {how} {img[:70]}")
        except Exception as e:
            print(f"  MISS {slug:36s} {str(e)[:90]}")
    json.dump(credits, open(cpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved credits:", len(credits))
