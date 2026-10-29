"""Scarica da Wikimedia Commons (licenza libera) la foto del trofeo del campionato piloti di F1 in video/extra/ con il credito.
Si lancia dal workflow «Foto trofeo» (da qui Commons risponde 429)."""
import json, sys, time
from pathlib import Path
import requests

UA = {"User-Agent": "GPOggiBot/1.0 (https://gpoggi.it; info@gpoggi.it)"}
OUT = Path(__file__).parent / "extra"
OUT.mkdir(exist_ok=True)
FILE = "File:F1 Drivers' World Championship trophy (cropped).jpg"
for k in range(5):
    r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=60,
                     params={"action": "query", "titles": FILE, "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 1400, "format": "json"})
    if r.status_code == 200:
        break
    time.sleep(10 * (k + 1))
r.raise_for_status()
p = next(iter(r.json()["query"]["pages"].values()))["imageinfo"][0]
img = requests.get(p["thumburl"], headers=UA, timeout=120); img.raise_for_status()
(OUT / "trofeo-f1.jpg").write_bytes(img.content)
m = p["extmetadata"]
cred = {"autore": m.get("Artist", {}).get("value", ""), "licenza": m.get("LicenseShortName", {}).get("value", ""), "pagina": p["descriptionurl"]}
(OUT / "trofeo-f1.json").write_text(json.dumps(cred, ensure_ascii=False, indent=1))
print(cred)
