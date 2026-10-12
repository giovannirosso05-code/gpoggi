"""Statistiche di stagione per F1 e MotoGP -> docs/data/statistiche.json, calcolate solo dai dati gia' salvati (risultati, griglie, giri).
Per pilota: gare, vittorie, podi, pole, giri veloci, ritiri, giri percorsi, gare a punti, posizione media, posizioni guadagnate tra griglia e arrivo.
Per coppie di compagni: testa a testa in qualifica e in gara.
Non ci sono sorpassi veri ne' giri in testa (servono le posizioni giro per giro) e nemmeno le cadute (i dati ufficiali dicono solo 'ritirato').
Prova:  python build_statistiche.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

D = Path(__file__).parent / "docs" / "data"


def nuovo(nome, team, extra):
    return {"nome": nome, "team": team, **extra, "gare": 0, "vittorie": 0, "podi": 0, "pole": 0, "giri_veloci": 0, "ritiri": 0, "giri": 0,
            "a_punti": 0, "somma_pos": 0, "classificati": 0, "guadagno": 0, "gare_griglia": 0, "rimonta": None, "crollo": None}


RITIRO = ("RIT", "OUTSTND", "NOTFINISHFIRST")   # F1 e MotoGP: ritirato (anche chi e' classificato ma si e' fermato prima della fine)


def registra(S, r, gara_nome, punti_fino, griglia, extra):
    if r.get("stato") == "NP":   # non partito: non conta come gara
        return None
    p = S.setdefault(r["nome"], nuovo(r["nome"], r["team"], extra))
    p["team"] = r["team"]
    p["gare"] += 1
    p["giri"] += r.get("giri") or 0
    pos = r.get("pos")
    if pos is None or r.get("stato") in RITIRO:
        p["ritiri"] += 1
    if pos is not None:
        p["classificati"] += 1
        p["somma_pos"] += pos
        p["vittorie"] += pos == 1
        p["podi"] += pos <= 3
        p["a_punti"] += pos <= punti_fino
        if griglia:
            d = griglia - pos
            p["guadagno"] += d
            p["gare_griglia"] += 1
            if p["rimonta"] is None or d > p["rimonta"]["posizioni"]:
                p["rimonta"] = {"posizioni": d, "gara": gara_nome, "da": griglia, "a": pos}
            if p["crollo"] is None or d < p["crollo"]["posizioni"]:
                p["crollo"] = {"posizioni": d, "gara": gara_nome, "da": griglia, "a": pos}
    return p


def testa_a_testa(H, per_team, colori, marche=None):
    """per_team: {team: [(nome, q, g), ...]} di una gara: confronta i due compagni."""
    for team, lista in per_team.items():
        if len(lista) != 2:
            continue
        (n1, q1, g1), (n2, q2, g2) = lista
        a, b = sorted([(n1, q1, g1), (n2, q2, g2)], key=lambda x: x[0])
        k = f"{a[0]}|{b[0]}"
        h = H.setdefault(k, {"team": team, "colore": colori.get(team), "a": a[0], "b": b[0], "q_a": 0, "q_b": 0, "g_a": 0, "g_b": 0})
        h["team"] = team
        if marche and marche.get(team):
            h["moto"] = marche[team]
        for ok, (x, y) in (("q", (a[1], b[1])), ("g", (a[2], b[2]))):
            if x is not None and (y is None or x < y):
                h[ok + "_a"] += 1
            elif y is not None and (x is None or y < x):
                h[ok + "_b"] += 1


def f1():
    S, H = {}, {}
    colori = {c["team"]: c["colore"] for c in json.load(open(D / "standings.json"))["costruttori"]}
    cols_p = {p["nome"]: p["colore"] for p in json.load(open(D / "standings.json"))["piloti"]}
    n_gare = 0
    for f in sorted(D.glob("gare/*.json")):
        g = json.load(open(f))
        sess = {s["tipo"]: s for s in g["sessioni"] if s.get("risultati")}
        gara = sess.get("Race")
        if not gara:
            continue
        n_gare += 1
        cron = D / "cronaca" / f"{f.stem}.json"
        cj = json.load(open(cron)) if cron.exists() else {}
        griglia = cj.get("griglia") or {}
        q = {r["numero"]: r.get("pos") for r in (sess.get("Qualifying") or {}).get("risultati", [])}
        per_team = {}
        for r in gara["risultati"]:
            p = registra(S, r, g["nome"], 10, griglia.get(str(r["numero"])), {"numero": r["numero"], "colore": cols_p.get(r["nome"]) or colori.get(r["team"])})
            if p is None:
                continue
            if q.get(r["numero"]) == 1:
                p["pole"] += 1
            per_team.setdefault(r["team"], []).append((r["nome"], q.get(r["numero"]), r.get("pos")))
        testa_a_testa(H, per_team, colori)
    for p in S.values():
        p["giri_veloci"] = None   # nei dati di F1 il giro veloce c'e' solo per l'ultima gara: meglio non mostrare un conteggio falso
    return {"gare": n_gare, "piloti": sorted(S.values(), key=lambda p: (-p["vittorie"], -p["podi"], p["nome"])), "compagni": list(H.values())}


def motogp():
    S, H = {}, {}
    gare = json.load(open(D / "motogp-gare.json"))
    n_gare = 0
    for nome, g in sorted(gare.items(), key=lambda kv: kv[1]["data"]):
        c = g["classifiche"]
        if not c.get("MotoGP"):
            continue
        n_gare += 1
        q = {x["nome"]: x["pos"] for x in c.get("MotoGP qualifiche", [])}
        per_team = {}
        for r in c["MotoGP"]:
            p = registra(S, r, nome, 15, r.get("griglia"), {"numero": r.get("numero"), "moto": r["moto"]})
            if p is None:
                continue
            if g.get("pole") is not None and g["pole"] == r.get("numero"):
                p["pole"] += 1
            if g.get("giro_veloce") is not None and g["giro_veloce"] == r.get("numero"):
                p["giri_veloci"] += 1
            per_team.setdefault(r["team"], []).append((r["nome"], q.get(r["nome"]), r.get("pos")))
        testa_a_testa(H, per_team, {}, {r["team"]: r["moto"] for r in c["MotoGP"]})
    return {"gare": n_gare, "piloti": sorted(S.values(), key=lambda p: (-p["vittorie"], -p["podi"], p["nome"])), "compagni": list(H.values())}


def main():
    out = {"generato_il": datetime.now(timezone.utc).isoformat(timespec="seconds"), "f1": f1(), "motogp": motogp()}
    (D / "statistiche.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    for k in ("f1", "motogp"):
        v = out[k]
        print(k, v["gare"], "gare,", len(v["piloti"]), "piloti,", len(v["compagni"]), "coppie")
        top = max(v["piloti"], key=lambda p: p["ritiri"])
        print("  piu' ritiri:", top["nome"], top["ritiri"], "| piu' giri:", max(v["piloti"], key=lambda p: p["giri"])["nome"])


if __name__ == "__main__":
    main()
