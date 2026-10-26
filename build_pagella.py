"""La pagella del weekend: voto a ogni pilota dell'ultimo weekend concluso di F1 e di MotoGP -> docs/data/pagella.json.

Il voto e' di GP Oggi: parte da un calcolo sui risultati ufficiali, che la redazione puo' correggere dichiarandolo. Metodo (scritto anche nella pagina del sito):
- ogni sessione vale un voto da posizione: 1° = 10, 2° = 8,5, 3° = 8, 4° = 7,5, 5° = 7, 6° = 6,5, poi si scende (7° 6,2 ... 10° 5,6, poi -0,15 a posizione, minimo 4);
- in gara si aggiungono 0,1 per ogni posizione guadagnata sulla griglia di partenza ufficiale (da -1 a +1,5, mai sopra 10);
- chi si ritira, o non ha un tempo, prende 4,5 in quella sessione (fino al 25 ottobre 2026 era 3: troppo severo, il ritiro non è sempre colpa del pilota);
- peso: qualifica 20%, sprint 20%, gara 60%. Arrotondato al mezzo voto.
- la redazione puo' correggere un voto con un motivo scritto (docs/data/pagella-correzioni.json): la pagina del sito la mostra sempre.
Prova:  python build_pagella.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

D = Path(__file__).parent / "docs" / "data"
PESI = {"q": 0.2, "s": 0.2, "g": 0.6}
RITIRO = 4.5   # ritiro o nessun tempo (era 3: troppo duro, la causa spesso non è del pilota)
TABELLA = {1: 10, 2: 8.5, 3: 8, 4: 7.5, 5: 7, 6: 6.5, 7: 6.2, 8: 6, 9: 5.8, 10: 5.6}


def da_posizione(p):
    if p is None:
        return RITIRO
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


import re


def fatti_cronaca(righe, voci):
    """Dalla cronaca giro per giro: sorpassi fatti e giro del ritiro di ogni pilota (solo quello che c'e' scritto)."""
    def trova(tok):
        m = [r for r in righe if r["nome"] == tok] or [r for r in righe if r["nome"].split()[-1] == tok]
        return m[0] if len(m) == 1 else None
    for r in righe:
        r["sorpassi"], r["ritiro_giro"] = 0, None
    for v in voci or []:
        t = v.get("testo", "")
        m = re.match(r"\*\*(.+?) supera ", t)
        if v.get("tipo") == "sorpasso" and m and trova(m.group(1)):
            trova(m.group(1))["sorpassi"] += 1
        m = re.match(r"\*\*(.+?) si ritira", t)
        if v.get("tipo") == "ritiro" and m and trova(m.group(1)):
            trova(m.group(1))["ritiro_giro"] = v.get("giro")


def perche(r, sprint):
    """Le ragioni del voto, solo da fatti verificabili nei dati (posizioni, griglia, cronaca). Frasi brevi, da dire a voce."""
    out = []
    g, q, s, gr = r["g"], r["q"], r["s"], r.get("griglia")
    if g is None:
        out.append(f"si è ritirato al giro {r['ritiro_giro']}" if r.get("ritiro_giro") else "non ha visto la bandiera a scacchi")
    else:
        guad = (gr - g) if gr else 0
        if guad >= 8: out.append(f"ha recuperato {guad} posizioni sulla griglia")
        elif guad >= 3: out.append(f"ha guadagnato {guad} posizioni sulla griglia")
        elif guad <= -3: out.append(f"ha perso {-guad} posizioni rispetto alla griglia")
        pos = [x for x in (q, s if sprint else None, g) if x is not None]
        if len(pos) == 3 and max(pos) - min(pos) <= 2 and guad > -3: out.append("è stato costante in tutte le sessioni")
        if r.get("sorpassi", 0) >= 2: out.append(f"ha fatto {r['sorpassi']} sorpassi")
        if sprint and s is None: out.append("è uscito nella sprint")
        if q is None: out.append("non ha firmato un tempo in qualifica")
        if g == 1 and q == 1 and (not sprint or s == 1): out.append("ha vinto tutto, dalla qualifica alla gara")
        elif g == 1: out.append("ha vinto la gara")
        elif g <= 3: out.append("è salito sul podio")
    if not out:
        out.append(("ha chiuso dove era partito" if r["g"] == r.get("griglia") else "ha chiuso a un passo dalla posizione di partenza") if r["g"] is not None else "weekend senza punti")
    return out[:2]


def correggi(righe, corr):
    """Applica le correzioni della redazione (docs/data/pagella-correzioni.json): il voto cambia ma resta scritto quanto e perche'."""
    for r in righe:
        c = corr.get(r["nome"])
        if c:
            r["voto_calcolato"] = r["voto"]
            r["correzione"], r["motivo"] = c["correzione"], c["motivo"]
            r["voto_esatto"] = round(r["voto_esatto"] + c["correzione"], 2)
            r["voto"] = mezzo(min(10, r["voto_esatto"]))
    righe.sort(key=lambda r: (-r["voto_esatto"], r["g"] is None, r["g"] or 99))
    return righe


