"""Foto dei piloti del motomondiale (MotoGP, Moto2, Moto3) da Wikimedia Commons, solo licenze libere.

Una ricerca raggruppata per volta (40 titoli per chiamata): evita i limiti di richieste di Wikipedia.
Scrive docs/data/foto-motogp.json ({id pilota: foto}) e le immagini in docs/img/foto/.
I risultati restano in foto_motogp_cache.json: chi e' gia' stato cercato non si ripete.
"""
import json
import re
import sys
import time
from urllib.parse import unquote
from pathlib import Path

import requests

import foto_wiki as fw

ROOT = Path(__file__).parent
DATA = ROOT / "docs" / "data"
CACHE = ROOT / "foto_motogp_cache.json"
PAROLE = ("motorcycle", "motorcyclist", "grand prix", "motogp", "moto2", "moto3", "racer")


REST = "https://en.wikipedia.org/api/rest_v1/page/summary/"


def riassunto(titolo):
    """Descrizione e file dell'immagine principale di una pagina (endpoint REST, meno limitato dell'API di ricerca)."""
    for tentativo in range(5):
        time.sleep(0.6 + 5 * tentativo)
        r = requests.get(REST + requests.utils.quote(titolo.replace(" ", "_")), headers=fw.HEADERS, timeout=30)
        if r.status_code == 404:
            return None, None
        if r.status_code != 429:
            r.raise_for_status()
            d = r.json()
            src = (d.get("originalimage") or d.get("thumbnail") or {}).get("source", "")
            m = re.search(r"/commons/(?:thumb/)?[0-9a-f]/[0-9a-f]{2}/([^/?]+)", src)
            return (d.get("description") or "").lower(), unquote(m.group(1)) if m else None
    raise requests.RequestException("troppe richieste")


def trova_file(nome):
    for titolo in (nome, f"{nome} (motorcyclist)", f"{nome} (motorcycle racer)"):
        descrizione, file = riassunto(titolo)
        if file and any(w in (descrizione or "") for w in PAROLE):
            return file
    return None


def main():
    piloti = json.loads((DATA / "motogp-piloti.json").read_text())
    ordine = {"MotoGP": 0, "Moto2": 1, "Moto3": 2}  # prima i piloti della classe regina
    nomi = list(dict.fromkeys(p["nome"] for p in sorted(piloti.values(), key=lambda p: (ordine.get(p.get("categoria"), 3), p.get("pos") or 99)) if p.get("nome")))
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    solo_cache = "--solo-cache" in sys.argv  # genera i file dalle foto gia' trovate, senza nuove ricerche
    for n in nomi:
        if n in cache or solo_cache:
            continue
        try:
            f = trova_file(n)
            cache[n] = fw._info_file(f, 500) if f else None
        except requests.RequestException as e:
            print(f"  {n}: errore di rete ({e}), riprovo alla prossima esecuzione")
            continue
        print(f"{n}: {'ok ' + cache[n]['licenza'] if cache[n] else 'nessuna foto libera'}")
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
    out = {}
    for i, p in piloti.items():
        foto = cache.get(p.get("nome"))
        if not foto:
            continue
        try:
            fw.salva_in_locale(foto, ROOT / "docs" / "img" / "foto", "img/foto")
        except Exception as e:
            print(f"  {p['nome']}: download non riuscito ({e})")
            continue
        out[i] = foto
        out["nome:" + p["nome"]] = foto  # per le pagine che conoscono solo il nome (es. podio dell'ultima gara)
    (DATA / "foto-motogp.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"Foto MotoGP/Moto2/Moto3: {len(out)} su {len(piloti)}")


if __name__ == "__main__":
    main()
