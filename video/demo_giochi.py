"""Video "provo un gioco di GP Oggi" per TikTok e Instagram: si gioca davvero sul sito (cursore che tocca, risposte giuste e una sbagliata, punteggio finale),
con la voce di Diego che accompagna ogni passaggio. Stesso metodo del tour del sito (demo_sito.py).

Uso:  python3 demo_giochi.py pixel|pilota|circuito|moto [--prova] [--uscita FILE]

Per rispondere in modo credibile, solo durante la ripresa la pagina espone le domande del gioco (window.__qs): il sito pubblicato non cambia.
"""
import argparse
import asyncio
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).parent))
import demo_sito as D  # noqa: E402

SITO = D.SITO
PORTA = 8142

GIOCHI = {
    "pixel": dict(chiave="pixel", nome="Chi è? Foto pixelata", modo=None, intro="Riconosci un pilota da una foto sgranata? Ecco il nuovo gioco di G P Oggi!",
                  apri="Sul sito ci sono nove giochi, tutti gratis e senza registrazione. Apriamo «Chi è? Foto pixelata».",
                  scelta="Tocco il gioco e si parte.",
                  prima="La foto parte molto sgranata e si schiarisce a poco a poco: prima indovini, più punti fai.",
                  sbaglio="Se sbagli, il gioco ti mostra chi era.",
                  avanti="Dieci foto, con tutti i piloti dell'archivio: da quelli di oggi alle leggende.",
                  fine="Alla fine vedi il punteggio su cinquanta e il tuo record. Quanto fai tu?"),
    "pilota": dict(chiave="pilota", nome="Chi è il pilota?", modo="oggi", intro="Sai riconoscere i piloti di Formula uno e di Moto G P? Mettiti alla prova con i giochi di G P Oggi!",
                   apri="Sul sito ci sono nove giochi, tutti gratis e senza registrazione. Apriamo «Chi è il pilota?».",
                   scelta="Scelgo la difficoltà: oggi i piloti della griglia.",
                   prima="Ti mostra una foto e quattro nomi: tocca quello giusto.",
                   sbaglio="Se sbagli, il gioco te lo dice subito e ti fa vedere la risposta.",
                   avanti="E così per dieci domande: più sei veloce, meglio è.",
                   fine="Alla fine vedi il punteggio e il tuo record, che resta sul telefono. Riesci a fare dieci su dieci?"),
    "circuito": dict(chiave="circuito", nome="Indovina il circuito", modo=None, intro="Conosci a memoria i circuiti della Formula uno? Proviamo con il gioco di G P Oggi!",
                     apri="Sul sito ci sono nove giochi, tutti gratis e senza registrazione. Apriamo «Indovina il circuito».",
                     scelta=None,
                     prima="Ti mostra solo il tracciato, senza nomi: di quale Gran Premio si tratta?",
                     sbaglio="Se sbagli, il gioco ti dice qual era quello giusto.",
                     avanti="Dieci tracciati da riconoscere: quanti ne indovini?",
                     fine="Alla fine vedi il punteggio e il tuo record. Riesci a farli tutti?"),
    "moto": dict(chiave="moto", nome="MotoGP: che moto guida?", modo=None, intro="Sai con che moto corre ogni pilota della Moto G P? Giochiamo insieme su G P Oggi!",
                 apri="Sul sito ci sono nove giochi, tutti gratis e senza registrazione. Apriamo «Moto G P: che moto guida?».",
                 scelta=None,
                 prima="Ti dice il pilota, tu scegli la marca della moto.",
                 sbaglio="Se sbagli, il gioco te lo dice subito.",
                 avanti="Dieci domande per scoprire quanto conosci la griglia.",
                 fine="Alla fine vedi il punteggio e il tuo record. Riesci a fare il pieno?"),
    "pronostico": dict(chiave="pronostico", nome="Pronostico del podio", modo=None, custom=True,
                       intro="Che podio fai a Singapore e in Indonesia? Chi è primo a fine anno vince una carta Amazon da cinquanta euro!",
                       voci=["Vai su G P Oggi punto it e tocca Giochi. Costa niente e non serve registrarsi.",
                             "Il primo gioco è il pronostico del podio. Chi è primo in classifica a fine anno vince una carta regalo Amazon da cinquanta euro.",
                             "Per ogni posto scegli un pilota: primo, secondo e terzo.",
                             "Scegli il podio di Formula uno, scrivi il tuo nickname e la tua email, che serve solo per mandarti il premio. Tocca Salva e fai uno screenshot del codice di recupero.",
                             "Lo stesso vale per la Moto G P: tocca Moto G P e scegli il podio dell'Indonesia.",
                             "Vedi anche chi ha già votato. La classifica si aggiorna dopo ogni gara, e il regolamento è sul sito. Vota su G P Oggi punto it: che podio fai tu?"],
                       did=["Giochi · gratis", "Premio: carta Amazon 50 €", "Scegli il podio", "Nickname, email e codice", "Anche per la MotoGP", "Chi ha già votato"]),
}
CHIUSURA = "G P Oggi. Lo trovi su G P Oggi punto it."


