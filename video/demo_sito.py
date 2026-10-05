"""Video "come funziona GP Oggi" (~1 minuto) per TikTok e Instagram: tour del sito vero con una freccia che si muove e tocca,
didascalia per ogni sezione, voce Diego sincronizzata scena per scena, chiusura con installazione come app e indirizzo.
Stile del video demo di MMA Oggi. Dei giochi si accenna soltanto, a voce: la scheda Giochi si vede solo con i nomi, come anticipazione.

Ogni fotogramma viene preparato (cursore, scroll) e poi catturato: il video e' fluido a prescindere dalla velocita' della macchina.
Viewport 360x640 a densita' 3 = esattamente 1080x1920.

Uso:  python3 demo_sito.py [--prova] [--uscita FILE]
  --prova  esegue solo le azioni sul sito (senza voce ne' video) per controllare che tutti i tocchi funzionino.
"""
import argparse
import asyncio
import base64
import json
import re
import ssl
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import edge_tts
import edge_tts.communicate as C
import requests
from playwright.async_api import async_playwright

C._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
QUI = Path(__file__).parent
SITO = QUI.parent / "docs"
FONT = QUI / "logo" / "font"
CHROMIUM = "/opt/pw-browsers/chromium"
W, H = 1080, 1920
VIEW = {"width": 360, "height": 640}
FPS = 30
VOCE = "it-IT-DiegoNeural"
VELOCITA = "+15%"
PAUSE, SCORRI = 0.7, 0.75
DURATA_DIDASCALIA = 2.8
ROSSO, NERO = "#e8352f", "#0b0b0e"

OVERLAY_CSS = """
html { scroll-behavior: auto !important; }
#demo-cursore { position: fixed; left: 0; top: 0; width: 26px; height: 26px; z-index: 2147483647; pointer-events: none; filter: drop-shadow(0 2px 3px rgba(0,0,0,.55)); }
#demo-onda { position: fixed; z-index: 2147483646; pointer-events: none; border-radius: 50%; border: 3px solid rgba(255,255,255,.9); background: rgba(232,53,47,.35); opacity: 0; }
#demo-didascalia { position: fixed; left: 50%; bottom: 46px; transform: translateX(-50%); z-index: 2147483645; pointer-events: none; white-space: nowrap;
  font-family: "Oswald", "Arial Narrow", sans-serif; font-weight: 700; font-size: 19px; letter-spacing: .04em; text-transform: uppercase; color: #fff;
  background: rgba(10,10,12,.92); border: 2px solid #e8352f; border-radius: 12px; padding: 8px 16px; box-shadow: 0 8px 24px rgba(0,0,0,.5); opacity: 0; }
"""
FRECCIA = ('<svg width="26" height="26" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M4 2 L4 19.5 L8.6 15.3 L11.7 22.2 L14.9 20.8 L11.8 14 L17.8 14 Z" '
           'fill="#fff" stroke="#111" stroke-width="1.4" stroke-linejoin="round"/></svg>')

