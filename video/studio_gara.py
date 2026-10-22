"""Studio di GP Oggi su chi può vincere la gara e chi può prendere la pole: non solo le ultime cinque gare.

Per ogni pilota si mettono insieme, con pesi dichiarati:
  - la forma (punti virtuali delle ultime 5 gare, oppure delle ultime 5 qualifiche)
  - come è andato lui sullo stesso circuito negli ultimi 3 anni (più peso all'anno scorso)
  - quanto la sua moto/macchina è adatta al circuito: i podi (o le prime file) del suo costruttore lì negli ultimi 3 anni
  - la classifica del campionato
  - chi ha vinto (o preso la pole) lì l'anno scorso
Dati: Jolpica (F1) e servizio pubblico MotoGP; nessun modello di linguaggio. I numeri a schermo e a voce sono quelli veri dello studio.

Prova:  python3 studio_gara.py f1|motogp     (stampa le classifiche con i motivi)
"""
import json, re, sys, time, unicodedata
from datetime import datetime, timezone
from pathlib import Path

import requests

QUI = Path(__file__).parent
ROOT = QUI.parent
DATA = ROOT / "docs" / "data"
sys.path.insert(0, str(ROOT))

PTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
PESI_ANNO = {1: 0.5, 2: 0.3, 3: 0.2}   # anno scorso, due anni fa, tre anni fa
NEUTRO = 0.2
H = {"User-Agent": "GPOggiBot/1.0 (+https://gpoggi.it; progetto non commerciale)"}
ORD = {1: "primo", 2: "secondo", 3: "terzo", 4: "quarto", 5: "quinto", 6: "sesto", 7: "settimo", 8: "ottavo", 9: "nono", 10: "decimo"}
UN = "zero uno due tre quattro cinque sei sette otto nove dieci undici dodici".split()


def norm(t):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", unicodedata.normalize("NFD", t or "").encode("ascii", "ignore").decode().lower())).strip()


def pp(pos):
    return PTS[pos - 1] / PTS[0] if pos and 1 <= pos <= 10 else 0.0


def ck(s):
    """Costruttore in forma confrontabile tra stagioni e fonti."""
    t = norm(s)
    for chiave, alias in (("racing bulls", "racingbulls"), ("rb f1", "racingbulls"), ("alphatauri", "racingbulls"), ("red bull", "redbull"), ("sauber", "sauber"), ("audi", "sauber"),
                          ("aston", "aston"), ("alpine", "alpine"), ("haas", "haas"), ("williams", "williams"), ("mclaren", "mclaren"), ("ferrari", "ferrari"), ("mercedes", "mercedes")):
        if chiave in t:
            return alias
    return t


# ---------- storico dello stesso circuito ----------
def jolpica(url):
    for t in range(5):
        r = requests.get(url, headers=H, timeout=30)
        if r.status_code != 429:
            r.raise_for_status()
            return r.json()["MRData"]
        time.sleep(3 + 4 * t)
    raise requests.RequestException("Jolpica occupata")


def storico_f1(gp, anni):
    luoghi = {norm(x) for x in (gp.get("circuito"), gp.get("localita")) if x}
    out = []
    for y in anni:
        try:
            gare = jolpica(f"https://api.jolpi.ca/ergast/f1/{y}/races/?limit=30")["RaceTable"]["Races"]
            r = next((x for x in gare if norm(x["Circuit"]["Location"]["locality"]) in luoghi or norm(x["Circuit"]["circuitName"]) in luoghi), None)
            if not r:
                continue
            ris = jolpica(f"https://api.jolpi.ca/ergast/f1/{y}/{r['round']}/results/?limit=30")["RaceTable"]["Races"][0]["Results"]
            qua = jolpica(f"https://api.jolpi.ca/ergast/f1/{y}/{r['round']}/qualifying/?limit=30")["RaceTable"]["Races"][0]["QualifyingResults"]
        except Exception as e:
            print(f"  F1 {y}: dati non disponibili ({e})")
            continue
        riga = lambda x, pos: {"nome": f"{x['Driver']['givenName']} {x['Driver']['familyName']}", "cod": x["Driver"].get("code"), "cost": ck(x["Constructor"]["name"]), "pos": pos}
        out.append({"anno": y, "gara": [riga(x, int(x["position"])) for x in ris if x["position"].isdigit()], "quali": [riga(x, int(x["position"])) for x in qua if x["position"].isdigit()]})
    return out


