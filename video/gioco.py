"""Gioco del giorno di GP Oggi in video (stile "Chi è?" di MMA Oggi): l'immagine parte molto sgranata e si schiarisce a gradini,
gli indizi compaiono uno alla volta (letti dalla voce) e alla fine arriva l'invito a scrivere la risposta nei commenti.
Tutti i dati vengono dal sito (docs/data): nessun testo da scrivere a mano, quindi può girare ogni giorno da solo su GitHub Actions.

  python3 gioco.py pilota  [--serie f1|moto] [--nome "Kimi Antonelli"] [--uscita FILE]   Indovina il pilota (foto pixelata)
  python3 gioco.py circuito [--nome "Gran Premio di Singapore"] [--uscita FILE]          Indovina il circuito (mappa sfocata, senza scritte)
Senza --nome sceglie in base al giorno (a rotazione). Scrive anche FILE.json con risposta e didascalia.
"""
import argparse, asyncio, base64, io, json, re, ssl, subprocess, sys, tempfile
from datetime import date, datetime
from pathlib import Path

import edge_tts, edge_tts.communicate as C
from PIL import Image, ImageFilter
from playwright.async_api import async_playwright

if Path("/root/.ccr/ca-bundle.crt").exists():
    C._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
QUI = Path(__file__).parent; SITO = QUI.parent / "docs"; DATA = SITO / "data"; FONT = QUI / "logo" / "font"
W, H = 1080, 1920
H_ = H
VOCE, VEL = "it-IT-DiegoNeural", "+8%"
PROFILO = "@gp.oggi"
b64 = lambda p: base64.b64encode(Path(p).read_bytes()).decode()
MESI = "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split()
UN = "zero uno due tre quattro cinque sei sette otto nove dieci undici dodici tredici quattordici quindici sedici diciassette diciotto diciannove".split()
DEC = ["", "", "venti", "trenta", "quaranta", "cinquanta", "sessanta", "settanta", "ottanta", "novanta"]
NAZ = {"Italian": "Italia", "British": "Regno Unito", "Dutch": "Paesi Bassi", "Monegasque": "Principato di Monaco", "Spanish": "Spagna", "German": "Germania", "French": "Francia",
       "Australian": "Australia", "Canadian": "Canada", "Thai": "Thailandia", "Japanese": "Giappone", "Finnish": "Finlandia", "Mexican": "Messico", "Brazilian": "Brasile",
       "Argentine": "Argentina", "New Zealander": "Nuova Zelanda", "Chinese": "Cina", "American": "Stati Uniti", "Danish": "Danimarca", "Swiss": "Svizzera", "Belgian": "Belgio",
       "Austrian": "Austria", "Portuguese": "Portogallo", "Polish": "Polonia", "Indonesian": "Indonesia", "South African": "Sudafrica", "Czech": "Repubblica Ceca"}


def it(n):
    n = int(n)
    if n < 20: return UN[n]
    if n < 100:
        d, u = divmod(n, 10); base = DEC[d]
        if u in (1, 8): base = base[:-1]
        return base + ("tré" if u == 3 else UN[u] if u else "")
    if n < 1000:
        c, r = divmod(n, 100); base = "cento" if c == 1 else UN[c] + "cento"
        if r and 80 <= r < 90: base = base[:-1]
        return base + (it(r) if r else "")
    m, r = divmod(n, 1000); return ("mille" if m == 1 else it(m) + "mila") + (it(r) if r else "")


def eta(nascita):
    d = datetime.fromisoformat(nascita).date(); t = date.today()
    return t.year - d.year - ((t.month, t.day) < (d.month, d.day))


def autore(a):
    return re.sub(r"Original:\s*", "", a or "").strip()


def foto_file(f):
    for k in ("file_grande", "file"):
        if f.get(k) and (SITO / f[k]).exists():
            return SITO / f[k]
    raise SystemExit("file foto mancante")


