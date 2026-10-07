"""Due video di notizie al giorno nello stile "ultim'ora" (alle 12:00 con GitHub Actions), raccontati e non letti.

1. sceglie le due notizie migliori della rassegna (una F1 e una MotoGP quando possibile): piloti, polemiche, annunci; niente tecnica pura né pubblicità di auto
2. legge l'articolo e chiede a Claude (API di Anthropic, chiave ANTHROPIC_API_KEY) di scrivere il racconto: solo fatti dell'articolo, parole proprie
3. controlla il testo (nessuna frase copiata, foto solo di piloti che abbiamo, lunghezza) e produce il video con notizia_sub.py
4. manda il video sul Telegram (TELEGRAM_BOT_TOKEN, TELEGRAM_CANALE) con la didascalia per TikTok e Instagram

Senza chiave, o se qualcosa non torna, ripiega sul video semplice (titolo e fonte) di auto_video.py: i video escono comunque.
Uso:  python3 notizie_giorno.py [--prova] [--n 2] [--risposta-modello FILE.json]
  --prova                  non invia nulla, lascia i video in /tmp
  --risposta-modello FILE  usa questo JSON al posto della chiamata al modello (per provare tutto il resto)
"""
import argparse, asyncio, html, json, os, re, subprocess, sys, unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import notizia_sub as NS  # noqa: E402

ROOT = Path(__file__).parent.parent
DATA = ROOT / "docs" / "data"
STATO = ROOT / "video_stato.json"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
MODELLO = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
CA = "/root/.ccr/ca-bundle.crt" if Path("/root/.ccr/ca-bundle.crt").exists() else True
norm = lambda s: re.sub(r"[^a-z0-9 ]", " ", unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower())

POSITIVE = ["ufficial", "annunci", "penalizz", "lite", "polemic", "contratt", "mercato", "rinnov", "lascia", "sostitu", "squalific", "multa", "incident", "infortun", "ritir", "ripesca",
            "tirata", "accus", "vittoria", "vince", "pole", "titolo", "campion", "format", "regol", "dopo la gara", "addio", "ritorno", "debutt", "sprint", "qualific"]
TECNICHE = ["aduo", "software", "gomme", "pneumatic", "carcassa", "freni", "turbo", "aerodinam", "assetto", "power unit", "set-up", "soft", "ala ", "telaio", "energia", "mgu", "motore"]
NO_RACING = ["suv", "supersportiva", "alfa romeo", "dacia", "porsche", "mini ", "xpeng", "orari", "programma e orari", "estoril", "gilet", "livrea", "storico", "documentario", "auto d", "vetrina", "gamma"]


def stato_leggi():
    return json.loads(STATO.read_text()) if STATO.exists() else {}


def testo_articolo(url):
    """Testo dell'articolo (JSON-LD o paragrafi). Vuoto se la pagina non si apre o non c'è abbastanza testo."""
    try:
        r = requests.get(url, headers=UA, timeout=30, verify=CA)
        r.raise_for_status()
    except requests.RequestException:
        return ""
    h = r.text
    m = re.search(r'"articleBody"\s*:\s*"((?:[^"\\]|\\.)*)"', h)
    if m:
        try:
            t = json.loads('"' + m.group(1) + '"')
            if len(t) > 400:
                return html.unescape(re.sub(r"<[^>]+>", " ", t)).strip()[:7000]
        except ValueError:
            pass
    ps = [html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in re.findall(r"<p[^>]*>(.*?)</p>", h, flags=re.S)]
    ps = [p for p in ps if len(p) > 70 and not re.search(r"notifiche|pubblicit|ad-blocker|newsletter|cookie|Iscriviti|More from|Ricevi", p, re.I)]
    return "\n".join(ps)[:7000]


def simili(a, arts):
    """Articoli che parlano della stessa storia (molte parole del titolo in comune): non si raccontano due volte."""
    parole_ = lambda t: {w for w in norm(t).split() if len(w) > 3}
    pa = parole_(a["titolo"])
    return [b["url"] for b in arts if b["url"] != a["url"] and pa and len(pa & parole_(b["titolo"])) >= max(3, int(0.5 * min(len(pa), len(parole_(b["titolo"])))))]