# Il testo parlato scrive le sigle come si leggono ("G P Oggi", "Formula uno"); la didascalia a schermo resta normale.
INTRO = "Ecco come funziona G P Oggi, il sito italiano su Formula uno e Moto G P."
SCENE = [
    {"voce": "Dalla home vedi il prossimo Gran Premio di Formula uno e di Moto G P, con il conto alla rovescia e il favorito.", "didascalia": "Home · prossimi Gran Premi"},
    {"voce": "Nella scheda Formula uno trovi il weekend in arrivo con tutti gli orari. Apri una gara: risultati, griglia di partenza e cronaca giro per giro.", "didascalia": "Formula 1 · risultati e cronaca"},
    {"voce": "La Moto G P ha la sua scheda, uguale a quella della Formula uno, con la classifica a colori delle marche.", "didascalia": "MotoGP · tutte le gare"},
    {"voce": "Tocca un pilota e apri la sua scheda: foto, carriera e biografia, di oggi e del passato.", "didascalia": "La scheda dei piloti"},
    {"voce": "Le classifiche di piloti e costruttori, sempre aggiornate.", "didascalia": "Classifiche"},
    {"voce": "Il calendario ha gli orari in ora italiana, ma puoi cambiare fuso, scaricarlo sul telefono scegliendo solo le sessioni che ti interessano.", "didascalia": "Calendario · il tuo fuso orario"},
    {"voce": "Ogni giorno le notizie dei due campionati, in italiano.", "didascalia": "Notizie ogni giorno"},
    {"voce": "Tutto gratis e senza registrazione. E sul sito ci sono già un sacco di giochi, che vi faremo scoprire presto.", "didascalia": "Giochi già online"},
    {"voce": "E lo installi sul telefono come una vera app. Su iPhone: Condividi, poi Aggiungi alla schermata Home. Su Android: Installa app.", "didascalia": None},
    {"voce": "G P Oggi. Lo trovi su G P Oggi punto it.", "didascalia": None},
]
MENU = ".nav-links a"
M_F1, M_MOTO, M_PILOTI, M_CLASS, M_CAL, M_NEWS, M_GIOCHI = 1, 2, 3, 4, 5, 6, 7


def _ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


