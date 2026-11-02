"""Video lezione «Diritto dei trasporti» (Argomenti 1-8): UNA voce che spiega, con gli schemi di ogni argomento mostrati mentre ne parla.
Il contenuto sta in video/lezione_testi/argN.py (solo il testo del documento «Diritto dei trasporti – risposte corrette sulle slide 2026-27»).
Pipeline: per ogni «battuta» (un pezzo di parlato + la voce di schema che compare) → voce (Azure / edge-tts / Piper) + immagine 1920x1080 → segmento video; poi si uniscono.
Uso:  python3 lezione.py [--prova N] [--solo 1,2] [--uscita FILE] [--invia]
  --prova N  : solo le prime N battute (controllo veloce)   --solo : solo alcuni argomenti"""
import argparse, asyncio, hashlib, html, importlib, json, os, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notizia_sub as NS  # noqa: E402

QUI = Path(__file__).parent
W, H = 1920, 1080
SPAZIO = 0.35        # pausa tra le battute (s)
SPAZIO_SLIDE = 0.9   # pausa a fine schermata
SPAZIO_ARG = 1.4     # pausa dopo la chiusura di un argomento

# ---------------------------------------------------------------- testo parlato
ABBR = [
    (r"\bC-(\d+)/(\d+)", r"C \1 barra \2"),
    (r"\bartt\.", "articoli"), (r"\bart\.", "articolo"), (r"\bD\.lgs\.", "decreto legislativo"), (r"\bD\.L\.", "decreto legge"), (r"\bD\.M\.", "decreto ministeriale"),
    (r"\bD\.P\.R\.", "decreto del Presidente della Repubblica"), (r"\bDPR\b", "decreto del Presidente della Repubblica"), (r"\bDPCM\b", "decreto del Presidente del Consiglio dei ministri"),
    (r"\bL\. cost\.", "legge costituzionale"), (r"\bL\.", "legge"), (r"\bn\.", "numero"), (r"\bReg\.", "regolamento"), (r"\bDir\.", "direttiva"),
    (r"\bcod\. nav\.", "codice della navigazione"), (r"\bcod\. civ\.", "codice civile"), (r"\bc\.c\.", "codice civile"), (r"\breg\. nav\. mar\.", "regolamento per la navigazione marittima"),
    (r"\bS\.p\.A\.", "società per azioni"), (r"\bs\.p\.a\.", "società per azioni"), (r"\bS\.r\.l\.", "società a responsabilità limitata"),
    (r"\bes\.", "ad esempio"), (r"\bss\.", "e seguenti"), (r"\becc\.", "eccetera"), (r"\bprof\.ssa", "professoressa"), (r"\bc\. (\d)", r"comma \1"), (r"\bpar\. (\d)", r"paragrafo \1"),
    (r"\blett\.", "lettera"), (r"(\d)°", r"\1"), (r"%", " per cento"), (r"\s/\s", " barra "), (r"(\d)/(\d)", r"\1 barra \2"), (r"\bGDPR\b", "G D P R"), (r"\bIA\b", "intelligenza artificiale"),
    (r"\bEUR\b", "euro"), (r"\bkg\b", "chilogrammi"), (r"\b(\d+) t\b", r"\1 tonnellate"), 
]


SIGLE = {"MIT": "emme i ti", "MEF": "emme e effe", "ART": "a erre ti", "AGCM": "a gi ci emme", "TFUE": "ti effe u e", "AdSP": "a di esse pi", "DPSS": "di pi esse esse",
         "PRP": "pi erre pi", "POT": "pi o ti", "DEASP": "di e a esse pi", "RFI": "erre effe i", "PEF": "pi e effe", "PIR": "pi i erre", "COA": "ci o a", "CIV": "ci i vu",
         "CIM": "ci i emme", "ICAO": "i cao", "IMO": "i emme o", "UE": "u e", "CE": "ci e", "CEE": "ci e e", "CCI": "ci ci i", "AM": "a emme", "TEN-T": "ten ti", "FS": "effe esse",
         "SGHA": "esse gi acca a", "AP": "a pi", "CdA": "ci di a", "USA": "u esse a", "COM": "ci o emme", "DM": "decreto ministeriale", "AI": "ei ai", "TV": "ti vu"}
