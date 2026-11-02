"""Aula virtuale per le video lezioni: si guarda dal banco (appunti in primo piano), dietro c'è lo schermo con la slide e, a destra, il professore al leggio che parla.
Il professore è un disegno (nessuna persona reale): la bocca si apre e chiude seguendo la voce, le braccia cambiano posa.
Livelli (tutti 1920x1080): sfondo (aula + cornice dello schermo) -> slide dentro lo schermo -> professore col leggio (6 posizioni) -> primo piano (teste degli studenti, banco, quaderno)."""
import asyncio
from pathlib import Path

W, H = 1920, 1080
SCHERMO = (96, 40, 1248, 702)   # x, y, larghezza, altezza dell'area della slide (1248 = 1920 * 0,65)

_PAGINA = """<!doctype html><meta charset=utf-8><style>html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:transparent}svg{display:block}</style>%s"""


def _teste(righe):
    """Teste e spalle degli studenti visti da dietro: (x, y, scala, colore capelli, colore maglia)."""
    cap = ["#2b2220", "#5a3b24", "#1d1a1a", "#8a6a3f", "#3a2d2a", "#b99a6b", "#4a4a52", "#6b3d2a", "#c9b79c", "#222"]
    mag = ["#2f4b7c", "#7a2f3f", "#3c6b5a", "#555a66", "#8a7a4a", "#2a2f3c", "#9a5a3a", "#47506b", "#6b6b6b", "#33445a"]
    out = []
    for r, (y, sc, n, x0, dx) in enumerate(righe):
        for i in range(n):
            k = (i * 7 + r * 3) % 10
            xx = x0 + i * dx + ((i * 37 + r * 11) % 23 - 11)
            yy = y + ((i * 19 + r * 5) % 17 - 8)
            s = sc * (0.92 + ((i * 13 + r) % 9) / 50)
            out.append(f'<g transform="translate({xx},{yy}) scale({s:.3f})">'
                       f'<path d="M-95 150 Q-95 70 -45 52 L45 52 Q95 70 95 150 Z" fill="{mag[k]}"/>'
                       f'<rect x="-14" y="30" width="28" height="40" fill="#d8a384"/>'
                       f'<ellipse cx="0" cy="0" rx="52" ry="62" fill="{cap[(k + r) % 10]}"/></g>')
    return "".join(out)


def svg_sfondo():
    pannelli = "".join(f'<rect x="{x}" y="60" width="3" height="640" fill="#8f6431" opacity=".55"/>' for x in range(0, 1920, 128))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
