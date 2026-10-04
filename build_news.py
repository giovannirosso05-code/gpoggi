"""Rassegna stampa F1: ultimi titoli da feed RSS di siti italiani, con fonte e link.

Non copia gli articoli: per ogni notizia salva titolo, un breve estratto (come lo offre il feed, tagliato)
e il link all'articolo originale. Scrive docs/data/rassegna.json. Nessuna chiave API necessaria.
Prova in locale:  python build_news.py --prova
"""
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests

FEEDS = {
    "Motorsport.com": "https://it.motorsport.com/rss/f1/news/",
    "FormulaPassion": "https://www.formulapassion.it/feed",
    "GPone": "https://www.gpone.com/rss.xml",
}
MAX_PER_FEED = 12
MAX_TOTALE = 30
ESTRATTO_MAX = 200
HEADERS = "GPOggiBot/1.0 (+https://gpoggi.it; progetto non commerciale, rassegna con link alle fonti)"
FILE = Path(__file__).parent / "docs" / "data" / "rassegna.json"


def testo(s):
    """Toglie i tag HTML e le entita' dai testi del feed."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", html.unescape(s or ""))).split())


def estratto(s):
    s = " ".join(testo(s).split())
    if len(s) <= ESTRATTO_MAX:
        return s
    return s[:ESTRATTO_MAX].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def data_iso(s):
    try:
        d = parsedate_to_datetime(s)
        return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        return None


def leggi_feed(url):
    r = requests.get(url, headers={"User-Agent": HEADERS}, timeout=30)
    r.raise_for_status()
    voci = []
    for item in ET.fromstring(r.content).iter("item"):
        t = lambda nome: (item.findtext(nome) or "").strip()
        voci.append({"title": t("title"), "link": t("link"), "summary": t("description"), "data": t("pubDate")})
    return voci


def main():
    articoli = []
    for fonte, url in FEEDS.items():
        try:
            voci = leggi_feed(url)
        except Exception as e:
            print(f"  {fonte}: feed non raggiungibile ({e}), salto")
            continue
        for e in voci[:MAX_PER_FEED]:
            titolo, link = testo(e["title"]), e["link"]
            if not titolo or not link.startswith("http"):
                continue
            articoli.append({"titolo": titolo, "estratto": estratto(e["summary"]), "fonte": fonte, "url": link, "pubblicato": data_iso(e["data"])})
        print(f"  {fonte}: {min(len(voci), MAX_PER_FEED)} articoli")
    if not articoli:
        print("Nessun feed raggiungibile: si lascia il file com'e'.")
        return
    articoli.sort(key=lambda a: a["pubblicato"] or "", reverse=True)
    articoli = articoli[:MAX_TOTALE]
    if "--prova" in sys.argv:
        for a in articoli[:5]:
            print(f"- {a['titolo']} [{a['fonte']}]\n  {a['estratto']}\n  {a['url']}")
        return
    FILE.write_text(json.dumps({"generato_il": datetime.now(timezone.utc).isoformat(timespec="seconds"), "articoli": articoli},
                               ensure_ascii=False, indent=1))
    print(f"Rassegna: {len(articoli)} articoli")


if __name__ == "__main__":
    main()