_RE_SIGLE = re.compile(r"(?<![\w-])(" + "|".join(re.escape(k) for k in sorted(SIGLE, key=len, reverse=True)) + r")(?![\w-])")


def parla(t):
    t = t.replace("**", "").replace("\u200b", "")
    for a, b in ABBR:
        t = re.sub(a, b, t)
    t = _RE_SIGLE.sub(lambda m: SIGLE[m.group(1)], t)
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------- struttura del contenuto
def S(tipo, titolo, beats, colonne=None, sotto=None, chiusura=False):
    """Una schermata. beats = [(voce_di_schema | None, parlato), ...]. tipo: lista | flusso | mappa | tabella | ricorda."""
    return dict(tipo=tipo, titolo=titolo, beats=beats, colonne=colonne, sotto=sotto, chiusura=chiusura)


def pagine(sl, per_pagina=None):
    """Spezza una schermata con troppe voci (o troppo testo) in più schermate dello stesso titolo, così nulla esce dallo schermo."""
    per = per_pagina or {"lista": 5, "flusso": 5, "mappa": 7, "tabella": 4, "ricorda": 6}[sl["tipo"]]
    budget = {"lista": 620, "flusso": 620, "mappa": 560, "tabella": 900, "ricorda": 620}[sl["tipo"]]
    out, cur, n, ch = [], [], 0, 0
    for v, p in sl["beats"]:
        if v is not None:
            L = len(v.replace("**", ""))
            if n and (n >= per or ch + L > budget):
                out.append(cur); cur, n, ch = [], 0, 0
            n += 1; ch += L
        cur.append((v, p))
    out.append(cur)
    tot = len(out)
    return [dict(sl, beats=b, titolo=sl["titolo"] if tot == 1 else f"{sl['titolo']} ({i + 1}/{tot})") for i, b in enumerate(out)]


def evid(t):
    return re.sub(r"\*\*(.+?)\*\*", r"<b class=k>\1</b>", html.escape(t, quote=False).replace("&lt;", "<").replace("&gt;", ">") if False else html.escape(t, quote=False))


def card(v):
    if "|" in v:
        a, b = v.split("|", 1)
        return f"<div class=l>{evid(a)}</div><div class=d>{evid(b)}</div>"
    return f"<div class=l>{evid(v)}</div>"


CSS = f"""{NS.CSS_FONT}
*{{box-sizing:border-box}} html,body{{margin:0;width:{W}px;height:{H}px;background:#0e1626;color:#f2f4f8;font-family:Inter,sans-serif;overflow:hidden;position:relative}}
.top{{position:absolute;left:70px;right:70px;top:34px;display:flex;justify-content:space-between;font:600 26px Inter;color:#8da2c0;letter-spacing:.04em;text-transform:uppercase}}
.arg{{color:#f5b301}}
h1{{position:absolute;left:70px;right:70px;top:82px;margin:0;font:700 66px/1.05 Oswald;letter-spacing:.01em}}
.sot{{position:absolute;left:70px;right:70px;top:162px;font:500 30px Inter;color:#9fb0c8}}
.area{{position:absolute;left:70px;right:70px;top:{{TOP}}px;bottom:70px}}
.bar{{position:absolute;left:0;bottom:0;height:10px;background:#f5b301}}
b.k{{color:#ffd24a;font-weight:700}}
.c{{background:#18243a;border:3px solid #24344f;border-radius:18px;padding:16px 26px;margin-bottom:{{GAP}}px;opacity:.78}}
.c.on{{opacity:1;border-color:#f5b301;background:#1f2e4a;box-shadow:0 0 0 2px rgba(245,179,1,.25)}}
.c .l{{font:700 {{FL}}px/1.15 Oswald;letter-spacing:.01em}} .c .d{{font:500 {{FD}}px/1.3 Inter;color:#c8d3e6;margin-top:6px}}
.fl{{text-align:center;color:#f5b301;font:700 34px/0.7 Oswald;margin:-2px 0 {{GAP}}px}}
.ric{{display:flex;gap:18px;align-items:flex-start}} .ric i{{font-style:normal;font-size:44px;color:#f5b301;line-height:1}}
table{{width:100%;border-collapse:separate;border-spacing:0 10px}} th{{text-align:left;font:700 28px Oswald;color:#f5b301;letter-spacing:.06em;text-transform:uppercase;padding:6px 18px}}
td{{background:#18243a;padding:14px 18px;font:500 {{FT}}px/1.25 Inter;vertical-align:top;border-top:3px solid #24344f;border-bottom:3px solid #24344f;opacity:.78}}
td:first-child{{border-left:3px solid #24344f;border-radius:14px 0 0 14px;font:700 {{FT1}}px/1.2 Oswald}} td:last-child{{border-right:3px solid #24344f;border-radius:0 14px 14px 0}}
tr.on td{{opacity:1;background:#1f2e4a;border-color:#f5b301}}
.mp{{display:flex;gap:56px;height:100%}} .mc{{width:520px;flex:none;align-self:center;background:#f5b301;color:#13203a;border-radius:24px;padding:34px;font:700 54px/1.1 Oswald;text-align:center}}
.mr{{flex:1;display:flex;flex-direction:column;justify-content:center;position:relative;padding-left:46px;border-left:6px solid #f5b301}}
.mr .c::before{{content:"";position:absolute;left:0;width:40px;height:4px;background:#f5b301;margin-top:30px}}
.mr .c{{position:relative;margin-left:0}}
.vt{{position:absolute;left:70px;right:70px;top:210px;font:500 38px/1.3 Inter;color:#c8d3e6}}
"""