async def hook_domande(route):
    """Serve giochi.js con una riga in più: la pagina tiene le domande in window.__qs (solo nella ripresa)."""
    f = SITO / "js" / "giochi.js"
    t = f.read_text(encoding="utf-8")
    assert "  partitaQuiz(chiave, qs);\n}" in t, "giochi.js è cambiato: aggiorna il punto di aggancio"
    t = t.replace("  partitaQuiz(chiave, qs);\n}", "  window.__qs = qs; partitaQuiz(chiave, qs);\n}", 1)
    t = t.replace("PASSO_PIXEL = 2200", "PASSO_PIXEL = 1e9", 1)   # nella ripresa le foto si schiariscono a comando (window.__px.avanza), non a tempo reale
    await route.fulfill(status=200, headers={"content-type": "text/javascript", "cache-control": "no-store"}, body=t)


VOTI = []


def contesto_pronostico():
    """Gran Premi della settimana (F1 e MotoGP con la gara entro 5 giorni) e i tre piloti in testa al campionato, dai dati del sito.
    Con PRON_ORA (ISO) si può simulare un altro momento. Ritorna None se questa settimana non c'è nessuna gara."""
    import datetime as dt
    import json as _j
    ora = dt.datetime.fromisoformat(os.environ["PRON_ORA"].replace("Z", "+00:00")) if os.environ.get("PRON_ORA") else dt.datetime.now(dt.timezone.utc)
    dati = SITO / "data"
    t = lambda x: dt.datetime.fromisoformat(x)
    f1 = moto = None
    for g in sorted(_j.load(open(dati / "events.json")), key=lambda g: g["inizio"]):
        gara = next((x for x in g["sessioni"] if x["nome"] == "Gara"), None)
        if gara and t(gara["inizio"]) > ora:
            f1 = (g["nome"], t(gara["inizio"])); break
    gare_m = [(w, next((x for x in w["sessioni"] if x["nome"] == "Gara"), None)) for w in _j.load(open(dati / "motogp.json"))["weekend"]]
    for w, gara in sorted([x for x in gare_m if x[1]], key=lambda x: x[1]["inizio"]):
        if t(gara["inizio"]) + dt.timedelta(minutes=45) > ora:
            moto = (w["nome"].replace("GP ", "Gran Premio ", 1), t(gara["inizio"])); break
    limite = ora + dt.timedelta(days=5)
    serie = []
    if f1 and f1[1] < limite:
        roster = sorted([p for p in _j.load(open(dati / "roster.json")) if p.get("nome")], key=lambda p: p.get("posizione") or 99)
        serie.append(dict(id="f1", gp=f1[0], nomi=[p["nome"] for p in roster[:3]], breve=f1[0]))
    if moto and moto[1] < limite:
        piloti = sorted(_j.load(open(dati / "motogp-classifica.json"))["piloti"], key=lambda p: p["pos"])
        serie.append(dict(id="moto", gp=moto[0], nomi=[p["nome"] for p in piloti[:3]], breve=moto[0]))
    return serie or None


