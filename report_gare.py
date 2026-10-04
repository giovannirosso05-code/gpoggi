"""Scrive docs/data/report.json: un breve report per ogni gara disputata, generato dai dati (nessun testo copiato).

Ogni report, una volta scritto, non viene piu' riscritto: cosi' restano com'erano il giorno della gara.
Solo il report della gara piu' recente cita la classifica del campionato, perche' la fonte offre solo quella attuale.
"""
import json
from pathlib import Path

DATA = Path(__file__).parent / "docs" / "data"


def _gara(scheda, tipo):
    for s in scheda["sessioni"]:
        if s.get("tipo") == tipo and s.get("risultati"):
            return s
    return None


def _nome(r):
    return r.get("nome") or f"Pilota #{r['numero']}"


def crea_report(scheda, standings=None):
    gara = _gara(scheda, "Race")
    if not gara:
        return None
    ris = sorted([r for r in gara["risultati"] if r.get("pos")], key=lambda r: r["pos"])
    if not ris:
        return None
    primo = ris[0]
    paragrafi = []
    frase = f"{_nome(primo)} ({primo.get('team') or 'team n.d.'}) vince il {scheda['nome']}"
    if primo.get("tempo"):
        frase += f" in {primo['tempo']}"
    sec = [r for r in ris[1:3]]
    if sec:
        pezzi = [f"{_nome(r)} ({r['distacco']})" if r.get("distacco") else _nome(r) for r in sec]
        frase += ", davanti a " + " e a ".join(pezzi)
    paragrafi.append(frase + ".")
    quali = _gara(scheda, "Qualifying")
    if quali:
        pole = sorted([r for r in quali["risultati"] if r.get("pos")], key=lambda r: r["pos"])[:1]
        if pole:
            p = pole[0]
            testo = f"La pole position era stata di {_nome(p)}" + (f" con {p['tempo']}" if p.get("tempo") else "") + "."
            paragrafi.append(testo)
    ritirati = [_nome(r) for r in gara["risultati"] if r.get("stato") == "RIT"]
    if ritirati:
        paragrafi.append(f"Si sono ritirati {len(ritirati)} piloti: " + ", ".join(ritirati[:6]) + ("…" if len(ritirati) > 6 else "") + ".")
    if standings and standings.get("piloti"):
        lead = standings["piloti"][0]
        testo = f"Dopo la gara guida il campionato piloti {_nome(lead)} con {lead['punti']:g} punti"
        if standings.get("costruttori"):
            c = standings["costruttori"][0]
            testo += f"; tra i costruttori è primo {c['team']} con {c['punti']:g}"
        paragrafi.append(testo + ".")
    return {
        "id": scheda["id"],
        "nome": scheda["nome"],
        "circuito": scheda["circuito"],
        "paese": scheda["paese"],
        "data": scheda["fine"],
        "titolo": f"{_nome(primo)} vince il {scheda['nome']}",
        "paragrafi": paragrafi,
    }


def aggiorna_report():
    eventi = json.loads((DATA / "events.json").read_text())
    standings = json.loads((DATA / "standings.json").read_text())
    file = DATA / "report.json"
    esistenti = {r["id"]: r for r in (json.loads(file.read_text()) if file.exists() else [])}
    ultimo = None
    nuovi = {}
    for ev in sorted(eventi, key=lambda e: e["fine"]):
        scheda = json.loads((DATA / "gare" / f"{ev['id']}.json").read_text())
        if _gara(scheda, "Race"):
            ultimo = scheda
            if scheda["id"] not in esistenti:
                nuovi[scheda["id"]] = scheda
    for id_, scheda in nuovi.items():
        # la classifica attuale vale solo per la gara piu' recente
        r = crea_report(scheda, standings if scheda is ultimo else None)
        if r:
            esistenti[id_] = r
    elenco = sorted(esistenti.values(), key=lambda r: r["data"], reverse=True)
    file.write_text(json.dumps(elenco, ensure_ascii=False, indent=1))
    print(f"Report di gara: {len(elenco)} ({len(nuovi)} nuovi)")


if __name__ == "__main__":
    aggiorna_report()