class Regista:
    """Tiene il tempo in fotogrammi e cattura la pagina uno alla volta (cattura spenta in modalita' --prova)."""

    def __init__(self, page, cdp, uscita):
        self.page, self.cdp, self.out = page, cdp, uscita
        self.n = 0
        self.cx, self.cy = VIEW["width"] + 30, VIEW["height"] * 0.6
        self.scroll = 0
        self.didascalia, self.op = "", 0.0
        self.t0 = 0.0

    @property
    def t(self):
        return self.n / FPS

    async def _overlay(self):
        await self.page.add_style_tag(content=OVERLAY_CSS)
        await self.page.evaluate("""(svg) => { if (!document.getElementById('demo-cursore')) {
            const c = document.createElement('div'); c.id = 'demo-cursore'; c.innerHTML = svg;
            const o = document.createElement('div'); o.id = 'demo-onda'; const d = document.createElement('div'); d.id = 'demo-didascalia';
            document.body.append(o, c, d); } }""", FRECCIA)
        await self._stato()

    async def _stato(self, premuto=0.0, onda=0.0):
        await self.page.evaluate("""(s) => {
            const c = document.getElementById('demo-cursore'); if (!c) return;
            c.style.transform = `translate(${s.x - 4}px, ${s.y - 2}px) scale(${1 - 0.18 * s.premuto})`;
            const o = document.getElementById('demo-onda'); const r = 6 + 22 * s.onda;
            o.style.width = o.style.height = (2 * r) + 'px'; o.style.left = (s.x - r) + 'px'; o.style.top = (s.y - r) + 'px';
            o.style.opacity = s.onda > 0 && s.onda < 1 ? (0.9 * (1 - s.onda)) : 0;
            const d = document.getElementById('demo-didascalia'); d.textContent = s.testo; d.style.opacity = s.testo ? s.op : 0;
            if (Math.abs(window.scrollY - s.scroll) > 0.5) window.scrollTo(0, s.scroll);
        }""", {"x": self.cx, "y": self.cy, "premuto": premuto, "onda": onda, "testo": self.didascalia, "op": self.op, "scroll": self.scroll})

    async def _scatta(self, premuto=0.0, onda=0.0):
        self._dissolvenza()
        if self.out is not None:
            await self._stato(premuto, onda)
            r = await self.cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 92})
            self.out.write(base64.b64decode(r["data"]))
        self.n += 1

    def _dissolvenza(self):
        """La didascalia entra a inizio scena e sparisce dopo qualche secondo (DURATA_DIDASCALIA), per non coprire visi e testi."""
        bersaglio = 1.0 if (self.t - self.t0) < DURATA_DIDASCALIA else 0.0
        passo = 1 / (0.3 * FPS)
        self.op = min(bersaglio, self.op + passo) if self.op < bersaglio else max(bersaglio, self.op - passo)

    async def _prepara(self):
        try:
            await self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        await self.page.evaluate("document.fonts.ready")
        alt = await self.page.evaluate("Math.min(document.documentElement.scrollHeight, 6000)")
        for y in range(0, int(alt), 500):
            await self.page.evaluate("y => window.scrollTo(0, y)", y)
            await self.page.wait_for_timeout(30)
        await self.page.evaluate("window.scrollTo(0, 0)")
        await self.page.wait_for_timeout(300)
        self.scroll = 0
        await self._overlay()

    async def vai(self, url):
        await self.page.goto(url, wait_until="load")
        await self._prepara()

    async def fermo(self, secondi):
        for _ in range(round(secondi * PAUSE * FPS)):
            await self._scatta()

    async def muovi(self, x, y, secondi=0.7):
        x0, y0 = self.cx, self.cy
        passi = max(1, round(secondi * FPS))
        for i in range(1, passi + 1):
            e = _ease(i / passi)
            self.cx, self.cy = x0 + (x - x0) * e, y0 + (y - y0) * e
            await self._scatta()

    async def scorri(self, y, secondi=1.2):
        alt = await self.page.evaluate("document.documentElement.scrollHeight - window.innerHeight")
        y = max(0, min(y, alt))
        y0 = self.scroll
        passi = max(1, round(secondi * SCORRI * FPS))
        for i in range(1, passi + 1):
            self.scroll = y0 + (y - y0) * _ease(i / passi)
            await self._scatta()

    async def tocca(self):
        passi = round(0.3 * FPS)
        for i in range(1, passi + 1):
            p = i / passi
            await self._scatta(premuto=min(1.0, p * 3) if p < 0.5 else max(0.0, 1 - (p - 0.5) * 3), onda=p)

    async def centro(self, selettore, indice=0, doc=True):
        return await self.page.evaluate("""(a) => { const el = document.querySelectorAll(a.s)[a.i]; if (!el) return null;
            const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2 + (a.doc ? window.scrollY : 0)]; }""",
                                        {"s": selettore, "i": indice, "doc": doc})

    async def _menu_visibile(self, indice):
        """Il menu in alto scorre di lato sul telefono: porta la voce cercata in vista."""
        obiettivo = await self.page.evaluate("""(i) => { const m = document.querySelector('.nav-links'); const el = m.querySelectorAll('a')[i];
            const r = el.getBoundingClientRect(); const dentro = r.left >= 30 && r.right <= window.innerWidth - 30;
            return dentro ? null : m.scrollLeft + r.left + r.width / 2 - window.innerWidth / 2; }""", indice)
        if obiettivo is None:
            return
        parte = await self.page.evaluate("document.querySelector('.nav-links').scrollLeft")
        passi = round(0.5 * FPS)
        for i in range(1, passi + 1):
            await self.page.evaluate("(x) => { document.querySelector('.nav-links').scrollLeft = x; }", parte + (obiettivo - parte) * _ease(i / passi))
            await self._scatta()

    async def _apri(self, selettore, indice):
        async with self.page.expect_navigation(wait_until="load", timeout=20000):
            await self.page.evaluate("(a) => document.querySelectorAll(a.s)[a.i].click()", {"s": selettore, "i": indice})
        await self._prepara()

    async def tocca_link(self, selettore, indice=0, menu=False, y_finestra=360, secondi_scroll=0.9):
        """Porta il cursore sul link, lo tocca davvero e aspetta la pagina nuova."""
        if menu:
            if self.scroll > 1:
                await self.scorri(0, 0.6)
            await self._menu_visibile(indice)
            x, y = await self.centro(selettore, indice, doc=False)
            await self.muovi(x, y, 0.5)
        else:
            c = await self.centro(selettore, indice)
            if c is None:
                raise RuntimeError(f"Elemento non trovato: {selettore}")
            await self.scorri(c[1] - y_finestra, secondi_scroll)
            x, y = await self.centro(selettore, indice, doc=False)
            await self.muovi(x, y, 0.5)
        await self.tocca()
        await self._apri(selettore, indice)

    async def tocca_bottone(self, selettore, indice=0, y_finestra=330):
        """Tocco su un elemento della stessa pagina (nessuna navigazione)."""
        c = await self.centro(selettore, indice)
        if c is None:
            raise RuntimeError(f"Elemento non trovato: {selettore}")
        await self.scorri(c[1] - y_finestra, 0.9)
        x, y = await self.centro(selettore, indice, doc=False)
        await self.muovi(x, y, 0.5)
        await self.tocca()

    async def js(self, codice, arg=None):
        return await self.page.evaluate(codice, arg)

    def nuova_scena(self, didascalia):
        self.didascalia, self.op, self.t0 = didascalia or "", 0.0, self.t