def pagina(arg, sl, k, progresso):
    """HTML della schermata allo stato k (voci 0..k visibili, la k evidenziata)."""
    tipo = sl["tipo"]
    voci = [v for v, _ in sl["beats"] if v is not None]
    # indice della voce corrente: quante voci non nulle fino alla battuta k
    nv = sum(1 for v, _ in sl["beats"][:k + 1] if v is not None)
    vis = voci[:nv]
    sotto = f"<div class=sot>{evid(sl['sotto'])}</div>" if sl.get("sotto") else ""
    top = 215 if sl.get("sotto") else 180
    n = max(len(voci), 1)
    fl, fd, gap = (58, 38, 20) if n <= 3 else (50, 35, 16) if n <= 4 else (44, 32, 14) if n <= 5 else (40, 30, 12) if n <= 6 else (36, 27, 10)
    ft, ft1 = (34, 38) if n <= 3 else (30, 34) if n <= 5 else (27, 31)
    corpo = ""
    if tipo in ("lista", "ricorda", "flusso"):
        for i, v in enumerate(vis):
            on = " on" if i == len(vis) - 1 else ""
            marca = "<i>⚠</i>" if tipo == "ricorda" else ""
            corpo += (f"<div class='c{on}'>" + (f"<div class=ric>{marca}<div>{card(v)}</div></div>" if marca else card(v)) + "</div>")
            if tipo == "flusso" and i < len(voci) - 1:
                corpo += "<div class=fl>▼</div>" if i < len(vis) - 1 else ""
    elif tipo == "mappa":
        centro = vis[0] if vis else ""
        ram = "".join(f"<div class='c{' on' if i == len(vis) - 2 else ''}'>{card(v)}</div>" for i, v in enumerate(vis[1:]))
        cA, _, cB = centro.partition("|")
        corpo = f"<div class=mp><div class=mc>{evid(cA)}" + (f"<div style='font:500 30px/1.3 Inter;margin-top:16px;color:#2a3a5a'>{evid(cB)}</div>" if cB else "") + f"</div><div class=mr>{ram}</div></div>"
    elif tipo == "tabella":
        cols = sl["colonne"]
        corpo = "<table><tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in cols) + "</tr>"
        for i, v in enumerate(vis):
            celle = v.split("|")
            corpo += f"<tr class='{'on' if i == len(vis) - 1 else ''}'>" + "".join(f"<td>{evid(c)}</td>" for c in celle) + "</tr>"
        corpo += "</table>"
    if sl.get("vt"):   # schermata di transizione: titolo grande
        return (f"<!doctype html><meta charset=utf-8><style>{CSS.replace('{TOP}', '0')}</style><div class=top><span class=arg>Diritto dei trasporti</span><span>slide 2026-27</span></div>"
                f"<div style='position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:0 160px'>"
                f"<div style='font:600 40px Inter;color:#f5b301;letter-spacing:.12em;text-transform:uppercase'>{html.escape(sl['vt'])}</div>"
                f"<div style='font:700 104px/1.05 Oswald;margin-top:26px'>{html.escape(sl['titolo'])}</div></div><div class=bar style='width:{progresso * W:.0f}px'></div>")
    css = CSS.replace("{TOP}", str(top)).replace("{GAP}", str(gap)).replace("{FL}", str(fl)).replace("{FD}", str(fd)).replace("{FT}", str(ft)).replace("{FT1}", str(ft1))
    return (f"<!doctype html><meta charset=utf-8><style>{css}</style><div class=top><span><span class=arg>Argomento {arg['n']}</span> · {html.escape(arg['titolo'])}</span><span>Diritto dei trasporti</span></div>"
            f"<h1>{evid(sl['titolo'])}</h1>{sotto}<div class=area>{corpo}</div><div class=bar style='width:{progresso * W:.0f}px'></div>")


