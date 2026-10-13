"""Video "Prossima gara": quando si corre, chi sono i favoriti (indice di GP Oggi, non una certezza), come è andata l'anno scorso, le ultime notizie.

Senza modelli di linguaggio: solo i dati del sito (pronostici.json, events.json, motogp.json, rassegna.json) e frasi fisse nostre.
Le notizie sono titoli citati con la fonte. Si sceglie la serie con --serie f1|motogp (di base la prossima gara in ordine di tempo).
Uso:  python3 anteprima_gara.py [--serie f1|motogp] [--prova] [--avvisa]
"""
import argparse, asyncio, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).parent.parent))
import notizie_giorno as NG  # noqa: E402
import notizia_sub as NS  # noqa: E402
import rassegna_giornaliera as RG  # noqa: E402

DATA = NG.DATA
ROMA = ZoneInfo("Europe/Rome")
GIORNI = "lunedì martedì mercoledì giovedì venerdì sabato domenica".split()
MESI = RG.MESI
MOTO = [("ducati", "e1251b"), ("gresini", "e1251b"), ("vr46", "e1251b"), ("aprilia", "7b2c8f"), ("trackhouse", "7b2c8f"), ("ktm", "f26a1b"), ("tech3", "f26a1b"), ("yamaha", "1d4fa3"), ("honda", "dcdce2"), ("lcr", "dcdce2")]
norm = NG.norm


def quando(iso):
    t = datetime.fromisoformat(iso).astimezone(ROMA)
    ora = f"{t.hour}" + (f" e {t.minute}" if t.minute else "")
    return f"{GIORNI[t.weekday()]} {t.day} {MESI[t.month - 1]} alle {ora}", t


def scegli_serie(serie):
    pron = json.load(open(DATA / "pronostici.json"))
    adesso = datetime.now(timezone.utc)
    cand = {k: pron[k] for k in ("f1", "motogp") if pron.get(k) and pron[k].get("favoriti") and datetime.fromisoformat(pron[k]["gara"]) > adesso}
    if serie:
        if serie not in cand:
            raise RuntimeError(f"nessuna gara in programma per {serie}")
        return serie, cand[serie]
    if not cand:
        raise RuntimeError("nessuna gara in programma")
    k = min(cand, key=lambda x: cand[x]["gara"])
    return k, cand[k]


def paese_e_orari(serie, p):
    if serie == "f1":
        gp = next(x for x in json.load(open(DATA / "events.json")) if x["circuito"] == p["circuito"] and x["fine"] > datetime.now(timezone.utc).isoformat())
    else:
        gp = next(x for x in json.load(open(DATA / "motogp.json"))["weekend"] if x["circuito"] == p["circuito"])
    return gp


def vincitore_anno_scorso(paese):
    """Chi ha vinto lo stesso Gran Premio nel 2025 (Jolpica, solo F1). None se non si trova: allora la scena non c'è."""
    try:
        H = {"User-Agent": "GPOggiBot/1.0 (+https://gpoggi.it)"}
        gare = requests.get("https://api.jolpi.ca/ergast/f1/2025/races/?limit=30", headers=H, timeout=30).json()["MRData"]["RaceTable"]["Races"]
        import scraper_f1 as sf
        r = next((x for x in gare if sf.PAESI_IT.get(x["Circuit"]["Location"]["country"], x["Circuit"]["Location"]["country"]) == paese), None)
        if not r:
            return None
        ris = requests.get(f"https://api.jolpi.ca/ergast/f1/2025/{r['round']}/results/", headers=H, timeout=30).json()["MRData"]["RaceTable"]["Races"][0]["Results"]
        return [f"{x['Driver']['givenName']} {x['Driver']['familyName']}" for x in ris[:3]]
    except Exception as e:
        print("  vincitore dell'anno scorso non disponibile:", e)
        return None


def colore(serie, f):
    if serie == "f1":
        return next((p["colore"] for p in json.load(open(DATA / "roster.json")) if p["nome"] == f["nome"]), "888888")
    t = norm(f.get("team", ""))
    return next((c for k, c in MOTO if k in t), "888888")


def cognome(n):
    return n.split()[-1]


def notizie_circuito(serie, p, favoriti, nomi, n=2):
    parole_chiave = {norm(p["circuito"]), norm(p["gp"]).replace("gran premio ", "").replace("gp ", "")} | {norm(x) for x in re.findall(r"\w{5,}", p["gp"]) if norm(x) not in ("gran", "premio")}
    cogn = [norm(cognome(f["nome"])) for f in favoriti[:3]] + ["ferrari", "leclerc", "hamilton"] * (serie == "f1")
    ora = datetime.now(timezone.utc)
    trovate = []
    for a in json.load(open(DATA / "rassegna.json"))["articoli"]:
        t = RG.pulisci(a["titolo"])
        try:
            if (ora - datetime.fromisoformat(a["pubblicato"])).total_seconds() > 96 * 3600:
                continue
        except Exception:
            continue
        if a["serie"] != ("F1" if serie == "f1" else "MotoGP") or "|" in t or RG.SIGLE.search(re.sub(r"\bF1\b", "", t)) or not 25 <= len(t) <= 125:
            continue
        nt = norm(t)
        circ = any(k and k in nt for k in parole_chiave)
        pil = any(k in nt for k in cogn)
        p_ = NG.punteggio(a, nomi)
        if (circ or pil) and p_ > -10:
            trovate.append((int(circ) * 10 + p_, a, t))
    trovate.sort(key=lambda x: -x[0])
    out = []
    for _, a, t in trovate:
        if not any(a["url"] in NG.simili(b[0], [a]) for b in out):
            out.append((a, t))
        if len(out) >= n:
            break
    return out


