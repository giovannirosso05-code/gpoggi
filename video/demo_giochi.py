"""Video "provo un gioco di GP Oggi" per TikTok e Instagram: si gioca davvero sul sito (cursore che tocca, risposte giuste e una sbagliata, punteggio finale),
con la voce di Diego che accompagna ogni passaggio. Stesso metodo del tour del sito (demo_sito.py).

Uso:  python3 demo_giochi.py pilota|circuito|moto [--prova] [--uscita FILE]

Per rispondere in modo credibile, solo durante la ripresa la pagina espone le domande del gioco (window.__qs): il sito pubblicato non cambia.
"""
import argparse
import asyncio
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
    "pilota": dict(chiave="pilota", nome="Chi è il pilota?", modo="oggi", intro="Sai riconoscere i piloti di Formula uno e di Moto G P? Mettiti alla prova con i giochi di G P Oggi!",
                   apri="Sul sito ci sono otto giochi, tutti gratis e senza registrazione. Apriamo «Chi è il pilota?».",
                   scelta="Scelgo la difficoltà: oggi i piloti della griglia.",
                   prima="Ti mostra una foto e quattro nomi: tocca quello giusto.",
                   sbaglio="Se sbagli, il gioco te lo dice subito e ti fa vedere la risposta.",
                   avanti="E così per dieci domande: più sei veloce, meglio è.",
                   fine="Alla fine vedi il punteggio e il tuo record, che resta sul telefono. Riesci a fare dieci su dieci?"),
    "circuito": dict(chiave="circuito", nome="Indovina il circuito", modo=None, intro="Conosci a memoria i circuiti della Formula uno? Proviamo con il gioco di G P Oggi!",
                     apri="Sul sito ci sono otto giochi, tutti gratis e senza registrazione. Apriamo «Indovina il circuito».",
                     scelta=None,
                     prima="Ti mostra solo il tracciato, senza nomi: di quale Gran Premio si tratta?",
                     sbaglio="Se sbagli, il gioco ti dice qual era quello giusto.",
                     avanti="Dieci tracciati da riconoscere: quanti ne indovini?",
                     fine="Alla fine vedi il punteggio e il tuo record. Riesci a farli tutti?"),
    "moto": dict(chiave="moto", nome="MotoGP: che moto guida?", modo=None, intro="Sai con che moto corre ogni pilota della Moto G P? Giochiamo insieme su G P Oggi!",
                 apri="Sul sito ci sono otto giochi, tutti gratis e senza registrazione. Apriamo «Moto G P: che moto guida?».",
                 scelta=None,
                 prima="Ti dice il pilota, tu scegli la marca della moto.",
                 sbaglio="Se sbagli, il gioco te lo dice subito.",
                 avanti="Dieci domande per scoprire quanto conosci la griglia.",
                 fine="Alla fine vedi il punteggio e il tuo record. Riesci a fare il pieno?"),
}
CHIUSURA = "G P Oggi. Lo trovi su G P Oggi punto it."


async def hook_domande(route):
    """Serve giochi.js con una riga in più: la pagina tiene le domande in window.__qs (solo nella ripresa)."""
    f = SITO / "js" / "giochi.js"
    t = f.read_text(encoding="utf-8")
    assert "  partitaQuiz(chiave, qs);\n}" in t, "giochi.js è cambiato: aggiorna il punto di aggancio"
    t = t.replace("  partitaQuiz(chiave, qs);\n}", "  window.__qs = qs; partitaQuiz(chiave, qs);\n}", 1)
    await route.fulfill(status=200, headers={"content-type": "text/javascript", "cache-control": "no-store"}, body=t)


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


async def risposta(r, giusta=True, veloce=False):
    """Risponde alla domanda in corso (giusta o sbagliata) e passa alla successiva. Ritorna False se il gioco è finito."""
    i, n = await stato(r)
    c = await r.centro(".quiz-testa", 0)
    await r.scorri(c[1] - 112, 0.35)   # la domanda intera (foto e risposte) sotto l'intestazione
    q = await r.js("(i) => { const q = window.__qs[i - 1]; return { o: q.opzioni, g: q.giusto }; }", i)
    corretto = q["o"].index(q["g"])
    k = corretto if giusta else next(j for j in range(len(q["o"])) if j != corretto)
    await r.fermo(0.3 if veloce else 1.2)
    await tocca_vis(r, ".quiz-opz", k, 0.25 if veloce else 0.6)
    await r.js("(k) => document.querySelectorAll('.quiz-opz')[k].click()", k)
    await r.fermo(0.4 if veloce else 1.3)
    await tocca_vis(r, "#avanti", 0, 0.22 if veloce else 0.5)
    await r.js("document.getElementById('avanti').click()")
    await r.fermo(0.1 if veloce else 0.5)
    return i < n


def azioni(g):
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
        await r.js("() => new Promise((ok) => { const t = setInterval(() => { if (window.__qs) { clearInterval(t); ok(); } }, 50); })")
        await r.scorri(0, 0.4)
        await r.fermo(0.8)

    async def a_prima(r, base):
        await risposta(r, giusta=True)

    async def a_sbaglio(r, base):
        await risposta(r, giusta=False)

    async def a_avanti(r, base):
        for k in range(10):
            if not await risposta(r, giusta=(k != 3), veloce=True):
                break

    async def a_fine(r, base):
        await r.scorri(0, 0.5)
        await r.fermo(2.0)

    return [a_apri, a_scelta, a_prima, a_sbaglio, a_avanti, a_fine]


def copione(g):
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