def scegli_pilota(serie, nome):
    sc = json.load(open(DATA / "schede.json")); anno = date.today().year
    cand = []
    if serie in (None, "f1"):
        for p in json.load(open(DATA / "roster.json")):
            s = sc.get(f"f1:{p['numero']}")
            if p.get("foto") and s and s.get("nascita") and NAZ.get(s.get("nazionalita")) and s.get("gare") is not None:
                cand.append(dict(serie="F1", nome=p["nome"], foto=p["foto"], naz=NAZ[s["nazionalita"]], eta=eta(s["nascita"]),
                                 numeri=(f"{s['gare']} GP · {s['vittorie']} vittorie", f"{it(s['gare'])} Gran Premi e {it(s['vittorie'])} {'vittoria' if s['vittorie'] == 1 else 'vittorie'}")))
    if serie in (None, "moto"):
        fm = json.load(open(DATA / "foto-motogp.json"))
        for i, p in json.load(open(DATA / "motogp-piloti.json")).items():
            s = sc.get(f"moto:{i}") or {}
            if p.get("categoria") != "MotoGP" or i not in fm or not s.get("nascita") or not p.get("paese"):
                continue
            t = s.get("totali")
            numeri = ((f"{t['gare']} GP · {t['vittorie']} vittorie", f"{it(t['gare'])} Gran Premi e {it(t['vittorie'])} {'vittoria' if t['vittorie'] == 1 else 'vittorie'}") if t
                      else (f"{p['vittorie']} {'vittoria' if p['vittorie'] == 1 else 'vittorie'} nel {anno}", f"{it(p['vittorie'])} {'vittoria' if p['vittorie'] == 1 else 'vittorie'} in questa stagione"))
            cand.append(dict(serie="MotoGP", nome=p["nome"], foto=fm[i], naz=p["paese"], eta=eta(s["nascita"]), numeri=numeri))
    if not cand:
        raise SystemExit("nessun pilota con tutti i dati")
    if nome:
        return next(c for c in cand if c["nome"] == nome)
    return cand[(date.today().toordinal() * 2 + (1 if serie == "moto" else 0)) % len(cand)] if serie else cand[date.today().toordinal() % len(cand)]


def immagine_pilota(c):
    im = Image.open(foto_file(c["foto"])).convert("RGB"); w, h = im.size; s = min(w, h)
    top = int((h - s) * 0.12) if h > w else 0; left = (w - s) // 2
    return im.crop((left, top, left + s, top + s)).resize((908, 908), Image.LANCZOS)


def livelli_pixel(im, passi=(6, 8, 11, 15, 21, 30)):
    out = []
    for n in passi:
        out.append(im.resize((n, n), Image.BILINEAR).resize((908, 908), Image.NEAREST))
    return out


def png64(im):
    b = io.BytesIO(); im.save(b, "PNG"); return base64.b64encode(b.getvalue()).decode()


CSS_FONT = (f"@font-face{{font-family:Oswald;font-weight:700;src:url(data:font/woff2;base64,{b64(FONT / 'oswald-latin-700-normal.woff2')})}}"
            f"@font-face{{font-family:Inter;font-weight:500;src:url(data:font/woff2;base64,{b64(FONT / 'inter-latin-500-normal.woff2')})}}")


