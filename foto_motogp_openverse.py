"""Seconda ricerca di foto per i piloti senza pagina Wikipedia illustrata: Openverse (openverse.org), che raccoglie
immagini con licenza Creative Commons da Wikimedia Commons e Flickr. Si accettano solo CC BY, CC BY-SA e CC0.
Aggiorna foto_motogp_cache.json (solo le voci rimaste vuote); poi `python foto_motogp.py --solo-cache` scrive i file del sito.
"""
import json
import re
import time
import unicodedata
from pathlib import Path

import requests

import foto_wiki as fw

CACHE = Path(__file__).parent / "foto_motogp_cache.json"
TENTATI = Path(__file__).parent / "foto_motogp_openverse_tentati.json"
OK = {"by", "by-sa", "cc0"}
norm = lambda s: unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()


def cerca(nome):
    cognome = norm(nome.split()[-1])
    for q in (f"{nome} motogp", nome):
        for tentativo in range(3):
            time.sleep(1.5 + 8 * tentativo)
            r = requests.get("https://api.openverse.org/v1/images/", params={"q": q, "page_size": 20, "license": "by,by-sa,cc0"}, headers=fw.HEADERS, timeout=30)
            if r.status_code != 429:
                break
        if r.status_code == 429:
            raise requests.RequestException("limite di richieste Openverse")
        r.raise_for_status()
        for x in r.json().get("results", []):
            titolo = norm(x.get("title"))
            if x["license"] not in OK or x["source"] not in ("wikimedia", "flickr") or cognome not in titolo:
                continue
            if x["source"] == "wikimedia":
                f = requests.utils.unquote(x["url"].split("/")[-1])
                info = fw._info_file(f, 500)
                if info:
                    return info
                continue
            lic = "CC0" if x["license"] == "cc0" else f"CC {x['license'].upper()} {x.get('license_version') or ''}".strip()
            return {"url": x.get("thumbnail") or x["url"], "grande": x["url"], "autore": x.get("creator") or "Autore sconosciuto", "licenza": lic, "pagina": x.get("foreign_landing_url") or x["url"]}
    return None


def main():
    cache = json.loads(CACHE.read_text())
    tentati = json.loads(TENTATI.read_text()) if TENTATI.exists() else []
    for nome in [n for n, v in cache.items() if v is None and n not in tentati]:
        try:
            foto = cerca(nome)
        except requests.RequestException as e:
            print(f"  {nome}: {e}, riprovo alla prossima esecuzione")
            break
        if foto:
            cache[nome] = foto
        tentati.append(nome)
        print(f"{nome}: {'ok ' + foto['licenza'] if foto else 'nessuna foto libera'}")
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
        TENTATI.write_text(json.dumps(tentati))


if __name__ == "__main__":
    main()
