"""Pulisce docs/sitemap.xml dopo i generatori di pagine: toglie i doppioni e scrive <lastmod> (la data in cui il contenuto del file è cambiato, ricordata in docs/data/sitemap_date.json: il checkout dei workflow non ha la storia di git).
Una sitemap con lo stesso indirizzo ripetuto decine di volte è un segnale di cattiva qualità per Google.
Uso: python3 build_sitemap.py"""
import hashlib, json, re
from datetime import date
from pathlib import Path

DOCS = Path(__file__).parent / "docs"
SITO = "https://gpoggi.it"


MEMORIA = DOCS / "data" / "sitemap_date.json"


def ultima_modifica(percorso, memoria):
    if not percorso:
        return None
    f = DOCS / percorso.split("?")[0]
    if not f.exists():
        return None
    h = hashlib.sha1(f.read_bytes()).hexdigest()[:12]
    prima = memoria.get(percorso)
    if not prima or prima[0] != h:
        memoria[percorso] = [h, date.today().isoformat()]
    return memoria[percorso][1]


def main():
    sm = DOCS / "sitemap.xml"
    url = []
    for loc in re.findall(r"<loc>([^<]+)</loc>", sm.read_text(encoding="utf-8")):
        if loc not in url:
            url.append(loc)
    memoria = json.loads(MEMORIA.read_text()) if MEMORIA.exists() else {}
    righe = []
    for loc in url:
        rel = loc.replace(SITO + "/", "", 1) if loc != SITO + "/" else "index.html"
        # gara.html?id=… e pilota.html?n=… sono la stessa pagina HTML: la data è quella del file
        lm = ultima_modifica(rel, memoria)
        righe.append(f"  <url><loc>{loc}</loc>" + (f"<lastmod>{lm}</lastmod>" if lm else "") + "</url>")
    MEMORIA.write_text(json.dumps(memoria, indent=0, sort_keys=True))
    sm.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(righe) + "\n</urlset>\n", encoding="utf-8")
    print(f"Sitemap: {len(url)} indirizzi (senza doppioni)")


if __name__ == "__main__":
    main()