# ---- le scene: ognuna dura quanto la sua voce (se le azioni finiscono prima, l'ultima inquadratura resta ferma)
async def _s_home(r, base):
    await r.vai(f"{base}/index.html")
    await r.fermo(0.5)
    await r.muovi(250, 360, 0.9)
    await r.scorri(520, 1.8)
    await r.fermo(0.5)
    await r.scorri(1250, 1.8)
    await r.fermo(0.4)
    await r.scorri(2000, 1.8)


async def _s_f1(r, base):
    await r.tocca_link(MENU, M_F1, menu=True)
    await r.fermo(0.5)
    await r.scorri(420, 1.4)
    await r.tocca_link("a.event-card.passata", 0, y_finestra=380, secondi_scroll=1.0)
    await r.fermo(0.5)
    await r.scorri(520, 1.5)
    await r.fermo(0.4)
    await r.scorri(1500, 1.8)
    await r.fermo(0.4)
    await r.scorri(2600, 1.8)


async def _s_moto(r, base):
    await r.tocca_link(MENU, M_MOTO, menu=True)
    await r.fermo(0.5)
    await r.scorri(450, 1.4)
    await r.tocca_link("a.event-card.passata", 0, y_finestra=380, secondi_scroll=1.0)
    await r.fermo(0.5)
    await r.scorri(520, 1.5)
    await r.fermo(0.4)
    await r.scorri(1300, 1.8)


async def _s_piloti(r, base):
    await r.tocca_link(MENU, M_PILOTI, menu=True)
    await r.fermo(0.4)
    await r.scorri(260, 1.2)
    await r.tocca_link("a.driver-card", 2, y_finestra=360, secondi_scroll=0.9)
    await r.fermo(0.5)
    await r.scorri(500, 1.4)
    await r.fermo(0.4)
    await r.scorri(1100, 1.6)


async def _s_class(r, base):
    await r.tocca_link(MENU, M_CLASS, menu=True)
    await r.fermo(0.4)
    await r.scorri(380, 1.4)
    await r.fermo(0.4)
    await r.scorri(1100, 1.8)
    await r.fermo(0.3)
    await r.scorri(1900, 1.8)


async def _s_cal(r, base):
    await r.tocca_link(MENU, M_CAL, menu=True)
    await r.fermo(0.6)
    await r.scorri(160, 1.0)
    await r.tocca_bottone("#fuso", 0, y_finestra=330)
    await r.js("(() => { const s = document.getElementById('fuso'); s.value = 'America/New_York'; s.dispatchEvent(new Event('change', {bubbles: true})); })()")
    await r.fermo(1.0)
    await r.js("(() => { const s = document.getElementById('fuso'); s.value = 'Europe/Rome'; s.dispatchEvent(new Event('change', {bubbles: true})); })()")
    await r.fermo(0.3)
    await r.scorri(0, 0.8)
    await r.tocca_bottone("#vai-scarica", 0, y_finestra=300)
    dest = await r.js("document.getElementById('scarica').getBoundingClientRect().top + window.scrollY - 140")
    await r.scorri(dest, 1.6)
    await r.fermo(0.4)
    # "Scarica .ics" apre la finestra con la scelta delle sessioni: il cursore passa dentro la finestra per restare visibile
    await r.tocca_bottone('[data-ics="f1"]', 0, y_finestra=380)
    await r.js("document.querySelector('[data-ics=\"f1\"]').click()")
    await r.fermo(0.6)
    await r.js("(() => { const d = document.querySelector('dialog[open]'); for (const id of ['demo-onda', 'demo-cursore', 'demo-didascalia']) d.appendChild(document.getElementById(id)); })()")

    async def tocca_in_finestra(selettore):
        x, y = await r.centro(selettore, 0, doc=False)
        await r.muovi(x, y, 0.6)
        await r.tocca()

    await tocca_in_finestra('.dlg-sessioni input[data-t="libere"]')
    await r.js("document.querySelector('.dlg-sessioni input[data-t=\"libere\"]').click()")
    await r.fermo(1.0)
    await tocca_in_finestra('.dlg-sessioni button[value="annulla"]')
    await r.js("for (const id of ['demo-onda', 'demo-cursore', 'demo-didascalia']) document.body.appendChild(document.getElementById(id))")
    await r.js("document.querySelector('.dlg-sessioni button[value=\"annulla\"]').click()")
    await r.fermo(0.6)


