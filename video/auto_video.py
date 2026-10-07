"""Video automatici di GP Oggi, pensati per girare su GitHub Actions senza intervento (voce Diego, schermate 1080x1920, ffmpeg).

  python video/auto_video.py notizia      una notizia della rassegna (prima quella scelta con il voto su Telegram, poi le altre, F1 e MotoGP a turno)
  python video/auto_video.py previsioni   i tre favoriti F1 e MotoGP del prossimo Gran Premio, dall'indice di pronostici.json

Nessun testo copiato: della notizia si usano solo titolo, fonte e link; i numeri dei pronostici vengono dai dati del sito.
Con --invia il video va al bot Telegram (TELEGRAM_BOT_TOKEN, TELEGRAM_CANALE) senza notifica; lo stato sta in video_stato.json.
"""
import argparse, asyncio, base64, html, json, os, re, ssl, subprocess, sys, tempfile, unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import edge_tts, edge_tts.communicate as C
import requests
from playwright.async_api import async_playwright

CA = "/root/.ccr/ca-bundle.crt"
if Path(CA).exists():
    C._SSL_CTX = ssl.create_default_context(cafile=CA)
QUI = Path(__file__).parent; ROOT = QUI.parent; SITO = ROOT / "docs"; DATA = SITO / "data"; FONT = QUI / "logo" / "font"
STATO = ROOT / "video_stato.json"
CHROMIUM = os.environ.get("GP_CHROMIUM") or ("/opt/pw-browsers/chromium" if Path("/opt/pw-browsers/chromium").exists() else None)
ROMA = ZoneInfo("Europe/Rome")
W, H = 1080, 1920
VOCE, VELOCITA = "it-IT-DiegoNeural", "+12%"
ROSSO, BLU = "#e8352f", "#1f5fd1"
norm = lambda s: unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower().strip()
b64 = lambda p: base64.b64encode(Path(p).read_bytes()).decode()
esc = lambda s: html.escape(s or "")
UN = "zero uno due tre quattro cinque sei sette otto nove dieci undici dodici tredici quattordici quindici sedici diciassette diciotto diciannove".split()
DEC = ["", "", "venti", "trenta", "quaranta", "cinquanta", "sessanta", "settanta", "ottanta", "novanta"]
def it(n):
    n = int(n)
    if n < 20: return UN[n]
    d, u = divmod(n, 10); base = DEC[d]
    if u in (1, 8): base = base[:-1]
    return base + (UN[u] if u else "") if n < 100 else str(n)
GIORNI = "lunedì martedì mercoledì giovedì venerdì sabato domenica".split()
MESI = "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split()

def foto_file(f):
    return SITO / (f.get("file_grande") or f["file"]) if f else None
def piloti():
    """[(cognome normalizzato, nome, foto)] da F1 (roster) e MotoGP (piloti + foto-motogp)."""
    out = []
    for p in json.load(open(DATA / "roster.json")):
        if p.get("foto"): out.append((norm(p["nome"]).split()[-1], p["nome"], p["foto"], "F1"))
    fm = json.load(open(DATA / "foto-motogp.json")); mp = json.load(open(DATA / "motogp-piloti.json"))
    for i, p in mp.items():
        if i in fm: out.append((norm(p["nome"]).split()[-1], p["nome"], fm[i], "MotoGP"))
    return out
def pilota_nel_titolo(titolo, serie):
    t = " " + re.sub(r"[^a-z ]", " ", norm(titolo)) + " "
    for cogn, nome, foto, s in piloti():
        if len(cogn) > 3 and f" {cogn} " in t and (s == serie or serie not in ("F1", "MotoGP")): return nome, foto
    return None, None

