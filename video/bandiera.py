"""Sfondo con la bandiera italiana che ondeggia (disegnata qui, nessuna foto) e composizioni 1080x1920 con il pilota ritagliato di ESPN davanti.
Uso: python bandiera.py "Kimi Antonelli" uscita.jpg [--trofeo]      (il trofeo è la foto libera di Commons in video/extra/)"""
import argparse, math, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

QUI = Path(__file__).parent
sys.path.insert(0, str(QUI))
W, H = 1080, 1920


def bandiera(w=W, h=H):
    """Tre bande verticali (verde, bianco, rosso) con onde e ombre, poi scurita in basso e in alto perché il testo si legga."""
    x = np.arange(w)[None, :].astype(float)
    y = np.arange(h)[:, None].astype(float)
    onda = 70 * np.sin(y / 230.0 + 0.0) + 34 * np.sin(y / 97.0 + 1.3) + 0 * x    # spostamento orizzontale delle bande
    xs = x + onda
    banda = np.clip((xs / (w / 3.0)).astype(int), 0, 2)
    verde, bianco, rosso = np.array([0, 146, 70]), np.array([241, 242, 240]), np.array([206, 43, 55])
    pal = np.stack([verde, bianco, rosso])
    img = pal[banda].astype(float)
    # luce e ombra delle pieghe: segue la stessa onda
    luce = 1.0 + 0.22 * np.cos(y / 230.0 + 0.0) + 0.10 * np.cos(y / 97.0 + 1.3) + 0.12 * np.sin(xs / 110.0)
    img = np.clip(img * luce[..., None], 0, 255)
    # velo scuro: più forte in alto (zona del logo) e in basso (titoli), centro libero
    v = 0.78 * np.clip((y - 1150) / 770, 0, 1) ** 1.2 + 0.55 * np.clip((380 - y) / 380, 0, 1) + 0.18
    img = img * (1 - np.clip(v, 0, 0.9))[..., None]
    return Image.fromarray(img.astype("uint8"))


# contorno del trofeo nella foto di Commons (coordinate sull'immagine 1308 px di larghezza; la foto ha lo sfondo pieno di gente, un ritaglio automatico non regge)
CONTORNO = [(255, 160), (420, 80), (700, 45), (980, 100), (1140, 230), (1150, 330), (1090, 400), (1000, 430), (950, 520), (920, 600), (880, 800), (850, 1000), (820, 1200),
            (790, 1400), (770, 1500), (760, 1540), (880, 1700), (940, 1800), (950, 1860), (870, 1925), (700, 1980), (400, 1960), (200, 1900), (140, 1830), (300, 1730),
            (500, 1650), (470, 1560), (440, 1480), (430, 1300), (432, 1100), (436, 900), (440, 700), (450, 560), (420, 480), (330, 400), (300, 320), (255, 250)]


def taglia_trofeo(percorso):
    """Ritaglia il trofeo con il contorno disegnato a mano (CONTORNO), bordo leggermente sfumato. RGBA."""
    im = Image.open(percorso).convert("RGB")
    k = im.width / 1308.0
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).polygon([(x * k, y * k) for x, y in CONTORNO], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(2.2))
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out.crop(out.getbbox())


def composizione(nome, uscita, trofeo=None):
    import ritratti_espn as R
    sfondo = bandiera().convert("RGBA")
    p = Image.open(R.scarica(nome)).convert("RGBA")
    s = 1250 / p.width
    p = p.resize((int(p.width * s), int(p.height * s)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.4, 60, 2))
    sx = 0 if trofeo else (W - p.width) // 2
    px = (-110 if trofeo else sx)
    # il ritratto finisce al petto: bordo basso sfumato nello sfondo
    al = np.asarray(p.getchannel("A")).astype(float)
    fade = np.clip((p.height - np.arange(p.height)) / 260.0, 0, 1)[:, None]
    p.putalpha(Image.fromarray((al * fade).astype("uint8")))
    py = 1560 - p.height
    sfondo.alpha_composite(p, (px, py)) if px >= 0 else sfondo.alpha_composite(p.crop((-px, 0, p.width, p.height)), (0, py))
    if trofeo:
        t = taglia_trofeo(trofeo)
        k = 760 / t.height
        t = t.resize((int(t.width * k), 760), Image.LANCZOS)
        ombra = Image.new("RGBA", t.size, (0, 0, 0, 0)); ombra.putalpha(t.getchannel("A").filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.6)))
        sfondo.alpha_composite(ombra, (730 - t.width // 2 + 10, 1500 - 760 + 14))
        sfondo.alpha_composite(t, (730 - t.width // 2, 1500 - 760))
    sfondo.convert("RGB").save(uscita, "JPEG", quality=92)
    return uscita


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("nome"); ap.add_argument("uscita"); ap.add_argument("--trofeo", action="store_true")
    a = ap.parse_args()
    composizione(a.nome, a.uscita, (QUI / "extra" / "trofeo-f1.jpg") if a.trofeo else None)
    print("fatto", a.uscita)
