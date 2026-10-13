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


def scegli_rassegna(n, nomi):
    arts = json.load(open(DATA / "rassegna.json"))["articoli"]
    ora = datetime.now(timezone.utc)
    buone = []
    for a in arts:
        try:
            if (ora - datetime.fromisoformat(a["pubblicato"])).total_seconds() > 30 * 3600:
                continue
        except Exception:
            continue
        t = pulisci(a["titolo"])
        if "|" in t or SIGLE.search(re.sub(r"\bF1\b", "", t)) or not 25 <= len(t) <= 125:
            continue
        p = NG.punteggio(a, nomi) + (4 if any(k in NG.norm(t) for k in FERRARI) else 0)
        if p > 0:
            buone.append((p, a))
    buone.sort(key=lambda x: -x[0])
    scelte = []
    for _, a in buone:
        if len(scelte) >= n:
            break
        if any(a["url"] in NG.simili(b, [a]) or b["url"] in NG.simili(a, [b]) for b in scelte):
            continue
        if sum(b["serie"] == a["serie"] for b in scelte) >= n - 1:
            continue   # mai tutte della stessa serie
        scelte.append(a)
    return scelte


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


def costruisci(scelte, nomi, oggi):
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
        citati = [n for n in nomi if len(cognome(n)) > 3 and cognome(n) in parole and nomi[n] == a["serie"]]
        f = citati[0] if citati else next((n for n in rot[a["serie"]][k:] + rot[a["serie"]] if n not in usate[-1:]), rot[a["serie"]][0])
        fonte = a["fonte"].strip()
        sc = {"foto": f, "nome": fonte, "testo": f"Secondo {fonte}: {t}"}
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
                sc = {"foto": f, "foto_file": str(rit), "credito": "Foto: ESPN", "nome": fonte, "testo": sc["testo"]}
            elif not citati:   # nessun pilota nel titolo: macchine, box e circuiti dalle foto ESPN delle notizie
                u = espn()
                if u:
                    sc = {"foto_url": u, "nome": fonte, "testo": sc["testo"]}
        elif f in (json.load(open(DATA / "foto-extra.json")) or {}) and "pista" in json.load(open(DATA / "foto-extra.json"))[f]:
            sc["alt"] = "pista"   # moto in pista invece del ritratto
        scene.append(sc)
        usate.append(f)
    data = f"{oggi.day} {MESI[oggi.month - 1]}"
    hook = f"Rassegna stampa di GP Oggi: {len(scene)} titoli da non perdere."
    hook_img = espn()
    if hook_img:
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", action="store_true")
    ap.add_argument("--forza", action="store_true", help="ignora l'orario e il segno 'già fatta oggi'")
    ap.add_argument("--n", type=int, default=5)
    a = ap.parse_args()
    adesso = ora_roma()
    oggi = adesso.strftime("%Y-%m-%d")
    stato = NG.stato_leggi()
    if not a.forza:
        if not (21 * 60 <= adesso.hour * 60 + adesso.minute <= 22 * 60 + 45):
            print(f"Sono le {adesso:%H:%M} a Roma: non è l'ora della rassegna.")
            return
        if stato.get("giorno_rassegna") == oggi:
            print("Rassegna di oggi già inviata.")
            return
    nomi = NG.nomi_con_foto()
    scelte = scegli_rassegna(a.n, nomi)
    print("Scelte:", [x["titolo"][:60] for x in scelte])
    try:
        if len(scelte) < 3:
            raise RuntimeError(f"oggi ci sono troppo poche notizie adatte ({len(scelte)})")
        spec, social = costruisci(scelte, nomi, adesso)
        uscita = Path("/tmp/rassegna_sera.mp4")
        asyncio.run(NS.genera(spec, uscita))
        if not a.prova:
            NG.telegram(uscita, f"📰 {spec['titolo_breve']} · titoli e fonti nella didascalia", social)
            STATO.write_text(json.dumps({**NG.stato_leggi(), "giorno_rassegna": oggi}, ensure_ascii=False, indent=1))
    except (Exception, SystemExit) as e:
        print(f"Rassegna non riuscita: {type(e).__name__}: {e}")
        if not a.prova:
            NG.avviso(f"⚠️ La rassegna stampa delle 21:30 non è riuscita: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