async def _s_news(r, base):
    await r.tocca_link(MENU, M_NEWS, menu=True)
    await r.fermo(0.4)
    await r.scorri(360, 1.3)
    await r.fermo(0.4)
    await r.scorri(1000, 1.8)


async def _s_giochi(r, base):
    """Solo anticipazione: i nomi dei giochi, senza descrizioni ne' risultati, e nessun gioco aperto."""
    await r.tocca_link(MENU, M_GIOCHI, menu=True)
    await r.page.add_style_tag(content=".gioco-card span, .gioco-card small, .gioco-card .rec { display: none !important; }")
    await r.fermo(0.6)
    await r.scorri(260, 1.6)
    await r.fermo(0.4)


AZIONI = [_s_home, _s_f1, _s_moto, _s_piloti, _s_class, _s_cal, _s_news, _s_giochi]
_CACHE = {}
_UA = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36"


async def _esterna(route):
    """Font e immagini esterne arrivano da Python (il browser non si fida del proxy); le statistiche sono bloccate."""
    url = route.request.url
    if "plausible.io" in url or "workers.dev" in url:   # niente statistiche e niente voti veri nelle riprese
        return await route.abort()
    if url not in _CACHE:
        def scarica():
            try:
                x = requests.get(url, headers={"User-Agent": _UA}, timeout=20, verify="/root/.ccr/ca-bundle.crt")
                return x.status_code, x.headers.get("content-type", "application/octet-stream"), x.content
            except requests.RequestException:
                return None
        _CACHE[url] = await asyncio.to_thread(scarica)
    v = _CACHE[url]
    if v is None:
        return await route.abort()
    await route.fulfill(status=v[0], headers={"content-type": v[1], "access-control-allow-origin": "*"}, body=v[2])


def _durata(f):
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)], capture_output=True, text=True)
    return float(o.stdout.strip())


async def _voce(testo, uscita):
    await edge_tts.Communicate(testo, VOCE, rate=VELOCITA).save(str(uscita))


def _encoder(uscita, ingresso="mjpeg"):
    return subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", ingresso, "-i", "-",
                             "-vf", f"scale={W}:{H}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(uscita)], stdin=subprocess.PIPE)


async def registra(base, tmp, durate_voce, prova):
    video = tmp / "tour.mp4"
    enc = None if prova else _encoder(video)
    inizi = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=CHROMIUM)
        ctx = await browser.new_context(viewport=VIEW, device_scale_factor=1 if prova else 3, is_mobile=True, has_touch=True)
        await ctx.route(re.compile(r"^https?://(?!localhost)"), _esterna)
        page = await ctx.new_page()
        cdp = await ctx.new_cdp_session(page)
        r = Regista(page, cdp, enc.stdin if enc else None)
        for i, azione in enumerate(AZIONI):
            inizi.append(r.t)
            r.nuova_scena(SCENE[i]["didascalia"])
            await azione(r, base)
            mancante = (inizi[-1] + durate_voce[i] + 0.35) - r.t
            if mancante > 0:
                await r.fermo(mancante)
            print(f"  scena {i + 1}/{len(AZIONI)} ok · {r.t:.1f}s", flush=True)
        await browser.close()
    if enc:
        enc.stdin.close()
        enc.wait()
    return video, inizi


