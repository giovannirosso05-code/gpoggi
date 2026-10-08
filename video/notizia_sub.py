"""Video "ULTIM'ORA" di GP Oggi: la notizia si racconta (non si legge la fonte), con la faccia del protagonista a tutto schermo,
striscia col titolo, etichetta col nome, sottotitoli a pezzetti sincronizzati parola per parola e domanda finale per i commenti.
Stile del video "ultim'ora" di MMA Oggi.

Uso:  python3 notizia_sub.py spec.json uscita.mp4

spec.json:
{ "serie": "MotoGP" | "F1", "titolo_breve": "…", "fonte": "Motorsport.com", "velocita": "+38%",
  "scene": [ {"foto": "Marc Marquez", "testo": "…", "nome": "MARC MARQUEZ" (opzionale), "hook": true (solo la prima)}, … ],
  "finale": {"foto": "Marc Marquez", "domanda": "Ha fatto bene …?"} }
Per spostare la foto nel riquadro si può aggiungere "pos": "0%" (0% = parte alta della foto) a una scena.
Nel testo: *parole* = gialle, [parole] = nel colore della serie (nomi). Ogni fatto deve venire dall'articolo, raccontato con parole proprie.
Le foto dei piloti sono quelle con licenza libera del sito (docs/img), con il credito scritto nel video.
"""
import os
import asyncio, base64, html, json, re, ssl, subprocess, sys, tempfile
from pathlib import Path

import edge_tts, edge_tts.communicate as C
from playwright.async_api import async_playwright

if os.path.exists("/root/.ccr/ca-bundle.crt"):
    C._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
QUI = Path(__file__).parent; SITO = QUI.parent / "docs"; DATA = SITO / "data"; FONT = QUI / "logo" / "font"
W, H = 1080, 1920
VOCE = "it-IT-DiegoNeural"
GIALLO = "#ffd21f"
b64 = lambda p: base64.b64encode(Path(p).read_bytes()).decode()
esc = html.escape


def trova_foto(nome, alt=None):
    """Foto libera di un pilota del sito (F1 dal roster, MotoGP dal file delle foto).
    Con alt ("ritratto", "sorriso"…) si usa una foto alternativa di docs/data/foto-extra.json, per non ripetere sempre la stessa."""
    if alt:
        extra = json.load(open(DATA / "foto-extra.json")).get(nome, {})
        if alt not in extra:
            raise SystemExit(f"Nessuna foto alternativa '{alt}' per {nome}: {', '.join(extra) or 'nessuna'}")
        return extra[alt]
    for p in json.load(open(DATA / "roster.json")):
        if p.get("nome") == nome and p.get("foto"):
            return p["foto"]
    fm = json.load(open(DATA / "foto-motogp.json"))
    if fm.get("nome:" + nome):
        return fm["nome:" + nome]
    raise SystemExit(f"Nessuna foto libera per {nome}")


def file_foto(f):
    for k in ("file_grande", "file"):
        if f.get(k) and (SITO / f[k]).exists():
            return SITO / f[k]
    raise SystemExit("file foto mancante")


def token(testo):
    """[(parola, 'g'|'s'|'')] da un testo con *gialle* e [nomi]; il testo da pronunciare è senza segni."""
    out = []
    for m in re.finditer(r"\*(.+?)\*|\[(.+?)\]|([^*\[\]]+)", testo):
        if m.group(1):
            out += [(w, "g") for w in m.group(1).split()]
        elif m.group(2):
            out += [(w, "s") for w in m.group(2).split()]
        else:
            out += [(w, "") for w in m.group(3).split()]
    return out


async def voce(testo, velocita, uscita):
    """Scrive l'audio e restituisce [(parola, inizio, fine)] in secondi."""
    c = edge_tts.Communicate(testo, VOCE, rate=velocita, boundary="WordBoundary")
    parole, audio = [], b""
    async for ch in c.stream():
        if ch["type"] == "audio":
            audio += ch["data"]
        elif ch["type"] == "WordBoundary":
            parole.append((ch["text"], ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7))
    Path(uscita).write_bytes(audio)
    return parole


def durata(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)], capture_output=True, text=True).stdout)


def pezzi(tok, tempi):
    """Raggruppa le parole in sottotitoli di 2 righe al massimo, spezzando sulla punteggiatura."""
    n = min(len(tok), len(tempi))
    out, cur = [], []
    for i in range(n):
        cur.append(i)
        testo = " ".join(tok[j][0] for j in cur)
        fine = tok[i][0][-1:] in ".!?;:,"
        if (fine and len(cur) >= 3) or len(testo) >= 30 or len(cur) >= 6:
            out.append(cur); cur = []
    if cur:
        if out and len(cur) < 2:
            out[-1] += cur
        else:
            out.append(cur)
    return [(c, tempi[c[0]][1]) for c in out]