def gioco_pronostico(serie):
    nomi_gp = " e nel ".join(x["gp"] for x in serie)
    primo = serie[0]
    due = len(serie) > 1
    voci = ["Apri G P Oggi punto it e tocca Giochi.",
            "Il primo gioco è il pronostico del podio. In palio, a fine anno, una carta Amazon da cinquanta euro.",
            f"Scegli primo, secondo e terzo del {primo['gp']}.",
            "Metti un nickname e la tua email, serve solo per il premio. Salva, e fai uno screenshot del codice di recupero.",
            (f"Poi fai lo stesso per il {serie[1]['gp']}." if due else "Puoi cambiare il podio fino all'inizio della gara."),
            "Qui vedi chi ha già votato. Ci vogliono trenta secondi: fai il tuo pronostico su G P Oggi punto it!"]
    return dict(chiave="pronostico", nome="Pronostico del podio", modo=None, custom=True, serie=serie,
                intro="Fai il tuo pronostico per questo weekend!",
                voci=voci,
                did=["Apri Giochi", "Premio: carta Amazon 50 €", "Scegli il podio", "Nickname e email", "Anche l'altra serie" if due else "Cambialo fino al via", "Chi ha già votato"])


async def finto_server_voti(route):
    """Durante la ripresa il server dei voti è finto: il voto della demo non finisce nella classifica vera."""
    h = {"access-control-allow-origin": "*", "access-control-allow-headers": "content-type", "access-control-allow-methods": "GET, POST, OPTIONS", "content-type": "application/json"}
    req = route.request
    if req.method == "OPTIONS":
        return await route.fulfill(status=204, headers=h, body="")
    if req.method == "POST" and req.url.endswith("/pronostico"):
        import json as _j
        VOTI.append(_j.loads(req.post_data or "{}"))
        return await route.fulfill(status=200, headers=h, body='{"ok":true}')
    if req.url.endswith("/pronostici"):
        import json as _j
        return await route.fulfill(status=200, headers=h, body=_j.dumps({"pronostici": [{"gp": v["gp"], "nick": v["nick"], "podio": v["podio"], "ts": int(time.time() * 1000)} for v in VOTI]}))
    return await route.fulfill(status=200, headers=h, body="{}")


async def stato(r):
    return await r.js("""() => { const t = document.querySelector('.quiz-testa span'); const m = t && t.textContent.match(/(\\d+) di (\\d+)/);
        return m ? [Number(m[1]), Number(m[2])] : null; }""")


async def tocca_vis(r, selettore, indice=0, secondi=0.55):
    """Porta il cursore sull'elemento (scorrendo solo se non si vede) e fa il tocco."""
    ok = await r.js("""(a) => { const el = document.querySelectorAll(a.s)[a.i]; if (!el) return false; const b = el.getBoundingClientRect();
        return b.top > 40 && b.bottom < window.innerHeight - 20; }""", {"s": selettore, "i": indice})
    if not ok:
        c = await r.centro(selettore, indice)
        await r.scorri(c[1] - 330, 0.7)
    x, y = await r.centro(selettore, indice, doc=False)
    await r.muovi(x, y, secondi)
    await r.tocca()


