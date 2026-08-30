#!/usr/bin/env python3
"""Fetch representative photos (Wikipedia page images / Wikimedia Commons) for sights and dishes.
Writes assets/img/<slug>.jpg + assets/image_credits.json (attribution for CC licenses)."""
import json, os, sys, time, urllib.parse, subprocess, io
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "assets", "img")
UA = "spain-trip-planner/1.0 (personal travel plan; https://github.com/Haeryangkim)"

# slug -> (wiki lang, exact article title)
SIGHTS = {
 "plaza-mayor": ("es", "Plaza Mayor de Madrid"),
 "puerta-del-sol": ("es", "Puerta del Sol"),
 "museo-del-prado": ("es", "Museo del Prado"),
 "retiro": ("es", "Parque del Retiro de Madrid"),
 "reina-sofia": ("commons", "File:Museo Reina Sofia, Madrid (6394601959).jpg"),
 "circulo-bellas-artes": ("es", "Círculo de Bellas Artes"),
 "royal-palace": ("es", "Palacio Real de Madrid"),
 "almudena": ("es", "Catedral de la Almudena"),
 "gran-via": ("es", "Gran Vía (Madrid)"),
 "plaza-espana": ("es", "Plaza de España (Madrid)"),
 "templo-debod": ("es", "Templo de Debod"),
 "parque-oeste": ("es", "Parque del Oeste (Madrid)"),
 "zocodover": ("es", "Plaza de Zocodover"),
 "alcazar-toledo": ("es", "Alcázar de Toledo"),
 "toledo-cathedral": ("es", "Catedral de Toledo"),
 "santo-tome": ("es", "Iglesia de Santo Tomé (Toledo)"),
 "santa-maria-blanca": ("es", "Sinagoga de Santa María la Blanca"),
 "san-juan-reyes": ("es", "Monasterio de San Juan de los Reyes"),
 "puente-san-martin": ("es", "Puente de San Martín (Toledo)"),
 "mirador-valle": ("commons", "File:Toledo - Panorama desde Mirador del Valle.jpg"),
 "la-seu": ("es", "Catedral de Mallorca"),
 "almudaina": ("es", "Palacio de la Almudaina"),
 "passeig-born": ("ca", "Passeig del Born (Palma)"),
 "soller": ("es", "Sóller"),
 "tren-soller": ("es", "Ferrocarril de Sóller"),
 "port-soller": ("ca", "Port de Sóller"),
 "santanyi": ("ca", "Santanyí"),
 "mondrago": ("ca", "Parc natural de Mondragó"),
 "coves-drac": ("es", "Cuevas del Drach"),
 "picasso-museum": ("es", "Museo Picasso de Barcelona"),
 "santa-maria-mar": ("es", "Basílica de Santa María del Mar"),
 "placa-rei": ("ca", "Plaça del Rei (Barcelona)"),
 "sant-felip-neri": ("ca", "Plaça de Sant Felip Neri"),
 "bcn-cathedral": ("es", "Catedral de Barcelona"),
 "sagrada-familia": ("commons", "File:Sagrada Familia 01.jpg"),
 "sant-pau": ("es", "Hospital de la Santa Cruz y San Pablo"),
 "casa-batllo": ("es", "Casa Batlló"),
 "casa-mila": ("es", "Casa Milà"),
 "park-guell": ("es", "Parque Güell"),
 "teleferic-montjuic": ("es", "Teleférico de Montjuic"),
 "castell-montjuic": ("es", "Castillo de Montjuic"),
 "mnac": ("commons", "File:Palau Nacional Quatre Columnes Barcelona 2013.jpg"),
 "barceloneta": ("es", "La Barceloneta"),
 "boqueria": ("es", "Mercado de La Boquería"),
 "palau-musica": ("es", "Palacio de la Música Catalana"),
 "gracia": ("es", "Gracia (Barcelona)"),
 "casa-vicens": ("es", "Casa Vicens"),
 "palma": ("en", "Palma de Mallorca"),
 "mercat-olivar": ("ca", "Mercat de l'Olivar"),
 "parc-mar": ("commons", "File:Palma Cathedral (La Seu) and reflection at Parc de la Mar.jpg"),
}
DISHES = {
 "churros": ("es", "Churro"),
 "tapas": ("es", "Tapa (gastronomía)"),
 "paella": ("es", "Paella"),
 "cocido": ("es", "Cocido madrileño"),
 "jamon": ("es", "Jamón ibérico"),
 "croquetas": ("es", "Croqueta"),
 "bocadillo": ("es", "Bocadillo de calamares"),
 "tortilla": ("es", "Tortilla de patatas"),
 "vermut": ("es", "Vermut"),
 "pintxos": ("es", "Pincho"),
 "cochinillo": ("es", "Cochinillo asado"),
 "mazapan": ("es", "Mazapán de Toledo"),
 "carcamusas": ("es", "Carcamusas"),
 "ensaimada": ("es", "Ensaimada"),
 "sobrasada": ("es", "Sobrasada"),
 "gelato": ("es", "Helado"),
 "marisco": ("es", "Marisco"),
 "pastry": ("es", "Cruasán"),
 "mercado": ("es", "Mercado de San Miguel"),
 "pantumaca": ("es", "Pan con tomate"),
 "cremacatalana": ("es", "Crema catalana"),
 "fideua": ("es", "Fideuá"),
 "cafe": ("es", "Café con leche"),
 "chocolate": ("es", "Chocolate a la taza"),
 "arroz": ("ca", "Arròs negre"),
}