def punteggio(a, nomi):
    t = norm(a["titolo"]) + " "
    p = sum(2 for k in POSITIVE if k in t) - sum(2 for k in TECNICHE if k in t)
    if any(k in t for k in NO_RACING):
        p -= 20
    if any(norm(n).split()[-1] in t for n in nomi if len(norm(n).split()[-1]) > 3):
        p += 3   # cita un pilota: ha una faccia da mostrare
    try:
        ore = (datetime.now(timezone.utc) - datetime.fromisoformat(a["pubblicato"])).total_seconds() / 3600
    except Exception:
        ore = 99
    if weekend_gara() and any(k in t for k in SESSIONI):
        p += 8   # weekend di gara: prove, qualifica e sprint passano avanti
    return p + (3 if ore < 12 else 1 if ore < 30 else -5)


SESSIONI = ["prove libere", "libere", "qualific", "pole", "sprint", "fp1", "fp2", "fp3", "griglia", "singapore"]


def weekend_gara():
    d = datetime.now(timezone.utc)
    return (d.month, d.day) in ((10, 9), (10, 10), (10, 11)) and d.year == 2026


ROTAZIONE = {"MotoGP": ["Fabio Quartararo", "Alex Marquez", "Pedro Acosta", "Fabio Di Giannantonio", "Francesco Bagnaia", "Marco Bezzecchi", "Franco Morbidelli", "Marc Marquez"]}   # volti che stanno bene in verticale


def nomi_con_foto():
    nomi = {p["nome"]: "F1" for p in json.load(open(DATA / "roster.json")) if p.get("foto") and p.get("nome")}
    for k in json.load(open(DATA / "foto-motogp.json")):
        if k.startswith("nome:"):
            nomi[k[5:]] = "MotoGP"
    for p in json.load(open(DATA / "foto-storici.json")):
        nomi.setdefault(p["nome"], p["serie"])
    return nomi


def scegli(n, nomi, fatte):
    arts = [a for a in json.load(open(DATA / "rassegna.json"))["articoli"] if a["url"] not in fatte]
    arts.sort(key=lambda a: -punteggio(a, nomi))
    scelte = []
    for serie in ("MotoGP", "F1"):   # una per serie, se c'è
        a = next((x for x in arts if x["serie"] == serie and punteggio(x, nomi) > 0), None)
        if a:
            scelte.append(a)
    for a in arts:
        if len(scelte) >= n:
            break
        if a not in scelte and punteggio(a, nomi) > 0:
            scelte.append(a)
    scelte.sort(key=lambda a: -punteggio(a, nomi))
    return scelte[:n]


SISTEMA = """Sei la redazione di GP Oggi, sito italiano non ufficiale su Formula 1 e MotoGP. Scrivi il testo di un video verticale di circa 30 secondi che RACCONTA una notizia.
Regole:
1. Usa SOLO fatti presenti nell'articolo. Nessun dato inventato, nessuna tua opinione, nessuna causa che l'articolo non indica.
2. Parole tue: non copiare frasi dall'articolo (mai più di 5 parole di fila uguali). Italiano semplice, frasi di 8-16 parole, tono diretto da notizia.
3. Niente sigle o termini tecnici non spiegati: racconta l'effetto concreto per piloti e tifosi.
4. Struttura: "hook_voce" (una frase, massimo 9 parole, che dà la notizia), "hook_titolo" (titolo grande, massimo 7 parole), poi da 5 a 7 "scene" ciascuna con "testo" (una frase), "foto" (il nome di un pilota citato nell'articolo, scelto SOLO dall'elenco; se nessuno è citato usa uno dei predefiniti) e, quando compare un pilota nuovo o cambia, "nome" (il suo nome).
5. Nel "testo" metti tra *asterischi* da 1 a 3 parole chiave (saranno gialle). Nessun altro segno speciale.
6. "domanda": una domanda neutra per i commenti, massimo 10 parole.
7. "titolo_breve": massimo 5 parole.
8. "social": didascalia per TikTok e Instagram: prima riga con la notizia e un'emoji, frasi corte una per riga con una riga vuota tra i blocchi, la domanda, "Fonte: <fonte>", "🔗 gpoggi.it", al massimo 5 hashtag con #gpoggi per primo.
Rispondi SOLO con un oggetto JSON valido con le chiavi: hook_voce, hook_titolo, titolo_breve, scene, domanda, social."""


