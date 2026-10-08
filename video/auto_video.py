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
if os.path.exists(CA):
    C._SSL_CTX = ssl.create_default_context(cafile=CA)
QUI = Path(__file__).parent; ROOT = QUI.parent; SITO = ROOT / "docs"; DATA = SITO / "data"; FONT = QUI / "logo" / "font"
STATO = ROOT / "video_stato.json"
CHROMIUM = os.environ.get("GP_CHROMIUM") or ("/opt/pw-browsers/chromium" if Path("/opt/pw-browsers/chromium").exists() else None)
ROMA = ZoneInfo("Europe/Rome")
W, H = 1080, 1920
VOCE, VELOCITA = "it-IT-DiegoNeural", "+23%"
VELOCITA_NOTIZIE = "+42%"  # circa +15% rispetto alla voce di base
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
    return f"{titolo}. Fonte: {a['fonte']}. Il link all'articolo completo è nella descrizione. Tutte le notizie su G P Oggi punto it."

ORD = "zero primo secondo terzo quarto quinto sesto settimo ottavo nono decimo undicesimo dodicesimo tredicesimo quattordicesimo quindicesimo sedicesimo diciassettesimo diciottesimo diciannovesimo ventesimo".split()
ANNO = datetime.now(ROMA).year


def _num(t, m=0):
    r = re.search(r"\d+", t or ""); return int(r.group()) if r else 0


def analisi_motivi(f):
    """Dai motivi del sito ricava le frasi: cosa fa bene (si) e cosa no (no), sia a voce sia a schermo."""
    si, no, circ = [], [], None
    for m in f.get("motivi", []):
        n = _num(m)
        if "vittori" in m and "ultime" in m:
            si.append((f"ha vinto {'una' if n == 1 else it(n)} delle ultime cinque gare", f"{n} {'vittoria' if n == 1 else 'vittorie'} nelle ultime 5 gare", "vit"))
        elif "podi" in m and "ultime" in m:
            si.append((f"è salito {it(n)} volte sul podio nelle ultime cinque gare", f"{n} podi nelle ultime 5 gare", "podi"))
        elif "campionato" in m:
            pt = re.search(r"\((\d+)", m); pt = pt.group(1) if pt else ""
            si.append((("è primo nel mondiale" if n == 1 else f"è {ORD[min(n, 20)]} nel mondiale") + (f" con {pt} punti" if pt else ""), f"{n}° nel campionato ({pt} punti)" if pt else f"{n}° nel campionato", "camp"))
        elif re.search(r"\b20\d\d:\s*\d+", m):
            anno = int(re.search(r"\b(20\d\d)", m).group(1)); pos = int(re.search(r":\s*(\d+)", m).group(1))
            quando = "l'anno scorso" if anno == ANNO - 1 else f"nel {anno}"
            circ = (pos, quando, f"Qui {anno}: {pos}°")
    return si, circ


def dati_motivi(f):
    d = {"camp": None, "vit": 0, "podi": 0, "circ": None}
    for m in f.get("motivi", []):
        n = _num(m)
        if "vittori" in m and "ultime" in m: d["vit"] = n
        elif "podi" in m and "ultime" in m: d["podi"] = n
        elif "campionato" in m: d["camp"] = n
        elif re.search(r"\b20\d\d:\s*\d+", m):
            anno = int(re.search(r"\b(20\d\d)", m).group(1)); d["circ"] = (int(re.search(r":\s*(\d+)", m).group(1)), anno == ANNO - 1, anno)
    return d


cognome = lambda nome: nome.split()[-1]


def studio_pole(chiave):
    """Chi ha preso la pole nelle ultime cinque qualifiche (dati del sito): [(nome, pole)] dal più frequente, e il nome da tenere d'occhio."""
    poli = []
    if chiave == "f1":
        gare = []
        for f in (DATA / "gare").glob("*.json"):
            d = json.load(open(f)); q = next((x for x in d["sessioni"] if x["nome"] == "Qualifiche" and x.get("risultati")), None)
            if q: gare.append((d["inizio"], q["risultati"][0]["nome"]))
        poli = [n for _, n in sorted(gare)[-5:]]
    else:
        m = json.load(open(DATA / "motogp-gare.json")); gare = []
        for g in m.values():
            r = next((x for x in (g.get("classifiche") or {}).get("MotoGP", []) if x.get("griglia") == 1), None)
            if r: gare.append((g.get("inizio") or g.get("data"), r["nome"]))
        poli = [n for _, n in sorted(gare)[-5:]]
    if not poli: return [], None
    conta = {}
    for n in poli: conta[n] = conta.get(n, 0) + 1
    ordine = sorted(conta.items(), key=lambda kv: (-kv[1], -max(i for i, n in enumerate(poli) if n == kv[0])))
    return ordine, ordine[0][0]


