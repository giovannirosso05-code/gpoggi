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
VOCE, VELOCITA = "it-IT-DiegoNeural", "+19%"
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


def tipo_sessione(nome):
    n = nome.lower()
    if n == "gara":
        return "gara"
    if n.startswith("qualifiche") and "sprint" not in n:
        return "qualifica"
    return "altro"


def pagina(d, gruppi):
    foto = SITO / (d["foto"].get("file_grande") or d["foto"]["file"])
    colore, ambra = d["colore"], "#f5b301"
    flat = [(g, n, o) for g, sess in gruppi for n, o, _, _ in sess]
    gara = [x for x in flat if tipo_sessione(x[1]) == "gara"]
    qual = [x for x in flat if tipo_sessione(x[1]) == "qualifica"]
    altre = [x for x in flat if tipo_sessione(x[1]) == "altro"]
    sigla_g = lambda g: g.split()[0][:3].upper() + " " + g.split()[1]
    font = (f"@font-face{{font-family:Oswald;font-weight:700;src:url(data:font/woff2;base64,{b64(FONT / 'oswald-latin-700-normal.woff2')})}}"
            f"@font-face{{font-family:Inter;font-weight:500;src:url(data:font/woff2;base64,{b64(FONT / 'inter-latin-500-normal.woff2')})}}")
    carte = ""
    for g, n, o in gara:
        carte += (f'<div class="carta gara"><div class="scacchi"></div><div><div class="et">{n}</div><div class="gg">{g}</div></div>'
                  f'<b class="ora" style="font-size:130px">{o}</b></div>')
    if qual:
        carte += '<div class="coppia">' + "".join(
            f'<div class="carta qual"><div><div class="et">{n}</div><div class="gg">{g}</div></div><b class="ora" style="font-size:{78 if len(qual) == 1 else 66}px">{o}</b></div>'
            for g, n, o in qual) + "</div>"
    chips = "".join(f'<div class="chip"><span class="cg">{sigla_g(g)}</span><span class="cn">{n}</span><b>{o}</b></div>' for g, n, o in altre)
    return f"""<!doctype html><meta charset=utf-8><style>{font}
*{{box-sizing:border-box}} html,body{{margin:0;width:{W}px;height:{H}px;background:#0b0b0e;color:#fff;font-family:Inter,sans-serif;overflow:hidden}}
/* zona sicura: i pulsanti di TikTok e Instagram stanno a destra (circa 160 px) e in alto, la didascalia in basso */
.logo{{position:absolute;left:0;right:0;top:135px;text-align:center}} .logo img{{width:210px}}
.foto{{position:absolute;left:0;top:260px;width:{W}px;height:600px;background:url(data:image/jpeg;base64,{b64(foto)}) center {'-175' if d['motogp'] else '-85'}px/{W}px auto no-repeat}}
.vel{{position:absolute;left:0;top:260px;width:{W}px;height:600px;background:linear-gradient(180deg,#0b0b0e 0%,rgba(11,11,14,0) 16%,rgba(11,11,14,0) 62%,#0b0b0e 100%)}}
.testata{{position:absolute;left:60px;width:860px;top:825px}}
.pill{{display:inline-block;font:700 28px Oswald;letter-spacing:.1em;background:{colore};padding:3px 16px;border-radius:8px;text-transform:uppercase;vertical-align:middle}}
.ora-it{{float:right;font:700 24px Oswald;letter-spacing:.1em;text-transform:uppercase;color:#c9c9d2;margin-top:6px}}
h1{{margin:12px 0 0;font:700 64px/1 Oswald;text-transform:uppercase;white-space:nowrap}}
.sotto{{font:500 28px Inter;color:#c9c9d2;margin-top:8px;white-space:nowrap}} .sotto b{{color:#fff}}
.blocco{{position:absolute;left:60px;width:860px;top:1050px}}
.carta{{position:relative;overflow:hidden;display:flex;justify-content:space-between;align-items:center;border-radius:20px;padding:0 30px;margin-bottom:16px}}
.carta .et{{font:700 38px Oswald;letter-spacing:.1em;text-transform:uppercase}} .carta .gg{{font:500 26px Inter;opacity:.85;text-transform:capitalize;margin-top:2px}}
.carta .ora{{font-family:Oswald;font-weight:700;line-height:1;letter-spacing:.01em}}
.carta.gara{{height:190px;background:linear-gradient(100deg,{colore} 0%,{colore} 55%,#0b0b0e 220%)}}
.carta.gara .et{{font-size:56px}}
.scacchi{{position:absolute;right:0;top:0;bottom:0;width:340px;opacity:.22;background:conic-gradient(#000 25%,transparent 0 50%,#000 0 75%,transparent 0) 0 0/46px 46px;-webkit-mask-image:linear-gradient(90deg,transparent,#000);mask-image:linear-gradient(90deg,transparent,#000)}}
.carta.gara .et,.carta.gara .gg,.carta.gara .ora{{position:relative}}
.coppia{{display:flex;gap:16px}} .coppia .carta{{flex:1;margin-bottom:16px;height:125px;padding:0 22px}}
.carta.qual{{background:linear-gradient(100deg,{ambra} 0%,#c98a00 100%);color:#1a1300}} .carta.qual .et{{font-size:34px}} .coppia .carta.qual .et{{font-size:27px;letter-spacing:.05em;white-space:nowrap}} .carta.qual .gg{{font-size:22px}}
.chips{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.chip{{display:flex;align-items:center;gap:12px;background:#17171d;border-radius:12px;padding:0 16px;height:60px;white-space:nowrap}}
.cg{{font:700 22px Oswald;letter-spacing:.06em;color:{colore};width:64px;flex:none}} .cn{{flex:1;font:500 25px Inter;color:#c9c9d2;overflow:hidden;text-overflow:ellipsis}}
.chip b{{font:700 32px Oswald;color:#fff}}
.piede{{margin-top:16px}} .url{{font:700 44px Oswald;color:{colore};letter-spacing:.04em}}
.piccolo{{font:500 20px Inter;color:#6d6d78;margin-top:4px}}
</style>
<div class=logo><img src="data:image/png;base64,{b64(SITO / 'img/logo-wide-scuro.png')}"></div>
<div class=foto></div><div class=vel></div>
<div class=testata><span class=pill>{d['sigla']}</span><span class=ora-it>Orari in ora italiana</span><h1>{d['titolo']}</h1>
<div class=sotto>{d['luogo'][:34]}</div><div class=sotto style='margin-top:2px'>Il nostro favorito: <b>{d['fav']}</b></div></div>
<div class=blocco>{carte}<div class=chips>{chips}</div>
<div class=piede><div class=url>gpoggi.it</div><div class=piccolo>Sito non ufficiale, non affiliato a Formula 1, FIA, MotoGP, Dorna o ai team</div>
<div class=piccolo>Foto: {d['foto'].get('autore', '')} · {d['foto'].get('licenza', '')} · via Wikimedia Commons</div></div></div>"""


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