async def risposta(r, giusta=True, veloce=False, passi=0):
    """Risponde alla domanda in corso (giusta o sbagliata) e passa alla successiva. Ritorna False se il gioco è finito."""
    i, n = await stato(r)
    c = await r.centro(".quiz-testa", 0)
    await r.scorri(c[1] - 112, 0.35)   # la domanda intera (foto e risposte) sotto l'intestazione
    for _ in range(passi):    # gioco pixelato: la foto si schiarisce un passo alla volta
        await r.fermo(0.45 if veloce else 0.9)
        await r.js("window.__px.avanza()")
    q = await r.js("(i) => { if (window.__px) return { o: window.__px.opzioni, g: window.__px.giusto }; const q = window.__qs[i - 1]; return { o: q.opzioni, g: q.giusto }; }", i)
    corretto = q["o"].index(q["g"])
    k = corretto if giusta else next(j for j in range(len(q["o"])) if j != corretto)
    await r.fermo(0.3 if veloce else 1.2)
    await tocca_vis(r, ".quiz-opz", k, 0.25 if veloce else 0.6)
    await r.js("(k) => document.querySelectorAll('.quiz-opz')[k].click()", k)
    await r.fermo(0.4 if veloce else 1.3)
    await tocca_vis(r, "#avanti", 0, 0.22 if veloce else 0.5)
    prima = await r.js("document.querySelector('.quiz-testa span').textContent")
    await r.js("document.getElementById('avanti').click()")
    # nel gioco pixelato la domanda dopo si carica con un attimo di ritardo (foto): si aspetta che cambi
    await r.page.wait_for_function("(t) => { const e = document.querySelector('.quiz-testa span'); return !e || e.textContent !== t; }", arg=prima, timeout=8000)
    await r.fermo(0.1 if veloce else 0.5)
    return i < n


def azioni_pronostico(g):
    serie = g["serie"]

    async def a_apri(r, base):
        await r.vai(base + "/index.html")
        await r.fermo(0.4)
        await r.tocca_link(D.MENU, D.M_GIOCHI, menu=True)
        await r.fermo(0.5)
        await r.scorri(220, 1.4)
        await r.fermo(0.4)

    async def a_scelta(r, base):
        await tocca_vis(r, '.gioco-card[data-gioco="pronostico"]', 0, 0.5)
        await r.js("document.querySelector('.gioco-card[data-gioco=\"pronostico\"]').click()")
        await r.js("() => new Promise((ok) => { const t = setInterval(() => { if (document.getElementById('p1')) { clearInterval(t); ok(); } }, 50); })")
        await r.scorri(0, 0.4)
        await r.fermo(1.3)

    async def scegli(r, idx, testo):
        await tocca_vis(r, f"#p{idx}", 0, 0.4)
        await r.js("(a) => { const s = document.getElementById('p' + a.i); const o = [...s.options].find((x) => x.textContent === a.t); s.value = o.value; s.dispatchEvent(new Event('change')); }", {"i": idx, "t": testo})
        await r.fermo(0.4)

    async def passa_a(r, ser):
        """Tocca la serie giusta (F1 o MotoGP) e aspetta il modulo con i piloti di quella serie."""
        sel = ".chip-serie." + ser["id"]
        attivo = await r.js("(s) => document.querySelector(s).classList.contains('attivo')", sel)
        if not attivo:
            c = await r.centro(".chip-serie-riga", 0)
            await r.scorri(c[1] - 140, 0.6)
            await tocca_vis(r, sel, 0, 0.6)
            await r.js("(s) => document.querySelector(s).click()", sel)
            await r.js("(n) => new Promise((ok) => { const t = setInterval(() => { const e = document.getElementById('p1'); if (e && [...e.options].some((o) => o.textContent === n)) { clearInterval(t); ok(); } }, 50); })", ser["nomi"][0])
            await r.fermo(0.6)

    async def a_podio(r, base):
        await passa_a(r, serie[0])
        for i, nome in enumerate(serie[0]["nomi"], 1):
            await scegli(r, i, nome)

    async def a_nome(r, base):
        await tocca_vis(r, "#nome", 0, 0.4)
        for k in range(1, 7):
            await r.js("(n) => { const e = document.getElementById('nome'); e.value = 'GP_Fan'.slice(0, n); e.dispatchEvent(new Event('input')); }", k)
            await r.fermo(0.06)
        await r.fermo(0.2)
        await tocca_vis(r, "#email", 0, 0.4)
        for k in range(1, 9):
            await r.js("(n) => { const e = document.getElementById('email'); e.value = 'tuamail@esempio.it'.slice(0, n * 2); e.dispatchEvent(new Event('input')); }", k)
            await r.fermo(0.05)
        await r.js("() => { document.getElementById('email').value = 'tuamail@esempio.it'; }")
        await r.fermo(0.5)
        await tocca_vis(r, "#salva", 0, 0.45)
        await r.js("document.getElementById('salva').click()")
        await r.fermo(1.5)

    async def a_altra(r, base):
        if len(serie) < 2:
            await r.fermo(1.0)
            return
        await passa_a(r, serie[1])
        for i, nome in enumerate(serie[1]["nomi"], 1):
            await scegli(r, i, nome)
        await tocca_vis(r, "#nome", 0, 0.5)
        await r.js("() => { const e = document.getElementById('nome'); e.value = 'GP_Fan'; e.dispatchEvent(new Event('input')); document.getElementById('email').value = 'tuamail@esempio.it'; }")
        await tocca_vis(r, "#salva", 0, 0.5)
        await r.js("document.getElementById('salva').click()")
        await r.fermo(1.4)

    async def a_fine(r, base):
        await r.js("() => new Promise((ok) => { const t = setInterval(() => { const e = document.querySelector('#votanti table'); if (e) { clearInterval(t); ok(); } }, 80); setTimeout(ok, 4000); })")
        c = await r.centro("#votanti", 0)
        await r.scorri(c[1] - 190, 1.0)
        await r.fermo(1.6)

    return [a_apri, a_scelta, a_podio, a_nome, a_altra, a_fine]