CSS = f"""@font-face{{font-family:Oswald;font-weight:700;src:url(data:font/woff2;base64,{b64(FONT / 'oswald-latin-700-normal.woff2')})}}
@font-face{{font-family:Inter;font-weight:500;src:url(data:font/woff2;base64,{b64(FONT / 'inter-latin-500-normal.woff2')})}}
*{{box-sizing:border-box}} html,body{{margin:0;width:{W}px;height:{H}px;background:#0b0b0e;color:#fff;font-family:Inter,sans-serif;overflow:hidden}}
.logo{{position:absolute;left:0;right:0;top:34px;text-align:center}} .logo img{{width:300px}}
.foto{{position:absolute;left:0;top:190px;width:{W}px;height:760px;background-size:{W}px auto;background-position:center -60px;background-repeat:no-repeat}}
.vel{{position:absolute;left:0;top:190px;width:{W}px;height:760px;background:linear-gradient(180deg,#0b0b0e 0%,rgba(11,11,14,0) 12%,rgba(11,11,14,0) 70%,#0b0b0e 100%)}}
.pill{{position:absolute;left:70px;font:700 34px Oswald;letter-spacing:.08em;padding:3px 20px;border-radius:8px;text-transform:uppercase}}
.cred{{position:absolute;left:70px;right:70px;font:500 24px Inter;color:#8a8a96}}
.url{{position:absolute;left:0;right:0;top:1700px;text-align:center;font:700 64px Oswald;letter-spacing:.04em}}
.avviso{{position:absolute;left:70px;right:70px;top:1835px;text-align:center;font:500 22px Inter;color:#6d6d78}}"""

def cornice(corpo, colore, foto=None, cred=True):
    sfondo = f"<div class=foto style=\"background-image:url(data:image/jpeg;base64,{b64(foto_file(foto))})\"></div><div class=vel></div>" if foto and foto_file(foto).exists() else ""
    c = f"<div class=cred style='top:1640px'>Foto: {esc(foto.get('autore',''))} · {esc(foto.get('licenza',''))} · via Wikimedia Commons</div>" if foto and cred else ""
    return (f"<!doctype html><meta charset=utf-8><style>{CSS}.url{{color:{colore}}}</style><div class=logo><img src='data:image/png;base64,{b64(SITO / 'img/logo-wide-scuro.png')}'></div>"
            f"{sfondo}{corpo}{c}<div class=url>gpoggi.it</div><div class=avviso>Sito non ufficiale, non affiliato a Formula 1, FIA, MotoGP, Dorna o ai team</div>")

def pagina_notizia(a, foto):
    colore = BLU if a.get("serie") == "MotoGP" else ROSSO
    t = a["titolo"]; px = 78 if len(t) < 55 else 64 if len(t) < 95 else 54
    if not foto: px += 10
    quando = ""
    try:
        d = datetime.fromisoformat(a["pubblicato"]).astimezone(ROMA); quando = f"{d.day} {MESI[d.month - 1]}"
    except Exception: pass
    corpo = (f"<span class=pill style='top:{800 if foto else 560}px;background:{colore}'>{esc(a.get('serie','F1'))} · notizia</span>"
             f"<h1 style=\"position:absolute;left:70px;right:70px;top:{868 if foto else 630}px;margin:0;font:700 {px}px/1.06 Oswald;text-transform:uppercase\">{esc(t)}</h1>"
             f"<div style='position:absolute;left:70px;right:70px;top:{1350 if foto else 1050}px;font:500 38px Inter;color:#c9c9d2'>Fonte: <b style='color:#fff'>{esc(a['fonte'])}</b>{' · ' + quando if quando else ''}</div>"
             f"<div style='position:absolute;left:70px;right:70px;top:{1430 if foto else 1130}px;font:500 34px Inter;color:#8a8a96'>Articolo completo sul sito della fonte: il link è nella descrizione.</div>")
    return cornice(corpo, colore, foto)

def testo_notizia(a, nome):
    serie = "Moto G P" if a.get("serie") == "MotoGP" else "Formula uno"
    titolo = re.sub(r"\b(ADUO\d?|DRS|ERS|KERS|MGU)\b", lambda m: " ".join(m.group(1)), a["titolo"])  # le sigle si leggono lettera per lettera
    return f"{serie}, notizia di oggi. {titolo}. Fonte: {a['fonte']}. Il link all'articolo completo è nella descrizione. Tutte le notizie su G P Oggi punto it."

