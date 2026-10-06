"""Video "orari del Gran Premio" da fissare sul profilo: una sola schermata che resta ferma dall'inizio alla fine (foto del favorito,
titolo e tutti gli orari in ora italiana) e la voce Diego che li legge. I dati vengono da docs/data (nessun orario scritto a mano).

Uso:  python3 orari_gp.py f1|moto [--uscita FILE]
"""
import argparse
import asyncio
import base64
import json
import ssl
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import edge_tts
import edge_tts.communicate as C
from playwright.async_api import async_playwright

C._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
QUI = Path(__file__).parent
SITO = QUI.parent / "docs"
FONT = QUI / "logo" / "font"
CHROMIUM = "/opt/pw-browsers/chromium"
ROMA = ZoneInfo("Europe/Rome")
W, H = 1080, 1920
VOCE, VELOCITA = "it-IT-DiegoNeural", "+8%"
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
UNITA = ["zero", "uno", "due", "tre", "quattro", "cinque", "sei", "sette", "otto", "nove", "dieci", "undici", "dodici", "tredici", "quattordici", "quindici",
         "sedici", "diciassette", "diciotto", "diciannove"]
DECINE = {2: "venti", 3: "trenta", 4: "quaranta", 5: "cinquanta"}


def numero(n):
    if n < 20:
        return UNITA[n]
    d, u = divmod(n, 10)
    base = DECINE[d]
    if u in (1, 8):
        base = base[:-1]
    return base + ("" if u == 0 else UNITA[u])


def a_voce(h, m):
    ore = "all'una" if h == 1 else f"alle {numero(h)}" if h else "a mezzanotte"
    return ore + ("" if m == 0 else " e " + numero(m))


def carica(serie):
    pron = json.load(open(SITO / "data/pronostici.json"))
    if serie == "f1":
        ev = json.load(open(SITO / "data/events.json"))
        gara = pron["f1"]["gara"]
        w = next(x for x in ev if any(s["nome"] == "Gara" and datetime.fromisoformat(s["inizio"]) == datetime.fromisoformat(gara) for s in x["sessioni"]))
        ro = json.load(open(SITO / "data/roster.json"))
        fav = pron["f1"]["favoriti"][0]["nome"]
        foto = next(p for p in ro if p["nome"] == fav)["foto"]
        return dict(sigla="F1", colore="#e8352f", titolo=w["nome"], luogo=w["paese"] or w["circuito"], fav=fav, foto=foto, sessioni=w["sessioni"], motogp=False)
    mg = json.load(open(SITO / "data/motogp.json"))["weekend"]
    gara = pron["motogp"]["gara"]
    w = next(x for x in mg if any(s["nome"] == "Gara" and datetime.fromisoformat(s["inizio"]) == datetime.fromisoformat(gara) for s in x["sessioni"]))
    fav = pron["motogp"]["favoriti"][0]
    fm = json.load(open(SITO / "data/foto-motogp.json"))
    return dict(sigla="MotoGP", colore="#1f5fd1", titolo=w["nome"], luogo=w["circuito"], fav=fav["nome"], foto=fm[fav["id"]], sessioni=w["sessioni"], motogp=True)


def righe(d):
    """[(giorno_testo, [(nome, 'HH:MM', h, m), ...]), ...] in ora italiana."""
    out = {}
    for s in d["sessioni"]:
        t = datetime.fromisoformat(s["inizio"]).astimezone(ROMA)
        nome = s["nome"]
        if d["motogp"] and nome == "Prove libere":
            nome = "Practice"
        out.setdefault((t.date(), f"{GIORNI[t.weekday()]} {t.day} {MESI[t.month - 1]}"), []).append((nome, t.strftime("%H:%M"), t.hour, t.minute))
    return [(g[1], v) for g, v in sorted(out.items())]


def copione(d, gruppi):
    nome_gp = d["titolo"].replace("GP ", "Gran Premio d'", 1) if d["titolo"].startswith("GP ") else d["titolo"]
    serie = "di Moto G P" if d["motogp"] else ""
    t = [(f"{nome_gp} {serie}").strip() + ".", "Ecco tutti gli orari, in ora italiana."]
    if d["motogp"]:
        t.append("Attenzione: le sessioni sono di prima mattina.")
    for giorno, sess in gruppi:
        parti = [f"{n.lower().replace('warm up', 'warm up').replace('qualifiche 1', 'qualifiche uno').replace('qualifiche 2', 'qualifiche due').replace('prove libere 1', 'prove libere uno').replace('prove libere 2', 'prove libere due')} {a_voce(h, m)}" for n, _, h, m in sess]
        parti[-1] = parti[-1].replace("gara ", "la gara ", 1) if parti[-1].startswith("gara") else parti[-1]
        t.append(f"{giorno[0].upper() + giorno[1:]}: " + ", ".join(parti) + ".")
    t.append(f"Il nostro favorito è {d['fav']}.")
    t.append("Tutto su G P Oggi punto it.")
    return " ".join(t)


def b64(p):
    return base64.b64encode(Path(p).read_bytes()).decode()


