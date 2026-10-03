"""Scarica i dati F1 da OpenF1 (https://openf1.org) e scrive i JSON statici in docs/data/.

Produce:
  roster.json           piloti della stagione con team e punti
  standings.json        classifica piloti e costruttori dopo l'ultima gara disputata
  events.json           calendario dei weekend di gara con le sessioni
  gare/<meeting>.json   risultati per sessione di un weekend

Niente foto: quelle di OpenF1 puntano a media.formula1.com (materiale protetto).
Uso: python scraper_f1.py [anno]
"""

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
DATA = ROOT / "docs" / "data"
BASE = "https://api.openf1.org/v1"
PAUSA = 0.4
GIORNI_CACHE = 2  # i dati di sessioni chiuse da piu' di N giorni non cambiano piu'

SESSIONI_IT = {
    "Practice 1": "Prove libere 1",
    "Practice 2": "Prove libere 2",
    "Practice 3": "Prove libere 3",
    "Sprint Qualifying": "Qualifiche sprint",
    "Sprint Shootout": "Qualifiche sprint",
    "Sprint": "Sprint",
    "Qualifying": "Qualifiche",
    "Race": "Gara",
}
ORDINE = list(SESSIONI_IT)

GP_IT = {
    "Australian": "d'Australia", "Chinese": "di Cina", "Japanese": "del Giappone", "Bahrain": "del Bahrain",
    "Saudi Arabian": "d'Arabia Saudita", "Miami": "di Miami", "Canadian": "del Canada", "Monaco": "di Monaco",
    "Barcelona": "di Barcellona", "Spanish": "di Spagna", "Austrian": "d'Austria", "British": "di Gran Bretagna",
    "Belgian": "del Belgio", "Hungarian": "d'Ungheria", "Dutch": "d'Olanda", "Italian": "d'Italia",
    "Azerbaijan": "dell'Azerbaigian", "Singapore": "di Singapore", "United States": "degli Stati Uniti",
    "Mexico City": "di Città del Messico", "São Paulo": "di San Paolo", "Las Vegas": "di Las Vegas",
    "Qatar": "del Qatar", "Abu Dhabi": "di Abu Dhabi", "Emilia Romagna": "dell'Emilia-Romagna",
}


def nome_gp(nome):
    """'Italian Grand Prix' -> 'Gran Premio d'Italia'; se non e' in elenco resta il nome della fonte."""
    if nome.endswith(" Grand Prix") and nome[:-11] in GP_IT:
        return f"Gran Premio {GP_IT[nome[:-11]]}"
    return nome


PAESI_IT = {
    "Australia": "Australia", "China": "Cina", "Japan": "Giappone", "Bahrain": "Bahrain",
    "Saudi Arabia": "Arabia Saudita", "United States": "Stati Uniti", "Italy": "Italia",
    "Monaco": "Monaco", "Spain": "Spagna", "Canada": "Canada", "Austria": "Austria",
    "United Kingdom": "Regno Unito", "Belgium": "Belgio", "Hungary": "Ungheria",
    "Netherlands": "Paesi Bassi", "Azerbaijan": "Azerbaigian", "Singapore": "Singapore",
    "Mexico": "Messico", "Brazil": "Brasile", "Qatar": "Qatar", "United Arab Emirates": "Emirati Arabi Uniti",
    "Portugal": "Portogallo", "Turkey": "Turchia", "Germany": "Germania", "France": "Francia",
    "Russia": "Russia", "South Korea": "Corea del Sud", "Malaysia": "Malesia",
}

ORA = datetime.now(timezone.utc)


def parse_data(s):
    return datetime.fromisoformat(s)


def get(path, params=None, definitivo=False):
    """GET su OpenF1 con retry su 429. 'No results found' (404) = lista vuota."""
    chiave = hashlib.md5(f"{path}{sorted((params or {}).items())}".encode()).hexdigest()
    file_cache = CACHE / f"{chiave}.json"
    if definitivo and file_cache.exists():
        return json.loads(file_cache.read_text())
    for tentativo in range(6):
        time.sleep(PAUSA)
        r = requests.get(f"{BASE}/{path}", params=params, timeout=30)
        if r.status_code == 200:
            dati = r.json()
            if definitivo:
                CACHE.mkdir(exist_ok=True)
                file_cache.write_text(json.dumps(dati))
            return dati
        if r.status_code == 404:
            return []
        if r.status_code == 429:
            time.sleep(2 * (tentativo + 1))
            continue
        r.raise_for_status()
    raise RuntimeError(f"OpenF1 non risponde su {path} {params}")