CSS_FONT = (f"@font-face{{font-family:Oswald;font-weight:700;src:url(data:font/woff2;base64,{b64(FONT / 'oswald-latin-700-normal.woff2')})}}"
            f"@font-face{{font-family:Inter;font-weight:500;src:url(data:font/woff2;base64,{b64(FONT / 'inter-latin-500-normal.woff2')})}}")


def pos_bg(scena):
    """Posizione della foto nel riquadro: "pos" = solo verticale ("14%") oppure orizzontale e verticale ("25% 10%")."""
    p = str(scena.get("pos", "14%")).strip()
    return p if " " in p else f"center {p}"


def pagina(spec, scena, foto_b64, credito, avanzamento, sub=None, nome=False, hook=False, finale=None):
    col = "#1f5fd1" if spec["serie"] == "MotoGP" else "#e8352f"
    nom = "#5b9bff" if spec["serie"] == "MotoGP" else "#ff5a52"
    logo = b64(SITO / "img/logo-wide-scuro.png")
    base = f"""<!doctype html><meta charset=utf-8><style>{CSS_FONT}
*{{box-sizing:border-box}} html,body{{margin:0;width:{W}px;height:{H}px;background:#0b0b0e;color:#fff;font-family:Inter,sans-serif;overflow:hidden;position:relative}}
.bg{{position:absolute;inset:0;background:url(data:image/jpeg;base64,{foto_b64}) {pos_bg(scena)}/cover no-repeat}}
.velo{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,0) 45%,rgba(8,8,10,.92) 78%,#0b0b0e 100%)}}
.prog{{position:absolute;left:0;top:0;height:10px;width:{avanzamento * 100:.1f}%;background:{col}}}
.logo{{position:absolute;left:50px;top:150px;width:190px}}
.tag{{position:absolute;left:265px;top:172px;font:700 30px Oswald;letter-spacing:.06em;text-transform:uppercase;background:{col};padding:4px 16px;border-radius:6px}}
.strip{{position:absolute;left:40px;top:300px;max-width:900px;background:{col};font:700 44px/1.1 Oswald;text-transform:uppercase;padding:10px 18px}}
.nome{{position:absolute;left:60px;top:{spec.get('nome_top', 930)}px;background:#000;font:700 38px Oswald;text-transform:uppercase;letter-spacing:.04em;padding:6px 18px}}
.sub{{position:absolute;left:90px;width:780px;top:{spec.get('sub_top', 1180)}px;text-align:center;font:700 62px/1.18 Oswald;text-transform:uppercase;word-spacing:.18em;-webkit-text-stroke:2px #000;paint-order:stroke fill;text-shadow:0 4px 18px rgba(0,0,0,.7)}}
.sub .g{{color:{GIALLO}}} .sub .s{{color:{nom}}}
.cred{{position:absolute;right:40px;bottom:36px;font:500 20px Inter;color:rgba(255,255,255,.75);max-width:600px;text-align:right}}
</style><div class=bg></div><div class=velo></div><div class=prog></div>"""
    if finale:
        return (f"""<!doctype html><meta charset=utf-8><style>{CSS_FONT}
*{{box-sizing:border-box}} html,body{{margin:0;width:{W}px;height:{H}px;background:#0b0b0e;color:#fff;overflow:hidden;position:relative}}
.bg{{position:absolute;inset:-60px;background:url(data:image/jpeg;base64,{foto_b64}) center 14%/cover no-repeat;filter:blur(38px) brightness(.5)}}
.prog{{position:absolute;left:0;top:0;height:10px;width:100%;background:{col}}}
.c{{position:absolute;left:0;right:0;top:560px;text-align:center}} .c img{{width:420px}}
.q{{margin:70px 100px 0;font:700 80px/1.08 Oswald;text-transform:uppercase;-webkit-text-stroke:2px #000;paint-order:stroke fill}}
.u{{margin-top:50px;font:700 56px Oswald;color:{nom};letter-spacing:.04em}} .n{{position:absolute;left:60px;right:60px;bottom:90px;text-align:center;font:500 22px Inter;color:rgba(255,255,255,.7)}}
</style><div class=bg></div><div class=prog></div><div class=c><img src="data:image/png;base64,{logo}"><div class=q>{esc(finale)}</div><div class=u>gpoggi.it</div></div>
<div class=n>Fonte: {esc(spec['fonte'])} · Sito non ufficiale, non affiliato a Formula 1, FIA, MotoGP, Dorna o ai team</div>""")
    corpo = f'<img class=logo src="data:image/png;base64,{logo}"><div class=tag>Ultim\'ora</div>'
    if hook:
        righe = "".join(f'<span style="display:inline-block;background:{col};padding:4px 16px;margin:4px 0">{esc(r)}</span><br>' for r in re.findall(r".{1,16}(?:\s|$)", spec["scene"][0]["hook_titolo"].upper()))
        corpo += f'<div style="position:absolute;left:60px;right:60px;top:860px;font:700 82px/1.12 Oswald;text-transform:uppercase;-webkit-text-stroke:2px #000;paint-order:stroke fill">{righe}</div>'
    else:
        corpo += f'<div class=strip>{esc(spec["titolo_breve"])}</div>'
        if nome and scena.get("nome"):
            corpo += f'<div class=nome>{esc(scena["nome"])}</div>'
        if sub:
            corpo += '<div class=sub>' + " ".join(f'<span class="{fl}">{esc(w)}</span>' for w, fl in sub) + '</div>'
    corpo += f'<div class=cred>{esc(credito)}</div>'
    return base + corpo


