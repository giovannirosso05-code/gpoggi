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
CACHE = ROOT / "foto_motogp_cache_v2.json"
SCHEDE = ROOT
CACHE_VECCHIA = ROOT / "foto_motogp_cache.json"
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


def immagine_verificata(i):
    """Nome del file dell'immagine nell'infobox della voce Wikipedia del pilota, ma solo se la voce e' stata verificata (stesso anno di nascita,
    vedi build_schede.wiki_en_stats). Mai una ricerca per nome: due piloti con lo stesso nome non si possono confondere."""
    f = SCHEDE / "schede_cache.json"
    ws = (json.loads(f.read_text()) if f.exists() else {}).get(f"wikistat:{i}", "assente")
    if ws == "assente":
        return "assente"
    return (ws or {}).get("immagine")


def main():
    piloti = json.loads((DATA / "motogp-piloti.json").read_text())
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    solo_cache = "--solo-cache" in sys.argv  # genera i file dalle foto gia' trovate, senza nuove ricerche
    for i, p in piloti.items():
        if i in cache or solo_cache or not p.get("nome"):
            continue
        f = immagine_verificata(i)
        if f == "assente":
            continue  # la voce non e' ancora stata verificata: si riprova al prossimo giro (nel frattempo resta la foto di prima, se c'era)
        try:
            cache[i] = fw._info_file(f, 500) if f else None
        except requests.RequestException as e:
            print(f"  {p['nome']}: errore di rete ({e}), riprovo alla prossima esecuzione")
            continue
        print(f"{p['nome']}: {'ok ' + cache[i]['licenza'] if cache[i] else 'nessuna foto libera verificata'}")
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
    vecchia = json.loads(CACHE_VECCHIA.read_text()) if CACHE_VECCHIA.exists() else {}
    out = {}
    for i, p in piloti.items():
        foto = cache[i] if i in cache else vecchia.get(p.get("nome"))  # provvisoria finche' la voce Wikipedia del pilota non e' verificata
        if not foto:
            continue
        try:
            fw.salva_in_locale(foto, ROOT / "docs" / "img" / "foto", "img/foto")
        except Exception as e:
            print(f"  {p['nome']}: download non riuscito ({e})")
            continue
        if p.get("categoria") == "MotoGP" and (p.get("pos") or 99) <= 6 and foto.get("grande"):
            try:  # i primi della classifica servono anche in grande (testata della home)
                fw.salva_in_locale(foto, ROOT / "docs" / "img" / "foto", "img/foto", "grande", "file_grande")
            except Exception as e:
                print(f"  {p['nome']}: foto grande non scaricata ({e})")
        out[i] = foto
        out["nome:" + p["nome"]] = foto  # per le pagine che conoscono solo il nome (es. podio dell'ultima gara)
    (DATA / "foto-motogp.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    n_piloti = sum(1 for k in out if not k.startswith("nome:"))
    print(f"Foto MotoGP/Moto2/Moto3: {n_piloti} su {len(piloti)}")


if __name__ == "__main__":
    main()