# ---------------------------------------------------------------- costruzione
def carica(solo=None):
    args = []
    for f in sorted(QUI.glob("lezione_testi/arg[0-9].py")):
        n = int(re.search(r"arg(\d)", f.name).group(1))
        if solo and n not in solo:
            continue
        m = importlib.import_module(f"lezione_testi.arg{n}")
        args.append(dict(n=n, titolo=m.TITOLO, intro=m.INTRO, schermate=[p for s in m.SCHERMATE for p in pagine(s)]))
    return args


def transizione(a, prec):
    """Breve transizione con il titolo dell'argomento (schermata + frase)."""
    frase = f"Argomento {a['n']}. {a['titolo']}."
    return dict(tipo="lista", titolo=a["titolo"], vt=f"Argomento {a['n']}", beats=[(None, parla(frase))], colonne=None, sotto=None, chiusura=False)


def battute(args):
    """[(arg, schermata, k, parlato, pausa_dopo)] in ordine."""
    out = []
    for ia, a in enumerate(args):
        tr = transizione(a, None)
        out.append((a, tr, 0, tr["beats"][0][1], SPAZIO_SLIDE))
        intro = dict(tipo="lista", titolo=a["titolo"], beats=[(None, parla(a["intro"]))], colonne=None, sotto=None, vt=f"Argomento {a['n']}")
        out.append((a, intro, 0, parla(a["intro"]), SPAZIO_SLIDE))
        for si, sl in enumerate(a["schermate"]):
            for k, (v, p) in enumerate(sl["beats"]):
                ult = k == len(sl["beats"]) - 1
                fine_arg = ult and si == len(a["schermate"]) - 1
                out.append((a, sl, k, parla(p), SPAZIO_ARG if fine_arg else (SPAZIO_SLIDE if ult else SPAZIO)))
    return out


def durata(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)], capture_output=True, text=True).stdout or 0)