def correzioni(serie, chiave):
    try:
        return json.load(open(D / "pagella-correzioni.json")).get(serie, {}).get(str(chiave), {})
    except Exception:
        return {}


def ordinale_corto(n):
    return f"{n}°"


def note_ritiri():
    try:
        return json.load(open(D / "pagella-note.json"))
    except Exception:
        return {}


def pesa_senza_sprint(righe):
    for x in righe:   # senza sprint il peso passa a qualifica e gara
        tot = 0.25 * voto_sessione(x["q"]) + 0.75 * voto_sessione(x["g"], x.get("griglia"))
        x["voto"], x["voto_esatto"] = mezzo(tot), round(tot, 2)
    righe.sort(key=lambda x: -x["voto_esatto"])


def f1_evento(g, gara, id_):
    sess = {s["tipo"]: s for s in g["sessioni"] if s.get("risultati")}
    cron = D / "cronaca" / f"{id_}.json"
    cj = json.load(open(cron)) if cron.exists() else {}
    griglia = cj.get("griglia") or {}
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
    if not hanno_sprint:
        pesa_senza_sprint(righe)
    fatti_cronaca(righe, cj.get("voci") or [])
    cause = note_ritiri().get("f1", {}).get(g["nome"], {})
    for x in righe:
        x["perche"] = perche(x, hanno_sprint)
        x["causa"] = cause.get(x["nome"], "sconosciuta")
    righe = correggi(righe, correzioni("f1", id_))
    return {"nome": g["nome"], "id": id_, "data": gara["inizio"], "sprint": hanno_sprint, "righe": righe}


def f1_tutti():
    out = []
    for f in D.glob("gare/*.json"):
        g = json.load(open(f))
        gara = next((s for s in g["sessioni"] if s["tipo"] == "Race" and s.get("risultati")), None)
        if gara:
            out.append(f1_evento(g, gara, f.stem))
    return sorted(out, key=lambda e: e["data"])


def moto_evento(nome, g):
    c = g["classifiche"]
    hanno_sprint = bool(c.get("MotoGP sprint"))
    q = {x["nome"]: x["pos"] for x in c.get("MotoGP qualifiche", [])}
    s = {x["nome"]: x["pos"] for x in c.get("MotoGP sprint", [])}
    piloti = {}
    for x in c["MotoGP"]:
        piloti[x["nome"]] = {"nome": x["nome"], "numero": x.get("numero"), "team": x["team"], "moto": x["moto"], "q": q.get(x["nome"]),
                             "s": s.get(x["nome"]) if hanno_sprint else None, "g": x["pos"], "griglia": x.get("griglia")}
    righe = calcola(piloti)
    if not hanno_sprint:
        pesa_senza_sprint(righe)
    fatti_cronaca(righe, g.get("cronaca"))
    cause = note_ritiri().get("motogp", {}).get(nome, {})
    for x in righe:
        x["perche"] = perche(x, hanno_sprint)
        x["causa"] = cause.get(x["nome"], "sconosciuta")
    righe = correggi(righe, correzioni("motogp", nome))
    return {"nome": nome, "data": g["data"], "sprint": hanno_sprint, "righe": righe}


def moto_tutti():
    out = []
    for nome, g in json.load(open(D / "motogp-gare.json")).items():
        if g.get("classifiche", {}).get("MotoGP"):
            out.append(moto_evento(nome, g))
    return sorted(out, key=lambda e: e["data"])


def f1():
    t = f1_tutti()
    return t[-1] if t else None


def motogp():
    t = moto_tutti()
    return t[-1] if t else None