def storico_moto(circuito, anni):
    import build_motogp as bm
    import build_report_moto as br
    out = []
    for y in anni:
        try:
            stag = next(x for x in bm.api("results/seasons") if x["year"] == y)["id"]
            cat = next(x["id"] for x in bm.api("results/categories", seasonUuid=stag) if x["name"].replace("™", "") == "MotoGP")
            ev = next((e for e in bm.api("results/events", seasonUuid=stag, isFinished="true") if not e.get("test") and norm((e.get("circuit") or {}).get("name")) == norm(circuito)), None)
            if not ev:
                continue
            sess = bm.api_cache("results/sessions", eventUuid=ev["id"], categoryUuid=cat)
            rac = next(q for q in sess if q["type"] == "RAC")
            righe = [x for x in bm.api_cache(f"results/session/{rac['id']}/classification", test="false")["classification"] if x.get("position")]
            griglia = br.griglia(sess)
        except Exception as e:
            print(f"  MotoGP {y}: dati non disponibili ({e})")
            continue
        riga = lambda x, pos: {"nome": x["rider"]["full_name"], "id": x["rider"]["id"], "cost": ck(x["constructor"]["name"]), "pos": pos}
        out.append({"anno": y, "gara": sorted((riga(x, x["position"]) for x in righe), key=lambda r: r["pos"]),
                    "quali": sorted((riga(x, griglia[x["rider"]["id"]]) for x in righe if x["rider"]["id"] in griglia), key=lambda r: r["pos"])})
    return out


# ---------- piloti di oggi e forma ----------
def piloti_f1():
    roster = json.load(open(DATA / "roster.json"))
    st = {p["numero"]: p for p in json.load(open(DATA / "standings.json"))["piloti"]}
    out = []
    for p in roster:
        if p["numero"] in st:
            out.append({"nome": p["nome"], "cod": p.get("acronimo"), "cost": ck(p["team"]), "costruttore": p["team"], "punti": st[p["numero"]]["punti"], "pos": st[p["numero"]]["posizione"]})
    return out


def forma_f1():
    ora = datetime.now(timezone.utc).isoformat()
    eventi = [g for g in json.load(open(DATA / "events.json")) if g["fine"] < ora][-5:]
    gara, quali = {}, {}
    for g in eventi:
        r = json.load(open(DATA / "gare" / f"{g['id']}.json"))
        for tipo, dest in (("Race", gara), ("Qualifying", quali)):
            s = next((x for x in r["sessioni"] if x["tipo"] == tipo), None)
            for x in (s or {}).get("risultati") or []:
                dest.setdefault(x["nome"], []).append(x["pos"])
    return gara, quali, len(eventi)


def piloti_moto():
    return [{"nome": p["nome"], "id": i, "cost": ck(p["moto"]), "costruttore": p["moto"], "punti": p["punti"], "pos": p["pos"]}
            for i, p in json.load(open(DATA / "motogp-piloti.json")).items() if p["categoria"] == "MotoGP"]


def forma_moto():
    piloti = json.load(open(DATA / "motogp-piloti.json"))
    date = {}
    for p in piloti.values():
        for g in p["gare"]:
            date[g["gp"]] = max(date.get(g["gp"], ""), g["data"])
    ultime = sorted(date, key=date.get)[-5:]
    gara = {}
    for p in piloti.values():
        if p["categoria"] != "MotoGP":
            continue
        for gp in ultime:
            g = next((x for x in p["gare"] if x["gp"] == gp), None)
            gara.setdefault(p["nome"], []).append(g["gara"] if g else None)
    quali = {}
    gare = json.load(open(DATA / "motogp-gare.json"))
    for gp in ultime:
        for r in ((gare.get(gp) or {}).get("classifiche") or {}).get("MotoGP", []):
            quali.setdefault(r["nome"], []).append(r.get("griglia"))
    return gara, quali, len(ultime)


# ---------- punteggi ----------
def pesato(valori):
    """valori = {anni_fa: x}: media pesata sugli anni disponibili, None se non ce ne sono."""
    tot = sum(PESI_ANNO[a] for a in valori)
    return sum(PESI_ANNO[a] * v for a, v in valori.items()) / tot if tot else None


def f_ord(n):
    return ORD.get(n, f"{n}°")