def pagina(col, titolo, sotto, img64, indizi_visibili, avanz, credito, finale, chi):
    logo = b64(SITO / "img/logo-wide-scuro.png")
    righe = "".join(f'<div class=r><span>{e}</span><b>{v}</b></div>' for e, v in indizi_visibili)
    fin = ""
    if finale:
        fin = (f'<div class=dim></div><div class=pan><div class=a>SCRIVI {chi}</div><div class=b>NEI COMMENTI</div><div class=btn>SEGUI {PROFILO.upper()}</div>'
               f'<div class=p>Un {"pilota" if "pilota" in sotto.lower() else "circuito"} nuovo ogni giorno</div></div>')
    return f"""<!doctype html><meta charset=utf-8><style>{CSS_FONT}
*{{box-sizing:border-box}} html,body{{margin:0;width:{W}px;height:{H}px;background:#0b0b0e;color:#fff;font-family:Inter,sans-serif;overflow:hidden;position:relative}}
.top{{position:absolute;inset:0;background:linear-gradient(180deg,{col} 0%,rgba(11,11,14,0) 38%)}} .top{{opacity:.55}}
.prog{{position:absolute;left:0;top:0;height:10px;width:{avanz * 100:.1f}%;background:{col};filter:brightness(1.4)}}
.logo{{position:absolute;left:50px;top:150px;width:190px}}
.tag{{position:absolute;left:265px;top:172px;font:700 28px Oswald;letter-spacing:.06em;text-transform:uppercase;background:{col};padding:4px 16px;border-radius:6px}}
.t{{position:absolute;left:0;right:0;top:250px;text-align:center;font:700 150px/1 Oswald;text-transform:uppercase;-webkit-text-stroke:2px #000;paint-order:stroke fill}}
.s{{position:absolute;left:0;right:0;top:412px;text-align:center;font:700 40px Oswald;letter-spacing:.04em;text-transform:uppercase;color:#fff}} .s i{{font-style:normal;color:{col};filter:brightness(1.5)}}
.img{{position:absolute;left:86px;top:490px;width:908px;height:908px;border-radius:22px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,.6)}} .img img{{width:100%;height:100%;display:block}}
.ind{{position:absolute;left:86px;top:1440px;width:830px}} .r{{display:flex;gap:30px;align-items:baseline;height:76px;font-size:30px}}
.r span{{width:280px;font:700 28px Oswald;letter-spacing:.1em;color:#ffd21f;text-transform:uppercase}} .r b{{font:700 46px Oswald;text-transform:uppercase}}
.cr{{position:absolute;right:40px;bottom:30px;font:500 20px Inter;color:rgba(255,255,255,.7)}}
.dim{{position:absolute;inset:0;background:rgba(0,0,0,.62)}}
.pan{{position:absolute;left:100px;right:100px;top:820px;text-align:center}} .a{{font:700 96px/1 Oswald}} .b{{font:700 96px/1.05 Oswald;color:{col};filter:brightness(1.5)}}
.btn{{display:inline-block;margin-top:50px;background:{col};font:700 54px Oswald;padding:14px 40px;border-radius:12px;letter-spacing:.03em}} .p{{margin-top:36px;font:500 34px Inter}}
</style><div class=top></div><div class=prog></div><img class=logo src="data:image/png;base64,{logo}"><div class=tag>Gioco del giorno</div>
<div class=t>{titolo}</div><div class=s>{sotto}</div><div class=img><img src="data:image/png;base64,{img64}"></div><div class=ind>{righe}</div>
<div class=cr>{credito}</div>{fin}"""


async def voce(testo, uscita):
    await edge_tts.Communicate(testo, VOCE, rate=VEL).save(str(uscita))
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(uscita)], capture_output=True, text=True).stdout)