<defs><linearGradient id="leg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d4a46a"/><stop offset="1" stop-color="#b5803f"/></linearGradient>
<linearGradient id="pav" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6f7f98"/><stop offset="1" stop-color="#46536b"/></linearGradient></defs>
<rect width="1920" height="1080" fill="#2a2018"/>
<rect y="0" width="1920" height="760" fill="url(#leg)"/>{pannelli}
<rect y="0" width="1920" height="62" fill="#4a4a4a"/><rect y="62" width="1920" height="8" fill="#2f2f2f"/>
<rect x="500" y="72" width="900" height="16" fill="#e8e1d0" opacity=".85"/>
<rect x="14" y="140" width="70" height="96" rx="6" fill="#161616"/><rect x="1838" y="140" width="70" height="96" rx="6" fill="#161616"/>
<circle cx="49" cy="188" r="22" fill="#2b2b2b"/><circle cx="1873" cy="188" r="22" fill="#2b2b2b"/>
<g transform="translate(20,300)"><rect width="6" height="260" fill="#5c5c5c"/><rect x="6" y="6" width="44" height="30" fill="#2a9d4a"/><rect x="28" y="6" width="22" height="30" fill="#f1f1f1"/><rect x="40" y="6" width="10" height="30" fill="#d12f2f"/></g>
<g transform="translate(1380,0)"><rect x="12" y="258" width="104" height="280" fill="#27358a"/><rect x="12" y="258" width="104" height="14" fill="#1c2766"/><circle cx="64" cy="330" r="22" fill="none" stroke="#dfe6ff" stroke-width="4"/><rect x="34" y="390" width="60" height="6" fill="#dfe6ff" opacity=".8"/><rect x="34" y="410" width="60" height="6" fill="#dfe6ff" opacity=".5"/></g>
<g transform="translate(1690,0)"><rect x="0" y="258" width="104" height="280" fill="#27358a"/><rect y="258" width="104" height="14" fill="#1c2766"/><circle cx="52" cy="330" r="22" fill="none" stroke="#dfe6ff" stroke-width="4"/><rect x="22" y="390" width="60" height="6" fill="#dfe6ff" opacity=".8"/><rect x="22" y="410" width="60" height="6" fill="#dfe6ff" opacity=".5"/></g>
<rect x="1800" y="300" width="100" height="400" rx="4" fill="#9a6a38" stroke="#7a5128" stroke-width="6"/><rect x="1808" y="262" width="84" height="26" rx="4" fill="#1f8f3d"/><rect x="1820" y="272" width="60" height="6" fill="#fff"/>
<rect x="0" y="700" width="1920" height="380" fill="url(#pav)"/>
<rect x="0" y="700" width="1920" height="14" fill="#2a3244" opacity=".6"/>
<rect x="84" y="28" width="1272" height="726" rx="8" fill="#101010"/><rect x="96" y="40" width="1248" height="702" fill="#ffffff"/>
<rect x="84" y="754" width="1272" height="10" fill="#101010" opacity=".5"/>
</svg>"""


def svg_prof(bocca, posa):
    """Professore al leggio. bocca: 0 chiusa, 1 socchiusa, 2 aperta. posa: 0 indica la slide, 1 gesto con le mani aperte."""
    giacca, pelle = "#2c3442", "#e2b08f"
    bocche = {0: '<path d="M1590 360 Q1610 366 1630 360" stroke="#7a3b2e" stroke-width="5" fill="none" stroke-linecap="round"/>',
              1: '<ellipse cx="1610" cy="362" rx="15" ry="6" fill="#5a1f1c"/>',
              2: '<ellipse cx="1610" cy="364" rx="16" ry="14" fill="#5a1f1c"/><ellipse cx="1610" cy="372" rx="9" ry="5" fill="#c95a5a"/>'}
    if posa == 0:
        bracci = (f'<path d="M1530 440 Q1480 420 1420 372" stroke="{giacca}" stroke-width="44" fill="none" stroke-linecap="round"/><circle cx="1414" cy="368" r="24" fill="{pelle}"/>'
                  f'<rect x="1380" y="364" width="70" height="7" rx="3" fill="#c9c9c9" transform="rotate(-26 1414 368)"/>'
                  f'<path d="M1690 440 Q1710 520 1675 580" stroke="{giacca}" stroke-width="44" fill="none" stroke-linecap="round"/><circle cx="1672" cy="586" r="23" fill="{pelle}"/>')
    else:
        bracci = (f'<path d="M1530 440 Q1490 500 1500 520" stroke="{giacca}" stroke-width="44" fill="none" stroke-linecap="round"/><circle cx="1498" cy="520" r="24" fill="{pelle}"/>'
                  f'<path d="M1690 440 Q1735 495 1715 520" stroke="{giacca}" stroke-width="44" fill="none" stroke-linecap="round"/><circle cx="1717" cy="520" r="24" fill="{pelle}"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
<path d="M1500 440 Q1500 392 1560 390 L1660 390 Q1720 392 1720 440 L1720 640 L1500 640 Z" fill="{giacca}"/>
<path d="M1572 392 L1610 470 L1648 392 Z" fill="#d7e4f7"/><path d="M1600 392 L1610 410 L1620 392 Z" fill="#b8312f"/>
<rect x="1590" y="372" width="40" height="30" fill="{pelle}"/>
{bracci}
<ellipse cx="1610" cy="330" rx="53" ry="62" fill="{pelle}"/>
<path d="M1556 322 Q1552 262 1610 258 Q1668 262 1664 322 Q1650 290 1610 288 Q1570 290 1556 322 Z" fill="#8e8f96"/>
<circle cx="1587" cy="330" r="15" fill="none" stroke="#2a2a2a" stroke-width="4"/><circle cx="1633" cy="330" r="15" fill="none" stroke="#2a2a2a" stroke-width="4"/><path d="M1602 330 L1618 330" stroke="#2a2a2a" stroke-width="4"/>
<circle cx="1587" cy="331" r="4" fill="#222"/><circle cx="1633" cy="331" r="4" fill="#222"/>
<path d="M1570 306 Q1587 298 1602 306" stroke="#6d6d74" stroke-width="5" fill="none" stroke-linecap="round"/><path d="M1618 306 Q1633 298 1650 306" stroke="#6d6d74" stroke-width="5" fill="none" stroke-linecap="round"/>
<path d="M1612 336 L1606 352 L1618 352" stroke="#b98568" stroke-width="3" fill="none"/>
{bocche[bocca]}
<rect x="1420" y="600" width="380" height="190" rx="6" fill="#a8743a"/><rect x="1420" y="592" width="380" height="20" rx="4" fill="#c58a4a"/>
<circle cx="1610" cy="700" r="38" fill="none" stroke="#6b4720" stroke-width="5"/><rect x="1590" y="686" width="40" height="30" fill="#6b4720" opacity=".5"/>
<rect x="1520" y="560" width="140" height="36" rx="4" fill="#3a3f4a"/><rect x="1532" y="566" width="116" height="22" fill="#9db9dd"/>
</svg>"""