def studio(chiave):
    ora = datetime.now(timezone.utc)
    anno = ora.year
    anni = [anno - 1, anno - 2, anno - 3]
    if chiave == "f1":
        gp = next((g for g in json.load(open(DATA / "events.json")) if g["fine"] > ora.isoformat()), None)
        stor = storico_f1(gp, anni)
        piloti = piloti_f1(); fg, fq, n = forma_f1()
        chiave_id = lambda p: p["cod"]; id_riga = lambda r: r.get("cod")
        nomi_veicolo = "macchina"
    else:
        pron = json.load(open(DATA / "pronostici.json"))["motogp"]
        gp = {"circuito": pron["circuito"]}
        stor = storico_moto(gp["circuito"], anni)
        piloti = piloti_moto(); fg, fq, n = forma_moto()
        chiave_id = lambda p: p["id"]; id_riga = lambda r: r.get("id")
        nomi_veicolo = "moto"
    n3 = len(stor)
    anni_fa = lambda y: anno - y
    maxp = max((p["punti"] for p in piloti), default=1) or 1
    risultati = []
    for p in piloti:
        pid = chiave_id(p)
        # --- sul circuito
        pos_g, pos_q = {}, {}
        for s in stor:
            a = anni_fa(s["anno"])
            rg = next((r for r in s["gara"] if id_riga(r) == pid), None); rq = next((r for r in s["quali"] if id_riga(r) == pid), None)
            if rg: pos_g[a] = rg["pos"]
            if rq: pos_q[a] = rq["pos"]
        circ_g = pesato({a: pp(x) for a, x in pos_g.items()}); circ_q = pesato({a: pp(x) for a, x in pos_q.items()})
        # --- moto/macchina sul circuito: podi (gara) e prime file (qualifica) del costruttore
        podi = sum(1 for s in stor for r in s["gara"][:3] if r["cost"] == p["cost"])
        file1 = sum(1 for s in stor for r in s["quali"][:3] if r["cost"] == p["cost"])
        cost_g = pesato({anni_fa(s["anno"]): sum(1 for r in s["gara"][:3] if r["cost"] == p["cost"]) / 3 for s in stor}); cost_q = pesato({anni_fa(s["anno"]): sum(1 for r in s["quali"][:3] if r["cost"] == p["cost"]) / 3 for s in stor})
        # --- forma
        pg = [x for x in fg.get(p["nome"], [])]; pq = [x for x in fq.get(p["nome"], [])]
        forma_g = sum(pp(x) for x in pg) / (n or 1); forma_q = sum(pp(x) for x in pq) / (n or 1)
        vitt = sum(1 for x in pg if x == 1); pod = sum(1 for x in pg if x and x <= 3); poles = sum(1 for x in pq if x == 1)
        camp = p["punti"] / maxp
        vinto = stor and any(r["pos"] == 1 and id_riga(r) == pid for r in stor[0]["gara"]) if stor and stor[0]["anno"] == anno - 1 else False
        pole_scorso = stor and any(r["pos"] == 1 and id_riga(r) == pid for r in stor[0]["quali"]) if stor and stor[0]["anno"] == anno - 1 else False
        bonus_g = 1.0 if vinto else 0.0; bonus_q = 1.0 if pole_scorso else 0.0
        sg = 0.30 * forma_g + 0.25 * (NEUTRO if circ_g is None else circ_g) + 0.25 * (NEUTRO if cost_g is None else cost_g) + 0.10 * camp + 0.10 * bonus_g
        sq = 0.30 * forma_q + 0.25 * (NEUTRO if circ_q is None else circ_q) + 0.25 * (NEUTRO if cost_q is None else cost_q) + 0.10 * forma_g + 0.10 * bonus_q
        # --- motivi con i numeri veri: (esito, testo a schermo, testo a voce, forza)
        mg, mq = [], []
        if vinto:
            mg.append(("si", "Ha vinto qui l'anno scorso", "ha vinto qui l'anno scorso", 9))
        elif 1 in pos_g and pos_g[1] <= 3:
            mg.append(("si", f"Qui {anno - 1}: {pos_g[1]}°", f"qui l'anno scorso è arrivato {f_ord(pos_g[1])}", 7))
        elif 1 in pos_g:
            mg.append(("no", f"Qui {anno - 1}: {pos_g[1]}°", f"qui l'anno scorso ha chiuso solo {f_ord(pos_g[1])}", 6))
        if n3 and cost_g is not None:
            tot = 3 * n3
            if podi >= max(3, tot // 3):
                mg.append(("si", f"Sua {nomi_veicolo}: {podi} dei {tot} podi qui in {n3} anni", f"negli ultimi {UN[n3]} anni {UN[podi] if podi < len(UN) else podi} dei {UN[tot] if tot < len(UN) else tot} posti sul podio qui sono stati della sua {nomi_veicolo}", 8))
            elif podi <= 1:
                mg.append(("no", f"Sua {nomi_veicolo}: {podi} dei {tot} podi qui in {n3} anni", f"negli ultimi {UN[n3]} anni solo {UN[podi]} dei {UN[tot] if tot < len(UN) else tot} posti sul podio qui {'è stato' if podi == 1 else 'è stato'} della sua {nomi_veicolo}" if podi == 1 else f"negli ultimi {UN[n3]} anni nessuno dei {UN[tot] if tot < len(UN) else tot} posti sul podio qui è stato della sua {nomi_veicolo}", 5))
        if vitt:
            mg.append(("si", f"{vitt} {'vittoria' if vitt == 1 else 'vittorie'} nelle ultime {n} gare", f"{'una vittoria' if vitt == 1 else UN[vitt] + ' vittorie'} nelle ultime {UN[n]}", 6))
        elif pod:
            mg.append(("si", f"{pod} {'podio' if pod == 1 else 'podi'} nelle ultime {n} gare", f"{'un podio' if pod == 1 else UN[pod] + ' podi'} nelle ultime {UN[n]} gare", 4))
        if p["pos"] <= 3:
            mg.append(("si", f"{p['pos']}° nel campionato ({p['punti']:g} punti)", f"{f_ord(p['pos'])} nel mondiale", 3))
        if pole_scorso:
            mq.append(("si", "Ha preso la pole qui l'anno scorso", "ha preso la pole qui l'anno scorso", 9))
        elif 1 in pos_q and pos_q[1] <= 3:
            mq.append(("si", f"Qualifica qui {anno - 1}: {pos_q[1]}°", f"qui l'anno scorso è partito {f_ord(pos_q[1])}", 7))
        if n3 and cost_q is not None and file1 >= max(3, 3 * n3 // 3):
            mq.append(("si", f"Sua {nomi_veicolo}: {file1} dei {3 * n3} primi 3 in griglia in {n3} anni", f"negli ultimi {UN[n3]} anni {UN[file1] if file1 < len(UN) else file1} dei {UN[3 * n3] if 3 * n3 < len(UN) else 3 * n3} primi posti in griglia qui sono stati della sua {nomi_veicolo}", 8))
        if poles:
            mq.append(("si", f"{poles} {'pole' if poles == 1 else 'pole'} nelle ultime {n} qualifiche", f"{'una pole' if poles == 1 else UN[poles] + ' pole'} nelle ultime {UN[n]} qualifiche", 6))
        risultati.append({"nome": p["nome"], "costruttore": p["costruttore"], "gara": sg, "pole": sq, "motivi_gara": sorted(mg, key=lambda m: -m[3]), "motivi_pole": sorted(mq, key=lambda m: -m[3])})
    scorso = {}
    if stor and stor[0]["anno"] == anno - 1:
        scorso = {"anno": anno - 1, "vincitore": stor[0]["gara"][0]["nome"] if stor[0]["gara"] else None, "pole": stor[0]["quali"][0]["nome"] if stor[0]["quali"] else None,
                  "podio": [r["nome"] for r in stor[0]["gara"][:3]]}
    return {"serie": chiave, "anni_studiati": [s["anno"] for s in stor], "gara": sorted(risultati, key=lambda r: -r["gara"]), "pole": sorted(risultati, key=lambda r: -r["pole"]), "scorso": scorso}


if __name__ == "__main__":
    d = studio(sys.argv[1] if len(sys.argv) > 1 else "f1")
    print("anni:", d["anni_studiati"], "scorso:", d["scorso"])
    for k in ("gara", "pole"):
        print("==", k)
        for r in d[k][:5]:
            print(f"  {r['nome']:22s} {r[k]:.3f}  " + " | ".join(m[1] for m in r["motivi_" + k]))