def scrivi(percorso, dati):
    percorso.parent.mkdir(parents=True, exist_ok=True)
    percorso.write_text(json.dumps(dati, ensure_ascii=False, indent=1))


def fmt_tempo(sec):
    if sec is None:
        return None
    if isinstance(sec, str):
        return sec
    ore, resto = divmod(sec, 3600)
    minuti, s = divmod(resto, 60)
    if ore:
        return f"{int(ore)}:{int(minuti):02d}:{s:06.3f}"
    if minuti:
        return f"{int(minuti)}:{s:06.3f}"
    return f"{s:.3f}"


def ultimo_valore(v):
    if isinstance(v, list):
        validi = [x for x in v if x is not None]
        return validi[-1] if validi else None
    return v


def fmt_distacco(v):
    v = ultimo_valore(v)
    if v is None or v == 0:
        return None
    if isinstance(v, str):
        return v
    return f"+{v:.3f}"


def risultati_sessione(sessione, piloti):
    righe = get("session_result", {"session_key": sessione["session_key"]}, definitivo=True)
    out = []
    for r in sorted(righe, key=lambda x: (x.get("position") is None, x.get("position") or 0)):
        p = piloti.get(r["driver_number"], {})
        stato = "RIT" if r.get("dnf") else "NP" if r.get("dns") else "SQ" if r.get("dsq") else None
        durata = ultimo_valore(r.get("duration"))
        out.append({
            "pos": r.get("position"),
            "numero": r["driver_number"],
            "acronimo": p.get("acronimo"),
            "nome": p.get("nome"),
            "team": p.get("team"),
            "giri": r.get("number_of_laps"),
            "stato": stato,
            "tempo": fmt_tempo(durata),
            "distacco": fmt_distacco(r.get("gap_to_leader")),
        })
    return out


def scrivi_schede_piloti(roster, schede):
    """Un file per pilota con il suo risultato in ogni weekend gia' iniziato."""
    def esito(sessione, numero):
        if not sessione or not sessione["risultati"]:
            return None
        r = next((x for x in sessione["risultati"] if x["numero"] == numero), None)
        return {"pos": r["pos"], "stato": r["stato"]} if r else None

    for p in roster:
        righe = []
        for g in schede:
            per_tipo = {s["tipo"]: s for s in g["sessioni"]}
            riga = {
                "id": g["id"], "nome": g["nome"], "inizio": g["inizio"],
                "qualifiche": esito(per_tipo.get("Qualifying"), p["numero"]),
                "sprint": esito(per_tipo.get("Sprint"), p["numero"]),
                "gara": esito(per_tipo.get("Race"), p["numero"]),
            }
            if riga["qualifiche"] or riga["sprint"] or riga["gara"]:
                righe.append(riga)
        arrivi = [r["gara"]["pos"] for r in righe if r["gara"] and r["gara"]["pos"] and not r["gara"]["stato"]]
        scrivi(DATA / "piloti" / f"{p['numero']}.json", p | {
            "weekend": righe,
            "vittorie": arrivi.count(1),
            "podi": sum(1 for x in arrivi if x <= 3),
            "pole": sum(1 for r in righe if r["qualifiche"] and r["qualifiche"]["pos"] == 1),
            "miglior_arrivo": min(arrivi) if arrivi else None,
            "ritiri": sum(1 for r in righe if r["gara"] and r["gara"]["stato"] == "RIT"),
        })