def chiedi_modello(a, testo, nomi, predefiniti):
    chiave = os.environ.get("ANTHROPIC_API_KEY")
    if not chiave:
        raise RuntimeError("ANTHROPIC_API_KEY mancante")
    utente = (f"Serie: {a['serie']}\nFonte: {a['fonte']}\nTitolo: {a['titolo']}\n\nTesto dell'articolo:\n{testo}\n\n"
              f"Piloti di cui abbiamo la foto (scegli solo da qui): {', '.join(sorted(nomi))}\nPredefiniti se nessun pilota è citato: {', '.join(predefiniti)}")
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=120, verify=CA,
                      headers={"x-api-key": chiave, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                      json={"model": MODELLO, "max_tokens": 2000, "system": SISTEMA, "messages": [{"role": "user", "content": utente}]})
    r.raise_for_status()
    t = "".join(b.get("text", "") for b in r.json()["content"])
    m = re.search(r"\{.*\}", t, re.S)
    return json.loads(m.group(0))


def parole(s):
    return norm(re.sub(r"[*\[\]]", "", s)).split()


def valida(j, a, testo, nomi, predefiniti):
    """Trasforma la risposta del modello nel file di istruzioni del video; alza ValueError se qualcosa non va."""
    canon = {norm(n): n for n in nomi}
    def foto(n):
        if not n:
            return None
        k = norm(str(n)).strip()
        if k in canon:
            return canon[k]
        cogn = k.split()[-1] if k.split() else ""
        return next((v for kk, v in canon.items() if kk.split()[-1] == cogn), None)
    scene = j.get("scene") or []
    if not 4 <= len(scene) <= 8:
        raise ValueError("numero di scene non valido")
    ref = parole(testo + " " + a["titolo"])
    ngram = {" ".join(ref[i:i + 6]) for i in range(len(ref) - 5)}
    tot = 0
    out = []
    for s in scene:
        t = re.sub(r"[\[\]]", "", str(s.get("testo", ""))).strip()
        if t.count("*") % 2:
            t = t.replace("*", "")
        if not 18 <= len(t) <= 150:
            raise ValueError("scena troppo corta o lunga")
        w = parole(t)
        tot += len(w)
        if any(" ".join(w[i:i + 6]) in ngram for i in range(len(w) - 5)):
            raise ValueError("frase troppo simile all'articolo")
        f = foto(s.get("foto")) or foto(predefiniti[0])
        out.append({"foto": f, "testo": t, **({"nome": str(s["nome"]).strip()} if s.get("nome") else {})})
    if tot > 175:
        raise ValueError("testo troppo lungo")
    # Le foto: resta quella scelta dal modello solo se il pilota è citato nell'articolo; altrimenti si ruota tra più piloti (mai sempre lo stesso)
    # e lo stesso volto non compare per più di due scene di fila.
    parole_art = set(norm(testo + " " + a["titolo"]).split())
    citati = {n for n in nomi if len(norm(n).split()[-1]) > 3 and norm(n).split()[-1] in parole_art}
    if a["serie"] == "F1":
        rot = [p["nome"] for p in json.load(open(DATA / "roster.json")) if p.get("foto") and p.get("nome") in nomi]
    else:
        rot = [n for n in ROTAZIONE.get(a["serie"], []) if n in nomi]
    rot = rot or list(predefiniti)
    giro = datetime.now(timezone.utc).toordinal()
    usate = []
    for sc in out:
        f = sc["foto"]
        if f not in citati or (len(usate) >= 2 and usate[-1] == f and usate[-2] == f):
            for _ in range(len(rot)):
                c = rot[giro % len(rot)]
                giro += 1
                if c != (usate[-1] if usate else None):
                    f = c
                    break
        sc["foto"] = f
        usate.append(f)
    hv = re.sub(r"[*\[\]]", "", str(j.get("hook_voce", ""))).strip()
    ht = re.sub(r"[*\[\]]", "", str(j.get("hook_titolo", ""))).strip()
    dom = re.sub(r"[*\[\]]", "", str(j.get("domanda", ""))).strip()
    if not (hv and ht and dom) or len(ht.split()) > 9 or len(dom.split()) > 14:
        raise ValueError("gancio o domanda non validi")
    for x in (hv, ht, dom):
        w = parole(x)
        if any(" ".join(w[i:i + 6]) in ngram for i in range(len(w) - 5)):
            raise ValueError("gancio troppo simile all'articolo")
    social = str(j.get("social", "")).strip()
    if "gpoggi.it" not in social or len(re.findall(r"#\w+", social)) > 5:
        social = f"{ht} 📰\n\n{dom} 👇\n\nFonte: {a['fonte']}\n🔗 gpoggi.it\n\n#gpoggi #{'motogp' if a['serie'] == 'MotoGP' else 'f1'} #notizie"
    return {"serie": a["serie"], "titolo_breve": str(j.get("titolo_breve") or ht)[:40], "fonte": a["fonte"].strip(), "velocita": "+25%",
            "scene": [{"foto": out[0]["foto"], "hook": True, "hook_titolo": ht, "testo": hv}] + out,
            "finale": {"foto": out[-1]["foto"], "domanda": dom}}, social


