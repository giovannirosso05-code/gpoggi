"""Video breve (circa 20 secondi) "Chi sale sul podio?": immagini fisse del sito, scritte grandi e voce, senza dimostrare come funziona.
I Gran Premi e i piloti sono quelli della settimana (stessa scelta di demo_giochi.contesto_pronostico). Senza gare in settimana esce con codice 75.

Uso:  python3 pronostico_breve.py [--uscita FILE]     (PRON_ORA=2026-10-08T10:00:00Z simula un altro momento)
Scrive anche FILE.txt con la didascalia per TikTok.
"""
import argparse
import asyncio
import base64
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).parent))
import demo_giochi as G  # noqa: E402
import demo_sito as D  # noqa: E402

D.VELOCITA = "+34%"
PORTA = 8143
W, H = D.W, D.H
SITO = D.SITO
ROSSO, BLU = "#e8352f", "#1f5fd1"


def uri_foto(percorso):
    f = SITO / percorso
    tipo = "png" if f.suffix == ".png" else "jpeg"
    return f"data:image/{tipo};base64," + base64.b64encode(f.read_bytes()).decode()


def foto_pilota(nome, serie_id):
    dati = SITO / "data"
    if serie_id == "f1":
        for p in json.load(open(dati / "roster.json")):
            if p.get("nome") == nome and p.get("foto"):
                return p["foto"].get("file") or p["foto"].get("file_grande")
        return None
    f = json.load(open(dati / "foto-motogp.json")).get("nome:" + nome)
    return (f or {}).get("file")


async def schermate(browser, base, serie, nomi_fotografati):
    """Tre immagini del sito (elenco giochi, premio, modulo compilato) con le coordinate della scheda da evidenziare."""
    k = 920 / 390
    ctx = await browser.new_context(viewport={"width": 390, "height": 600}, device_scale_factor=k, is_mobile=True)
    # il server dei voti è finto: nessun voto vero, nessuna rete
    await ctx.route(G.re.compile(r"gpoggivotti\.giovannirosso05\.workers\.dev"), G.finto_server_voti)
    await ctx.route(G.re.compile(r"^https?://(?!localhost)"), D._esterna)
    page = await ctx.new_page()
    out = {}
    await page.goto(base + "/giochi.html")
    await page.wait_for_selector('.gioco-card[data-gioco="pronostico"]')
    await page.evaluate("document.querySelector('.gioco-card[data-gioco=\"pronostico\"]').scrollIntoView({block:'start'}); window.scrollBy(0, -200)")
    # nel video niente premi in denaro: TikTok lo scambia per una scommessa
    await page.evaluate("document.querySelector('.gioco-card[data-gioco=\"pronostico\"] span').textContent = 'Scegli il podio di F1 e MotoGP ed entra nella classifica dei tifosi.'")
    await page.wait_for_timeout(400)
    box = await page.evaluate("(() => { const r = document.querySelector('.gioco-card[data-gioco=\"pronostico\"]').getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; })()")
    out["elenco"] = (await page.screenshot(type="png"), box)
    await page.click('.gioco-card[data-gioco="pronostico"]')
    await page.wait_for_selector("#p1")
    if serie[0]["id"] == "moto":
        await page.click(".chip-serie.moto")
        await page.wait_for_function("(n) => { const e = document.getElementById('p1'); return e && [...e.options].some((o) => o.textContent === n); }", arg=serie[0]["nomi"][0])
    for i, nome in enumerate(serie[0]["nomi"], 1):
        await page.evaluate("(a) => { const s = document.getElementById('p' + a.i); const o = [...s.options].find((x) => x.textContent === a.t); s.value = o.value; }", {"i": i, "t": nome})
    # pole al primo e giro veloce al secondo: si vede che oltre al podio ci sono altre due scelte
    for campo, nome in (("pole", serie[0]["nomi"][0]), ("giro", serie[0]["nomi"][1])):
        await page.evaluate("(a) => { const s = document.getElementById(a.c); const o = [...s.options].find((x) => x.textContent === a.t); if (o) s.value = o.value; }", {"c": campo, "t": nome})
    await page.fill("#nome", "GP_Fan")
    # nella schermata del modulo la testata del sito coprirebbe il titolo: si toglie, così si vedono podio, pole e giro veloce
    await page.add_style_tag(content=".site-header{display:none!important} body{padding-top:0!important} .pron-premio,.pron-doppio,.chip-serie-riga,.pron-testa,.page-title,main > h1,main > p,.section-title{display:none!important}")
    await page.evaluate("(() => { const s = document.querySelector('#vista-voto .quiz-titolo'); window.scrollTo(0, s.getBoundingClientRect().top + window.scrollY - 24); })()")
    await page.wait_for_timeout(300)
    out["modulo"] = (await page.screenshot(type="png"), None)
    await ctx.close()
    return out