def motivo(r, sprint):
    """Una frase breve col perche' del voto, solo da fatti nei dati (posizioni, griglia, cronaca, correzioni dichiarate)."""
    g, q, s, gr = r["g"], r["q"], r["s"], r.get("griglia")
    if g is None:
        giro = f" al giro {r['ritiro_giro']}" if r.get("ritiro_giro") else ""
        base = ("Caduto" if r.get("causa") == "caduta" else "Ritirato") + giro
        if r.get("causa") == "fisico":
            base += " per il dolore alla spalla"
        elif r.get("causa") == "tecnico":
            base += " per un problema tecnico: voto da dividere con il team"
        return base
    if g == 1 and q == 1 and (not sprint or s == 1):
        t = "Pole, sprint e gara" if sprint else "Pole e vittoria"
    elif g == 1:
        t = f"Vince partendo {ordinale_corto(gr)}" if gr and gr > 1 else "Vince la gara"
    elif gr and gr - g >= 3:
        t = f"Dal {ordinale_corto(gr)} al {ordinale_corto(g)} in gara"
    elif gr and g - gr >= 3:
        t = f"Perde {g - gr} posizioni: dal {ordinale_corto(gr)} al {ordinale_corto(g)}"
    elif g <= 3:
        t = f"{ordinale_corto(g)} in gara" + (f" dopo il {ordinale_corto(q)} in qualifica" if q and q != g else "")
    else:
        t = f"{ordinale_corto(g)} in gara" + (f", {ordinale_corto(q)} in qualifica" if q else "")
    if r.get("sorpassi", 0) >= 2:
        t += f", {r['sorpassi']} sorpassi"
    if r.get("correzione"):
        t += f" ({r['motivo']})"
    return t


def riepilogo(e):
    """Per la scheda 'Voti GP Oggi' di ogni gara: top 3 (il primo e' l'MVP), flop 3 e sorpresa, ognuno con la sua frase."""
    righe, sprint = e["righe"], e["sprint"]
    voce = lambda r: {"nome": r["nome"], "team": r.get("team"), "colore": r.get("colore"), "moto": r.get("moto"), "voto": r["voto"], "perche": motivo(r, sprint)}
    top = [voce(r) for r in righe[:3]]
    # flop: i tre voti piu' bassi, a parita' prima chi parte piu' avanti (piu' strano che sia andata male)
    flop = [voce(r) for r in sorted(righe, key=lambda r: (r["voto_esatto"], r.get("griglia") or 99))[:3]]
    limite = 10 if "sorpassi" in righe[0] and e.get("id") else 15   # a punti: 10 in F1, 15 in MotoGP
    cand = [r for r in righe[1:] if r["g"] and r.get("griglia") and r["g"] <= limite and r["griglia"] - r["g"] >= 5]
    sorpresa = None
    if cand:
        r = max(cand, key=lambda r: (r["griglia"] - r["g"], r["voto_esatto"]))
        v = voce(r)
        v["perche"] = f"Dal {ordinale_corto(r['griglia'])} al {ordinale_corto(r['g'])}: {r['griglia'] - r['g']} posizioni guadagnate"
        sorpresa = v
    return {"top": top, "flop": flop, "sorpresa": sorpresa}


def main():
    f1_all, moto_all = f1_tutti(), moto_tutti()
    out = {"generato_il": datetime.now(timezone.utc).isoformat(timespec="seconds"), "f1": f1_all[-1] if f1_all else None, "motogp": moto_all[-1] if moto_all else None}
    (D / "pagella.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    # un riepilogo per ogni gara (le schede 'Voti GP Oggi' delle pagine gara)
    tutte = {"generato_il": out["generato_il"], "f1": {e["id"]: {"gp": e["nome"], **riepilogo(e)} for e in f1_all},
             "motogp": {e["nome"]: riepilogo(e) for e in moto_all}}
    (D / "pagelle.json").write_text(json.dumps(tutte, ensure_ascii=False, separators=(",", ":")))
    for k in ("f1", "motogp"):
        if out[k]:
            print(out[k]["nome"], [(r["nome"].split()[-1], r["voto"]) for r in out[k]["righe"]][:25])
    print("pagelle:", len(tutte["f1"]), "gare F1,", len(tutte["motogp"]), "gare MotoGP")


if __name__ == "__main__":
    main()
