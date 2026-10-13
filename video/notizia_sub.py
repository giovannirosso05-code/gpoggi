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


def foto_da_url(url, credito="Foto: ESPN"):
    """Foto orizzontale scaricata al momento (mai nel repository) e portata a 1080x1920: sfondo sfocato e la foto a tutta larghezza al centro.
    Serve per mostrare macchine e circuiti; la scena ha "foto_url" e il credito scritto nel video."""
    import hashlib, requests
    from PIL import Image, ImageFilter
    cache = QUI / "_cache" / "url"; cache.mkdir(parents=True, exist_ok=True)
    f = cache / (hashlib.sha1(url.encode()).hexdigest()[:16] + ".jpg")
    if not f.exists():
        r = requests.get(url, headers={"User-Agent": "GPOggiBot/0.1 (sito non ufficiale; giovannirosso05@gmail.com)"}, timeout=40,
                         verify="/root/.ccr/ca-bundle.crt" if os.path.exists("/root/.ccr/ca-bundle.crt") else True)
        r.raise_for_status()
        f.write_bytes(r.content)
    im = Image.open(f).convert("RGB")
    sfondo = im.resize((int(H * im.width / im.height), H)).filter(ImageFilter.GaussianBlur(40))
    sfondo = sfondo.crop(((sfondo.width - W) // 2, 0, (sfondo.width - W) // 2 + W, H))
    sfondo = Image.eval(sfondo, lambda v: int(v * 0.45))
    alto = 880   # la foto riempie la fascia centrale (ritagliata al centro), sopra i sottotitoli
    fg = im.resize((int(alto * im.width / im.height), alto))
    x0 = max(0, (fg.width - W) // 2)
    sfondo.paste(fg.crop((x0, 0, x0 + W, alto)), (0, 330))
    out = f.with_suffix(".1080.png"); sfondo.save(out)
    return out, credito


def file_foto(f):
    for k in ("file_grande", "file"):
        if f.get(k) and (SITO / f[k]).exists():
            return SITO / f[k]
    raise SystemExit("file foto mancante")


# Come la voce deve dire alcuni nomi (i sottotitoli restano scritti giusti)
PRONUNCIA = {"Russell": "Rassel", "Leclerc": "Leclèr", "Lawson": "Lòson", "Hadjar": "Adgiàr", "Martin": "Martìn", "Vasseur": "Vasér", "Button": "Bàtton", "Schiff": "Sciff"}


def pronuncia(parola):
    nuda = parola.strip(".,:;!?'\"…")
    return parola.replace(nuda, PRONUNCIA[nuda]) if nuda in PRONUNCIA else parola


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
    # un segno di punteggiatura da solo (per esempio la virgola dopo [Nome]) non è una parola: va attaccato a quella prima,
    # altrimenti i sottotitoli contano una parola in più della voce e scalano di un posto
    res = []
    for w, fl in out:
        if res and not any(c.isalnum() for c in w):
            res[-1] = (res[-1][0] + w, res[-1][1])
        else:
            res.append((w, fl))
    return res


VOCE_PIPER = "it_IT-riccardo-x_low"   # voce di riserva (maschile, gira sul computer, senza internet) se Microsoft rifiuta la connessione


def _tempi_stimati(testo, uscita):
    """Le voci di riserva non danno i tempi delle parole: si stimano in proporzione alla lunghezza."""
    tot = durata(uscita)
    parole = testo.split()
    pesi = [len(w) + (4 if w[-1:] in ",.;:!?" else 0) + 1 for w in parole]
    t, out = 0.0, []
    for w, pe in zip(parole, pesi):
        d = tot * pe / sum(pesi)
        out.append((w, t, t + d)); t += d
    return out


def voce_azure(testo, velocita, uscita, grido=False):
    """Voce ufficiale Azure (la stessa it-IT-DiegoNeural di sempre, con i tempi veri delle parole). Serve la chiave gratuita in due segreti:
    AZURE_SPEECH_KEY e AZURE_SPEECH_REGION (impostazioni del repository su GitHub, mai scritte nei file)."""
    import azure.cognitiveservices.speech as sdk
    chiave, regione = os.environ["AZURE_SPEECH_KEY"].strip(), os.environ["AZURE_SPEECH_REGION"].strip()
    cfg = sdk.SpeechConfig(subscription=chiave, region=regione)
    cfg.speech_synthesis_voice_name = VOCE
    cfg.set_speech_synthesis_output_format(sdk.SpeechSynthesisOutputFormat.Audio24Khz96KBitRateMonoMp3)
    sint = sdk.SpeechSynthesizer(speech_config=cfg, audio_config=sdk.audio.AudioOutputConfig(filename=str(uscita)))
    parole = []
    sint.synthesis_word_boundary.connect(lambda e: parole.append((e.text, e.audio_offset / 1e7, e.audio_offset / 1e7 + e.duration.total_seconds())))
    rate, vol = ("+55%", "+100%") if grido else (velocita, "+0%")
    ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="it-IT"><voice name="{VOCE}">'
            f'<prosody rate="{rate}" volume="{vol}">{esc(testo)}</prosody></voice></speak>')
    r = sint.speak_ssml_async(ssml).get()
    if r.reason != sdk.ResultReason.SynthesizingAudioCompleted:
        raise RuntimeError(f"Azure: {r.reason}")
    del sint
    return parole


def voce_kokoro(testo, velocita, uscita, grido=False):
    """Prima riserva: Kokoro (modello neurale che gira sul computer, voce maschile italiana 'nicola'), molto piu' naturale di Piper."""
    import urllib.request
    import soundfile as sf
    from kokoro_onnx import Kokoro
    cart = QUI / "_cache" / "voci"; cart.mkdir(parents=True, exist_ok=True)
    for nome in ("kokoro-v1.0.int8.onnx", "voices-v1.0.bin"):
        if not (cart / nome).exists():
            urllib.request.urlretrieve(f"https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/{nome}", cart / nome)
    k = Kokoro(str(cart / "kokoro-v1.0.int8.onnx"), str(cart / "voices-v1.0.bin"))
    pct = 55 if grido else int(re.sub(r"[^\d-]", "", str(velocita)) or 0)
    campioni, sr = k.create(testo, voice="im_nicola", speed=min(2.0, 1 + pct / 100), lang="it")
    wav = Path(uscita).with_suffix(".wav")
    sf.write(str(wav), campioni, sr)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-ar", "24000", str(uscita)], check=True)
    wav.unlink()
    return _tempi_stimati(testo, uscita)


def voce_piper(testo, velocita, uscita, grido=False):
    """Riserva quando edge-tts da' errore 403: voce Piper. Non da' i tempi delle parole: si stimano in proporzione alla lunghezza."""
    import urllib.request, wave
    from piper import PiperVoice, SynthesisConfig
    cart = QUI / "_cache" / "voci"; cart.mkdir(parents=True, exist_ok=True)
    for est in ("onnx", "onnx.json"):
        f = cart / f"{VOCE_PIPER}.{est}"
        if not f.exists():
            urllib.request.urlretrieve(f"https://huggingface.co/rhasspy/piper-voices/resolve/main/it/it_IT/riccardo/x_low/{VOCE_PIPER}.{est}", f)
    v = PiperVoice.load(str(cart / f"{VOCE_PIPER}.onnx"))
    pct = 55 if grido else int(re.sub(r"[^\d-]", "", str(velocita)) or 0)
    wav = Path(uscita).with_suffix(".wav")
    with wave.open(str(wav), "wb") as w:
        v.synthesize_wav(testo, w, SynthesisConfig(length_scale=1 / (1 + pct / 100)))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-ar", "24000", str(uscita)], check=True)
    wav.unlink()
    return _tempi_stimati(testo, uscita)


RALLENTA = 0.985   # tutte le voci 1,5% più lente (3% era troppo, dimezzato su richiesta del gestore, 13 ottobre 2026)


def rallenta(velocita):
    pct = int(re.sub(r"[^\d-]", "", str(velocita)) or 0)
    return f"{round((1 + pct / 100) * RALLENTA * 100 - 100):+d}%"


async def voce(testo, velocita, uscita, grido=False):
    """Scrive l'audio e restituisce [(parola, inizio, fine)] in secondi.
    Con grido=True la voce è la stessa di sempre (stesso tono) ma molto più forte e più veloce, come un urlo di esultanza.
    Se la voce Microsoft (edge-tts) rifiuta la connessione, si usa la voce di riserva Piper."""
    parole, audio = [], b""
    velocita = rallenta(velocita)
    if os.environ.get("AZURE_SPEECH_KEY") and os.environ.get("AZURE_SPEECH_REGION"):
        try:
            parole = voce_azure(testo, velocita, uscita, grido)
            if parole:
                return _dopo_grido(uscita, grido, parole)
        except Exception as e:
            print("Azure non risponde (%s): provo le altre voci" % str(e)[:80], flush=True)
    extra = dict(rate="+55%", volume="+100%") if grido else dict(rate=velocita)
    try:
        c = edge_tts.Communicate(testo, VOCE, boundary="WordBoundary", **extra)
        async for ch in c.stream():
            if ch["type"] == "audio":
                audio += ch["data"]
            elif ch["type"] == "WordBoundary":
                parole.append((ch["text"], ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7))
        if not audio:
            raise RuntimeError("nessun audio")
        Path(uscita).write_bytes(audio)
    except Exception as e:
        print("edge-tts non risponde (%s): voce di riserva" % str(e)[:80], flush=True)
        try:
            parole = voce_piper(testo, velocita, uscita, grido)
        except Exception as e2:
            print("Piper non disponibile (%s): voce Kokoro" % str(e2)[:80], flush=True)
            parole = voce_kokoro(testo, velocita, uscita, grido)
    return _dopo_grido(uscita, grido, parole)


def _dopo_grido(uscita, grido, parole):
    if grido:   # ancora più volume, senza distorcere (limitatore)
        grezzo = Path(uscita).with_suffix(".raw.mp3")
        Path(uscita).replace(grezzo)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(grezzo), "-af", "volume=2.2,alimiter=limit=0.9", str(uscita)], check=True)
        grezzo.unlink()
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
.sub{{position:absolute;left:90px;width:780px;top:{scena.get('sub_top', spec.get('sub_top', 1180))}px;text-align:center;font:700 62px/1.18 Oswald;text-transform:uppercase;word-spacing:.18em;-webkit-text-stroke:2px #000;paint-order:stroke fill;text-shadow:0 4px 18px rgba(0,0,0,.7)}}
.sub .g{{color:{GIALLO}}} .sub .s{{color:{nom}}}
.fg{{position:absolute;left:0;width:1080px;top:400px;height:760px;background:url(data:image/jpeg;base64,{foto_b64}) center/contain no-repeat;filter:drop-shadow(0 30px 60px rgba(0,0,0,.6))}}
.cla{{position:absolute;left:60px;right:60px;top:450px;background:rgba(11,11,14,.82);border-radius:22px;padding:26px 30px;box-shadow:0 30px 80px rgba(0,0,0,.6)}}
.cla h3{{margin:0 0 14px;font:700 40px Oswald;text-transform:uppercase;letter-spacing:.04em;color:{GIALLO}}}
.cla .r{{display:flex;align-items:center;gap:20px;padding:13px 0;border-top:1px solid rgba(255,255,255,.12);font:600 40px Oswald;text-transform:uppercase}}
.cla .p{{width:44px;text-align:right;color:rgba(255,255,255,.7)}} .cla .b{{width:12px;height:44px;border-radius:4px}}
.cla .n{{flex:1}} .cla .pt{{font-variant-numeric:tabular-nums}} .cla .d{{width:110px;text-align:right;color:#4ade80;font-size:32px}} .cla .d.z{{color:rgba(255,255,255,.45)}}
.alto{{position:absolute;left:0;right:0;top:0;height:880px;background:url(data:image/jpeg;base64,{foto_b64}) {scena.get('pos_pista', 'center')}/cover no-repeat}}
.basso{{position:absolute;left:0;right:0;top:880px;bottom:0;background:url(data:image/jpeg;base64,{scena.get('_volto', '')}) center {scena.get('pos_volto', '12%')}/cover no-repeat}}
.cuci{{position:absolute;left:0;right:0;top:874px;height:12px;background:{col}}}
.velo2{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.5) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,0) 62%,rgba(0,0,0,.55) 82%,rgba(0,0,0,.8) 100%)}}
.diviso .nome{{top:790px}} .diviso .sub{{top:1430px}}
.gri{{position:absolute;left:40px;right:40px;top:440px;height:1300px;overflow:hidden;-webkit-mask-image:linear-gradient(180deg,transparent 0,#000 40px,#000 1220px,transparent 1300px)}}
.gri .l{{position:absolute;left:0;right:0;top:{40 - scena.get('_scroll', 0)}px}}
.gri h3{{margin:0 0 18px;font:700 44px Oswald;text-transform:uppercase;color:{GIALLO};text-align:center}}
.gri .r{{display:flex;align-items:center;gap:16px;width:600px;margin:0 0 14px;background:rgba(11,11,14,.85);border-radius:14px;padding:12px 18px;font:600 38px Oswald;text-transform:uppercase}}
.gri .r.pari{{margin-left:auto}} .gri .p{{width:56px;color:{GIALLO};font-weight:700}} .gri .b{{width:10px;height:46px;border-radius:4px}}
.gri .n{{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}} .gri .x{{font:600 24px Inter;color:#ff8a80;text-transform:none}}
.gri .nota{{text-align:center;font:500 26px Inter;color:rgba(255,255,255,.75);margin-top:10px}}
.pista .bg{{inset:-60px;filter:blur(36px) brightness(.45)}}
.cred{{position:absolute;right:40px;bottom:36px;font:500 20px Inter;color:rgba(255,255,255,.75);max-width:600px;text-align:right}}
</style>""" + ('<div class=alto></div><div class=basso></div><div class=velo2></div><div class=cuci></div><div class=diviso>' if scena.get("_volto") else '') + ('' if scena.get("_volto") else '<div class=pista><div class=bg></div></div><div class=velo></div>' + ('' if scena.get("classifica") or scena.get("griglia") else '<div class=fg></div>') if scena.get("pista") or scena.get("classifica") or scena.get("griglia") else '<div class=bg></div><div class=velo></div>') + """<div class=prog></div>"""
    if finale:
        return (f"""<!doctype html><meta charset=utf-8><style>{CSS_FONT}
*{{box-sizing:border-box}} html,body{{margin:0;width:{W}px;height:{H}px;background:#0b0b0e;color:#fff;overflow:hidden;position:relative}}
.bg{{position:absolute;inset:-60px;background:url(data:image/jpeg;base64,{foto_b64}) center 14%/cover no-repeat;filter:blur(38px) brightness(.5)}}
.prog{{position:absolute;left:0;top:0;height:10px;width:100%;background:{col}}}
.c{{position:absolute;left:0;right:0;top:560px;text-align:center}} .c img{{width:420px}}
.q{{margin:70px 100px 0;font:700 80px/1.08 Oswald;text-transform:uppercase;-webkit-text-stroke:2px #000;paint-order:stroke fill}}
.cm{{margin:34px 100px 0;font:600 50px/1.1 Oswald;text-transform:uppercase;color:{GIALLO};letter-spacing:.03em}}
.u{{margin-top:50px;font:700 56px Oswald;color:{nom};letter-spacing:.04em}} .n{{position:absolute;left:60px;right:60px;bottom:90px;text-align:center;font:500 22px Inter;color:rgba(255,255,255,.7)}}
</style><div class=bg></div><div class=prog></div><div class=c><img src="data:image/png;base64,{logo}"><div class=q>{esc(finale)}</div><div class=cm>Dimmi la tua nei commenti</div><div class=u>gpoggi.it</div></div>
<div class=n>Fonte: {esc(spec['fonte'])} · Sito non ufficiale, non affiliato a Formula 1, FIA, MotoGP, Dorna o ai team. Eventuali voti: a scopo divertente, senza offendere nessuno</div>""")
    etichetta = esc(spec.get("etichetta", "Ultim'ora"))
    corpo = f'<img class=logo src="data:image/png;base64,{logo}"><div class=tag>{etichetta}</div>'
    if hook:
        righe = "".join(f'<span style="display:inline-block;background:{col};padding:4px 16px;margin:4px 0">{esc(r)}</span><br>' for r in re.findall(r".{1,16}(?:\s|$)", spec["scene"][0]["hook_titolo"].upper()))
        corpo += f'<div style="position:absolute;left:60px;right:60px;top:860px;font:700 82px/1.12 Oswald;text-transform:uppercase;-webkit-text-stroke:2px #000;paint-order:stroke fill">{righe}</div>'
    else:
        corpo += f'<div class=strip>{esc(spec["titolo_breve"])}</div>'
        if nome and scena.get("nome"):
            corpo += f'<div class=nome>{esc(scena["nome"])}</div>'
        if sub:
            corpo += '<div class=sub>' + " ".join(f'<span class="{fl}">{esc(w)}</span>' for w, fl in sub) + '</div>'
    if scena.get("classifica"):
        c = scena["classifica"]
        corpo += f'<div class=cla><h3>{esc(c["titolo"])}</h3>' + "".join(
            f'<div class=r>{"<span class=p>" + str(r["pos"]) + "</span>" if r["pos"] != "" else ""}<span class=b style="background:#{r["colore"]}"></span><span class=n>{esc(r["nome"])}</span>'
            f'<span class=pt>{r.get("voto", r.get("punti"))}</span><span class="d{"" if r.get("piu", 1) else " z"}">{esc(r["nota"]) if r.get("nota") else "+" + str(r["piu"])}</span></div>' for r in c["righe"]) + '</div>'
    if scena.get("griglia"):
        g = scena["griglia"]
        corpo += f'<div class=gri><div class=l><h3>{esc(g["titolo"])}</h3>' + "".join(
            f'<div class="r{" pari" if i % 2 else ""}"><span class=p>{r["pos"]}</span><span class=b style="background:#{r["colore"]}"></span><span class=n>{esc(r["nome"])}</span>'
            + (f'<span class=x>{esc(r["nota"])}</span>' if r.get("nota") else "") + '</div>' for i, r in enumerate(g["righe"])) + (f'<div class=nota>{esc(g["nota"])}</div>' if g.get("nota") else "") + '</div></div>'
    corpo += f'<div class=cred>{esc(credito)}</div>'
    return base + corpo


async def genera(spec, uscita):
    vel = spec.get("velocita", "+38%")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        scene = list(spec["scene"])
        finale = spec["finale"]
        for sc in scene + [finale]:
            if sc.get("foto_url"):
                sc["foto_file"], sc["credito"] = foto_da_url(sc["foto_url"], sc.get("credito", "Foto: ESPN"))
                sc.setdefault("foto", "ESPN")
        # subito dopo il gancio (la fine del video non la ascolta nessuno): invito a seguire il canale; "segui": false nella scaletta lo toglie
        if spec.get("segui", True) and scene and scene[0].get("hook") and not any("Seguici" in x.get("testo", "") for x in scene):
            scene.insert(1, {**{k: v for k, v in scene[0].items() if k in ("foto", "alt", "pista", "volto_alt", "foto_file", "credito", "pos")},
                             "testo": "*Seguici* per altri contenuti come questo.", "pausa": 0.2})
        # audio e tempi
        t = 0.0; lavoro = []
        for i, s in enumerate(scene + [dict(finale, testo=finale["domanda"] + " Dimmi la tua nei commenti.", finale=True)]):
            tok = token(s["testo"]); parlato = " ".join(pronuncia(w) for w, _ in tok)
            mp3 = tmp / f"v{i}.mp3"
            tempi = await voce(parlato, vel, mp3, grido=bool(s.get("grido")))
            lead = (tempi[0][1] + 0.03) if tempi else 0
            if lead > 0.05 and not s.get("grido"):   # anche il silenzio iniziale si toglie
                tagliato = mp3.with_suffix(".t.mp3")
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{lead:.3f}", "-i", str(mp3), str(tagliato)], check=True)
                tagliato.replace(mp3); tempi = [(w, a - lead, b - lead) for w, a, b in tempi]
            d = durata(mp3)
            # il file della voce finisce con un silenzio: si taglia dopo l'ultima parola.
            # "attacca": true sulla scena successiva = nessuna pausa, la frase continua di seguito
            if tempi and not s.get("finale"):
                d = min(d, tempi[-1][2] + 0.15)
            if lavoro and s.get("attacca"):
                prec = lavoro[-1]; prec["dur"] = min(prec["dur"], prec["tempi"][-1][2] + 0.02) if prec["tempi"] else prec["dur"]
                t = prec["ini"] + prec["dur"]; prec["gap"] = 0.0
            d = max(d, s.get("durata_min", 0))
            if lavoro and s.get("pausa"):
                t += s["pausa"]   # silenzio tra il gancio e la scena seguente (l'immagine resta quella di prima)
            lavoro.append(dict(s=s, tok=tok, tempi=tempi, ini=t, dur=d, mp3=mp3, gap=0.1))
            t += d + 0.1
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
                if s["s"].get("pista") and not s["s"].get("classifica") and not s["s"].get("finale") and s["s"].get("volto", True):
                    # schermo diviso: sopra la macchina in pista, sotto il volto del pilota (niente spazio vuoto)
                    v = trova_foto(s["s"]["foto"], s["s"].get("volto_alt"))
                    s["s"]["_volto"] = b64(file_foto(v))
                    cred = cred.replace(" · Wikimedia Commons", "") + " / " + re.sub(r"Original:\s*", "", v["autore"]) + f" · {v['licenza']} · Wikimedia Commons"
                fine_scena = (lavoro[idx + 1]["ini"] if idx < len(lavoro) - 1 else s["ini"] + s["dur"] + 0.6)
                if s["s"].get("finale"):
                    f = await scatta(pagina(spec, s["s"], fb, cred, 1.0, finale=s["s"]["domanda"]))
                    quadri.append((f, s["ini"], fine_scena)); continue
                if s["s"].get("hook"):
                    f = await scatta(pagina(spec, s["s"], fb, cred, s["ini"] / totale, hook=True))
                    quadri.append((f, s["ini"], fine_scena)); continue
                if s["s"].get("griglia"):
                    fps, ferma_ini, ferma_fine = 15, 1.0, 1.2
                    corsa = s["s"]["griglia"].get("scorri", 1300)
                    durata_sc = fine_scena - s["ini"]
                    nq = max(2, int(durata_sc * fps))
                    for q in range(nq):
                        t_rel = q / fps
                        x = min(1, max(0, (t_rel - ferma_ini) / max(0.1, durata_sc - ferma_ini - ferma_fine)))
                        x = x * x * (3 - 2 * x)   # parte e si ferma morbida
                        s["s"]["_scroll"] = int(corsa * x)
                        f = await scatta(pagina(spec, s["s"], fb, cred, (s["ini"] + t_rel) / totale))
                        quadri.append((f, s["ini"] + t_rel, min(fine_scena, s["ini"] + (q + 1) / fps) if q < nq - 1 else fine_scena))
                    continue
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