async def monta(col, titolo, sotto, livelli, indizi, finale_chi, credito, intro, uscita, minimo=3.8, chi_video=None):
    """indizi = [(etichetta, valore a video, frase a voce)]; livelli = immagini dalla più sgranata alla più chiara."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        seg = [("intro", intro, None)] + [(f"i{k}", ind[2], k) for k, ind in enumerate(indizi)] + [("fine", f"Scrivi {finale_chi} nei commenti!", None)]
        t = 0.0; tempi = []
        for n, (nome, testo, k) in enumerate(seg):
            f = tmp / f"v{n}.mp3"; d = await voce(testo, f); dur = max(d + 0.5, minimo if nome != "fine" else 4.2)
            tempi.append((t, dur, f)); t += dur
        tot = t
        quadri = []
        async with async_playwright() as p:
            b = await p.chromium.launch(**({"executable_path": "/opt/pw-browsers/chromium"} if Path("/opt/pw-browsers/chromium").exists() else {}), args=["--no-sandbox"])
            pg = await b.new_page(viewport={"width": W, "height": H}); n_img = 0
            for n, (nome, testo, k) in enumerate(seg):
                ini, dur, _ = tempi[n]; fine_ = nome == "fine"
                passi = max(1, round(dur / 1.7)) if not fine_ else 1
                for q in range(passi):
                    t0 = ini + dur * q / passi; t1 = ini + dur * (q + 1) / passi
                    lv = livelli[min(len(livelli) - 1, int(((t0 + t1) / 2) / (tot - tempi[-1][1]) * len(livelli))) if not fine_ else len(livelli) - 1]
                    vis = [(e, v) for e, v, _ in indizi[:(k + 1 if k is not None else (len(indizi) if fine_ else 0))]]
                    await pg.set_content(pagina(col, titolo, sotto, png64(lv), vis, t0 / tot, credito, fine_, (chi_video or finale_chi).upper())); await pg.wait_for_timeout(100)
                    f = tmp / f"q{n_img}.png"; n_img += 1; await pg.screenshot(path=str(f)); quadri.append((f, t1 - t0))
            await b.close()
        (tmp / "l.txt").write_text("\n".join(f"file '{f}'\nduration {d:.3f}" for f, d in quadri) + f"\nfile '{quadri[-1][0]}'")
        ins, filtri = [], []
        for n, (ini, dur, f) in enumerate(tempi):
            ins += ["-i", str(f)]; filtri.append(f"[{n + 1}:a]adelay={int(ini * 1000)}:all=1[a{n}]")
        mix = "".join(f"[a{n}]" for n in range(len(tempi))) + f"amix=inputs={len(tempi)}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[out]"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(tmp / "l.txt"), *ins, "-filter_complex", ";".join(filtri) + ";" + mix, "-map", "0:v", "-map", "[out]",
                        "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "21", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest", "-movflags", "+faststart", str(uscita)], check=True)
        print(f"Fatto: {uscita} ({tot:.1f} s, {len(quadri)} fotogrammi)")


def video_pilota(a):
    c = scegli_pilota({"f1": "f1", "moto": "moto"}.get(a.serie), a.nome)
    col = "#1f5fd1" if c["serie"] == "MotoGP" else "#e8352f"
    serie_voce = "MotoGP" if c["serie"] == "MotoGP" else "Formula uno"
    indizi = [("Categoria", c["serie"].replace("F1", "Formula 1"), f"Corre in {serie_voce}."),
              ("Nazionalità", c["naz"], f"Nazionalità: {c['naz']}."),
              ("Età", f"{c['eta']} anni", f"Ha {it(c['eta'])} anni."),
              ("Numeri", c["numeri"][0], f"{c['numeri'][1][0].upper() + c['numeri'][1][1:]}.")]
    cred = f"Foto: {autore(c['foto']['autore'])} · {c['foto']['licenza']} · Wikimedia Commons"
    asyncio.run(monta(col, "CHI È?", f"Indovina il pilota di <i>{'MotoGP' if c['serie'] == 'MotoGP' else 'Formula 1'}</i>", livelli_pixel(immagine_pilota(c)), indizi, "il nome", cred,
                      f"Chi è? Indovina il pilota di {serie_voce}!", a.uscita))
    tag = "#motogp" if c["serie"] == "MotoGP" else "#f1 #formula1"
    social = f"Chi è? {'🏍️' if c['serie'] == 'MotoGP' else '🏁'}\n\nIndovina il pilota!\n\nScrivi il nome nei commenti 👇\n\nUn pilota nuovo ogni giorno.\nSeguici per scoprire la risposta.\n\n🔗 gpoggi.it\n\n#gpoggi {tag} #indovinailpilota #giocodelgiorno"
    json.dump({"tipo": "pilota", "risposta": c["nome"], "social": social}, open(str(a.uscita) + ".json", "w"), ensure_ascii=False)


def video_circuito(a):
    ev = sorted(json.load(open(DATA / "events.json")), key=lambda e: e["inizio"])
    puliti = []
    for i, e in enumerate(ev):
        m = e.get("mappa") or {}; f = m.get("file") or ""
        if f.endswith(".svg") and (SITO / f).exists():
            t = (SITO / f).read_text(errors="ignore")
            if "<image" not in t:
                puliti.append((i, e))
    if not puliti:
        raise SystemExit("nessuna mappa pulita")
    i, e = next(x for x in puliti if x[1]["nome"] == a.nome) if a.nome else puliti[date.today().toordinal() % len(puliti)]
    svg = re.sub(r"<(text|title|desc|metadata)\b.*?</\1>", "", (SITO / e["mappa"]["file"]).read_text(errors="ignore"), flags=re.S)
    d = datetime.fromisoformat(e["inizio"])

    async def mappa_png():
        async with async_playwright() as p:
            b = await p.chromium.launch(**({"executable_path": "/opt/pw-browsers/chromium"} if Path("/opt/pw-browsers/chromium").exists() else {}), args=["--no-sandbox"])
            pg = await b.new_page(viewport={"width": 908, "height": 908})
            uri = base64.b64encode(svg.encode()).decode()
            await pg.set_content(f'<body style="margin:0;background:#f4f3ef;width:908px;height:908px"><img src="data:image/svg+xml;base64,{uri}" style="position:absolute;left:44px;top:44px;width:820px;height:820px;object-fit:contain">')
            await pg.wait_for_timeout(300); await pg.screenshot(path="/tmp/_mappa.png"); await b.close()
    asyncio.run(mappa_png())
    base = Image.open("/tmp/_mappa.png").convert("RGB")
    livelli = [base.filter(ImageFilter.GaussianBlur(r)) for r in (46, 34, 24, 16, 9, 4)]
    col = "#e8352f"
    indizi = [("Categoria", "Formula 1", "Si corre in Formula uno."),
              ("Mese", MESI[d.month - 1], f"La gara è a {MESI[d.month - 1]}."),
              ("Tappa", f"{i + 1}ª del calendario", f"È la tappa numero {it(i + 1)} del campionato.")]
    cred = f"Mappa: {autore(e['mappa']['autore'])} · {e['mappa']['licenza']} · Wikimedia Commons"
    asyncio.run(monta(col, "CHE GP È?", "Indovina il <i>circuito</i> di Formula 1", livelli, indizi, "il Gran Premio", cred, "Che Gran Premio è? Indovina il circuito di Formula uno!", a.uscita, chi_video="il GP"))
    social = "Che Gran Premio è? 🏁\n\nIndovina il circuito!\n\nScrivi il Gran Premio nei commenti 👇\n\nUn circuito nuovo ogni giorno.\nSeguici per scoprire la risposta.\n\n🔗 gpoggi.it\n\n#gpoggi #f1 #formula1 #indovinailcircuito #giocodelgiorno"
    json.dump({"tipo": "circuito", "risposta": e["nome"], "social": social}, open(str(a.uscita) + ".json", "w"), ensure_ascii=False)


def invia_telegram(uscita):
    """Manda su Telegram (senza notifica) il video con la risposta nascosta come spoiler, poi la didascalia per TikTok e Instagram da copiare."""
    import html as H, os, requests
    tok = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN"); chat = os.environ.get("TELEGRAM_CANALE") or os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        print("Token Telegram mancante: video non inviato."); return False
    d = json.load(open(str(uscita) + ".json"))
    cap = f"🎮 <b>Gioco del giorno</b> · {'Chi è?' if d['tipo'] == 'pilota' else 'Che GP è?'}\nRisposta: <tg-spoiler>{H.escape(d['risposta'])}</tg-spoiler>"
    with open(uscita, "rb") as f:
        requests.post(f"https://api.telegram.org/bot{tok}/sendVideo", data={"chat_id": chat, "caption": cap, "parse_mode": "HTML", "supports_streaming": "true", "disable_notification": "true", "width": W, "height": H_},
                      files={"video": f}, timeout=300).raise_for_status()
    requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": chat, "parse_mode": "HTML", "disable_notification": "true",
                  "text": "📋 <b>Didascalia per TikTok e Instagram</b> (tocca per copiare)\n\n<pre>" + H.escape(d["social"]) + "</pre>"}, timeout=60).raise_for_status()
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("tipo", choices=["pilota", "circuito", "giorno"]); ap.add_argument("--invia", action="store_true"); ap.add_argument("--serie", choices=["f1", "moto"]); ap.add_argument("--nome"); ap.add_argument("--uscita", type=Path, default=QUI / "gioco.mp4")
    a = ap.parse_args()
    tipo = a.tipo
    if tipo == "giorno":   # a rotazione: pilota F1, pilota MotoGP, circuito
        tipo, a.serie = [("pilota", "f1"), ("pilota", "moto"), ("circuito", None)][date.today().toordinal() % 3]
    video_pilota(a) if tipo == "pilota" else video_circuito(a)
    if a.invia:
        invia_telegram(a.uscita)