def _get(url, binary=False):
    r = subprocess.run(["curl", "-sS", "-L", "-m", "45", "-A", UA, url],
                       capture_output=True, check=True)
    return r.stdout if binary else json.loads(r.stdout)

def api(lang, params):
    return _get(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params))

def commons(params):
    return _get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params))

def fetch_group(items):
    """items: {slug: (lang, title)} -> {slug: {thumb, file, title, lang}}
    lang == "commons" means `title` is an exact Commons File: name."""
    found_direct = {}
    for slug, (lang, title) in list(items.items()):
        if lang != "commons":
            continue
        items.pop(slug)
        try:
            d = commons({"action": "query", "titles": title, "prop": "imageinfo",
                         "iiprop": "url", "iiurlwidth": 800, "format": "json"})
            pg = list(d["query"]["pages"].values())[0]
            ii = pg["imageinfo"][0]
            found_direct[slug] = {"thumb": ii.get("thumburl") or ii["url"],
                                  "file": title.replace("File:", ""), "title": title, "lang": "commons"}
        except Exception as e:
            print("  MISS(commons)", slug, title, e)
    by_lang = {}
    for slug, (lang, title) in items.items():
        by_lang.setdefault(lang, []).append((slug, title))
    found = {}
    for lang, pairs in by_lang.items():
        for i in range(0, len(pairs), 20):
            chunk = pairs[i:i+20]
            titles = "|".join(t for _, t in chunk)
            try:
                d = api(lang, {"action": "query", "titles": titles, "prop": "pageimages",
                               "piprop": "thumbnail|name", "pithumbsize": 800, "format": "json", "redirects": 1})
            except Exception as e:
                print("API fail", lang, e); continue
            pages = d.get("query", {}).get("pages", {})
            norm = {}
            for p in pages.values():
                norm[p["title"].lower()] = p
            for r in d.get("query", {}).get("redirects", []):
                pass
            redirects = {r["from"].lower(): r["to"].lower() for r in d.get("query", {}).get("redirects", [])}
            normalized = {n["from"].lower(): n["to"].lower() for n in d.get("query", {}).get("normalized", [])}
            for slug, title in chunk:
                key = title.lower()
                key = normalized.get(key, key)
                key = redirects.get(key, key)
                p = norm.get(key)
                if not p or "thumbnail" not in p:
                    print("  MISS", slug, title)
                    continue
                found[slug] = {"thumb": p["thumbnail"]["source"], "file": p.get("pageimage", ""),
                               "title": p["title"], "lang": lang}
            time.sleep(0.3)
    found.update(found_direct)
    return found

def credit_for(filename):
    try:
        d = commons({"action": "query", "titles": "File:" + filename, "prop": "imageinfo",
                     "iiprop": "extmetadata|url", "format": "json"})
        p = list(d["query"]["pages"].values())[0]
        ii = p["imageinfo"][0]
        m = ii.get("extmetadata", {})
        def g(k):
            v = m.get(k, {}).get("value", "")
            import re
            return re.sub(r"<[^>]+>", "", v).strip()
        return {"file": filename, "author": g("Artist") or "unknown",
                "license": g("LicenseShortName") or g("License") or "?",
                "url": ii.get("descriptionurl", "")}
    except Exception as e:
        return {"file": filename, "author": "unknown", "license": "?", "url": "", "error": str(e)}

def save_thumb(slug, url, size=(360, 240)):
    data = _get(url, binary=True)
    im = Image.open(io.BytesIO(data)).convert("RGB")
    w, h = im.size
    tw, th = size
    scale = max(tw / w, th / h)
    im = im.resize((max(tw, int(w * scale + .5)), max(th, int(h * scale + .5))), Image.LANCZOS)
    w, h = im.size
    left, top = (w - tw) // 2, int((h - th) * 0.35)   # bias slightly above center
    im = im.crop((left, top, left + tw, top + th))
    path = os.path.join(OUT, slug + ".jpg")
    im.save(path, "JPEG", quality=72, optimize=True, progressive=True)
    return os.path.getsize(path)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    want = {}
    want.update(SIGHTS); want.update(DISHES)
    only = sys.argv[1:] 
    if only: want = {k: v for k, v in want.items() if k in only}
    print(f"fetching {len(want)} images…")
    found = fetch_group(want)
    credits = {}
    if os.path.exists(os.path.join(ROOT, "assets", "image_credits.json")):
        credits = json.load(open(os.path.join(ROOT, "assets", "image_credits.json"), encoding="utf-8"))
    total = 0
    for slug, info in sorted(found.items()):
        try:
            n = save_thumb(slug, info["thumb"]); total += n
            c = credit_for(info["file"])
            c["article"] = info["title"]; c["lang"] = info["lang"]
            credits[slug] = c
            print(f"  ok {slug:22s} {n//1024:4d}KB  {c['license'][:28]:30s} {info['title'][:40]}")
        except Exception as e:
            print("  ERR", slug, e)
        time.sleep(0.2)
    json.dump(credits, open(os.path.join(ROOT, "assets", "image_credits.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"total {total//1024} KB, {len(credits)} credits, missing: {sorted(set(want) - set(found))}")
