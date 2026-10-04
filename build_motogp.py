"""Calendario MotoGP per il conto alla rovescia: docs/data/motogp.json.

Legge il calendario pubblico del campionato (stesso servizio usato dal sito ufficiale, senza chiave) e salva solo
i weekend non ancora conclusi con le sessioni della classe MotoGP, in orario UTC. Nessun risultato, nessuna foto.
Prova in locale:  python build_motogp.py --prova
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

URL = "https://api.motogp.pulselive.com/motogp/v1/events"
FILE = Path(__file__).parent / "docs" / "data" / "motogp.json"
PAESI = {"United Kingdom of Great Britain and Northern Ireland": "Regno Unito", "Indonesia": "Indonesia", "Australia": "Australia", "Malaysia": "Malesia", "Qatar": "Qatar", "Portugal": "Portogallo",
         "Spain": "Spagna", "Italy": "Italia", "France": "Francia", "Germany": "Germania", "Netherlands": "Paesi Bassi",
         "United Kingdom": "Regno Unito", "Austria": "Austria", "Czechia": "Repubblica Ceca", "Hungary": "Ungheria",
         "San Marino": "San Marino", "Japan": "Giappone", "Thailand": "Thailandia", "India": "India",
         "United States": "Stati Uniti", "Argentina": "Argentina", "Brazil": "Brasile", "Kazakhstan": "Kazakistan",
         "Turkey": "Turchia", "Finland": "Finlandia"}
SESSIONI = {"FP1": "Prove libere 1", "FP2": "Prove libere 2", "PR": "Prove libere", "Q1": "Qualifiche 1", "Q2": "Qualifiche 2",
            "SPR": "Sprint", "WUP": "Warm up", "RAC": "Gara"}


GP_MOTO = {"THAILAND": "Thailandia", "BRAZIL": "Brasile", "UNITED STATES": "Stati Uniti", "SPAIN": "Spagna", "FRANCE": "Francia", "CATALONIA": "Catalogna",
           "ITALY": "Italia", "HUNGARY": "Ungheria", "CZECHIA": "Repubblica Ceca", "NETHERLANDS": "Paesi Bassi", "GERMANY": "Germania", "GREAT BRITAIN": "Gran Bretagna",
           "ARAGON": "Aragona", "SAN MARINO": "San Marino", "AUSTRIA": "Austria", "JAPAN": "Giappone", "INDONESIA": "Indonesia", "AUSTRALIA": "Australia",
           "MALAYSIA": "Malesia", "QATAR": "Qatar", "PORTUGAL": "Portogallo", "VALENCIA": "Valencia", "ARGENTINA": "Argentina", "AMERICAS": "delle Americhe"}


def nome_gp_moto(nome_evento, country=None):
    """'PETRONAS GRAND PRIX OF MALAYSIA' -> 'GP Malesia' (il nome della gara, non solo il paese: la Spagna ne ospita piu' d'una)."""
    import re
    m = re.search(r"GRAND PRIX (?:OF|DE)\s+(?:THE\s+)?(.+?)\s*$", (nome_evento or "").upper())
    chiave = m.group(1).strip() if m else ""
    if chiave in GP_MOTO:
        return f"GP {GP_MOTO[chiave]}"
    return f"GP {PAESI.get(country, country or chiave.title())}"


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


CACHE = Path(__file__).parent / "cache" / "motogp"


def api_cache(percorso, **p):
    """Le gare gia' concluse non cambiano: si salvano in cache e non si riscaricano."""
    import hashlib
    f = CACHE / (hashlib.md5(f"{percorso}{sorted(p.items())}".encode()).hexdigest() + ".json")
    if f.exists():
        return json.loads(f.read_text())
    time.sleep(0.3)
    d = api(percorso, **p)
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(d))
    return d


def riga_rider(x):
    r = x["rider"]
    return {"id": r["id"], "nome": r["full_name"], "numero": r.get("number"), "paese": paese(r.get("country")), "team": x["team"]["name"], "moto": x["constructor"]["name"], "riders_id": r.get("riders_id")}