# ---- schermate grafiche: intro animata, installazione come app, chiusura
def _font_css():
    def b64(f):
        return base64.b64encode((FONT / f).read_bytes()).decode()
    return (f"@font-face{{font-family:Oswald;font-weight:700;src:url(data:font/woff2;base64,{b64('oswald-latin-700-normal.woff2')})}}"
            f"@font-face{{font-family:Inter;font-weight:500;src:url(data:font/woff2;base64,{b64('inter-latin-500-normal.woff2')})}}")


def _logo_uri():
    return "data:image/png;base64," + base64.b64encode((SITO / "img" / "logo-wide-scuro.png").read_bytes()).decode()


def _html(corpo, css=""):
    return f"""<!doctype html><meta charset=utf-8><style>{_font_css()}
html,body{{margin:0;width:{W}px;height:{H}px;background:{NERO};overflow:hidden;color:#fff;font-family:Inter,sans-serif}}
.o{{font-family:Oswald,sans-serif;font-weight:700;text-transform:uppercase}} .r{{color:{ROSSO}}} .c{{position:absolute;left:0;right:0;text-align:center}}{css}</style>{corpo}"""


def _html_intro():
    return _html(f'<img id=logo style="position:absolute;left:90px;width:900px;top:520px" src="{_logo_uri()}">'
                 '<div id=sub class="c o" style="top:1130px;font-size:54px;color:#b9b9c3">Tutto su F1 e MotoGP · in italiano</div>'
                 '<div id=url class="c o r" style="top:1650px;font-size:70px">gpoggi.it</div>')


async def clip_intro(browser, secondi, uscita):
    page = await browser.new_page(viewport={"width": W, "height": H})
    await page.set_content(_html_intro())
    await page.wait_for_timeout(400)
    enc = _encoder(uscita)
    for i in range(round(secondi * FPS)):
        t = i / FPS
        await page.evaluate("""(t) => {
            const e = x => { x = Math.min(1, Math.max(0, x)); return x * x * (3 - 2 * x); };
            const l = document.getElementById('logo'), pl = e(t / 0.55);
            const rimb = t >= 0.4 ? 1 + 0.06 * Math.max(0, 1 - Math.abs(t - 0.55) / 0.25) : 1;
            l.style.opacity = pl; l.style.transform = `scale(${(0.6 + 0.4 * pl) * rimb})`;
            const s = document.getElementById('sub'), u = document.getElementById('url');
            s.style.opacity = e((t - 0.9) / 0.4); s.style.transform = `translateY(${(1 - e((t - 0.9) / 0.4)) * 30}px)`;
            u.style.opacity = e((t - 1.3) / 0.4); u.style.transform = `translateY(${(1 - e((t - 1.3) / 0.4)) * 30}px)`;
        }""", t)
        enc.stdin.write(await page.screenshot(type="jpeg", quality=92))
    enc.stdin.close()
    enc.wait()
    await page.close()


async def clip_fermo(browser, html, secondi, uscita):
    page = await browser.new_page(viewport={"width": W, "height": H})
    await page.set_content(html)
    await page.wait_for_timeout(400)
    img = await page.screenshot(type="png")
    png = Path(str(uscita) + ".png")
    png.write_bytes(img)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(png), "-t", f"{secondi:.2f}", "-vf", f"scale={W}:{H},fade=t=in:d=0.25",
                    "-r", str(FPS), "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(uscita)], check=True)
    await page.close()


