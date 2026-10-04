"""Calendario MotoGP per il conto alla rovescia: docs/data/motogp.json.

Legge il calendario pubblico del campionato (stesso servizio usato dal sito ufficiale, senza chiave) e salva solo
i weekend non ancora conclusi con le sessioni della classe MotoGP, in orario UTC. Nessun risultato, nessuna foto.
Prova in locale:  python build_motogp.py --prova
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

URL = "https://api.motogp.pulselive.com/motogp/v1/events"
FILE = Path(__file__).parent / "docs" / "data" / "motogp.json"
PAESI = {"Indonesia": "Indonesia", "Australia": "Australia", "Malaysia": "Malesia", "Qatar": "Qatar", "Portugal": "Portogallo",
         "Spain": "Spagna", "Italy": "Italia", "France": "Francia", "Germany": "Germania", "Netherlands": "Paesi Bassi",
         "United Kingdom": "Regno Unito", "Austria": "Austria", "Czechia": "Repubblica Ceca", "Hungary": "Ungheria",
         "San Marino": "San Marino", "Japan": "Giappone", "Thailand": "Thailandia", "India": "India",
         "United States": "Stati Uniti", "Argentina": "Argentina", "Brazil": "Brasile", "Kazakhstan": "Kazakistan",
         "Turkey": "Turchia", "Finland": "Finlandia"}
SESSIONI = {"FP1": "Prove libere 1", "FP2": "Prove libere 2", "PR": "Prove libere", "Q1": "Qualifiche 1", "Q2": "Qualifiche 2",
            "SPR": "Sprint", "WUP": "Warm up", "RAC": "Gara"}


def utc(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z").astimezone(timezone.utc).isoformat(timespec="seconds")


BASE = "https://api.motogp.pulselive.com/motogp/v1"
H = {"User-Agent": "GPOggiBot/1.0 (+https://gpoggi.it; progetto non commerciale)"}


def api(percorso, **p):
    r = requests.get(f"{BASE}/{percorso}", params=p, headers=H, timeout=40)
    r.raise_for_status()
    return r.json()


def paese(c):
    return PAESI.get((c or {}).get("name"), (c or {}).get("name"))


def classifica_e_ultima():
    """Classifica piloti MotoGP e risultato dell'ultima gara disputata."""
    anno = datetime.now(timezone.utc).year
    stagione = next(x for x in api("results/seasons") if x["year"] == anno)["id"]
    cat = next(x for x in api("results/categories", seasonUuid=stagione) if x["name"].startswith("MotoGP"))["id"]
    cl = api("results/standings", seasonUuid=stagione, categoryUuid=cat)["classification"]
    piloti = [{"pos": x["position"], "nome": x["rider"]["full_name"], "numero": x["rider"].get("number"), "paese": paese(x["rider"].get("country")),
               "team": x["team"]["name"], "moto": x["constructor"]["name"], "punti": x["points"], "vittorie": x.get("race_wins", 0)} for x in cl]
    eventi = [e for e in api("results/events", seasonUuid=stagione, isFinished="true") if not e.get("test")]
    eventi.sort(key=lambda e: e["date_start"])
    ultima = None
    if eventi:
        e = eventi[-1]
        sess = api("results/sessions", eventUuid=e["id"], categoryUuid=cat)
        gara = next((s for s in sess if s["type"] == "RAC"), None)
        if gara:
            ris = api(f"results/session/{gara['id']}/classification", test="false")["classification"]
            ultima = {"nome": f"GP {PAESI.get((e.get('country') or {}).get('name'), (e.get('country') or {}).get('name') or '')}".strip(), "circuito": (e.get("circuit") or {}).get("name"),
                      "data": e["date_end"], "risultati": [{"pos": x["position"], "nome": x["rider"]["full_name"], "numero": x["rider"].get("number"), "team": x["team"]["name"],
                                                            "moto": x["constructor"]["name"], "tempo": x.get("time"), "distacco": (x.get("gap") or {}).get("first"), "giri": x.get("total_laps"),
                                                            "stato": x.get("status"), "punti": x.get("points")} for x in ris]}
    return {"aggiornata_dopo": ultima["nome"] if ultima else None, "piloti": piloti}, ultima


def main():
    r = requests.get(URL, params={"seasonYear": datetime.now(timezone.utc).year}, headers={"User-Agent": "GPOggiBot/1.0 (+https://gpoggi.it; progetto non commerciale)"}, timeout=40)
    r.raise_for_status()
    ora = datetime.now(timezone.utc)
    weekend = []
    for e in sorted(r.json(), key=lambda e: e.get("date_start") or ""):
        if e.get("test") or e.get("kind") != "GP" or not e.get("date_end"):
            continue
        sess = [{"nome": SESSIONI.get(b["shortname"], b["name"].strip()), "codice": b["shortname"], "inizio": utc(b["date_start"]), "fine": utc(b["date_end"])}
                for b in e.get("broadcasts", []) if b.get("type") == "SESSION" and (b.get("category") or {}).get("acronym") == "MGP" and b["shortname"] in SESSIONI]
        if not sess or max(s["fine"] for s in sess) < ora.isoformat(timespec="seconds"):
            continue
        paese = (e.get("circuit") or {}).get("country") or ""
        weekend.append({"nome": f"GP {PAESI.get(paese, paese)}", "circuito": (e.get("circuit") or {}).get("name"), "paese": PAESI.get(paese, paese),
                        "sessioni": sorted(sess, key=lambda s: s["inizio"])})
    if "--prova" in sys.argv:
        for w in weekend[:2]:
            print(w["nome"], w["circuito"])
            for s in w["sessioni"]:
                print("  ", s["inizio"], s["nome"])
        return
    FILE.write_text(json.dumps({"generato_il": ora.isoformat(timespec="seconds"), "weekend": weekend}, ensure_ascii=False, indent=1))
    try:
        classifica, ultima = classifica_e_ultima()
        (FILE.parent / "motogp-classifica.json").write_text(json.dumps(classifica, ensure_ascii=False, indent=1))
        if ultima:
            (FILE.parent / "motogp-ultima.json").write_text(json.dumps(ultima, ensure_ascii=False, indent=1))
        print(f"MotoGP: classifica di {len(classifica['piloti'])} piloti, ultima gara {ultima and ultima['nome']}")
    except Exception as e:  # la classifica e' un di piu': se la fonte non risponde si lasciano i file com'erano
        print("MotoGP: classifica non aggiornata:", e)
    print(f"MotoGP: {len(weekend)} weekend in programma")


if __name__ == "__main__":
    main()
