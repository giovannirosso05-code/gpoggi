"""Classifica di ogni sessione MotoGP (prove, qualifiche, sprint, gara) del weekend in corso e dell'ultimo concluso.

Serve al bot Telegram (/sessionerisultati): l'altro file dei dati, motogp-gare.json, tiene solo gara e sprint dei GP finiti.
Fonte: la stessa API ufficiale usata da build_motogp.py. Scrive docs/data/motogp-sessioni.json.
Uso: python build_motogp_sessioni.py
"""
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import build_motogp as bm

DATA = Path(__file__).parent / "docs" / "data"
NOMI = {"FP1": "Prove libere 1", "PR": "Practice", "FP2": "Prove libere 2", "Q1": "Qualifiche 1", "Q2": "Qualifiche 2", "SPR": "Sprint", "WUP": "Warm up", "RAC": "Gara"}


def codice(s):
    t, n = s.get("type"), s.get("number")
    return f"{t}{n}" if t in ("FP", "Q") and n else t


def tempo(t):
    """'01:30.132' -> '1:30.132'"""
    return re.sub(r"^0(\d:)", r"\1", t) if isinstance(t, str) else t


def riga(x, gara):
    r = x.get("rider") or {}
    return {"pos": x.get("position"), "nome": r.get("full_name"), "numero": r.get("number"), "team": (x.get("team") or {}).get("name"),
            "tempo": tempo(x.get("time") if gara else (x.get("best_lap") or {}).get("time")),
            "distacco": (x.get("gap") or {}).get("first"), "giri": x.get("total_laps"), "stato": x.get("status")}


def main():
    anno = datetime.now(timezone.utc).year
    stagione = next(x for x in bm.api("results/seasons") if x["year"] == anno)["id"]
    cat = next(x["id"] for x in bm.api("results/categories", seasonUuid=stagione) if x["name"].replace("™", "") == "MotoGP")
    eventi = sorted((e for e in bm.api("results/events", seasonUuid=stagione) if not e.get("test")), key=lambda e: e["date_start"])
    corrente = [e for e in eventi if e.get("status") == "CURRENT"]
    finiti = [e for e in eventi if e.get("status") == "FINISHED"]
    scelti = (finiti[-1:] if finiti else []) + corrente[:1]
    # gli orari veri (UTC) stanno nel calendario già costruito: l'API dà l'ora locale con un fuso sbagliato
    cal = {}
    try:
        for w in json.load(open(DATA / "motogp.json"))["weekend"]:
            cal[w["nome"]] = {s["codice"]: s for s in w["sessioni"]}
    except Exception:
        pass
    out = []
    for e in scelti:
        nome = bm.nome_gp_moto(e.get("name"), (e.get("country") or {}).get("name"))
        sessioni = []
        for s in bm.api("results/sessions", eventUuid=e["id"], categoryUuid=cat):
            cod = codice(s)
            if cod not in NOMI or s.get("status") != "FINISHED":
                continue
            time.sleep(0.3)
            try:
                cl = bm.api(f"results/session/{s['id']}/classification", test="false")["classification"]
            except Exception as errore:
                print(f"  {nome} {cod}: classifica non disponibile ({errore})")
                continue
            if not cl:
                continue
            sessioni.append({"nome": NOMI[cod], "codice": cod, "inizio": (cal.get(nome, {}).get(cod) or {}).get("inizio"), "risultati": [riga(x, cod in ("RAC", "SPR")) for x in cl]})
        out.append({"nome": nome, "stato": e.get("status"), "sessioni": sessioni})
    (DATA / "motogp-sessioni.json").write_text(json.dumps({"generato_il": datetime.now(timezone.utc).isoformat(timespec="seconds"), "weekend": out}, ensure_ascii=False, indent=1))
    print("MotoGP sessioni:", [(w["nome"], [s["codice"] for s in w["sessioni"]]) for w in out])


if __name__ == "__main__":
    main()
