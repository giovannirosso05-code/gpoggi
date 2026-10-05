"""Foto di piloti del passato (F1) e campioni della MotoGP da Wikimedia Commons, solo licenze libere.

Prende i piloti con almeno un titolo o tre vittorie e i campioni della classe regina del motomondiale. Se per un pilota non c'e' una foto
con licenza libera, viene saltato. Scrive docs/data/foto-storici.json e le immagini in docs/img/storici/. I risultati restano in
foto_storici_cache.json: le ricerche gia' fatte non si ripetono.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

import foto_wiki as fw

ROOT = Path(__file__).parent
DATA = ROOT / "docs" / "data"
CARTELLA = ROOT / "docs" / "img" / "storici"
CACHE = ROOT / "foto_storici_cache.json"


def foto_motociclista(nome):
    for titolo in (nome, f"{nome} (motorcyclist)", f"{nome} (motorcycle racer)"):
        descrizione, file = fw._immagine_pagina(titolo)
        d = descrizione.lower()
        if file and ("motorcycle" in d or "motorcyclist" in d or "grand prix" in d):
            return fw._info_file(file, 500)
    return None


def main():
    attuali = {p["nome"] for p in json.loads((DATA / "roster.json").read_text()) if p.get("nome")}
    storici = json.loads((DATA / "storici.json").read_text())["piloti"]
    anno = datetime.now(timezone.utc).year
    # campioni e vincitori di sempre, piu' tutti quelli corsi negli ultimi 20 anni (gli stessi della pagina Piloti)
    f1 = [p for p in storici if (p["titoli"] >= 1 or p["vittorie"] >= 3 or p["stagioni"][-1] >= anno - 20) and p["nome"] not in attuali]
    campioni = {}
    for s in json.loads((DATA / "motogp-archivio.json").read_text())["anni"]:
        c = next((p for p in s["classifica"] if p["pos"] == 1), None)
        if c and c.get("nome"):
            campioni.setdefault(c["nome"], []).append(s["anno"])
    lavoro = [(p["nome"], "Formula 1", f"{p['stagioni'][0]}–{p['stagioni'][-1]}", fw.foto_pilota) for p in f1] + \
             [(n, "MotoGP", f"{min(a)}–{max(a)}" if len(a) > 1 else str(a[0]), foto_motociclista) for n, a in campioni.items()]
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    out = []
    for i, (nome, serie, anni, f) in enumerate(lavoro, 1):
        chiave = f"{serie}:{nome}"
        if chiave not in cache:
            try:
                cache[chiave] = f(nome)
            except requests.RequestException as e:
                print(f"  {nome}: errore di rete ({e}), riprovo alla prossima esecuzione")
                continue
            CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
        foto = cache[chiave]
        if not foto:
            print(f"[{i}/{len(lavoro)}] {nome}: nessuna foto libera")
            continue
        try:
            fw.salva_in_locale(foto, CARTELLA, "img/storici")
        except Exception as e:
            print(f"  {nome}: download non riuscito ({e})")
            continue
        out.append({"nome": nome, "serie": serie, "anni": anni, "foto": foto})
        print(f"[{i}/{len(lavoro)}] {nome}: ok ({foto['licenza']})")
    (DATA / "foto-storici.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"Foto storiche: {len(out)} su {len(lavoro)}")


if __name__ == "__main__":
    main()