async def genera(args, uscita, prova=None):
    from playwright.async_api import async_playwright
    bt = battute(args)
    if prova:
        bt = bt[:prova]
    lav = QUI / "_cache" / "lezione"; lav.mkdir(parents=True, exist_ok=True)
    tot = len(bt)
    print(f"{tot} battute", flush=True)
    segmenti, capitoli, t = [], [], 0.0
    async with async_playwright() as p:
        b = await p.chromium.launch(**({"executable_path": "/opt/pw-browsers/chromium"} if Path("/opt/pw-browsers/chromium").exists() else {}), args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": W, "height": H})
        ult_arg = None
        for i, (a, sl, k, testo, pausa) in enumerate(bt):
            h = hashlib.sha1(f"{testo}|{sl['titolo']}|{k}|{NS.VOCE}".encode()).hexdigest()[:12]
            mp3, png, seg = lav / f"{h}.mp3", lav / f"{h}.png", lav / f"{h}_{int(pausa * 100)}.mp4"
            if not seg.exists():
                if not mp3.exists():
                    if os.environ.get("LEZIONE_SENZA_VOCE"):   # prova grafica in locale: silenzio lungo quanto servirebbe il parlato
                        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{max(1.0, len(testo.split()) / 2.7):.2f}", str(mp3)], check=True)
                    else:
                        await NS.voce(testo, "+0%", mp3)
                await pg.set_content(pagina(a, sl, k, (i + 1) / tot)); await pg.wait_for_timeout(60)
                await pg.screenshot(path=str(png))
                d = durata(mp3) + pausa
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "1", "-i", str(png), "-i", str(mp3), "-af", f"apad=pad_dur={pausa}",
                                "-t", f"{d:.2f}", "-vf", "scale=1280:720,format=yuv420p", "-c:v", "libx264", "-tune", "stillimage", "-crf", "36", "-r", "2", "-g", "20",
                                "-c:a", "aac", "-b:a", "28k", "-ar", "24000", "-ac", "1", str(seg)], check=True)
            if a["n"] != ult_arg and sl.get("vt"):
                capitoli.append((t, f"Argomento {a['n']} – {a['titolo']}")); ult_arg = a["n"]
            t += durata(seg)
            segmenti.append(seg)
            if i % 25 == 0:
                print(f"  {i}/{tot}  {t / 60:.1f} min", flush=True)
        await b.close()
    lista = lav / "lista.txt"
    lista.write_text("".join(f"file '{s}'\n" for s in segmenti))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", "-movflags", "+faststart", str(uscita)], check=True)
    cap = "\n".join(f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d} {nome}" for s, nome in capitoli)
    Path(uscita).with_suffix(".capitoli.txt").write_text(cap + "\n")
    print(f"Fatto: {uscita} ({t / 60:.1f} min)\n{cap}")
    return capitoli


def invia_telegram(video, capitoli, titolo="video lezione (argomenti 1-8)"):
    """Manda il video sul Telegram del proprietario (se supera i 48 MB lo divide agli argomenti, senza ricodificare) e i capitoli come messaggio."""
    import requests
    tok = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_CANALE") or os.environ.get("TELEGRAM_CHAT_ID") or "559225883"
    if not tok:
        print("Token Telegram mancante: video non inviato."); return
    video = Path(video); parti = [video]
    if video.stat().st_size > 48 * 2 ** 20:
        n = video.stat().st_size // (45 * 2 ** 20) + 1
        tot = durata(video); tagli = []
        for k in range(1, n):
            target = tot * k / n
            tagli.append(min((c[0] for c in capitoli), key=lambda t: abs(t - target)))
        tagli = sorted(set(tagli)); parti = []
        for k, a in enumerate([0.0] + tagli):
            b = (tagli + [tot])[k]
            f = video.with_name(f"{video.stem}_parte{k + 1}.mp4")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.2f}", "-to", f"{b:.2f}", "-i", str(video), "-c", "copy", "-movflags", "+faststart", str(f)], check=True)
            parti.append(f)
    for k, f in enumerate(parti):
        with open(f, "rb") as fh:
            requests.post(f"https://api.telegram.org/bot{tok}/sendVideo", data={"chat_id": chat, "caption": f"🎓 Diritto dei trasporti, {titolo}" + (f" · parte {k + 1}/{len(parti)}" if len(parti) > 1 else ""),
                          "supports_streaming": "true", "disable_notification": "true", "width": 1280, "height": 720}, files={"video": fh}, timeout=900, verify=NS.CA if hasattr(NS, "CA") else True).raise_for_status()
    cap = "\n".join(f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d} {nome}" for s, nome in capitoli)
    requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": chat, "text": "📚 Capitoli (tempi del video intero)\n\n" + cap + ("\n\nIl video è diviso in %d parti agli argomenti." % len(parti) if len(parti) > 1 else "")}, timeout=60).raise_for_status()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", type=int); ap.add_argument("--solo"); ap.add_argument("--uscita", type=Path, default=QUI / "lezione.mp4"); ap.add_argument("--invia", action="store_true")
    a = ap.parse_args()
    solo = {int(x) for x in a.solo.split(",")} if a.solo else None
    cap = asyncio.run(genera(carica(solo), a.uscita, a.prova))
    if a.invia and not a.prova:   # le prove non vanno mai sul Telegram
        invia_telegram(a.uscita, cap, "video lezione, argomento " + a.solo if a.solo and "," not in a.solo else "video lezione (argomenti 1-8)")


if __name__ == "__main__":
    main()