def classifica_e_ultima():
    """Classifiche piloti di MotoGP, Moto2 e Moto3, ultima gara e risultati di ogni gara per le schede dei piloti."""
    anno = datetime.now(timezone.utc).year
    stagione = next(x for x in api("results/seasons") if x["year"] == anno)["id"]
    categorie = {x["name"].replace("\u2122", ""): x["id"] for x in api("results/categories", seasonUuid=stagione)}
    eventi = [e for e in api("results/events", seasonUuid=stagione, isFinished="true") if not e.get("test")]
    eventi.sort(key=lambda e: e["date_start"])
    out_class, ultime, piloti = {}, {}, {}
    for nome, cat in categorie.items():
        cl = api("results/standings", seasonUuid=stagione, categoryUuid=cat)["classification"]
        out_class[nome] = [{"pos": x["position"], **riga_rider(x), "punti": x["points"], "vittorie": x.get("race_wins", 0)} for x in cl]
        for x in cl:
            piloti[x["rider"]["id"]] = {**riga_rider(x), "categoria": nome, "pos": x["position"], "punti": x["points"], "vittorie": x.get("race_wins", 0), "gare": []}
        for e in eventi:
            sess = api_cache("results/sessions", eventUuid=e["id"], categoryUuid=cat)
            nome_gp = nome_gp_moto(e.get("name"), (e.get("country") or {}).get("name"))
            ris_gara = {}
            for tipo in ("SPR", "RAC"):
                sd = next((q for q in sess if q["type"] == tipo), None)
                if not sd:
                    continue
                try:
                    cls = api_cache(f"results/session/{sd['id']}/classification", test="false")["classification"]
                except Exception:
                    continue
                if tipo == "RAC":
                    ris_gara = cls
                for x in cls:
                    p = piloti.get(x["rider"]["id"])
                    if p is None:
                        piloti[x["rider"]["id"]] = p = {**riga_rider(x), "categoria": nome, "pos": None, "punti": 0, "vittorie": 0, "gare": []}
                    voce = next((g for g in p["gare"] if g["gp"] == nome_gp), None)
                    if voce is None:
                        voce = {"gp": nome_gp, "data": e["date_end"], "sprint": None, "gara": None, "stato_gara": None, "punti": 0}
                        p["gare"].append(voce)
                    voce["sprint" if tipo == "SPR" else "gara"] = x["position"]
                    if tipo == "RAC":
                        voce["stato_gara"] = x.get("status")
                    voce["punti"] += x.get("points") or 0
            if e is eventi[-1] and ris_gara:
                ultime[nome] = {"nome": nome_gp, "circuito": (e.get("circuit") or {}).get("name"), "data": e["date_end"],
                                "risultati": [{"pos": x["position"], **{k: v for k, v in riga_rider(x).items() if k != "id"}, "tempo": x.get("time"), "distacco": (x.get("gap") or {}).get("first"),
                                               "giri": x.get("total_laps"), "stato": x.get("status"), "punti": x.get("points")} for x in ris_gara]}
    for p in piloti.values():
        p["gare"].sort(key=lambda g: g["data"])
    return {"categorie": out_class, "piloti": out_class.get("MotoGP", [])}, {"categorie": ultime, **(ultime.get("MotoGP") or {})}, piloti


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
        weekend.append({"nome": nome_gp_moto(e.get("name"), paese), "circuito": (e.get("circuit") or {}).get("name"), "paese": PAESI.get(paese, paese),
                        "sessioni": sorted(sess, key=lambda s: s["inizio"])})
    if "--prova" in sys.argv:
        for w in weekend[:2]:
            print(w["nome"], w["circuito"])
            for s in w["sessioni"]:
                print("  ", s["inizio"], s["nome"])
        return
    FILE.write_text(json.dumps({"generato_il": ora.isoformat(timespec="seconds"), "weekend": weekend}, ensure_ascii=False, indent=1))
    try:
        classifica, ultima, piloti = classifica_e_ultima()
        (FILE.parent / "motogp-classifica.json").write_text(json.dumps(classifica, ensure_ascii=False, separators=(",", ":")))
        (FILE.parent / "motogp-ultima.json").write_text(json.dumps(ultima, ensure_ascii=False, separators=(",", ":")))
        (FILE.parent / "motogp-piloti.json").write_text(json.dumps(piloti, ensure_ascii=False, separators=(",", ":")))
        print(f"MotoGP: {sum(len(v) for v in classifica['categorie'].values())} piloti in classifica, {len(piloti)} schede")
    except Exception as e:  # la classifica e' un di piu': se la fonte non risponde si lasciano i file com'erano
        print("MotoGP: classifica non aggiornata:", e)
    print(f"MotoGP: {len(weekend)} weekend in programma")


if __name__ == "__main__":
    main()
