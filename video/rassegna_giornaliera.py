"""Rassegna stampa della sera (21:30 italiane): un video con i titoli del giorno, ciascuno attribuito alla sua fonte, inviato sul Telegram.

Nessun modello di linguaggio: i testi sono i titoli delle testate (citati con il nome della fonte) e frasi fisse nostre.
Le foto sono i piloti citati nel titolo (foto libere con credito). Una volta al giorno (marker in video_stato.json).
Uso:  python3 rassegna_giornaliera.py [--prova] [--forza] [--n 5]
"""
import argparse, asyncio, json, re, sys
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notizie_giorno as NG  # noqa: E402
import notizia_sub as NS  # noqa: E402

DATA, STATO = NG.DATA, NG.STATO
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
FERRARI = ["ferrari", "leclerc", "hamilton"]
SIGLE = re.compile(r"\b(?:[A-Z]{2,5}\d*|[A-Z]\d+)\b")   # PU, VSC, FP1…: la voce le leggerebbe male
CHIUSURE = ["Quale di queste notizie ti ha colpito di più?", "Quale titolo ti sembra il più importante di oggi?", "Di cosa parlerete domani al bar?"]


def ora_roma(adesso=None):
    adesso = adesso or datetime.now(timezone.utc)
    return adesso.astimezone(timezone(timedelta(hours=2 if _estate(adesso) else 1)))


def _estate(d):
    """Ora legale europea: dall'ultima domenica di marzo all'ultima di ottobre (01:00 UTC)."""
    def ultima_dom(mese):
        g = datetime(d.year, mese, 31, 1, tzinfo=timezone.utc)
        return g - timedelta(days=(g.weekday() + 1) % 7)
    return ultima_dom(3) <= d < ultima_dom(10)


def pulisci(t):
    t = re.sub(r"^(F1|MotoGP|Formula 1)\s*\|\s*", "", t.strip())
    t = t.replace("“", "«").replace("”", "»").replace('"', "").replace("‘", "").replace("’", "'")
    return re.sub(r"\s+", " ", t).strip()


def frase_estratto(a, titolo):
    """Seconda frase della notizia, dall'estratto che la testata stessa pubblica nel suo feed: così si capisce di cosa parla. None se è troncato male,
    troppo simile al titolo o difficile da leggere ad alta voce."""
    t = pulisci(a.get("estratto", "")).replace("Hamiltn", "Hamilton")
    if not t:
        return None
    troncato = t.endswith("…") or t.endswith("...")
    t = t.rstrip("….").strip()
    equilibrate = lambda x: x.count("«") == x.count("»")
    if troncato or len(t) > 200:
        limite = len(t) if troncato else 200
        tagli = sorted((i for sep in (". ", "? ", "! ", ", ") for i in [m.start() for m in re.finditer(re.escape(sep), t[:limite])]), reverse=True)
        if troncato and not tagli:
            return None
        for i in tagli:   # l'ultimo punto o la virgola più avanti possibile, purché le virgolette siano chiuse e la frase non sia cortissima
            cand = t[:i + 1] if t[i] != "," else t[:i]
            ultima = re.sub(r"[^\wàèéìòù]", "", cand.split()[-1].lower()) if cand.split() else ""
            if ultima in ("perché", "che", "e", "ma", "di", "da", "se", "dove", "come", "con", "per", "il", "la", "lo", "un", "una", "a", "in", "o", "quando", "mentre", "anche", "non", "più", "del", "della", "dei", "delle", "nel", "nella", "al", "alla"):
                continue   # frase lasciata a metà
            if i >= 40 and equilibrate(cand):
                t = cand
                break
        else:
            return None
    t = t.strip()
    ok = ("VSC", "FIA", "DRS")
    sigle = [x for x in SIGLE.findall(re.sub(r"\bF1\b", "", t)) if x not in ok]
    if len(t) < 40 or sigle or "|" in t or t.endswith("?"):
        return None
    pt, pe = set(NG.norm(titolo).split()), set(NG.norm(t).split())
    if pt and len(pt & pe) / len(pt) > 0.7:
        return None
    if t[-1] not in ".?!»":
        t += "."
    return t