def telegram(video, didascalia, social):
    tok = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_CANALE") or os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        print("Token Telegram mancante: video non inviato.")
        return False
    with open(video, "rb") as f:
        requests.post(f"https://api.telegram.org/bot{tok}/sendVideo", data={"chat_id": chat, "caption": didascalia[:1000], "supports_streaming": "true", "disable_notification": "true", "width": 1080, "height": 1920},
                      files={"video": f}, timeout=300, verify=CA).raise_for_status()
    requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": chat, "parse_mode": "HTML", "disable_notification": "true",
                  "text": "📋 <b>Didascalia per TikTok e Instagram</b> (tocca per copiare)\n\n<pre>" + html.escape(social) + "</pre>"}, timeout=60, verify=CA).raise_for_status()
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", action="store_true")
    ap.add_argument("--n", type=int, default=2)
    ap.add_argument("--risposta-modello")
    ap.add_argument("--una-volta-al-giorno", action="store_true", help="esce subito se oggi (ora italiana) i video sono già stati fatti")
    a = ap.parse_args()
    nomi = nomi_con_foto()
    stato = stato_leggi()
    oggi = datetime.now(timezone(timedelta(hours=2 if 3 < datetime.now(timezone.utc).month < 11 else 1))).strftime("%Y-%m-%d")
    if a.una_volta_al_giorno and stato.get("giorno_notizie") == oggi:
        print("Video di oggi già fatti.")
        return
    fatte = set(stato.get("storie", [])) | set(stato.get("notizie", []))
    predef = {"F1": ["Kimi Antonelli"], "MotoGP": ["Marc Marquez"]}
    prima = json.load(open(DATA / "roster.json"))
    if prima and prima[0].get("nome") in nomi:
        predef["F1"] = [prima[0]["nome"]]
    scelte = scegli(a.n, nomi, fatte)
    print("Scelte:", [x["titolo"][:70] for x in scelte])
    fatti = 0
    for k, art in enumerate(scelte):
        uscita = Path(f"/tmp/notizia_{k}.mp4")
        try:
            testo = testo_articolo(art["url"])
            if len(testo) < 500:
                raise RuntimeError("articolo illeggibile o troppo corto")
            j = json.load(open(a.risposta_modello)) if a.risposta_modello else chiedi_modello(art, testo, nomi, predef[art["serie"]])
            spec, social = valida(j, art, testo, nomi, predef[art["serie"]])
            asyncio.run(NS.genera(spec, uscita))
            did = f"📰 {spec['titolo_breve']} · Fonte: {art['fonte'].strip()}\n{art['url'].split('?')[0]}"
            if not a.prova:
                telegram(uscita, did, social)
            stato.setdefault("storie", []).insert(0, art["url"])
            stato["storie"] = simili(art, json.load(open(DATA / "rassegna.json"))["articoli"]) + stato["storie"]
            fatti += 1
        except Exception as e:   # ripiego: video semplice (titolo e fonte), così il video esce comunque
            print(f"  racconto non riuscito ({type(e).__name__}: {e}); uso il video semplice")
            if not a.prova:
                subprocess.run([sys.executable, str(Path(__file__).parent / "auto_video.py"), "notizia", "--invia", "--uscita", str(uscita)], check=False)
    stato["storie"] = stato.get("storie", [])[:400]
    if not a.prova:
        STATO.write_text(json.dumps({**stato_leggi(), "storie": stato["storie"], "giorno_notizie": oggi}, ensure_ascii=False, indent=1))
    print(f"Fatto: {fatti} racconti su {len(scelte)}.")


if __name__ == "__main__":
    main()