def foto_per_nome(nome, chiave):
    if chiave == "f1":
        return next((p.get("foto") for p in json.load(open(DATA / "roster.json")) if p["nome"] == nome), None)
    return json.load(open(DATA / "foto-motogp.json")).get("nome:" + nome)


def chiusura_voti(p, chiave):
    """Orario in cui si chiude il voto (inizio delle qualifiche): ("sabato alle quindici", "SABATO 15:00")."""
    orari = json.load(open(DATA / "gara-orari.json"))
    if chiave == "f1":
        gara_id = next((g["id"] for g in json.load(open(DATA / "events.json")) if g["nome"] == p["gp"]), None)
        k = f"q:{gara_id}"
    else:
        k = "q:m" + re.sub(r"\W", "", p["gp"])
    if k not in orari: return None, None
    d = datetime.fromisoformat(orari[k]).astimezone(ROMA)
    ora = f"alle {it(d.hour)}" + (f" e {it(d.minute)}" if d.minute else "")
    return f"{GIORNI[d.weekday()]} {ora}", f"{GIORNI[d.weekday()]} {d:%H:%M}".upper()


def scene_previsione(chiave):
    pron = json.load(open(DATA / "pronostici.json")); p = pron.get(chiave)
    if not p or not p.get("favoriti"): return []
    colore, sigla = (ROSSO, "Formula 1") if chiave == "f1" else (BLU, "MotoGP")
    fav = p["favoriti"][:3]; f0 = fav[0]
    luogo = re.sub(r"^(Gran Premio (di|del|dello|della|d')\s*|GP )", "", p["gp"]).strip()
    foto0 = foto_per_nome(f0["nome"], chiave)
    si, circ = analisi_motivi(f0)
    # --- scena 1: il favorito, perché sì e perché no
    parole_si = [t for t, _, c in sorted(si[:2], key=lambda x: x[2] != "camp")]
    no_voce = no_schermo = ""
    if circ and circ[0] > 3:
        no_voce = f" Ma {circ[1]} qui ha chiuso solo {ORD[min(circ[0], 20)]}."; no_schermo = f"Ma {circ[2].replace('Qui', 'qui')}"
    else:
        camp = next((x for x in si if x[2] == "camp"), None)
        primo = next((f for f in p["favoriti"] if "1° nel campionato" in " ".join(f.get("motivi", []))), None)
        if camp and primo and primo is not f0:
            pt0 = _num(re.search(r"\((\d+)", next(m for m in f0["motivi"] if "campionato" in m)).group(0)); pt1 = _num(re.search(r"\((\d+)", next(m for m in primo["motivi"] if "campionato" in m)).group(0))
            if pt1 > pt0:
                no_voce = f" Il dubbio? In campionato {primo['nome']} è davanti di {it(pt1 - pt0)} punti."; no_schermo = f"Dubbio: {primo['nome']} è davanti di {pt1 - pt0} punti"
    d0 = dati_motivi(f0); pezzi = []
    if d0["camp"]: pezzi.append(("primo" if d0["camp"] == 1 else ORD[min(d0["camp"], 20)]) + " nel mondiale")
    if d0["vit"]: pezzi.append(("una vittoria" if d0["vit"] == 1 else f"{it(d0['vit'])} vittorie") + " nelle ultime cinque")
    elif d0["podi"]: pezzi.append(f"{it(d0['podi'])} podi nelle ultime cinque")
    voce1 = f"{luogo}, chi sale sul podio? Per noi il favorito è {cognome(f0['nome'])}: " + ", ".join(pezzi[:2]) + "."
    if d0["circ"] and d0["circ"][0] > 3:
        scorso = "l'anno scorso " if d0["circ"][1] else ""
        voce1 += f" Ma qui {scorso}solo {ORD[min(d0['circ'][0], 20)]}."
    elif no_voce:
        primo_ = next((f for f in p["favoriti"] if dati_motivi(f)["camp"] == 1), None)
        if primo_ and primo_ is not f0: voce1 += f" Il dubbio: {cognome(primo_['nome'])} in campionato è davanti."
    righe1 = "".join(f"<div style='font:500 46px Inter;color:#e8e8ee;padding:14px 0'><b style='color:#35d07f'>SÌ</b>&nbsp; {esc(s[1])}</div>" for s in si[:2])
    if no_schermo: righe1 += f"<div style='font:500 46px Inter;color:#e8e8ee;padding:14px 0'><b style='color:#ff5a52'>NO</b>&nbsp; {esc(no_schermo)}</div>"
    c1 = (f"<span class=pill style='top:790px;background:{colore}'>{sigla} · il favorito</span>"
          f"<h1 style='position:absolute;left:70px;right:70px;top:850px;margin:0;font:700 96px/1 Oswald;text-transform:uppercase'>{esc(f0['nome'])}</h1>"
          f"<div style='position:absolute;left:70px;right:70px;top:1010px;font:500 30px Inter;color:#9a9aa6'>{esc(p['gp'])}</div>"
          f"<div style='position:absolute;left:70px;right:70px;top:1090px'>{righe1}</div>")
    # --- scena 2: gli altri due
    # notizie del weekend che non stanno nei dati del sito (penalità in griglia ecc.): video/note_weekend.json
    nf = QUI / "note_weekend.json"; note = (json.load(open(nf)).get(chiave) or {}) if nf.exists() else {}
    penal = note.get("penalizzati") or {}
    ordine, tip = studio_pole(chiave); conta_pole = dict(ordine)

    def motivi_rivale(f):
        """Perché guardarlo: [(frase a voce, riga a schermo)], i più forti per primi, dai dati del sito."""
        d = dati_motivi(f); out = []
        if d["circ"] and d["circ"][0] <= 3:
            pos, scorso, anno = d["circ"]
            quando = "l'anno scorso " if scorso else f"nel {anno} "
            out.append((f"{quando}qui ha vinto" if pos == 1 else f"{ORD[pos]} qui {quando.strip()}", f"Qui {anno}: {pos}°"))
        if d["vit"]: out.append((("una vittoria" if d["vit"] == 1 else f"{it(d['vit'])} vittorie") + " nelle ultime cinque", f"{d['vit']} {'vittoria' if d['vit'] == 1 else 'vittorie'} nelle ultime 5 gare"))
        c = conta_pole.get(f["nome"], 0)
        if c: out.append((("una pole" if c == 1 else f"{it(c)} pole") + " nelle ultime cinque qualifiche", f"{c} pole nelle ultime 5 qualifiche"))
        if d["podi"]: out.append((f"{it(d['podi'])} podi nelle ultime cinque", f"{d['podi']} podi nelle ultime 5 gare"))
        if d["camp"] and d["camp"] <= 4: out.append((("primo" if d["camp"] == 1 else ORD[d["camp"]]) + " nel mondiale", f"{d['camp']}° nel campionato"))
        return out[:2]

    rivali = [(i + 1, f) for i, f in enumerate(p["favoriti"][:6]) if i > 0 and f["nome"] not in penal][:2]
    a_ = lambda c: ("ad " if c[0] in "AEIOU" else "a ") + c
    voce2 = ""
    for f in p["favoriti"][1:3]:
        if f["nome"] in penal: voce2 += f"{cognome(f['nome'])} parte dal fondo: {penal[f['nome']]}. "
    voce2 += f"Occhio {a_(cognome(rivali[0][1]['nome']))}: {', '.join(v for v, _ in motivi_rivale(rivali[0][1]))}." + (f" E {a_(cognome(rivali[1][1]['nome']))}: {', '.join(v for v, _ in motivi_rivale(rivali[1][1]))}." if len(rivali) > 1 else "")
    def blocco(f, n):
        sch = " · ".join(sc for _, sc in motivi_rivale(f))
        return (f"<div style='padding:18px 0;border-bottom:2px solid #26262e'><div style='display:flex;align-items:center;gap:22px'><span style='font:700 72px Oswald;color:{colore};width:60px'>{n}</span>"
                f"<div><div style='font:700 56px Oswald;text-transform:uppercase'>{esc(f['nome'])}</div><div style='font:500 28px Inter;color:#b6b5bd'>{esc(f['team'])}</div></div></div>"
                f"<div style='font:500 34px Inter;color:#e8e8ee;margin-top:8px;padding-left:82px'>{esc(sch)}</div></div>")
    avvisi = "".join(f"<div style='font:500 34px Inter;color:#ff6a62;padding:16px 0;border-bottom:2px solid #26262e'><b>ATTENZIONE</b> · {esc(nm)} parte dal fondo ({esc(mot)})</div>" for nm, mot in penal.items() if nm in [x['nome'] for x in p['favoriti'][:5]])
    foto1 = foto_per_nome(rivali[0][1]["nome"], chiave)
    c2 = (f"<span class=pill style='top:790px;background:{colore}'>{sigla} · occhio a loro</span>"
          f"<div style='position:absolute;left:70px;right:70px;top:880px'>{''.join(blocco(f, n) for n, f in rivali)}{avvisi}</div>")
    scene = [(cornice(c1, colore, foto0), voce1), (cornice(c2, colore, foto1), voce2)]
    # --- scena 3: la pole, dallo studio di GP Oggi
    if tip:
        n = dict(ordine)[tip]
        voce3 = f"E la pole? Dal nostro studio sulle ultime cinque qualifiche: {cognome(tip)}, " + (f"{it(n)} pole su cinque." if n > 1 else "ha preso l'ultima pole.")
        righe3 = "".join(f"<div style='display:flex;justify-content:space-between;font:700 48px Oswald;text-transform:uppercase;padding:12px 0;border-bottom:2px solid #26262e'><span>{esc(nm)}</span><span style='color:{colore}'>{c} {'pole' if c == 1 else 'pole'}</span></div>" for nm, c in ordine[:4])
        c3 = (f"<span class=pill style='top:790px;background:{colore}'>La pole · studio GP Oggi</span>"
              f"<h1 style='position:absolute;left:70px;right:70px;top:850px;margin:0;font:700 90px/1 Oswald;text-transform:uppercase'>{esc(tip)}</h1>"
              f"<div style='position:absolute;left:70px;right:70px;top:970px;font:500 30px Inter;color:#9a9aa6'>Pole nelle ultime 5 qualifiche</div>"
              f"<div style='position:absolute;left:70px;right:70px;top:1040px'>{righe3}</div>")
        scene.append((cornice(c3, colore, foto_per_nome(tip, chiave)), voce3))
    # --- scena 4: tu che dici? vai a votare
    quando_v, quando_s = chiusura_voti(p, chiave)
    voce4 = "E tu che dici? Scrivilo nei commenti e vai a votare il tuo pronostico su G P Oggi punto it, prima delle qualifiche."
    c4 = (f"<div style='position:absolute;left:70px;right:70px;top:480px;text-align:center;font:700 150px/1 Oswald;text-transform:uppercase'>Tu che<br><span style='color:{colore}'>dici?</span></div>"
          f"<div style='position:absolute;left:70px;right:70px;top:900px;text-align:center;font:500 46px Inter;color:#e8e8ee'>Scrivilo nei commenti 👇</div>"
          f"<div style='position:absolute;left:90px;right:90px;top:1060px;text-align:center;background:{colore};border-radius:28px;padding:34px 20px;font:700 62px/1.1 Oswald;text-transform:uppercase'>Vota il tuo pronostico<br>su gpoggi.it</div>"
          + (f"<div style='position:absolute;left:70px;right:70px;top:1330px;text-align:center;font:500 38px Inter;color:#ffd21f'>Si vota fino alle qualifiche<br><b>{esc(quando_s)}</b></div>" if quando_s else ""))
    scene.append((cornice(c4, colore, None), voce4))
    return scene