def pagine_previsioni():
    pron = json.load(open(DATA / "pronostici.json")); ro = {p["nome"]: p for p in json.load(open(DATA / "roster.json"))}
    fm = json.load(open(DATA / "foto-motogp.json")); out = []
    for chiave, sigla, colore in (("f1", "Formula 1", ROSSO), ("motogp", "MotoGP", BLU)):
        p = pron.get(chiave)
        if not p or not p.get("favoriti"): continue
        top = p["favoriti"][:3]
        d = datetime.fromisoformat(p["gara"]).astimezone(ROMA)
        foto = (ro.get(top[0]["nome"], {}).get("foto") if chiave == "f1" else fm.get(top[0].get("id")))
        righe = "".join(f"<div style='display:flex;align-items:center;gap:22px;padding:14px 0;border-bottom:2px solid #26262e'><span style='font:700 64px Oswald;color:{colore};width:60px'>{i}</span>"
                        f"<div style='flex:1'><div style='font:700 46px Oswald;text-transform:uppercase'>{esc(f['nome'])}</div><div style='font:500 28px Inter;color:#b6b5bd'>{esc(f['team'])} · {esc(f['motivi'][0] if f.get('motivi') else '')}</div></div>"
                        f"<b style='font:700 54px Oswald'>{f['indice']}</b></div>" for i, f in enumerate(top, 1))
        corpo = (f"<span class=pill style='top:800px;background:{colore}'>{sigla} · il pronostico</span>"
                 f"<h1 style='position:absolute;left:70px;right:70px;top:858px;margin:0;font:700 66px/1 Oswald;text-transform:uppercase'>{esc(p['gp'])}</h1>"
                 f"<div style='position:absolute;left:70px;right:70px;top:942px;font:500 32px Inter;color:#c9c9d2'>Gara {GIORNI[d.weekday()]} {d.day} {MESI[d.month-1]} · indice da 0 a 100</div>"
                 f"<div style='position:absolute;left:70px;right:70px;top:1010px'>{righe}</div>"
                 f"<div style='position:absolute;left:70px;right:70px;top:1470px;font:500 28px Inter;color:#8a8a96'>Opinione di GP Oggi basata sui numeri (forma, classifica, circuito), non una previsione ufficiale. Tu chi dici? Gioca sul sito.</div>")
        a = ", ".join(f"{f['nome']} con indice {f['indice']}" for f in top)
        voce = (f"Il pronostico di G P Oggi per il {p['gp']}, gara {GIORNI[d.weekday()]} {it(d.day)} {MESI[d.month-1]}. " +
                f"I tre favoriti: {a}. È un indice che mette insieme la forma, la classifica e il risultato sullo stesso circuito. È un'opinione, non una certezza: tu chi dici? Fai il tuo pronostico su G P Oggi punto it.")
        out.append((cornice(corpo, colore, foto), voce))
    return out