def main():
    anno = int(sys.argv[1]) if len(sys.argv) > 1 else ORA.year
    print(f"OpenF1 — stagione {anno}")

    sessioni = get("sessions", {"year": anno})
    meetings = {m["meeting_key"]: m for m in get("meetings", {"year": anno})}
    if not sessioni or not meetings:
        sys.exit(f"Nessun dato OpenF1 per il {anno}")

    per_meeting = {}
    for s in sessioni:
        if s["session_name"] in SESSIONI_IT and not s.get("is_cancelled"):
            per_meeting.setdefault(s["meeting_key"], []).append(s)

    eventi = []
    schede = []
    visti = {}
    for key, sess in sorted(per_meeting.items(), key=lambda kv: min(s["date_start"] for s in kv[1])):
        m = meetings.get(key)
        if not m or "testing" in m["meeting_name"].lower():
            continue
        sess.sort(key=lambda s: s["date_start"])
        finiti = [s for s in sess if parse_data(s["date_end"]) < ORA]
        recente = bool(finiti) and (ORA - parse_data(finiti[-1]["date_end"])).days < GIORNI_CACHE

        piloti = {}
        if finiti:
            for d in get("drivers", {"meeting_key": key}, definitivo=not recente):
                piloti[d["driver_number"]] = {
                    "nome": d["full_name"].title() if d.get("full_name") else None,
                    "acronimo": d.get("name_acronym"),
                    "team": d.get("team_name"),
                    "colore": d.get("team_colour"),
                }
                visti[d["driver_number"]] = piloti[d["driver_number"]]

        lista = []
        for s in sorted(sess, key=lambda s: s["date_start"]):
            finita = parse_data(s["date_end"]) < ORA
            lista.append({
                "key": s["session_key"],
                "nome": SESSIONI_IT[s["session_name"]],
                "tipo": s["session_name"],
                "inizio": s["date_start"],
                "fine": s["date_end"],
                "risultati": risultati_sessione(s, piloti) if finita else None,
            })
        paese = m["country_name"]
        scheda = {
            "id": key,
            "nome": nome_gp(m["meeting_name"]),
            "circuito": m["circuit_short_name"],
            "localita": m["location"],
            "paese": PAESI_IT.get(paese, paese),
            "inizio": min(s["date_start"] for s in sess),
            "fine": max(s["date_end"] for s in sess),
            "sessioni": lista,
        }
        scrivi(DATA / "gare" / f"{key}.json", scheda)
        schede.append(scheda)
        eventi.append({k: scheda[k] for k in ("id", "nome", "circuito", "localita", "paese", "inizio", "fine")}
                      | {"sessioni": [{k: s[k] for k in ("nome", "tipo", "inizio", "fine")} for s in lista]})
        print(f"  {m['meeting_name']}: {len(finiti)}/{len(sess)} sessioni disputate")

    scrivi(DATA / "events.json", eventi)

    gare_fatte = [s for s in sessioni if s["session_name"] == "Race" and parse_data(s["date_end"]) < ORA and not s.get("is_cancelled")]
    roster, standings = [], {"dopo": None, "piloti": [], "costruttori": []}
    if gare_fatte:
        ultima = max(gare_fatte, key=lambda s: s["date_start"])
        standings["dopo"] = nome_gp(meetings[ultima["meeting_key"]]["meeting_name"])
        drivers = {d["driver_number"]: d for d in get("drivers", {"session_key": ultima["session_key"]})}
        punti = {c["driver_number"]: c for c in get("championship_drivers", {"session_key": ultima["session_key"]})}
        for num, d in drivers.items():
            c = punti.get(num, {})
            roster.append({
                "numero": num,
                "acronimo": d.get("name_acronym"),
                "nome": d["full_name"].title(),
                "team": d.get("team_name"),
                "colore": d.get("team_colour"),
                "posizione": c.get("position_current"),
                "punti": c.get("points_current"),
            })
        for num, c in punti.items():
            if num not in drivers:
                v = visti.get(num, {})
                roster.append({"numero": num, "acronimo": v.get("acronimo"), "nome": v.get("nome"), "team": v.get("team"),
                               "colore": v.get("colore"), "posizione": c.get("position_current"), "punti": c.get("points_current")})
        roster.sort(key=lambda p: (p["posizione"] is None, p["posizione"] or 0, p["numero"]))
        standings["piloti"] = [p for p in roster if p["posizione"] is not None]
        colori = {d.get("team_name"): d.get("team_colour") for d in drivers.values()}
        for c in sorted(get("championship_teams", {"session_key": ultima["session_key"]}), key=lambda x: x["position_current"]):
            standings["costruttori"].append({"posizione": c["position_current"], "team": c["team_name"],
                                             "colore": colori.get(c["team_name"]), "punti": c["points_current"]})

    scrivi(DATA / "roster.json", roster)
    scrivi_schede_piloti(roster, schede)
    scrivi(DATA / "standings.json", standings)
    scrivi(DATA / "meta.json", {"anno": anno, "aggiornato": ORA.isoformat(timespec="seconds"), "fonte": "OpenF1"})
    print(f"Fatto: {len(eventi)} weekend, {len(roster)} piloti, aggiornato {ORA:%Y-%m-%d %H:%M} UTC")


if __name__ == "__main__":
    main()
