"""
Scraper F1 da OpenF1 API (https://openf1.org/).

OpenF1 fornisce dati F1 real-time: piloti, team, sessioni (FP1/2/3, qualifiche, gara),
risultati e posizioni. API pubblica, nessuna chiave richiesta, rate limit: 10 req/sec.

Uso:
  python scraper_f1.py                 # genera cache locale + docs/data/
  python scraper_f1.py 2024            # solo il campionato 2024
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
DOCS_DATA = ROOT / "docs" / "data"
CACHE.mkdir(exist_ok=True)

# OpenF1 API endpoints
BASE_URL = "https://api.openf1.org/v1"
TIMEOUT = 10

# Le sessioni F1 in ordine di una gara weekend
TIPI_SESSIONE = {
    "Practice 1": "FP1",
    "Practice 2": "FP2",
    "Practice 3": "FP3",
    "Qualifying": "Q",
    "Sprint": "S",
    "Race": "R"
}


def fetch_json(endpoint: str, params: dict = None) -> Optional[dict | list]:
    """Fetch JSON da OpenF1 con retry."""
    url = f"{BASE_URL}{endpoint}"
    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:  # Rate limit
                time.sleep(2 ** attempt)
                continue
            else:
                print(f"⚠️  {endpoint}: {resp.status_code}")
                return None
        except Exception as e:
            print(f"❌ Errore fetching {endpoint}: {e}")
            time.sleep(1)
    return None


def get_anni_disponibili() -> list:
    """Scarica la lista degli anni con dati disponibili."""
    data = fetch_json("/seasons")
    if data and isinstance(data, list):
        return sorted(set(s.get("year") for s in data if s.get("year")))
    return []


def scarica_campionato(anno: int):
    """Scarica piloti, team e gare per un campionato."""
    print(f"\n📥 Scaricando campionato {anno}...")

    # Piloti
    piloti = fetch_json("/drivers", {"season_year": anno})
    if piloti:
        cache_piloti = CACHE / f"drivers_{anno}.json"
        with open(cache_piloti, "w") as f:
            json.dump(piloti, f)
        print(f"  ✓ {len(piloti)} piloti")

    # Team
    team = fetch_json("/teams", {"season_year": anno})
    if team:
        cache_team = CACHE / f"teams_{anno}.json"
        with open(cache_team, "w") as f:
            json.dump(team, f)
        print(f"  ✓ {len(team)} team")

    # Gare (raceMeetings)
    gare = fetch_json("/meetings", {"season_year": anno})
    if gare:
        cache_gare = CACHE / f"meetings_{anno}.json"
        with open(cache_gare, "w") as f:
            json.dump(gare, f)
        print(f"  ✓ {len(gare)} gare")

        # Per ogni gara, scarica sessioni e risultati
        for gara in gare:
            gara_id = gara.get("meeting_key")
            if gara_id:
                sessioni = fetch_json("/sessions", {"meeting_key": gara_id})
                if sessioni:
                    cache_sessioni = CACHE / f"sessions_{gara_id}.json"
                    with open(cache_sessioni, "w") as f:
                        json.dump(sessioni, f)
                time.sleep(0.11)  # Rispetta rate limit

    return piloti, team, gare


def build_piloti_json(anno: int, piloti: list, team: list):
    """Costruisce roster.json (lista piloti con foto, team, numero, nazionalità)."""
    if not piloti:
        return

    # Mappa team_id -> nome team
    team_map = {t.get("team_id"): t.get("team_name") for t in (team or [])}

    roster = []
    for p in piloti:
        entry = {
            "id": p.get("driver_id"),
            "nome": p.get("full_name", ""),
            "numero": p.get("driver_number"),
            "nazionalita": p.get("country_code", ""),
            "team": team_map.get(p.get("team_id"), ""),
            "foto": f"https://media.formula1.com/image/upload/f_auto/q_auto/v1406375847/f1_website_v2/drivers/{p.get('driver_id'):03d}.jpg"
            if p.get("driver_id") else ""
        }
        roster.append(entry)

    out = DOCS_DATA / "roster.json"
    with open(out, "w") as f:
        json.dump(sorted(roster, key=lambda x: (x.get("team", ""), x.get("numero", 0))), f)
    print(f"✓ roster.json ({len(roster)} piloti)")


def build_gare_json(anno: int, gare: list):
    """Costruisce events.json (lista gare con date, sessioni)."""
    if not gare:
        return

    eventi = []
    for gara in gare:
        try:
            data_gara = datetime.fromisoformat(gara.get("date_start", "").replace("Z", "+00:00"))
            stato = "Programmato"
            if datetime.fromisoformat(datetime.now(data_gara.tzinfo).isoformat()) > data_gara:
                stato = "Passato"

            entry = {
                "id": gara.get("meeting_key"),
                "nome": gara.get("meeting_name", ""),
                "circuito": gara.get("circuit_short_name", ""),
                "paese": gara.get("country_name", ""),
                "data": data_gara.isoformat(),
                "stato": stato
            }
            eventi.append(entry)
        except Exception as e:
            print(f"⚠️  Errore parsing gara {gara.get('meeting_name')}: {e}")

    out = DOCS_DATA / "events.json"
    with open(out, "w") as f:
        json.dump(sorted(eventi, key=lambda x: x.get("data", "")), f)
    print(f"✓ events.json ({len(eventi)} gare)")


if __name__ == "__main__":
    import sys

    # Determina anni da scaricare
    if len(sys.argv) > 1:
        anni = [int(sys.argv[1])]
    else:
        anni = get_anni_disponibili()
        if not anni:
            print("❌ Nessun anno disponibile su OpenF1")
            sys.exit(1)
        anni = [max(anni)]  # Scarica solo l'anno più recente per default

    print(f"📊 OpenF1 scraper — Scaricando anni: {anni}")

    for anno in anni:
        piloti, team, gare = scarica_campionato(anno)

        if piloti and gare:
            build_piloti_json(anno, piloti, team)
            build_gare_json(anno, gare)

    print("\n✅ Fatto!")