def scegli_rassegna(n, nomi, stato=None):
    """Le notizie di OGGI (dalla mezzanotte italiana) mai usate in una rassegna precedente né raccontate in un video; se sono troppo poche si allarga a 30 ore,
    ma le notizie già usate restano escluse (e anche quelle che parlano della stessa storia)."""
    stato = stato or {}
    arts_tutti = json.load(open(DATA / "rassegna.json"))["articoli"]
    ora = datetime.now(timezone.utc)
    mezzanotte = ora_roma(ora).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    gia = set(stato.get("rassegna_usate", [])) | set(stato.get("storie", [])) | set(stato.get("notizie", []))
    usate = [x for x in arts_tutti if x["url"] in gia]   # per scartare anche le versioni della stessa storia di altre testate

    def candidati(da):
        out = []
        for a in arts_tutti:
            try:
                if datetime.fromisoformat(a["pubblicato"]) < da:
                    continue
            except Exception:
                continue
            if a["url"] in gia or any(a["url"] in NG.simili(u, [a]) or u["url"] in NG.simili(a, [u]) for u in usate):
                continue
            out.append(a)
        return out
    arts = candidati(mezzanotte)
    if len(arts) < n + 2:
        arts = candidati(ora - timedelta(hours=30))
    buone = []
    for a in arts:
        t = pulisci(a["titolo"])
        if "|" in t or SIGLE.search(re.sub(r"\bF1\b", "", t)) or not 25 <= len(t) <= 125 or t.endswith("?"):
            continue   # i titoli-domanda (\"perché non è stato penalizzato?\") senza risposta nel video non hanno senso: si saltano
        p = NG.punteggio(a, nomi) + (4 if any(k in NG.norm(t) for k in FERRARI) else 0) + (3 if a.get("citazione") else 0)   # le dichiarazioni dei piloti hanno la precedenza
        if p > 0:
            buone.append((p, a))
    buone.sort(key=lambda x: -x[0])
    per_serie = {"F1": [], "MotoGP": []}
    for _, x in buone:
        lista = per_serie.setdefault(x["serie"], [])
        if not any(x["url"] in NG.simili(y, [x]) or y["url"] in NG.simili(x, [y]) for y in lista):
            lista.append(x)
    # una F1, una MotoGP, di nuovo F1, di nuovo MotoGP (incrociate); se una serie finisce si continua con l'altra
    scelte, turno = [], ["F1", "MotoGP"]
    k = 0
    while len(scelte) < n and (per_serie["F1"] or per_serie["MotoGP"]):
        serie = turno[k % 2]
        k += 1
        if per_serie.get(serie):
            scelte.append(per_serie[serie].pop(0))
    return scelte


def articoli_da_url(urls):
    """Gli articoli della rassegna con questi indirizzi (nell'ordine dato; la query dopo «?» non conta)."""
    arts = json.load(open(DATA / "rassegna.json"))["articoli"]
    chiave = lambda u: u.split("?")[0].rstrip("/")
    out = []
    for u in urls:
        a = next((x for x in arts if chiave(x["url"]) == chiave(u)), None)
        if a and a not in out:
            out.append(a)
    return out


def leggi_forzata(giorno):
    """video/rassegna_forzata.json: per un giorno preciso, un articolo che deve aprire la rassegna (gancio) con un titolo scelto da noi."""
    try:
        f = json.load(open(Path(__file__).parent / "rassegna_forzata.json"))
        return f if f.get("giorno") == giorno else None
    except (OSError, ValueError):
        return None


def foto_espn_f1():
    """[(titolo in minuscolo senza accenti, indirizzo foto)] dalle notizie di ESPN sulla F1 (foto orizzontali 1296x729). Vuoto se ESPN non risponde."""
    try:
        r = requests.get("https://site.api.espn.com/apis/site/v2/sports/racing/f1/news?limit=50", headers=NG.UA, timeout=30, verify=NG.CA)
        r.raise_for_status()
    except requests.RequestException as e:
        print("  foto ESPN non disponibili:", e)
        return []
    out, viste = [], set()
    for a in r.json().get("articles", []):
        t = NG.norm(a.get("headline", ""))
        if any(k in t for k in ("kardashian", "nba", "nfl", "owners")):
            continue
        for i in a.get("images", []):
            u = i.get("url", "")
            if i.get("width") == 1296 and "/photo/" in u and u not in viste:
                viste.add(u); out.append((t, u)); break
    return out