async def componi(scene, uscita):
    """scene = [(html, testo)] -> mp4 verticale con la voce."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); clip = []
        async with async_playwright() as p:
            b = await p.chromium.launch(**({"executable_path": CHROMIUM} if CHROMIUM else {}), args=["--no-sandbox"])
            pg = await b.new_page(viewport={"width": W, "height": H})
            for i, (h, t) in enumerate(scene):
                await edge_tts.Communicate(t, VOCE, rate=VELOCITA).save(str(tmp / f"v{i}.mp3"))
                await pg.set_content(h); await pg.wait_for_timeout(500); await pg.screenshot(path=str(tmp / f"s{i}.png"))
            await b.close()
        for i in range(len(scene)):
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(tmp / f"v{i}.mp3")], capture_output=True, text=True).stdout)
            c = tmp / f"c{i}.mp4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", str(tmp / f"s{i}.png"), "-i", str(tmp / f"v{i}.mp3"),
                            "-af", "adelay=400:all=1,apad=pad_dur=0.9,loudnorm=I=-14:TP=-1.5:LRA=9", "-t", f"{dur + 1.3:.2f}", "-c:v", "libx264", "-tune", "stillimage", "-crf", "21",
                            "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", str(c)], check=True)
            clip.append(f"file '{c}'")
        (tmp / "l.txt").write_text("\n".join(clip))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(tmp / "l.txt"), "-c", "copy", "-movflags", "+faststart", str(uscita)], check=True)

def pulisci_titolo(t):
    """Toglie il prefisso della fonte ("MotoGP | ", "F1 | "): a video e a voce non serve."""
    return re.sub(r"^\s*(?:MotoGP|F1|Formula\s*1|Formula\s*Uno)\s*[|:–-]\s*", "", t or "", flags=re.I).strip()


def scegli_notizia(stato):
    fatte = set(stato.get("notizie", []))
    rass = json.load(open(DATA / "rassegna.json"))["articoli"]
    scelta = ROOT / "video" / "scelta.json"
    if scelta.exists():
        s = json.load(open(scelta))
        if s.get("url") and s["url"] not in fatte:
            return next((a for a in rass if a["url"] == s["url"]), None) or {"titolo": s["titolo"], "fonte": s["fonte"], "serie": s.get("serie", "F1"), "url": s["url"]}
    libere = [a for a in rass if a["url"] not in fatte]
    turno = "MotoGP" if stato.get("ultima_serie") == "F1" else "F1"
    return next((a for a in libere if a.get("serie", "F1") == turno), None) or (libere[0] if libere else None)

def social_notizia(n):
    tag = "#motogp" if n["serie"] == "MotoGP" else "#f1 #formula1"
    return f"{n['titolo']} 📰\n\nFonte: {n['fonte']}.\n\nCosa ne pensi? Scrivilo nei commenti 👇\n\n🔗 gpoggi.it\n\n#gpoggi {tag} #notizie"


def social_previsioni():
    pron = json.load(open(DATA / "pronostici.json")); righe = []
    for chiave, icona in (("f1", "🏁"), ("motogp", "🏍️")):
        p = pron.get(chiave)
        if p and p.get("favoriti"):
            righe.append(f"{icona} {p['gp']}\n" + "\n".join(f"{i}. {f['nome']}" for i, f in enumerate(p["favoriti"][:3], 1)))
    return "Il pronostico di GP Oggi 🔮\n\n" + "\n\n".join(righe) + "\n\nÈ un'opinione basata sui numeri, non una certezza.\n\nTu chi dici? 👇\n\n🔗 gpoggi.it\n\n#gpoggi #f1 #motogp #pronostici #previsioni"


def invia_testo(testo):
    """Didascalia pronta per TikTok e Instagram, in un messaggio a parte dentro un riquadro: un tocco e si copia tutta."""
    tok = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN"); chat = os.environ.get("TELEGRAM_CANALE") or os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat: return
    r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": chat, "parse_mode": "HTML", "disable_notification": "true", "disable_web_page_preview": "true",
                      "text": "📋 <b>Didascalia per TikTok e Instagram</b> (tocca per copiare)\n\n<pre>" + html.escape(testo) + "</pre>"}, timeout=60)
    r.raise_for_status()


def invia(video, didascalia):
    tok = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN"); chat = os.environ.get("TELEGRAM_CANALE") or os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat: print("Token Telegram mancante: video non inviato."); return False
    with open(video, "rb") as f:
        r = requests.post(f"https://api.telegram.org/bot{tok}/sendVideo", data={"chat_id": chat, "caption": didascalia[:1000], "supports_streaming": "true", "disable_notification": "true", "width": W, "height": H}, files={"video": f}, timeout=300)
    r.raise_for_status(); return True

def main():
    social = None
    ap = argparse.ArgumentParser(); ap.add_argument("cosa", choices=["notizia", "previsioni"]); ap.add_argument("--invia", action="store_true"); ap.add_argument("--uscita", type=Path, default=QUI / "auto.mp4")
    a = ap.parse_args()
    stato = json.load(open(STATO)) if STATO.exists() else {}
    if a.cosa == "notizia":
        n = scegli_notizia(stato)
        if not n: print("Nessuna notizia nuova."); return
        n.setdefault("serie", "F1")
        n = {**n, "titolo": pulisci_titolo(n["titolo"])}
        nome, foto = pilota_nel_titolo(n["titolo"], n["serie"])
        scene = [(pagina_notizia(n, foto), testo_notizia(n, nome))]
        social = social_notizia(n)
        did = f"📰 {n['titolo']}\n\nFonte: {n['fonte']}\nArticolo: {n['url']}\n\n🏁 Tutte le notizie: https://gpoggi.it\n\n#{'MotoGP' if n['serie']=='MotoGP' else 'F1'} #gpoggi"
    else:
        scene = pagine_previsioni()
        if not scene: print("Nessun pronostico disponibile."); return
        social = social_previsioni()
        did = "🔮 Il pronostico di GP Oggi per il prossimo weekend: F1 e MotoGP.\nUn'opinione basata sui numeri, non una certezza. Tu chi dici? Fai il tuo pronostico: https://gpoggi.it/giochi.html\n\n#F1 #MotoGP #gpoggi"
    asyncio.run(componi(scene, a.uscita)); print("Video:", a.uscita)
    if a.invia and invia(a.uscita, did):
        invia_testo(social)
        if a.cosa == "notizia":
            stato.setdefault("notizie", []).insert(0, n["url"]); stato["notizie"] = stato["notizie"][:400]; stato["ultima_serie"] = n["serie"]
        else:
            stato["previsioni"] = datetime.now(ROMA).strftime("%Y-%m-%d")
        STATO.write_text(json.dumps(stato, ensure_ascii=False, indent=1)); print("Inviato.")

if __name__ == "__main__":
    main()
