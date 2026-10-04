"""Pronostico del prossimo Gran Premio di F1 e di MotoGP: un indice trasparente, non una previsione ufficiale.

Indice = 45% forma (punti virtuali delle ultime 5 gare) + 35% classifica del campionato + 20% risultato sullo stesso circuito
l'anno scorso (se il pilota c'era; altrimenti un valore neutro). Ogni favorito riporta i motivi con i numeri veri.
Fonti: dati del sito (docs/data), Jolpica per la F1 2025, servizio pubblico MotoGP per il 2025.
Scrive docs/data/pronostici.json.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

import build_motogp as bm
import scraper_f1 as sf

DATA = Path(__file__).parent / "docs" / "data"
H = {"User-Agent": "GPOggiBot/1.0 (+https://gpoggi.it; progetto non commerciale)"}
PTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
NEUTRO = 0.2
PESI = (0.45, 0.35, 0.20)


def punti_pos(pos):
    return PTS[pos - 1] if pos and 1 <= pos <= 10 else 0


def ordinale(p):
    return f"{p}°"


def indice(forma, camp, pista):
    return PESI[0] * forma + PESI[1] * camp + PESI[2] * pista


def motivi(vitt, podi, n, pos_camp, pts, pista_pos, luogo):
    m = []
    if vitt:
        m.append(f"{vitt} {'vittoria' if vitt == 1 else 'vittorie'} nelle ultime {n} gare")
    elif podi:
        m.append(f"{podi} {'podio' if podi == 1 else 'podi'} nelle ultime {n} gare")
    m.append(f"{ordinale(pos_camp)} nel campionato ({pts:g} punti)")
    if pista_pos:
        m.append(f"{luogo} 2025: {ordinale(pista_pos)}")
    return m


def f1():
    ora = datetime.now(timezone.utc).isoformat()
    eventi = json.loads((DATA / "events.json").read_text())
    gp = next((g for g in eventi if g["fine"] > ora), None)
    if not gp:
        return None
    roster = {p["numero"]: p for p in json.loads((DATA / "roster.json").read_text())}
    st = json.loads((DATA / "standings.json").read_text())["piloti"]
    pts_camp = {p["numero"]: p["punti"] for p in st}
    pos_camp = {p["numero"]: p["posizione"] for p in st}
    passati = [g for g in eventi if g["fine"] < ora][-5:]
    forma, vitt, podi = {}, {}, {}
    for g in passati:
        r = json.loads((DATA / "gare" / f"{g['id']}.json").read_text())
        gara = next((s for s in r["sessioni"] if s["tipo"] == "Race"), None)
        for x in (gara or {}).get("risultati") or []:
            n = x["numero"]
            forma[n] = forma.get(n, 0) + punti_pos(x["pos"])
            vitt[n] = vitt.get(n, 0) + (x["pos"] == 1)
            podi[n] = podi.get(n, 0) + (bool(x["pos"]) and x["pos"] <= 3)
    # lo stesso circuito nel 2025 (Jolpica): si riconosce dal paese
    pista, luogo = {}, gp["paese"]
    try:
        gare25 = requests.get("https://api.jolpi.ca/ergast/f1/2025/races/?limit=30", headers=H, timeout=30).json()["MRData"]["RaceTable"]["Races"]
        r25 = next((x for x in gare25 if sf.PAESI_IT.get(x["Circuit"]["Location"]["country"], x["Circuit"]["Location"]["country"]) == gp["paese"]), None)
        if r25:
            ris = requests.get(f"https://api.jolpi.ca/ergast/f1/2025/{r25['round']}/results/", headers=H, timeout=30).json()["MRData"]["RaceTable"]["Races"][0]["Results"]
            codice = {p.get("acronimo"): n for n, p in roster.items()}
            for x in ris:
                n = codice.get(x["Driver"].get("code"))
                if n:
                    pista[n] = int(x["position"])
            luogo = gp["circuito"]
    except Exception as e:
        print("  F1: dati 2025 non disponibili:", e)
    maxf = max(forma.values(), default=1) or 1
    maxc = max(pts_camp.values(), default=1) or 1
    righe = []
    for n, p in roster.items():
        if n not in pos_camp:
            continue
        pf = forma.get(n, 0) / (PTS[0] * len(passati) or 1)
        pc = pts_camp[n] / maxc
        pp = punti_pos(pista[n]) / PTS[0] if n in pista else NEUTRO
        righe.append({"numero": n, "nome": p["nome"], "team": p["team"], "indice": indice(pf, pc, pp),
                      "motivi": motivi(vitt.get(n, 0), podi.get(n, 0), len(passati), pos_camp[n], pts_camp[n], pista.get(n), luogo)})
    return finale(gp["nome"], gp["circuito"], righe, next(s["inizio"] for s in gp["sessioni"] if s["nome"] == "Gara"))


def moto():
    cal = json.loads((DATA / "motogp.json").read_text())["weekend"]
    if not cal:
        return None
    w = cal[0]
    piloti = {i: p for i, p in json.loads((DATA / "motogp-piloti.json").read_text()).items() if p["categoria"] == "MotoGP"}
    pts_camp = {i: p["punti"] for i, p in piloti.items()}
    forma, vitt, podi, n_gare = {}, {}, {}, 0
    tutte = sorted({g["gp"] for p in piloti.values() for g in p["gare"]}, key=lambda gp: max(g["data"] for p in piloti.values() for g in p["gare"] if g["gp"] == gp))[-5:]
    for gp in tutte:
        n_gare += 1
        for i, p in piloti.items():
            g = next((x for x in p["gare"] if x["gp"] == gp), None)
            pos = g["gara"] if g else None
            forma[i] = forma.get(i, 0) + punti_pos(pos)
            vitt[i] = vitt.get(i, 0) + (pos == 1)
            podi[i] = podi.get(i, 0) + (bool(pos) and pos <= 3)
    pista = {}
    try:
        s25 = next(x for x in bm.api("results/seasons") if x["year"] == 2025)["id"]
        cat = next(x["id"] for x in bm.api("results/categories", seasonUuid=s25) if x["name"].replace("™", "") == "MotoGP")
        e25 = next((e for e in bm.api("results/events", seasonUuid=s25, isFinished="true") if bm.nome_gp_moto(e.get("name"), (e.get("country") or {}).get("name")) == w["nome"]), None)
        if e25:
            rac = next(q for q in bm.api_cache("results/sessions", eventUuid=e25["id"], categoryUuid=cat) if q["type"] == "RAC")
            for x in bm.api_cache(f"results/session/{rac['id']}/classification", test="false")["classification"]:
                if x.get("position"):
                    pista[x["rider"]["id"]] = x["position"]
    except Exception as e:
        print("  MotoGP: dati 2025 non disponibili:", e)
    maxc = max(pts_camp.values(), default=1) or 1
    righe = []
    for i, p in piloti.items():
        pp = punti_pos(pista[i]) / PTS[0] if i in pista else NEUTRO
        righe.append({"id": i, "nome": p["nome"], "team": p["team"], "indice": indice(forma.get(i, 0) / (PTS[0] * (n_gare or 1)), pts_camp[i] / maxc, pp),
                      "motivi": motivi(vitt.get(i, 0), podi.get(i, 0), n_gare, p["pos"], pts_camp[i], pista.get(i), w["nome"])})
    gara = next((s for s in w["sessioni"] if s["codice"] == "RAC"), w["sessioni"][-1])
    return finale(w["nome"], w["circuito"], righe, gara["inizio"])


def finale(gp, circuito, righe, inizio):
    righe.sort(key=lambda r: -r["indice"])
    top = righe[0]["indice"] or 1
    for r in righe:
        r["indice"] = round(100 * r["indice"] / top)
    return {"gp": gp, "circuito": circuito, "gara": inizio, "favoriti": righe[:5]}


def main():
    out = {"aggiornato": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "metodo": "Indice da 0 a 100 calcolato da GP Oggi: 45% forma nelle ultime 5 gare, 35% classifica del campionato, 20% risultato sullo stesso circuito l'anno scorso. È un'opinione basata sui numeri, non una previsione ufficiale né una certezza.",
           "f1": f1(), "motogp": moto()}
    (DATA / "pronostici.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for k in ("f1", "motogp"):
        if out[k]:
            print(k, out[k]["gp"], [(r["nome"], r["indice"]) for r in out[k]["favoriti"]])


if __name__ == "__main__":
    main()
