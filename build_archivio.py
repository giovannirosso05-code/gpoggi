"""Archivio storico della Formula 1 dal 1950: classifiche finali, vincitori di ogni gara e schede dei piloti storici.

Fonte: Jolpica F1 (continuazione di Ergast), dati CC BY-NC-SA 4.0, uso non commerciale.
Scrive docs/data/archivio/<anno>.json, docs/data/archivio/indice.json e docs/data/storici.json.
Le stagioni gia' scritte non si riscaricano (si rifa solo l'anno appena concluso): python build_archivio.py [anno_iniziale]
"""
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from scraper_f1 import nome_gp

ROOT = Path(__file__).parent
OUT = ROOT / "docs" / "data" / "archivio"
CACHE = ROOT / "cache" / "jolpica"
BASE = "https://api.jolpi.ca/ergast/f1"
HEADERS = {"User-Agent": "GPOggiBot/1.0 (+https://gpoggi.it; progetto non commerciale)"}
NAZ = {"Italian": "Italia", "British": "Regno Unito", "German": "Germania", "French": "Francia", "Spanish": "Spagna", "Brazilian": "Brasile",
       "Finnish": "Finlandia", "Dutch": "Paesi Bassi", "Australian": "Australia", "Austrian": "Austria", "American": "Stati Uniti",
       "Argentine": "Argentina", "Belgian": "Belgio", "Canadian": "Canada", "Swiss": "Svizzera", "Swedish": "Svezia", "Japanese": "Giappone",
       "Mexican": "Messico", "Monegasque": "Monaco", "Danish": "Danimarca", "Thai": "Thailandia", "Chinese": "Cina", "New Zealander": "Nuova Zelanda",
       "South African": "Sudafrica", "Colombian": "Colombia", "Venezuelan": "Venezuela", "Polish": "Polonia", "Russian": "Russia",
       "Portuguese": "Portogallo", "Irish": "Irlanda", "Hungarian": "Ungheria", "Indian": "India", "Czech": "Repubblica Ceca",
       "Indonesian": "Indonesia", "Uruguayan": "Uruguay", "Chilean": "Cile", "Liechtensteiner": "Liechtenstein", "Rhodesian": "Rhodesia",
       "East German": "Germania Est", "Malaysian": "Malesia", "Argentinian": "Argentina", "Argentine-Italian": "Argentina", "Estonian": "Estonia"}


def get(percorso, **params):
    chiave = hashlib.md5(f"{percorso}{sorted(params.items())}".encode()).hexdigest()
    f = CACHE / f"{chiave}.json"
    if f.exists():
        return json.loads(f.read_text())
    for tentativo in range(8):
        time.sleep(0.5)
        r = requests.get(f"{BASE}/{percorso}", params=params, headers=HEADERS, timeout=40)
        if r.status_code == 200:
            CACHE.mkdir(parents=True, exist_ok=True)
            dati = r.json()["MRData"]
            f.write_text(json.dumps(dati))
            return dati
        if r.status_code == 429:
            time.sleep(5 * (tentativo + 1))
            continue
        r.raise_for_status()
    raise RuntimeError(f"Jolpica non risponde su {percorso}")


def nome(d):
    return f"{d['givenName']} {d['familyName']}".strip()


def stagione(anno):
    sp = get(f"{anno}/driverstandings.json", limit=100)["StandingsTable"]["StandingsLists"]
    if not sp:
        return None
    piloti = []
    for x in sp[0]["DriverStandings"]:
        d = x["Driver"]
        piloti.append({"pos": int(x["position"]) if str(x.get("position", "")).isdigit() else None, "id": d["driverId"], "nome": nome(d),
                       "naz": NAZ.get(d.get("nationality"), d.get("nationality")), "team": " / ".join(c["name"] for c in x.get("Constructors", [])),
                       "punti": float(x["points"]), "vittorie": int(x["wins"])})
    cs = get(f"{anno}/constructorstandings.json", limit=100)["StandingsTable"]["StandingsLists"]
    costruttori = [{"pos": int(x["position"]) if str(x.get("position", "")).isdigit() else None, "team": x["Constructor"]["name"], "punti": float(x["points"]),
                    "vittorie": int(x["wins"])} for x in (cs[0]["ConstructorStandings"] if cs else [])]
    gare = []
    for r in get(f"{anno}/results/1.json", limit=100)["RaceTable"]["Races"]:
        w = r["Results"][0] if r.get("Results") else None
        if w:
            gare.append({"round": int(r["round"]), "nome": nome_gp(r["raceName"]), "data": r["date"], "circuito": r["Circuit"]["circuitName"],
                         "vincitore": nome(w["Driver"]), "id": w["Driver"]["driverId"], "team": w["Constructor"]["name"]})
    return {"anno": anno, "campione": next((p for p in piloti if p["pos"] == 1), None), "piloti": piloti, "costruttori": costruttori, "gare": gare}


def main():
    ultimo = datetime.now(timezone.utc).year - 1
    inizio = int(sys.argv[1]) if len(sys.argv) > 1 else 1950
    OUT.mkdir(parents=True, exist_ok=True)
    for anno in range(inizio, ultimo + 1):
        f = OUT / f"{anno}.json"
        if f.exists() and anno != ultimo:
            continue
        s = stagione(anno)
        if s:
            f.write_text(json.dumps(s, ensure_ascii=False, separators=(",", ":")))
            print(anno, len(s["piloti"]), "piloti,", len(s["gare"]), "gare")
    # indice delle stagioni e schede dei piloti storici
    indice, piloti = [], {}
    for anno in range(1950, ultimo + 1):
        f = OUT / f"{anno}.json"
        if not f.exists():
            continue
        s = json.loads(f.read_text())
        c = s["campione"]
        cc = next((x for x in s["costruttori"] if x["pos"] == 1), None)
        indice.append({"anno": anno, "campione": c["nome"] if c else None, "team": c["team"] if c else None, "costruttori": cc["team"] if cc else None, "gare": len(s["gare"])})
        for p in s["piloti"]:
            sch = piloti.setdefault(p["id"], {"id": p["id"], "nome": p["nome"], "naz": p["naz"], "stagioni": [], "titoli": 0, "vittorie": 0, "migliore": None, "team": []})
            sch["stagioni"].append(anno)
            sch["titoli"] += 1 if p["pos"] == 1 else 0
            sch["vittorie"] += p["vittorie"]
            if p["pos"] and (sch["migliore"] is None or p["pos"] < sch["migliore"]):
                sch["migliore"] = p["pos"]
            for t in p["team"].split(" / "):
                if t and t not in sch["team"]:
                    sch["team"].append(t)
    (OUT / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, separators=(",", ":")))
    elenco = sorted(piloti.values(), key=lambda p: (-p["titoli"], -p["vittorie"], p["nome"]))
    (ROOT / "docs" / "data" / "storici.json").write_text(json.dumps({"fonte": "Jolpica F1 (CC BY-NC-SA 4.0)", "piloti": elenco}, ensure_ascii=False, separators=(",", ":")))
    print(f"Archivio: {len(indice)} stagioni, {len(elenco)} piloti")


if __name__ == "__main__":
    main()