async def genera(spec, uscita):
    vel = spec.get("velocita", "+38%")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        scene = list(spec["scene"])
        finale = spec["finale"]
        # audio e tempi
        t = 0.0; lavoro = []
        for i, s in enumerate(scene + [dict(finale, testo=finale["domanda"], finale=True)]):
            tok = token(s["testo"]); parlato = " ".join(w for w, _ in tok)
            mp3 = tmp / f"v{i}.mp3"
            tempi = await voce(parlato, vel, mp3)
            d = durata(mp3)
            lavoro.append(dict(s=s, tok=tok, tempi=tempi, ini=t, dur=d, mp3=mp3))
            t += d + 0.22
        totale = t
        fotos = {}
        for s in lavoro:
            nome = s["s"]["foto"]; chiave = f"{nome}|{s['s'].get('alt', '')}|{s['s'].get('foto_file', '')}"
            if chiave not in fotos and s["s"].get("foto_file"):
                # immagine già pronta 1080x1920 (per esempio da ritratti_espn.py) con il suo credito
                fotos[chiave] = (b64(s["s"]["foto_file"]), s["s"].get("credito", ""))
            elif chiave not in fotos:
                f = trova_foto(nome, s["s"].get("alt")); autore = re.sub(r"Original:\s*", "", f["autore"]); fotos[chiave] = (b64(file_foto(f)), f"Foto: {autore} · {f['licenza']} · Wikimedia Commons")
        # fotogrammi
        quadri = []   # (png, inizio, fine)
        async with async_playwright() as p:
            b = await p.chromium.launch(**({"executable_path": "/opt/pw-browsers/chromium"} if Path("/opt/pw-browsers/chromium").exists() else {}), args=["--no-sandbox"])
            pg = await b.new_page(viewport={"width": W, "height": H})
            k = 0
            async def scatta(html_):
                nonlocal k
                await pg.set_content(html_); await pg.wait_for_timeout(120)
                f = tmp / f"q{k}.png"; k += 1
                await pg.screenshot(path=str(f)); return f
            for idx, s in enumerate(lavoro):
                fb, cred = fotos[f"{s['s']['foto']}|{s['s'].get('alt', '')}|{s['s'].get('foto_file', '')}"]
                fine_scena = s["ini"] + s["dur"] + (0.22 if idx < len(lavoro) - 1 else 0.6)
                if s["s"].get("finale"):
                    f = await scatta(pagina(spec, s["s"], fb, cred, 1.0, finale=s["s"]["domanda"]))
                    quadri.append((f, s["ini"], fine_scena)); continue
                if s["s"].get("hook"):
                    f = await scatta(pagina(spec, s["s"], fb, cred, s["ini"] / totale, hook=True))
                    quadri.append((f, s["ini"], fine_scena)); continue
                gruppi = pezzi(s["tok"], s["tempi"])
                for gi, (ids, t0) in enumerate(gruppi):
                    ini = s["ini"] + (0 if gi == 0 else t0)
                    fine = s["ini"] + gruppi[gi + 1][1] if gi + 1 < len(gruppi) else fine_scena
                    f = await scatta(pagina(spec, s["s"], fb, cred, ini / totale, sub=[s["tok"][j] for j in ids], nome=(ini - s["ini"]) < 3.0))
                    quadri.append((f, ini, fine))
            await b.close()
        # montaggio
        lista = []
        for f, ini, fine in quadri:
            lista.append(f"file '{f}'\nduration {fine - ini:.3f}")
        lista.append(f"file '{quadri[-1][0]}'")
        (tmp / "l.txt").write_text("\n".join(lista))
        ins = []; filtri = []
        for i, s in enumerate(lavoro):
            ins += ["-i", str(s["mp3"])]
            filtri.append(f"[{i + 1}:a]adelay={int(s['ini'] * 1000)}:all=1[a{i}]")
        mix = "".join(f"[a{i}]" for i in range(len(lavoro))) + f"amix=inputs={len(lavoro)}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[out]"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(tmp / "l.txt"), *ins, "-filter_complex", ";".join(filtri) + ";" + mix,
                        "-map", "0:v", "-map", "[out]", "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "21", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest", "-movflags", "+faststart", str(uscita)], check=True)
        print(f"Fatto: {uscita} ({totale:.1f} s, {len(quadri)} fotogrammi)")


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    asyncio.run(genera(spec, sys.argv[2]))