def social_serie(chiave):
    pron = json.load(open(DATA / "pronostici.json")); p = pron.get(chiave)
    if not p or not p.get("favoriti"): return ""
    luogo = re.sub(r"^(Gran Premio (di|del|dello|della|d')\s*|GP )", "", p["gp"]).strip(); f0 = p["favoriti"][0]["nome"]
    _, tip = studio_pole(chiave); icona, tag = ("🏁", "#f1 #formula1") if chiave == "f1" else ("🏍️", "#motogp")
    pole = f"🎯 Pole? Dal nostro studio sulle ultime 5 qualifiche occhio a {tip}\n" if tip else ""
    return (f"{icona} {luogo}: chi sale sul PODIO? {icona}\n\n"
            f"👑 Il nostro favorito: {f0}\n{pole}\n"
            f"🗳️ E tu che dici?\n"
            f"✍️ Scrivilo nei commenti 👇\n"
            f"📲 Vota il tuo pronostico su gpoggi.it PRIMA delle qualifiche!\n\n"
            f"🔗 gpoggi.it → Giochi\n"
            f"👥 Segui @gp.oggi\n\n"
            f"ℹ️ Opinione basata sui numeri, non una certezza.\n\n"
            f"#gpoggi {tag} #previsioni #podio #pole")


