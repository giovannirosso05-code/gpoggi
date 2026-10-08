"""Salva l'ora di partenza di ogni gara (F1 e MotoGP) in docs/data/gara-orari.json, per chiudere i voti del pronostico a quell'ora.
Le gare già salvate restano: dopo la gara l'ora non esce più dal calendario."""
import json, re
from pathlib import Path

DATA = Path(__file__).parent / "docs" / "data"
OUT = DATA / "gara-orari.json"


def chiave_moto(nome):
    return "m" + re.sub(r"\W", "", nome, flags=re.ASCII)[:38]


def main():
    orari = json.loads(OUT.read_text()) if OUT.exists() else {}
    for g in json.loads((DATA / "events.json").read_text()):
        gara = next((s for s in g["sessioni"] if s.get("tipo") == "Race" or s["nome"] == "Gara"), None)
        if gara:
            orari[str(g["id"])] = gara["inizio"]
        quali = next((s for s in g["sessioni"] if s.get("tipo") == "Qualifying"), None)
        if quali:
            orari["q:" + str(g["id"])] = quali["inizio"]
    mp = DATA / "motogp.json"
    if mp.exists():
        for w in json.loads(mp.read_text())["weekend"]:
            gara = next((s for s in w["sessioni"] if s["nome"] == "Gara"), None)
            if gara:
                orari[chiave_moto(w["nome"])] = gara["inizio"]
            quali = next((s for s in w["sessioni"] if s["nome"] in ("Qualifiche 1", "Qualifiche")), None)
            if quali:
                orari["q:" + chiave_moto(w["nome"])] = quali["inizio"]
    OUT.write_text(json.dumps(dict(sorted(orari.items())), ensure_ascii=False, indent=1))
    print(f"{len(orari)} orari di gara salvati")


if __name__ == "__main__":
    main()