def svg_primo_piano():
    teste = _teste([(850, 0.62, 18, 40, 108), (925, 0.8, 14, 20, 140)])
    righe = "".join(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y + dy}" stroke="#7fa0d8" stroke-width="2" opacity=".7"/>' for x0, x1, y, dy in [(520, 1380, 1000 + i * 24, -6) for i in range(4)])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
{teste}
<rect x="0" y="1004" width="1920" height="76" fill="#b0773a"/><rect x="0" y="996" width="1920" height="14" fill="#cc9358"/>
<g transform="rotate(-2 940 1030)"><rect x="500" y="978" width="900" height="130" rx="6" fill="#f7f5ee" stroke="#d0cdc0" stroke-width="3"/>
<rect x="500" y="978" width="14" height="130" fill="#e4e0d0"/>{righe}
<rect x="610" y="1000" width="260" height="8" rx="3" fill="#2b3f8a" opacity=".85"/><rect x="610" y="1022" width="380" height="8" rx="3" fill="#2b3f8a" opacity=".6"/><rect x="610" y="1044" width="200" height="8" rx="3" fill="#2b3f8a" opacity=".5"/></g>
<g transform="rotate(28 1480 1040)"><rect x="1380" y="1030" width="230" height="16" rx="8" fill="#1a1a1a"/><rect x="1380" y="1030" width="60" height="16" rx="8" fill="#e2b33a"/></g>
<rect x="1650" y="1010" width="90" height="80" rx="8" fill="#ece4d8"/><rect x="1736" y="1030" width="24" height="36" rx="12" fill="none" stroke="#ece4d8" stroke-width="8"/>
</svg>"""


async def _png(pg, svg, uscita, trasparente=True):
    await pg.set_content(_PAGINA % svg)
    await pg.screenshot(path=str(uscita), omit_background=trasparente)


async def prepara(cart, pw_launch):
    """Disegna una volta sola i livelli fissi nella cartella `cart` (sfondo, primo piano e le 6 posizioni del professore)."""
    cart = Path(cart); cart.mkdir(parents=True, exist_ok=True)
    b = await pw_launch()
    pg = await b.new_page(viewport={"width": W, "height": H})
    await _png(pg, svg_sfondo(), cart / "sfondo.png", False)
    await _png(pg, svg_primo_piano(), cart / "primo.png")
    for bocca in range(3):
        for posa in range(2):
            await _png(pg, svg_prof(bocca, posa), cart / f"prof_{bocca}{posa}.png")
    await b.close()
    return cart


class Aula:
    def __init__(self, cart):
        from PIL import Image
        self.Image = Image
        c = Path(cart)
        self.sfondo = Image.open(c / "sfondo.png").convert("RGBA")
        self.primo = Image.open(c / "primo.png").convert("RGBA")
        self.prof = {(b, p): Image.open(c / f"prof_{b}{p}.png").convert("RGBA") for b in range(3) for p in range(2)}

    def base(self, slide_png):
        """Sfondo + slide dentro lo schermo + primo piano (senza professore)."""
        x, y, w, h = SCHERMO
        sl = self.Image.open(slide_png).convert("RGB").resize((w, h), self.Image.LANCZOS)
        f = self.sfondo.copy(); f.paste(sl, (x, y))
        return f

    def fotogramma(self, base, bocca, posa, uscita):
        f = self.Image.alpha_composite(base, self.prof[(bocca, posa)])
        f = self.Image.alpha_composite(f, self.primo)
        f.convert("RGB").save(uscita, "JPEG", quality=90)


def inviluppo(mp3, fps):
    """Energia della voce per fotogramma (0..1): serve a muovere la bocca."""
    import subprocess
    import numpy as np
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-f", "s16le", "-ac", "1", "-ar", "8000", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768
    n = max(1, int(8000 / fps))
    e = np.array([float(np.sqrt(np.mean(a[i:i + n] ** 2))) if len(a[i:i + n]) else 0.0 for i in range(0, len(a), n)])
    return np.clip(e / (float(np.percentile(e, 90)) or 1), 0, 1.5)


def sequenza(env, fps, durata_tot):
    """[(bocca, posa)] per ogni fotogramma: bocca da l'energia, posa cambia ogni circa 2,5 secondi mentre parla."""
    n = int(round(durata_tot * fps)) or 1
    out = []
    for i in range(n):
        e = float(env[i]) if i < len(env) else 0.0
        bocca = 0 if e < 0.2 else (1 if e < 0.65 else 2)
        posa = int(i / fps / 2.5) % 2 if i < len(env) else 0
        out.append((bocca, posa))
    return out
