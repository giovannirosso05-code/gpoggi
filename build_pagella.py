"""La pagella del weekend: voto a ogni pilota dell'ultimo weekend concluso di F1 e di MotoGP -> docs/data/pagella.json.

Il voto e' un calcolo di GP Oggi sui risultati ufficiali, senza opinioni. Metodo (scritto anche nella pagina del sito):
- ogni sessione vale un voto da posizione: 1° = 10, 2° = 8,5, 3° = 8, 4° = 7,5, 5° = 7, 6° = 6,5, poi si scende (7° 6,2 ... 10° 5,6, poi -0,15 a posizione, minimo 4);
- in gara si aggiungono 0,1 per ogni posizione guadagnata sulla griglia di partenza ufficiale (da -1 a +1,5, mai sopra 10);
- chi si ritira, o non ha un tempo, prende 3 in quella sessione;
- peso: qualifica 20%, sprint 20%, gara 60%. Arrotondato al mezzo voto.
Prova:  python build_pagella.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

D = Path(__file__).parent / "docs" / "data"
PESI = {"q": 0.2, "s": 0.2, "g": 0.6}
TABELLA = {1: 10, 2: 8.5, 3: 8, 4: 7.5, 5: 7, 6: 6.5, 7: 6.2, 8: 6, 9: 5.8, 10: 5.6}


def da_posizione(p):
    if p is None:
        return 3.0
    return TABELLA.get(p, max(4.0, 5.6 - 0.15 * (p - 10)))


def voto_sessione(pos, griglia=None):
    v = da_posizione(pos)
    if pos is not None and griglia:
        v = min(10, v + max(-1, min(1.5, 0.1 * (griglia - pos))))
    return round(v, 2)


def mezzo(x):
    return round(x * 2) / 2


def calcola(piloti):
    """piloti: {chiave: {nome, team, colore, q, s, g, griglia}} con q/s/g = posizione o None (ritirato / senza tempo)."""
    righe = []
    for k, p in piloti.items():
        vq, vs, vg = voto_sessione(p["q"]), voto_sessione(p["s"]), voto_sessione(p["g"], p.get("griglia"))
        tot = PESI["q"] * vq + PESI["s"] * vs + PESI["g"] * vg
        righe.append({**p, "voto": mezzo(tot), "voto_esatto": round(tot, 2)})
    righe.sort(key=lambda r: (-r["voto_esatto"], r["g"] is None, r["g"] or 99))
    return righe


def f1():
    ultimo = None
    for f in D.glob("gare/*.json"):
        g = json.load(open(f))
        gara = next((s for s in g["sessioni"] if s["tipo"] == "Race" and s.get("risultati")), None)
        if gara and (ultimo is None or gara["inizio"] > ultimo[1]["inizio"]):
            ultimo = (g, gara, f.stem)
    if not ultimo:
        return None
    g, gara, id_ = ultimo
    sess = {s["tipo"]: s for s in g["sessioni"] if s.get("risultati")}
    try:
        griglia = json.load(open(D / "cronaca" / f"{id_}.json")).get("griglia") or {}
    except Exception:
        griglia = {}
    colori = {c["team"]: c["colore"] for c in json.load(open(D / "standings.json"))["costruttori"]}

    def pos(tipo):
        return {r["numero"]: r.get("pos") for r in (sess.get(tipo) or {}).get("risultati", [])}
    q, s, r = pos("Qualifying"), pos("Sprint"), pos("Race")
    hanno_sprint = "Sprint" in sess
    piloti = {}
    for x in gara["risultati"]:
        n = x["numero"]
        piloti[n] = {"nome": x["nome"], "numero": n, "team": x["team"], "colore": colori.get(x["team"], "888888"),
                     "q": q.get(n), "s": s.get(n) if hanno_sprint else None, "g": r.get(n),
                     "griglia": griglia.get(str(n))}
    righe = calcola(piloti)
    if not hanno_sprint:   # senza sprint il peso passa a qualifica e gara
        for x in righe:
            tot = 0.25 * voto_sessione(x["q"]) + 0.75 * voto_sessione(x["g"], x.get("griglia"))
            x["voto"], x["voto_esatto"] = mezzo(tot), round(tot, 2)
        righe.sort(key=lambda x: -x["voto_esatto"])
    return {"nome": g["nome"], "id": id_, "data": gara["inizio"], "sprint": hanno_sprint, "righe": righe}


def motogp():
    gare = json.load(open(D / "motogp-gare.json"))
    if not gare:
        return None
    nome, g = max(gare.items(), key=lambda kv: kv[1]["data"])
    c = g["classifiche"]
    if not c.get("MotoGP"):
        return None
    hanno_sprint = bool(c.get("MotoGP sprint"))
    q = {x["nome"]: x["pos"] for x in c.get("MotoGP qualifiche", [])}
    s = {x["nome"]: x["pos"] for x in c.get("MotoGP sprint", [])}
    piloti = {}
    for x in c["MotoGP"]:
        piloti[x["nome"]] = {"nome": x["nome"], "numero": x.get("numero"), "team": x["team"], "moto": x["moto"], "q": q.get(x["nome"]),
                             "s": s.get(x["nome"]) if hanno_sprint else None, "g": x["pos"], "griglia": x.get("griglia")}
    righe = calcola(piloti)
    if not hanno_sprint:
        for x in righe:
            tot = 0.25 * voto_sessione(x["q"]) + 0.75 * voto_sessione(x["g"], x.get("griglia"))
            x["voto"], x["voto_esatto"] = mezzo(tot), round(tot, 2)
        righe.sort(key=lambda x: -x["voto_esatto"])
    return {"nome": nome, "data": g["data"], "sprint": hanno_sprint, "righe": righe}


def main():
    out = {"generato_il": datetime.now(timezone.utc).isoformat(timespec="seconds"), "f1": f1(), "motogp": motogp()}
    (D / "pagella.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    for k in ("f1", "motogp"):
        if out[k]:
            print(out[k]["nome"], [(r["nome"].split()[-1], r["voto"]) for r in out[k]["righe"]][:25])


if __name__ == "__main__":
    main()
