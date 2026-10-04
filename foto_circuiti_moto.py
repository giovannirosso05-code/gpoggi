"""Mappe dei circuiti della MotoGP da Wikimedia Commons (solo licenze libere).

Il file della mappa si legge dall'infobox della pagina Wikipedia del circuito (testo grezzo, nessun limite di ricerca).
Scrive docs/data/mappe-motogp.json ({nome del circuito: mappa}) e le immagini in docs/img/foto/.
I risultati restano in foto_circuiti_moto_cache.json.
"""
import json
import re
import time
from pathlib import Path

import requests

import foto_wiki as fw

ROOT = Path(__file__).parent
CACHE = ROOT / "foto_circuiti_moto_cache.json"
# nome del circuito nel servizio MotoGP -> titolo della pagina su Wikipedia (le varianti dello stesso circuito hanno lo stesso titolo)
CIRCUITI = {
    "Autodromo Internazionale del Mugello": "Mugello Circuit",
    "Autódromo Internacional de Goiânia - Ayrton Senna": "Autódromo Internacional Ayrton Senna (Goiânia)",
    "Autódromo Internacional do Algarve": "Algarve International Circuit",
    "Balaton Park Circuit": "Balaton Park Circuit",
    "CREDITAS Autodrom Brno": "Brno Circuit",
    "Chang International Circuit": "Chang International Circuit",
    "Circuit Of The Americas": "Circuit of the Americas",
    "Circuit Ricardo Tormo": "Circuit Ricardo Tormo",
    "Circuit de Barcelona-Catalunya": "Circuit de Barcelona-Catalunya",
    "Circuito de Jerez - Ángel Nieto": "Circuito de Jerez",
    "Le Mans": "Bugatti Circuit",
    "Lusail International Circuit": "Lusail International Circuit",
    "Misano World Circuit Marco Simoncelli": "Misano World Circuit Marco Simoncelli",
    "Mobility Resort Motegi": "Mobility Resort Motegi",
    "MotorLand Aragón": "Ciudad del Motor de Aragón",
    "Pertamina Mandalika Circuit": "Mandalika International Street Circuit",
    "Pertamina Mandalika International Circuit": "Mandalika International Street Circuit",
    "Petronas Sepang International Circuit": "Sepang International Circuit",
    "Phillip Island": "Phillip Island Grand Prix Circuit",
    "Red Bull Ring - Spielberg": "Red Bull Ring",
    "Sachsenring": "Sachsenring",
    "Silverstone Circuit": "Silverstone Circuit",
    "TT Circuit Assen": "TT Circuit Assen",
}


def file_infobox(titolo, profondita=0):
    for tentativo in range(5):
        time.sleep(1 + 4 * tentativo)
        r = requests.get("https://en.wikipedia.org/w/index.php", params={"title": titolo, "action": "raw"}, headers=fw.HEADERS, timeout=30)
        if r.status_code == 429:
            continue
        if r.status_code != 200:
            return None
        w = r.text[:8000]
        rid = re.match(r"\s*#redirect\s*\[\[([^\]|#]+)", w, re.I)
        if rid and profondita < 2:  # la pagina e' un rimando: si segue
            return file_infobox(rid.group(1).strip(), profondita + 1)
        m = re.search(r"\|\s*(?:image|map)\s*=\s*(?:\[\[)?(?:(?:File|Image):)?([^|\]\n{]+?\.(?:svg|png))", w, re.I)
        return m.group(1).strip() if m else None
    raise requests.RequestException("troppe richieste")


def main():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    for titolo in sorted(set(CIRCUITI.values())):
        if titolo in cache:
            continue
        try:
            f = file_infobox(titolo)
            cache[titolo] = fw._info_file(f, 800) if f else None
        except requests.RequestException as e:
            print(f"  {titolo}: errore di rete ({e}), riprovo alla prossima esecuzione")
            continue
        print(f"{titolo}: {'ok ' + cache[titolo]['licenza'] if cache[titolo] else 'nessuna mappa libera'}")
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
    out = {}
    for nome, titolo in CIRCUITI.items():
        mappa = cache.get(titolo)
        if not mappa:
            continue
        try:
            fw.salva_in_locale(mappa, ROOT / "docs" / "img" / "foto", "img/foto")
        except Exception as e:
            print(f"  {nome}: download non riuscito ({e})")
            continue
        out[nome] = mappa
    (ROOT / "docs" / "data" / "mappe-motogp.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"Mappe MotoGP: {len(out)} circuiti su {len(CIRCUITI)}")


if __name__ == "__main__":
    main()