def pagina(d, gruppi):
    foto = SITO / (d["foto"].get("file_grande") or d["foto"]["file"])
    n_righe = sum(len(s) for _, s in gruppi)
    riga_h = 66 if n_righe <= 5 else 48
    nome_px, ora_px, giorno_px, giorno_mt = (44, 56, 40, 26) if n_righe <= 5 else (36, 46, 34, 18)
    righe_html = ""
    for giorno, sess in gruppi:
        righe_html += f'<div class="giorno">{giorno}</div>'
        for nome, ora, _, _ in sess:
            righe_html += f'<div class="riga{" gara" if nome == "Gara" else ""}" style="height:{riga_h}px"><span>{nome}</span><b>{ora}</b></div>'
    spazio = n_righe * riga_h + len(gruppi) * (giorno_px + giorno_mt + 14)
    fine_tab = 1030 + spazio
    font = (f"@font-face{{font-family:Oswald;font-weight:700;src:url(data:font/woff2;base64,{b64(FONT / 'oswald-latin-700-normal.woff2')})}}"
            f"@font-face{{font-family:Inter;font-weight:500;src:url(data:font/woff2;base64,{b64(FONT / 'inter-latin-500-normal.woff2')})}}")
    return f"""<!doctype html><meta charset=utf-8><style>{font}
*{{box-sizing:border-box}} html,body{{margin:0;width:{W}px;height:{H}px;background:#0b0b0e;color:#fff;font-family:Inter,sans-serif;overflow:hidden}}
.logo{{position:absolute;left:0;right:0;top:34px;text-align:center}} .logo img{{width:300px}}
.foto{{position:absolute;left:0;top:190px;width:{W}px;height:610px;background:url(data:image/jpeg;base64,{b64(foto)}) center {'-98' if d['motogp'] else '-105'}px/{W}px auto no-repeat}}
.vel{{position:absolute;left:0;top:190px;width:{W}px;height:610px;background:linear-gradient(180deg,#0b0b0e 0%,rgba(11,11,14,0) 14%,rgba(11,11,14,0) 66%,#0b0b0e 100%)}}
.pill{{position:absolute;left:70px;top:786px;font:700 32px Oswald;letter-spacing:.08em;background:{d['colore']};padding:3px 20px;border-radius:8px;text-transform:uppercase}}
h1{{position:absolute;left:70px;right:70px;top:846px;margin:0;font:700 78px/1 Oswald;text-transform:uppercase;white-space:nowrap}}
.sotto{{position:absolute;left:70px;right:70px;top:946px;font:500 32px Inter;color:#c9c9d2;white-space:nowrap}}
.ora-it{{position:absolute;right:70px;top:792px;font:700 30px Oswald;letter-spacing:.08em;text-transform:uppercase;color:#c9c9d2}}
.tab{{position:absolute;left:70px;right:70px;top:1030px}}
.giorno{{font:700 {giorno_px}px Oswald;letter-spacing:.08em;text-transform:uppercase;color:{d['colore']};margin-top:{giorno_mt}px;padding-bottom:6px}}
.giorno:first-child{{margin-top:0}}
.riga{{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #26262e;font:500 {nome_px}px Inter}}
.riga b{{font:700 {ora_px}px Oswald;letter-spacing:.02em}}
.riga.gara{{background:{d['colore']}30;border-bottom:0;border-radius:10px;padding:0 14px;margin:0 -14px;border-left:8px solid {d['colore']}}}
.fav{{position:absolute;left:70px;right:70px;top:{fine_tab + 34}px;font:500 36px Inter;color:#e6e6ec}} .fav b{{color:#fff}}
.cred{{position:absolute;left:70px;right:70px;top:{fine_tab + 90}px;font:500 24px Inter;color:#8a8a96}}
.url{{position:absolute;left:0;right:0;top:{max(fine_tab + 140, 1730)}px;text-align:center;font:700 60px Oswald;color:{d['colore']};letter-spacing:.04em}}
.avviso{{position:absolute;left:70px;right:70px;top:1835px;text-align:center;font:500 22px Inter;color:#6d6d78}}
</style>
<div class=logo><img src="data:image/png;base64,{b64(SITO / 'img/logo-wide-scuro.png')}"></div>
<div class=foto></div><div class=vel></div>
<span class=pill>{d['sigla']}</span><h1>{d['titolo']}</h1><span class=ora-it>Orari in ora italiana</span><div class=sotto>{d['luogo']}</div>
<div class=tab>{righe_html}</div>
<div class=fav>Il nostro favorito: <b>{d['fav']}</b></div>
<div class=cred>Foto: {d['foto'].get('autore', '')} · {d['foto'].get('licenza', '')} · via Wikimedia Commons</div>
<div class=url>gpoggi.it</div>
<div class=avviso>Sito non ufficiale, non affiliato a Formula 1, FIA, MotoGP, Dorna o ai team</div>"""


async def main(args):
    d = carica(args.serie)
    gruppi = righe(d)
    testo = copione(d, gruppi)
    print("VOCE:", testo)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        await edge_tts.Communicate(testo, VOCE, rate=VELOCITA).save(str(tmp / "voce.mp3"))
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path=CHROMIUM)
            pg = await b.new_page(viewport={"width": W, "height": H})
            await pg.set_content(pagina(d, gruppi))
            await pg.wait_for_timeout(600)
            await pg.screenshot(path=str(tmp / "copertina.png"))
            await pg.screenshot(path=str(args.uscita.with_suffix(".png")))
            await b.close()
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(tmp / "voce.mp3")], capture_output=True, text=True).stdout)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", str(tmp / "copertina.png"), "-i", str(tmp / "voce.mp3"),
                        "-af", "adelay=500:all=1,apad=pad_dur=1.2,loudnorm=I=-14:TP=-1.5:LRA=9", "-t", f"{dur + 1.9:.2f}", "-c:v", "libx264", "-tune", "stillimage",
                        "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", str(args.uscita)], check=True)
        print(f"Fatto: {args.uscita} ({dur + 1.9:.1f}s)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("serie", choices=["f1", "moto"])
    ap.add_argument("--uscita", type=Path, default=None)
    a = ap.parse_args()
    a.uscita = a.uscita or QUI / f"orari-{a.serie}.mp4"
    asyncio.run(main(a))