def slide(titolo_html, sottotitolo, immagine=None, evidenzia=None, extra_html="", css_extra=""):
    k = 920 / 390
    img_html = ""
    if immagine:
        b64 = base64.b64encode(immagine).decode()
        marker = ""
        if evidenzia:
            x, y, w, h = evidenzia
            marker = f'<div style="position:absolute;left:{x * k - 10:.0f}px;top:{y * k - 10:.0f}px;width:{w * k + 20:.0f}px;height:{h * k + 20:.0f}px;border:10px solid {ROSSO};border-radius:36px;box-shadow:0 0 0 9999px rgba(0,0,0,.35)"></div>'
        img_html = (f'<div style="position:absolute;left:80px;top:430px;width:920px;height:1415px;border-radius:52px;overflow:hidden;box-shadow:0 30px 90px rgba(0,0,0,.6);background:#fff">'
                    f'<img src="data:image/png;base64,{b64}" style="width:920px;display:block">{marker}</div>')
    corpo = (f'<div class="c o" style="top:70px;font-size:104px;line-height:1.02;padding:0 50px">{titolo_html}</div>'
             f'<div class="c o" style="top:{300 if immagine else 330}px;font-size:56px;color:#ffd21f;padding:0 60px">{sottotitolo}</div>' + img_html + extra_html)
    return D._html(corpo, css_extra + ".y{color:#ffd21f}")


def slide_apertura(serie):
    righe = ""
    top = 740
    for s in serie:
        colore = BLU if s["id"] == "moto" else ROSSO
        sigla = "MotoGP" if s["id"] == "moto" else "F1"
        faccine = ""
        for n, nome in enumerate(s["nomi"]):
            f = foto_pilota(nome, s["id"])
            if f:
                faccine += f'<img src="{uri_foto(f)}" style="width:220px;height:220px;border-radius:50%;object-fit:cover;object-position:center 15%;border:8px solid {colore};margin:0 16px">'
        righe += (f'<div class="c" style="top:{top}px"><span class="o" style="background:{colore};padding:8px 30px;border-radius:12px;font-size:56px">{sigla}</span>'
                  f'<div class="o" style="font-size:76px;margin:18px 0 22px">{s["gp"]}</div><div style="display:flex;justify-content:center">{faccine}</div></div>')
        top += 600
    corpo = ('<div class="c o" style="top:110px;font-size:150px;line-height:1">Chi sale<br>sul <span class="r">podio</span>?</div>'
             '<div class="c o" style="top:470px;font-size:64px;line-height:1.05;color:#ffd21f">Indovinalo e sfida i tifosi</div>' + righe)
    return D._html(corpo)