def azioni(g):
    if g.get("custom"):
        return azioni_pronostico(g)

    async def a_apri(r, base):
        await r.vai(base + "/index.html")
        await r.fermo(0.4)
        await r.tocca_link(D.MENU, D.M_GIOCHI, menu=True)
        await r.fermo(0.5)
        await r.scorri(220, 1.4)
        await r.fermo(0.4)

    async def a_scelta(r, base):
        await tocca_vis(r, f'.gioco-card[data-gioco="{g["chiave"]}"]', 0, 0.7)
        await r.js("(c) => document.querySelector('.gioco-card[data-gioco=\"' + c + '\"]').click()", g["chiave"])
        if g["modo"]:
            await r.fermo(1.2)
            await tocca_vis(r, f'[data-m="{g["modo"]}"]', 0, 0.7)
            await r.js("(m) => document.querySelector('[data-m=\"' + m + '\"]').click()", g["modo"])
        await r.js("() => new Promise((ok) => { const t = setInterval(() => { if (window.__qs || window.__px) { clearInterval(t); ok(); } }, 50); })")
        await r.scorri(0, 0.4)
        await r.fermo(0.8)

    pix = g["chiave"] == "pixel"

    async def a_prima(r, base):
        await risposta(r, giusta=True, passi=3 if pix else 0)

    async def a_sbaglio(r, base):
        await risposta(r, giusta=False, passi=2 if pix else 0)

    async def a_avanti(r, base):
        for k in range(10):
            if not await risposta(r, giusta=(k != 3), veloce=True, passi=1 if pix else 0):
                break

    async def a_fine(r, base):
        await r.scorri(0, 0.5)
        await r.fermo(2.0)

    return [a_apri, a_scelta, a_prima, a_sbaglio, a_avanti, a_fine]


def copione(g):
    if g.get("custom"):
        return g["voci"], g["did"]
    voci = [g["apri"], g["scelta"] or f"Tocco «{g['nome']}» e si parte.", g["prima"], g["sbaglio"], g["avanti"], g["fine"]]
    didascalie = ["Giochi · gratis", g["nome"], "Tocca la risposta giusta", "Se sbagli lo vedi subito", "Dieci domande", "Punteggio e record"]
    return voci, didascalie