def costruisci(scelte, nomi, oggi, gancio=False, gancio_titolo=None):
    cognome = lambda n: NG.norm(n).split()[-1]
    rot_f1 = [p["nome"] for p in json.load(open(DATA / "roster.json")) if p.get("foto") and p.get("nome") in nomi]
    rot = {"F1": rot_f1, "MotoGP": [n for n in NG.ROTAZIONE["MotoGP"] if n in nomi]}
    pool = foto_espn_f1()
    usate_url = set()

    def espn(cogn=None):
        """Foto ESPN non ancora usata: prima una il cui titolo parla del pilota, poi la prima libera."""
        for t, u in pool:
            if u not in usate_url and cogn and cogn in t.split():
                usate_url.add(u); return u
        for t, u in pool:
            if u not in usate_url and not any(c in t for c in ("hamilton",)):
                usate_url.add(u); return u
        return None

    scene, usate = [], []
    for k, a in enumerate(scelte):
        t = pulisci(a["titolo"])
        parole = set(NG.norm(t).split())
        n_c = NG.pilota_citato(t, nomi, a["serie"])   # «Marquez» da solo è ambiguo (Marc / Alex): vale solo il nome completo
        citati = [n_c] if n_c else []
        f = citati[0] if citati else next((n for n in rot[a["serie"]][k:] + rot[a["serie"]] if n not in usate[-1:]), rot[a["serie"]][0])
        fonte = a["fonte"].strip()
        sc = {"foto": f, "nome": fonte, "testo": t, "pausa": 0.5 if k else 0.3}
        if a["serie"] == "F1":
            rit = None
            if citati:   # il pilota citato: ritratto ESPN (la persona giusta) sul colore della sua squadra
                try:
                    import ritratti_espn as RE
                    col = next((p["colore"] for p in json.load(open(DATA / "roster.json")) if p["nome"] == f), "e8352f")
                    rit = RE.ritratto(f, tuple(int(col[i:i + 2], 16) for i in (0, 2, 4)))
                except Exception as e:
                    print(f"  ritratto ESPN di {f} non disponibile ({type(e).__name__}): uso la foto libera")
            if rit:
                sc = {"foto": f, "foto_file": str(rit), "credito": "Foto: ESPN", "nome": fonte, "testo": sc["testo"], "pausa": sc["pausa"]}
            elif not citati:   # nessun pilota nel titolo: macchine, box e circuiti dalle foto ESPN delle notizie
                u = espn()
                if u:
                    sc = {"foto_url": u, "nome": fonte, "testo": sc["testo"], "pausa": sc["pausa"]}
        elif f in (json.load(open(DATA / "foto-extra.json")) or {}) and "pista" in json.load(open(DATA / "foto-extra.json"))[f]:
            sc["alt"] = "pista"   # moto in pista invece del ritratto
        scene.append(sc)
        ex = frase_estratto(a, t)
        if ex:
            scene.append({**{k2: v for k2, v in sc.items() if k2 not in ("testo", "pausa")}, "testo": ex})   # stessa foto, un po' di più sull'argomento
        if k == 0:
            n_prima = len(scene)   # le scene della prima notizia (titolo, e la frase in più se c'è): servono se è il gancio
        usate.append(f)
    data = f"{oggi.day} {MESI[oggi.month - 1]}"
    hook = f"Rassegna stampa di GP Oggi: {len(scelte)} notizie da non perdere."
    hook_img = espn()
    if gancio:
        # la prima notizia è il gancio: la sua scena diventa l'apertura (titolo grande) e subito dopo si dice che è la rassegna di oggi
        s0 = scene.pop(0)
        scene_hook = {**{k2: v for k2, v in s0.items() if k2 not in ("pausa", "nome")}, "hook": True,
                      "hook_titolo": gancio_titolo or NG.titolo_copertina(pulisci(scelte[0]["titolo"])), "testo": s0["testo"]}
        trans = {"foto_url": hook_img, "testo": f"Questa e altre {len(scelte) - 1} notizie nella rassegna stampa di GP Oggi.", "pausa": 0.4} if hook_img else \
                {**{k2: v for k2, v in s0.items() if k2 not in ("pausa", "nome", "testo")}, "testo": f"Questa e altre {len(scelte) - 1} notizie nella rassegna stampa di GP Oggi.", "pausa": 0.4}
        scene.insert(n_prima - 1, trans)
    elif hook_img:
        scene_hook = {"foto_url": hook_img, "hook": True, "hook_titolo": f"Rassegna stampa del {data}", "testo": hook}
    else:
        scene_hook = {"foto": scene[0]["foto"], "hook": True, "hook_titolo": f"Rassegna stampa del {data}", "testo": hook}
    fin_img = espn()
    finale = {"foto_url": fin_img, "domanda": CHIUSURE[oggi.toordinal() % len(CHIUSURE)]} if fin_img else {"foto": scene[-1].get("foto", "ESPN") if scene[-1].get("foto") else usate[-1], "domanda": CHIUSURE[oggi.toordinal() % len(CHIUSURE)]}
    spec = {"serie": "F1", "titolo_breve": f"Rassegna stampa {data}", "fonte": "testate citate nel video", "velocita": "+38%", "etichetta": "Rassegna",
            "scene": [scene_hook] + scene,
            "finale": finale}
    righe = [f"📰 Rassegna stampa del {data}", ""] + [f"• {pulisci(a['titolo'])} — {a['fonte'].strip()}" for a in scelte]
    tag = "#gpoggi #f1 #motogp #rassegnastampa #notizie"
    social = "\n".join(righe) + f"\n\n{spec['finale']['domanda']} 👇\n\nTitoli e link originali nelle fonti.\n🔗 gpoggi.it\n\n{tag}"
    return spec, social