def chiusure(serie):
    """Orario di chiusura dei voti (inizio qualifiche) per ogni serie della settimana, in ora italiana."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    orari = json.load(open(SITO / "data" / "gara-orari.json"))
    adesso = datetime.now(ZoneInfo("UTC"))
    giorni = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
    out = []
    for s in serie:
        qs = sorted(datetime.fromisoformat(v) for k, v in orari.items() if k.startswith("q:") and (k[2:].startswith("m") == (s["id"] == "moto"))
                    and datetime.fromisoformat(v) > adesso)
        if qs:
            t = qs[0].astimezone(ZoneInfo("Europe/Rome"))
            out.append((s, f"{giorni[t.weekday()]} {t:%H:%M}"))
    return out


def slide_chiusura(serie):
    righe, top = "", 640
    for s, quando in chiusure(serie):
        colore = BLU if s["id"] == "moto" else ROSSO
        sigla = "MotoGP" if s["id"] == "moto" else "F1"
        righe += (f'<div class="c" style="top:{top}px"><span class="o" style="background:{colore};padding:8px 30px;border-radius:12px;font-size:60px">{sigla}</span>'
                  f'<div class="o" style="font-size:96px;margin-top:22px">{quando}</div></div>')
        top += 340
    corpo = ('<div class="c o" style="top:150px;font-size:130px;line-height:1">Si chiude<br>alle <span class="r">qualifiche</span></div>'
             '<div class="c o" style="top:480px;font-size:56px;color:#ffd21f">Dopo non si cambia più niente</div>' + righe +
             f'<div class="c o" style="top:{top + 80}px;font-size:66px;line-height:1.1;padding:0 60px">Vota <span class="r">F1</span> + <span style="color:{BLU}">MotoGP</span><br>i punti si sommano</div>')
    return D._html(corpo)


def slide_fine():
    corpo = (f'<img src="{D._logo_uri()}" style="position:absolute;left:90px;top:300px;width:900px">'
             '<div class="c o r" style="top:830px;font-size:150px;line-height:1">Gioca ora</div>'
             '<div class="c o" style="top:1030px;font-size:84px">gpoggi.it → Giochi</div>'
             '<div class="c" style="top:1200px;font-size:50px;color:#ffd21f;font-weight:700">Gratis · classifica F1 e MotoGP</div>'
             '<div class="c o" style="top:1310px;font-size:62px">Segui <span class="r">@gp.oggi</span></div>'
             '<div class="c" style="top:1700px;font-size:28px;color:#85858f;padding:0 60px">Sito non ufficiale, non affiliato a Formula 1, FIA, MotoGP, Dorna o ai team</div>')
    return D._html(corpo)


def clip_da_png(png, secondi, uscita):
    frames = int(secondi * D.FPS) + 1
    vf = (f"scale={W * 2}:{H * 2},zoompan=z='1+0.07*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={D.FPS},"
          f"fade=t=in:d=0.12")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(png), "-t", f"{secondi:.2f}", "-vf", vf,
                    "-r", str(D.FPS), "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(uscita)], check=True)


async def principale(uscita):
    serie = G.contesto_pronostico()
    if not serie:
        print("Questa settimana non c'è nessuna gara: nessun video.")
        sys.exit(75)
    nomi_gp = " e nel ".join(x["gp"] for x in serie)
    Path(str(uscita) + ".txt").write_text(
        f"Chi sale sul podio nel {nomi_gp}? 🏁 Scegli podio, pole e giro più veloce e sfida gli altri tifosi nella classifica di GP Oggi. Si vota fino all'inizio delle qualifiche! Gioco gratuito, link nel commento fissato. #f1 #motogp #formula1 #gpoggi",
        encoding="utf-8")
    base = f"http://localhost:{PORTA}"
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORTA), "-d", str(SITO)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            gp_parlato = " e il ".join(x["gp"] for x in serie)
            testi = [f"Chi sale sul podio questo weekend? {gp_parlato}. Indovinalo e sfida gli altri tifosi!",
                     "Vai su G P Oggi punto it e tocca Giochi: è il primo gioco.",
                     "Scegli il podio, poi chi fa la pole e il giro più veloce. Più indovini, più punti fai.",
                     "Ma attenzione: si vota solo fino alle qualifiche. Fai Formula 1 e MotoGP, i punti si sommano.",
                     "È gratis. Segui G P punto oggi e gioca su G P Oggi punto it!"]
            voci, durate = [], []
            for i, t in enumerate(testi):
                f = tmp / f"voce{i}.mp3"
                await D._voce(t, f)
                voci.append(f)
                durate.append(D._durata(f) + 0.35)
            async with async_playwright() as p:
                browser = await p.chromium.launch(executable_path=D.CHROMIUM)
                sh = await schermate(browser, base, serie, None)
                htmls = [slide_apertura(serie),
                         slide('Tocca <span class="r">Giochi</span>', "Primo gioco: il podio del weekend", *sh["elenco"][:1], evidenzia=sh["elenco"][1]),
                         slide('Podio, <span class="r">pole</span><br>e giro veloce', "Più indovini, più punti fai", sh["modulo"][0]),
                         slide_chiusura(serie),
                         slide_fine()]
                clips = []
                for i, h in enumerate(htmls):
                    pg = await browser.new_page(viewport={"width": W, "height": H})
                    await pg.set_content(h)
                    await pg.wait_for_timeout(500)
                    png = tmp / f"s{i}.png"
                    png.write_bytes(await pg.screenshot(type="png"))
                    await pg.close()
                    clip = tmp / f"c{i}.mp4"
                    clip_da_png(png, durate[i], clip)
                    clips.append(clip)
                await browser.close()
            lista = tmp / "lista.txt"
            lista.write_text("".join(f"file '{c}'\n" for c in clips))
            video = tmp / "video.mp4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(video)], check=True)
            partenze, t = [], 0.0
            for d in durate:
                partenze.append(t)
                t += d
            ingressi, filtri = [], []
            for i, (f, t0) in enumerate(zip(voci, partenze)):
                ingressi += ["-i", str(f)]
                filtri.append(f"[{i + 1}:a]adelay={int((t0 + 0.12) * 1000)}:all=1[v{i}]")
            mix = "".join(f"[v{i}]" for i in range(len(voci)))
            filtri.append(f"{mix}amix=inputs={len(voci)}:normalize=0,aformat=sample_rates=44100:channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=9[a]")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), *ingressi, "-filter_complex", ";".join(filtri), "-map", "0:v", "-map", "[a]",
                            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", str(uscita)], check=True)
            print(f"Fatto: {uscita} ({D._durata(uscita):.1f}s)")
    finally:
        srv.terminate()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--uscita", default=str(Path(__file__).parent / "pronostico-breve.mp4"))
    asyncio.run(principale(ap.parse_args().uscita))