async def componi(scene, uscita, velocita=None, rapido=False):
    """scene = [(html, testo)] -> mp4 verticale con la voce."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); clip = []
        async with async_playwright() as p:
            b = await p.chromium.launch(**({"executable_path": CHROMIUM} if CHROMIUM else {}), args=["--no-sandbox"])
            pg = await b.new_page(viewport={"width": W, "height": H})
            for i, (h, t) in enumerate(scene):
                await edge_tts.Communicate(t, VOCE, rate=velocita or VELOCITA).save(str(tmp / f"v{i}.mp3"))
                await pg.set_content(h); await pg.wait_for_timeout(500); await pg.screenshot(path=str(tmp / f"s{i}.png"))
            await b.close()
        for i in range(len(scene)):
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(tmp / f"v{i}.mp3")], capture_output=True, text=True).stdout)
            c = tmp / f"c{i}.mp4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", str(tmp / f"s{i}.png"), "-i", str(tmp / f"v{i}.mp3"),
                            "-af", f"adelay={150 if rapido else 400}:all=1,apad=pad_dur={0.25 if rapido else 0.9},loudnorm=I=-14:TP=-1.5:LRA=9", "-t", f"{dur + (0.55 if rapido else 1.3):.2f}", "-c:v", "libx264", "-tune", "stillimage", "-crf", "21",
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
    return "Il pronostico di GP Oggi 🔮\n\n" + "\n\n".join(righe) + "\n\nÈ un'opinione basata sui numeri, non una certezza.\n\nTu che dici? 👇\n\n🔗 gpoggi.it\n\n#gpoggi #f1 #motogp #pronostici #previsioni"


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
        # un video per serie: F1 e MotoGP separati, ciascuno con favorito, rivali, pole e invito al voto
        fatti = 0
        for chiave in ("f1", "motogp"):
            scene = scene_previsione(chiave)
            if not scene: continue
            uscita = a.uscita.with_name(f"{a.uscita.stem}-{chiave}{a.uscita.suffix}")
            social = social_serie(chiave)
            did = social.split("\n\n")[0] + "\n\nVota il tuo pronostico: https://gpoggi.it/giochi.html?gioco=pronostico" + ("&serie=moto" if chiave == "motogp" else "") + "\n\n#gpoggi " + ("#MotoGP" if chiave == "motogp" else "#F1")
            asyncio.run(componi(scene, uscita, VELOCITA_NOTIZIE, rapido=True)); print("Video:", uscita)
            if a.invia and invia(uscita, did): invia_testo(social); fatti += 1
        if a.invia and fatti:
            stato["previsioni"] = datetime.now(ROMA).strftime("%Y-%m-%d"); STATO.write_text(json.dumps(stato, ensure_ascii=False, indent=1)); print("Inviato.")
        if not fatti and not a.invia: print("Video pronti.")
        return
    asyncio.run(componi(scene, a.uscita, VELOCITA_NOTIZIE if a.cosa == "notizia" else None)); print("Video:", a.uscita)
    if a.invia and invia(a.uscita, did):
        invia_testo(social)
        stato.setdefault("notizie", []).insert(0, n["url"]); stato["notizie"] = stato["notizie"][:400]; stato["ultima_serie"] = n["serie"]
        STATO.write_text(json.dumps(stato, ensure_ascii=False, indent=1)); print("Inviato.")

if __name__ == "__main__":
    main()
