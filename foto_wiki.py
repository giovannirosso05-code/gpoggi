"""Foto dei piloti e mappe dei tracciati da Wikimedia Commons (solo licenze libere).

Ogni immagine porta con se' autore, licenza e pagina del file: le licenze CC BY/BY-SA
obbligano a citarli, il sito li mostra accanto alla foto.
"""

import hashlib
import html
import io
import re
import time
from pathlib import Path

import requests
from PIL import Image

WIKI = "https://en.wikipedia.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "GPOggiBot/0.1 (sito non ufficiale; giovannirosso05@gmail.com)"}
LICENZE_OK = ("CC BY", "CC BY-SA", "CC0", "Public domain", "PD", "OGL")

CIRCUITI = {
    "Austin": "Circuit of the Americas", "Baku": "Baku City Circuit", "Catalunya": "Circuit de Barcelona-Catalunya",
    "Hungaroring": "Hungaroring", "Interlagos": "Interlagos Circuit", "Las Vegas": "Las Vegas Strip Circuit",
    "Lusail": "Lusail International Circuit", "Madring": "Madring", "Melbourne": "Albert Park Circuit",
    "Mexico City": "Autódromo Hermanos Rodríguez", "Miami": "Miami International Autodrome",
    "Monte Carlo": "Circuit de Monaco", "Montreal": "Circuit Gilles Villeneuve", "Monza": "Monza Circuit",
    "Shanghai": "Shanghai International Circuit", "Silverstone": "Silverstone Circuit",
    "Singapore": "Marina Bay Street Circuit", "Spa-Francorchamps": "Circuit de Spa-Francorchamps",
    "Spielberg": "Red Bull Ring", "Suzuka": "Suzuka International Racing Course",
    "Yas Marina Circuit": "Yas Marina Circuit", "Zandvoort": "Circuit Zandvoort",
    "Sakhir": "Bahrain International Circuit", "Jeddah": "Jeddah Corniche Circuit", "Imola": "Imola Circuit",
}


def _api(url, **params):
    for tentativo in range(6):
        time.sleep(1 + 5 * tentativo)
        r = requests.get(url, params={"action": "query", "format": "json", "redirects": 1, **params}, headers=HEADERS, timeout=30)
        if r.status_code != 429:
            break
    r.raise_for_status()
    return list(r.json()["query"].get("pages", {}).values())


def _testo(v):
    return html.unescape(re.sub(r"<[^>]+>", "", v or "")).strip()


def _info_file(nome_file, larghezza):
    pagine = _api(COMMONS, prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=larghezza, titles=f"File:{nome_file}")
    if not pagine or "imageinfo" not in pagine[0]:
        return None  # file non su Commons (es. immagine non libera caricata solo su en.wikipedia)
    ii = pagine[0]["imageinfo"][0]
    meta = ii.get("extmetadata", {})
    licenza = _testo(meta.get("LicenseShortName", {}).get("value"))
    if not licenza.startswith(LICENZE_OK):
        return None
    originale = ii["url"].split("?")[0]
    miniatura = (ii.get("thumburl") or originale).split("?")[0]
    grande = re.sub(r"/\d+px-", "/1280px-", miniatura) if ii.get("width", 0) > 1280 and "thumburl" in ii else originale
    return {
        "url": miniatura,
        "grande": grande,
        "autore": _testo(meta.get("Artist", {}).get("value")) or "Autore sconosciuto",
        "licenza": licenza,
        "pagina": ii["descriptionurl"],
    }


def _immagine_pagina(titolo):
    pagine = _api(WIKI, prop="description|pageimages", piprop="name", titles=titolo)
    p = pagine[0] if pagine else {}
    return p.get("description") or "", p.get("pageimage")


def foto_pilota(nome):
    if not nome:
        return None
    for titolo in (nome, f"{nome} (racing driver)", f"{nome} Jr."):
        descrizione, file = _immagine_pagina(titolo)
        if "racing driver" in descrizione.lower() and file:
            return _info_file(file, 500)
    return None


def mappa_circuito(circuito):
    titolo = CIRCUITI.get(circuito)
    if not titolo:
        return None
    _, file = _immagine_pagina(titolo)
    if not file or not file.lower().endswith((".svg", ".png")):
        return None
    return _info_file(file, 800)


def con_cache(cache, chiave, funzione, *args):
    if chiave not in cache:
        try:
            cache[chiave] = funzione(*args)
        except requests.RequestException as e:
            print(f"  foto non disponibile per {chiave}: {e}")
            return None
    return cache[chiave]


def salva_in_locale(foto, cartella, prefisso_web, chiave_url="url", chiave_file="file"):
    """Copia l'immagine nel sito: niente dipendenza da Wikimedia a ogni visita."""
    if not foto:
        return
    url = foto[chiave_url]
    estensione = Path(url.split("?")[0]).suffix.lower() or ".jpg"
    if estensione == ".png":
        estensione = ".jpg"  # i PNG fotografici pesano troppo: li salviamo in JPEG
    nome = hashlib.md5(url.encode()).hexdigest()[:16] + estensione
    destinazione = cartella / nome
    if not destinazione.exists():
        for tentativo in range(5):
            time.sleep(1 + 5 * tentativo)
            r = requests.get(url, headers=HEADERS, timeout=60)
            if r.status_code != 429:
                break
        r.raise_for_status()
        if not r.headers.get("content-type", "").startswith("image/"):
            raise ValueError(f"{url} non e' un'immagine ({r.headers.get('content-type')})")
        cartella.mkdir(parents=True, exist_ok=True)
        if r.headers["content-type"].startswith("image/png"):
            immagine = Image.open(io.BytesIO(r.content)).convert("RGBA")
            sfondo = Image.new("RGB", immagine.size, (255, 255, 255))
            sfondo.paste(immagine, mask=immagine.split()[3])
            sfondo.save(destinazione, "JPEG", quality=85, optimize=True)
        else:
            destinazione.write_bytes(r.content)
    foto[chiave_file] = f"{prefisso_web}/{nome}"
