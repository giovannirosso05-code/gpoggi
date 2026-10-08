"""Ritratti dei piloti di F1 dal sito di ESPN, messi su uno sfondo a gradiente nel colore del team (1080x1920) per i video.

Le foto di ESPN sono protette da copyright: NON vanno nella cartella del sito (docs/) né nel repository. Si scaricano al momento
in video/_cache/ (ignorata da git) e nel video si scrive "Foto: ESPN". L'uso è una scelta di rischio dichiarata dal gestore del sito.
"""
import io, json, re, sys, unicodedata
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter

QUI = Path(__file__).parent
CACHE = QUI / "_cache"
HEADERS = {"User-Agent": "GPOggiBot/0.1 (sito non ufficiale; giovannirosso05@gmail.com)"}
W, H = 1080, 1920


def id_espn(nome):
    r = requests.get("https://site.web.api.espn.com/apis/common/v3/search", params={"query": nome, "limit": 5, "type": "player"}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    for x in r.json().get("items", []):
        if x.get("league") == "f1" and x.get("displayName", "").lower() == nome.lower():
            return x["id"]
    return None


def scarica(nome):
    CACHE.mkdir(exist_ok=True)
    f = CACHE / (re.sub(r"[^a-z0-9]+", "_", nome.lower()) + "_espn.png")
    if not f.exists():
        i = id_espn(nome)
        if not i:
            raise SystemExit(f"{nome}: nessun ritratto ESPN")
        r = requests.get(f"https://a.espncdn.com/i/headshots/rpm/players/full/{i}.png", headers=HEADERS, timeout=40)
        r.raise_for_status()
        f.write_bytes(r.content)
    return f


def _sfondo(colore):
    """Gradiente dal colore del team (in alto) al nero (in basso), con un alone dietro al volto."""
    r, g, b = colore
    base = Image.new("RGB", (W, H))
    px = Image.new("RGB", (1, H))
    for y in range(H):
        t = min(1.0, y / (H * 0.78))
        k = 0.85 * (1 - t) ** 1.4 + 0.04
        px.putpixel((0, y), (int(r * k), int(g * k), int(b * k)))
    base = px.resize((W, H))
    alone = Image.new("L", (W, H), 0)
    ImageDraw.Draw(alone).ellipse((W * 0.05, 120, W * 0.95, 1100), fill=120)
    alone = alone.filter(ImageFilter.GaussianBlur(160))
    chiaro = Image.new("RGB", (W, H), (min(255, r + 40), min(255, g + 40), min(255, b + 40)))
    return Image.composite(chiaro, base, alone)


def ritratto(nome, colore=(232, 53, 47), larghezza=1380, centro_volto_y=720, volto_rel=0.39, sfx=""):
    """Percorso di un JPG 1080x1920 con il pilota di ESPN sul gradiente del team."""
    uscita = CACHE / (re.sub(r"[^a-z0-9]+", "_", nome.lower()) + sfx + "_scena.jpg")
    if uscita.exists():
        return uscita
    img = Image.open(scarica(nome)).convert("RGBA")
    s = larghezza / img.width
    img = img.resize((int(img.width * s), int(img.height * s)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.4, percent=60, threshold=2))
    # sfuma il bordo basso (il ritratto finisce al petto)
    a = img.getchannel("A")
    fade = Image.new("L", img.size, 255)
    d = ImageDraw.Draw(fade)
    for y in range(img.height - 230, img.height):
        d.line([(0, y), (img.width, y)], fill=int(255 * (img.height - y) / 230))
    img.putalpha(Image.composite(Image.new("L", img.size, 0), a, Image.eval(fade, lambda v: 255 - v)) if False else Image.fromarray(__import__("numpy").minimum(__import__("numpy").array(a), __import__("numpy").array(fade))))
    sfondo = _sfondo(colore)
    x0 = (W - img.width) // 2
    y0 = int(centro_volto_y - img.height * volto_rel)
    sfondo.paste(img, (x0, y0), img)
    sfondo.save(uscita, "JPEG", quality=92)
    return uscita


def ritratto_libero(percorso, nome_uscita, larghezza=1080, y0=170, fondo=None):
    """Ritratto con licenza libera (già un JPG) sullo stesso formato 1080x1920: sfondo sfocato della stessa foto e sfumatura in basso."""
    uscita = CACHE / (nome_uscita + "_scena.jpg")
    CACHE.mkdir(exist_ok=True)
    img = Image.open(percorso).convert("RGB")
    sfondo = img.copy()
    sc = max(W / sfondo.width, H / sfondo.height)
    sfondo = sfondo.resize((int(sfondo.width * sc), int(sfondo.height * sc)), Image.LANCZOS)
    sfondo = sfondo.crop(((sfondo.width - W) // 2, 0, (sfondo.width - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(40))
    if fondo:  # sfondo a gradiente del colore dato, al posto della foto sfocata (utile quando il bordo della foto è scuro o uniforme)
        sfondo = _sfondo(fondo)
    s = larghezza / img.width
    img = img.resize((larghezza, int(img.height * s)), Image.LANCZOS)
    mask = Image.new("L", img.size, 255)
    d = ImageDraw.Draw(mask)
    for y in range(img.height - 200, img.height):
        d.line([(0, y), (img.width, y)], fill=int(255 * (img.height - y) / 200))
    sfondo.paste(img, ((W - larghezza) // 2, y0), mask)
    sfondo.save(uscita, "JPEG", quality=92)
    return uscita


if __name__ == "__main__":
    print(ritratto(sys.argv[1]))