async def registra(g, base, tmp, durate, prova):
    video = tmp / "partita.mp4"
    enc = None if prova else D._encoder(video)
    voci, didascalie = copione(g)
    inizi = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=D.CHROMIUM)
        ctx = await browser.new_context(viewport=D.VIEW, device_scale_factor=1 if prova else 3, is_mobile=True, has_touch=True)
        await ctx.route(re.compile(r"/js/giochi\.js"), hook_domande)
        await ctx.route(re.compile(r"^https?://(?!localhost)"), D._esterna)
        await ctx.route(re.compile(r"gpoggivotti\.giovannirosso05\.workers\.dev"), finto_server_voti)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: print("  errore nella pagina:", e))
        cdp = await ctx.new_cdp_session(page)
        r = D.Regista(page, cdp, enc.stdin if enc else None)
        for i, azione in enumerate(azioni(g)):
            inizi.append(r.t)
            r.nuova_scena(didascalie[i])
            await azione(r, base)
            mancante = (inizi[-1] + durate[i] + 0.35) - r.t
            if mancante > 0:
                await r.fermo(mancante)
            print(f"  scena {i + 1}/6 ok · {r.t:.1f}s", flush=True)
        await browser.close()
    if enc:
        enc.stdin.close()
        enc.wait()
    return video, inizi


async def principale(args):
    if args.gioco == "pronostico":
        serie = contesto_pronostico()
        if not serie:
            print("Questa settimana non c'è nessuna gara: nessun video.")
            sys.exit(75)
        GIOCHI["pronostico"] = gioco_pronostico(serie)
        nomi = " e nel ".join(x["gp"] for x in serie)
        Path(str(args.uscita) + ".txt").write_text(
            f"Che podio fai nel {nomi}? Chi è primo a fine anno vince una carta regalo Amazon da 50 €. Gratis. Cerca GP Oggi su Google, Giochi, Pronostico del podio. Regolamento sul sito. Amazon non è sponsor. #f1 #motogp #pronostici #gpoggi", encoding="utf-8")
    g = GIOCHI[args.gioco]
    base = f"http://localhost:{PORTA}"
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORTA), "-d", str(SITO)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            voci_testo, _ = copione(g)
            testi = [g["intro"]] + voci_testo + [CHIUSURA]
            if args.prova:
                await registra(g, base, tmp, [3.0] * 6, True)
                print("Prova completata: la partita funziona.")
                return
            voci, durate = [], []
            for i, testo in enumerate(testi):
                f = tmp / f"voce{i}.mp3"
                await D._voce(testo, f)
                voci.append(f)
                durate.append(D._durata(f))
            dur_intro = durate[0] + 0.9
            async with async_playwright() as p:
                browser = await p.chromium.launch(executable_path=D.CHROMIUM)
                await D.clip_intro(browser, dur_intro, tmp / "intro.mp4")
                dur_fine = durate[7] + 1.4
                await D.clip_fermo(browser, D.html_fine(), dur_fine, tmp / "fine.mp4")
                await browser.close()
            partita, inizi = await registra(g, base, tmp, durate[1:7], False)
            dur_partita = D._durata(partita)
            lista = tmp / "lista.txt"
            lista.write_text("".join(f"file '{tmp / c}'\n" for c in ("intro.mp4", "partita.mp4", "fine.mp4")))
            video = tmp / "video.mp4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(video)], check=True)
            partenze = [0.0] + [dur_intro + t for t in inizi] + [dur_intro + dur_partita]
            ingressi, filtri = [], []
            for i, (f, t0) in enumerate(zip(voci, partenze)):
                ingressi += ["-i", str(f)]
                filtri.append(f"[{i + 1}:a]adelay={int((t0 + 0.25) * 1000)}:all=1[v{i}]")
            mix = "".join(f"[v{i}]" for i in range(len(voci)))
            filtri.append(f"{mix}amix=inputs={len(voci)}:normalize=0,aformat=sample_rates=44100:channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=9[a]")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), *ingressi, "-filter_complex", ";".join(filtri), "-map", "0:v", "-map", "[a]",
                            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", str(args.uscita)], check=True)
            print(f"Fatto: {args.uscita} ({D._durata(args.uscita):.1f}s)")
    finally:
        srv.terminate()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("gioco", choices=list(GIOCHI))
    ap.add_argument("--prova", action="store_true")
    ap.add_argument("--uscita", default=None)
    a = ap.parse_args()
    a.uscita = a.uscita or str(Path(__file__).parent / f"gioco-{a.gioco}.mp4")
    asyncio.run(principale(a))