def costruisci(serie, p, nomi):
    S = "F1" if serie == "f1" else "MotoGP"
    gp = paese_e_orari(serie, p)
    fav = [f for f in p["favoriti"] if f["nome"] in nomi][:5]
    if len(fav) < 3:
        raise RuntimeError("meno di tre favoriti con foto libera")
    giorno_gara, t_gara = quando(p["gara"])
    luogo = f"{p['circuito']}" + (f", {gp['paese']}" if gp.get("paese") and norm(gp["paese"]) != norm(p["circuito"]) else "")
    scene = [{"foto": fav[0]["nome"], "hook": True, "hook_titolo": f"{p['gp']}: chi vince?", "testo": f"Si avvicina il {p['gp']}. Chi può vincere?"},
             {"foto": fav[1]["nome"], "nome": fav[1]["nome"], "testo": f"Si corre a *{luogo}*. La gara parte *{giorno_gara}*, ora italiana."}]
    ult = vincitore_anno_scorso(gp["paese"]) if serie == "f1" else None
    if ult:
        scene.append({"foto": ult[0] if ult[0] in nomi else fav[0]["nome"], "nome": ult[0] if ult[0] in nomi else None,
                      "testo": f"Lo scorso anno qui ha vinto *{ult[0]}*, davanti a {ult[1]} e {ult[2]}."})
    top = fav[0]
    motivo = (top.get("motivi") or [""])[0].replace("nelle ultime 5 gare", "nelle ultime cinque gare")
    tab = {"titolo": "Favoriti di GP Oggi", "righe": [{"pos": "", "colore": colore(serie, f), "nome": cognome(f["nome"]).upper(), "voto": f["indice"], "nota": " "} for f in fav]}
    scene.append({"foto": top["nome"], "nome": top["nome"], "pista": True, "classifica": tab, "sub_top": 1360,
                  "testo": f"Per i nostri numeri il favorito è *{cognome(top['nome'])}*" + (f": {motivo}." if motivo else ".") + f" Poi {cognome(fav[1]['nome'])} e {cognome(fav[2]['nome'])}. È un'opinione basata sui numeri, non una certezza."})
    if serie == "f1":
        for pil in ("Charles Leclerc", "Lewis Hamilton"):
            f = next((x for x in p["favoriti"] if x["nome"] == pil), None)
            if f and pil in nomi and pil != top["nome"]:
                m = (f.get("motivi") or [""])[0].replace("nelle ultime 5 gare", "nelle ultime cinque gare")
                scene.append({"foto": pil, "nome": pil, "testo": f"In casa *Ferrari*: {cognome(pil)} " + (f"ha {m.lower()}." if m and m[0].isdigit() and "campionato" not in m else f"è nei favoriti di GP Oggi, con indice {f['indice']}.")})
    notizie = notizie_circuito(serie, p, fav, nomi)
    for a, t in notizie:
        cit = [n for n in nomi if len(norm(cognome(n))) > 3 and norm(cognome(n)) in norm(t).split() and nomi[n] == S]
        f = cit[0] if cit else fav[len(scene) % len(fav)]["nome"]
        scene.append({"foto": f, "nome": a["fonte"].strip(), "testo": f"Secondo {a['fonte'].strip()}: {t}"})
    domanda = f"Chi vince secondo te il {p['gp']}?"
    spec = {"serie": S, "titolo_breve": p["gp"], "etichetta": "Prossima gara", "fonte": "dati GP Oggi", "velocita": "+38%", "scene": scene, "finale": {"foto": fav[0]["nome"], "domanda": domanda}}
    righe = [f"🏁 {p['gp']}: chi vince?", "", f"📍 {luogo}", f"🕒 Gara {giorno_gara}", ""]
    righe += [f"{i}. {f['nome']}" for i, f in enumerate(fav[:3], 1)]
    if ult:
        righe += ["", f"Lo scorso anno ha vinto {ult[0]}."]
    righe += ["", "Il pronostico è un'opinione basata sui numeri, non una certezza.", ""]
    righe += [f"• {t} — {a['fonte'].strip()}" for a, t in notizie] + ([""] if notizie else [])
    social = "\n".join(righe) + f"{domanda} Dimmi la tua nei commenti 👇\n\n🔗 gpoggi.it\n\n#gpoggi #{'f1' if serie == 'f1' else 'motogp'} #pronostici #granpremio"
    return spec, social


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serie", choices=["f1", "motogp"])
    ap.add_argument("--prova", action="store_true")
    ap.add_argument("--avvisa", action="store_true")
    a = ap.parse_args()
    try:
        nomi = NG.nomi_con_foto()
        serie, p = scegli_serie(a.serie)
        spec, social = costruisci(serie, p, nomi)
        uscita = Path("/tmp/anteprima_gara.mp4")
        asyncio.run(NS.genera(spec, uscita))
        if not a.prova:
            NG.telegram(uscita, f"🏁 {p['gp']}: chi vince? · pronostico di GP Oggi", social)
    except (Exception, SystemExit) as e:
        print(f"Anteprima non riuscita: {type(e).__name__}: {e}")
        if a.avvisa and not a.prova:
            NG.avviso(f"⚠️ Non sono riuscito a fare il video sulla prossima gara: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