def html_app():
    blocco = lambda titolo, passi: (f'<div style="margin:0 90px 50px;padding:40px 50px;border:3px solid #3c3c42;border-radius:28px;background:#16161a"><div class="o r" style="font-size:52px">{titolo}</div>'
                                    + "".join(f'<div style="display:flex;align-items:center;gap:26px;margin-top:32px;font-size:42px"><span style="flex:none;width:56px;height:56px;border-radius:50%;background:{ROSSO};display:flex;align-items:center;justify-content:center;font-weight:700">{n}</span>{p}</div>' for n, p in enumerate(passi, 1)) + "</div>")
    return _html(f'<img src="{_logo_uri()}" style="position:absolute;left:290px;top:150px;width:500px">'
                 '<div class="c o" style="top:420px;font-size:86px;line-height:1.1">Installalo<br>come un\'app</div>'
                 f'<div style="position:absolute;left:0;right:0;top:760px">{blocco("iPhone · Safari", ["Tocca Condividi", "«Aggiungi alla schermata Home»", "Tocca Aggiungi"])}'
                 f'{blocco("Android · Chrome", ["Tocca il menu in alto", "«Installa app»", "Conferma"])}</div>')


def html_fine():
    return _html(f'<img src="{_logo_uri()}" style="position:absolute;left:90px;top:520px;width:900px">'
                 f'<div class="c o r" style="top:1130px;font-size:110px">gpoggi.it</div>'
                 '<div class="c" style="top:1290px;font-size:46px;color:#b9b9c3">Gratis · senza registrazione</div>'
                 '<div class="c o" style="top:1420px;font-size:52px">Instagram e TikTok · @gp.oggi</div>'
                 '<div class="c" style="top:1760px;font-size:30px;color:#85858f">Sito non ufficiale, non affiliato a Formula 1, FIA, MotoGP, Dorna o ai team</div>')


async def principale(args):
    base = "http://localhost:8141"
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8141", "-d", str(SITO)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            testi = [INTRO] + [x["voce"] for x in SCENE]
            if args.prova:
                durate = [3.0] * len(testi)
                await registra(base, tmp, durate[1:1 + len(AZIONI)], True)
                print("Prova completata: tutte le azioni funzionano.")
                return
            voci, durate = [], []
            for i, testo in enumerate(testi):
                f = tmp / f"voce{i}.mp3"
                await _voce(testo, f)
                voci.append(f)
                durate.append(_durata(f))
            n = len(AZIONI)
            dur_intro = durate[0] + 0.9
            async with async_playwright() as p:
                browser = await p.chromium.launch(executable_path=CHROMIUM)
                await clip_intro(browser, dur_intro, tmp / "intro.mp4")
                dur_app = durate[1 + n] + 0.6
                await clip_fermo(browser, html_app(), dur_app, tmp / "app.mp4")
                dur_fine = durate[2 + n] + 1.4
                await clip_fermo(browser, html_fine(), dur_fine, tmp / "fine.mp4")
                await browser.close()
            tour, inizi = await registra(base, tmp, durate[1:1 + n], False)
            dur_tour = _durata(tour)
            lista = tmp / "lista.txt"
            lista.write_text("".join(f"file '{tmp / c}'\n" for c in ("intro.mp4", "tour.mp4", "app.mp4", "fine.mp4")))
            video = tmp / "video.mp4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(video)], check=True)
            partenze = [0.0] + [dur_intro + t for t in inizi] + [dur_intro + dur_tour, dur_intro + dur_tour + dur_app]
            ingressi, filtri = [], []
            for i, (f, t0) in enumerate(zip(voci, partenze)):
                ingressi += ["-i", str(f)]
                filtri.append(f"[{i + 1}:a]adelay={int((t0 + 0.25) * 1000)}:all=1[v{i}]")
            mix = "".join(f"[v{i}]" for i in range(len(voci)))
            filtri.append(f"{mix}amix=inputs={len(voci)}:normalize=0,aformat=sample_rates=44100:channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=9[a]")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), *ingressi, "-filter_complex", ";".join(filtri), "-map", "0:v", "-map", "[a]",
                            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", str(args.uscita)], check=True)
            print(f"Fatto: {args.uscita} ({_durata(args.uscita):.1f}s)")
    finally:
        srv.terminate()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", action="store_true")
    ap.add_argument("--uscita", default=str(QUI / "video-demo-sito.mp4"))
    asyncio.run(principale(ap.parse_args()))