def crea_copertina(spec, data, uscita):
    """Copertina F1 1080x1920: ritratto o foto ESPN a tutto schermo e «RASSEGNA STAMPA» con la data, come le altre copertine di GP Oggi."""
    import copertina as C
    ritratti = [sc for sc in spec["scene"] if sc.get("foto_file") and sc.get("foto") not in (None, "ESPN") and not sc.get("hook")]
    sfondo = next((sc["foto_file"] for sc in ritratti if sc.get("foto") != "Lewis Hamilton"), ritratti[0]["foto_file"] if ritratti else None)
    if not sfondo:
        url = next((sc["foto_url"] for sc in spec["scene"] if sc.get("foto_url")), None)
        sfondo = NS.foto_da_url(url)[0] if url else None
    if not sfondo:
        return None
    html = C.html_copertina("x", ["RASSEGNA", "STAMPA", data.upper()], "F1", None, "center 12%", sfondo, 1040, "Foto: ESPN")
    asyncio.run(C.scatta(html, str(uscita)))
    return uscita


def crea_copertina_moto(scelte, nomi, data, uscita):
    """Copertina MotoGP (blu) con un pilota di MotoGP: quello citato nelle notizie MotoGP di oggi, altrimenti uno a rotazione. Foto libera del sito."""
    import copertina as C
    citati = []
    for a in scelte:
        if a["serie"] == "MotoGP":
            n = NG.pilota_citato(pulisci(a["titolo"]), nomi, "MotoGP")
            if n and n not in citati:
                citati.append(n)
    rot = [n for n in NG.ROTAZIONE["MotoGP"] if n in nomi]
    pilota = citati[0] if citati else rot[datetime.now().toordinal() % len(rot)]
    html = C.html_copertina(pilota, ["RASSEGNA", "STAMPA", data.upper()], "MotoGP", None, "center 12%")
    asyncio.run(C.scatta(html, str(uscita)))
    return uscita


def telegram_foto(percorso, didascalia):
    tok = __import__("os").environ.get("TELEGRAM_BOT_TOKEN") or __import__("os").environ.get("TELEGRAM_TOKEN")
    chat = __import__("os").environ.get("TELEGRAM_CANALE") or __import__("os").environ.get("TELEGRAM_CHAT_ID") or "559225883"
    if not tok:
        return
    with open(percorso, "rb") as f:
        requests.post(f"https://api.telegram.org/bot{tok}/sendPhoto", data={"chat_id": chat, "caption": didascalia[:1000], "disable_notification": "true"},
                      files={"photo": f}, timeout=120, verify=NG.CA).raise_for_status()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", action="store_true")
    ap.add_argument("--forza", action="store_true", help="ignora l'orario e il segno 'già fatta oggi'")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--scelte", default="", help="indirizzi (separati da spazio) degli articoli scelti da te: il primo è il gancio")
    ap.add_argument("--gancio-titolo", default="", help="titolo grande del gancio (se manca si ricava dal titolo dell'articolo)")
    a = ap.parse_args()
    adesso = ora_roma()
    oggi = adesso.strftime("%Y-%m-%d")
    stato = NG.stato_leggi()
    if not a.forza and not a.scelte:
        if not (21 * 60 <= adesso.hour * 60 + adesso.minute <= 22 * 60 + 45):
            print(f"Sono le {adesso:%H:%M} a Roma: non è l'ora della rassegna.")
            return
        if stato.get("giorno_rassegna") == oggi:
            print("Rassegna di oggi già inviata.")
            return
    nomi = NG.nomi_con_foto()
    gancio, gancio_titolo = False, a.gancio_titolo or None
    forz = leggi_forzata(oggi)
    if a.scelte:   # articoli scelti da te (comando /rassegna): il primo è il gancio
        scelte = articoli_da_url(a.scelte.split())
        gancio = bool(scelte)
    else:
        scelte = scegli_rassegna(a.n, nomi, stato)
        if forz and forz.get("gancio_url"):   # per oggi un articolo deve aprire la rassegna
            art = next(iter(articoli_da_url([forz["gancio_url"]])), None)
            if not art and forz.get("gancio_articolo_titolo"):   # l'articolo non è più nel feed: si usano i dati salvati
                art = {"url": forz["gancio_url"], "titolo": forz["gancio_articolo_titolo"], "estratto": "", "fonte": forz.get("gancio_fonte", ""), "serie": "F1",
                       "pubblicato": datetime.now(timezone.utc).isoformat()}
            if art:
                altre = [x for x in scelte if x["url"] != art["url"] and x["url"] not in NG.simili(art, [x]) and art["url"] not in NG.simili(x, [art])]
                scelte = ([art] + altre)[:a.n]
                gancio, gancio_titolo = True, gancio_titolo or forz.get("gancio_titolo")
    print("Scelte:", [x["titolo"][:60] for x in scelte])
    try:
        if len(scelte) < (2 if a.scelte else 3):
            raise RuntimeError(f"oggi ci sono troppo poche notizie adatte ({len(scelte)})")
        spec, social = costruisci(scelte, nomi, adesso, gancio, gancio_titolo)
        uscita = Path("/tmp/rassegna_sera.mp4")
        asyncio.run(NS.genera(spec, uscita))
        data = f"{adesso.day} {MESI[adesso.month - 1]}"
        copertine = []   # una copertina con un pilota di F1 e una con un pilota di MotoGP: si sceglie quella che piace
        for etichetta, fai in (("F1", lambda: crea_copertina(spec, data, Path("/tmp/rassegna_copertina_f1.png"))),
                               ("MotoGP", lambda: crea_copertina_moto(scelte, nomi, data, Path("/tmp/rassegna_copertina_moto.png")))):
            try:
                c = fai()
                if c:
                    copertine.append((etichetta, c))
            except (Exception, SystemExit) as e:
                print(f"  copertina {etichetta} non riuscita ({type(e).__name__}: {e}): il video parte lo stesso")
        if not a.prova:
            for etichetta, c in copertine:
                telegram_foto(c, f"🖼 Copertina {etichetta} · Rassegna stampa del {data}")
            NG.telegram(uscita, f"📰 {spec['titolo_breve']} · titoli e fonti nella didascalia", social)
            if not a.forza and not a.scelte:   # una rassegna chiesta a mano non spegne quella automatica delle 21:30 e non "consuma" le notizie
                nuovo_stato = NG.stato_leggi()
                nuovo_stato["rassegna_usate"] = ([x["url"] for x in scelte] + nuovo_stato.get("rassegna_usate", []))[:80]   # domani non si rimettono
                STATO.write_text(json.dumps({**nuovo_stato, "giorno_rassegna": oggi}, ensure_ascii=False, indent=1))
    except (Exception, SystemExit) as e:
        print(f"Rassegna non riuscita: {type(e).__name__}: {e}")
        if not a.prova:
            NG.avviso(f"⚠️ La rassegna stampa delle 21:30 non è riuscita: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
