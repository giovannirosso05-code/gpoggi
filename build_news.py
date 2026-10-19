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

def serie_da_indirizzo(link, predefinita):
    """Il feed di FormulaPassion mescola F1 e MotoGP: la serie si legge dal percorso dell'articolo (/motogp/, /f1/), altrimenti vale quella del feed."""
    l = link.lower().split("?")[0]
    if "/motogp/" in l or "/moto2/" in l or "/moto3/" in l:
        return "MotoGP"
    if "/f1/" in l or "/formula-1/" in l:
        return "F1"
    return predefinita


FEEDS = {  # nome della fonte: (indirizzo del feed, serie). Solo feed dedicati a F1 o MotoGP: quello generale di FormulaPassion mescolava auto, WEC, Formula E (le "6 ore di Barcellona" comparivano come notizie F1) e GPone è in inglese e mescola WSBK e GT3.
    "Motorsport.com": ("https://it.motorsport.com/rss/f1/news/", "F1"),
    "FormulaPassion": ("https://www.formulapassion.it/f1/feed", "F1"),
    "Motorsport.com ": ("https://it.motorsport.com/rss/motogp/news/", "MotoGP"),
    "FormulaPassion ": ("https://www.formulapassion.it/motogp/feed", "MotoGP"),
    # fonti ricche di interviste e dichiarazioni (le più viste sui social)
    "OA Sport": ("https://www.oasport.it/category/formula-1/feed/", "F1"),
    "OA Sport ": ("https://www.oasport.it/category/motogp/feed/", "MotoGP"),
    "Tuttosport": ("https://www.tuttosport.com/rss/formula-1", "F1"),
}
MAX_PER_FEED = 30
MAX_TOTALE = 120
ESTRATTO_MAX = 200
# titolo con una dichiarazione di pilota/team principal/tecnico: virgolette o verbi del "dire" (il radar le mette in evidenza)
CITAZIONE = re.compile(r"[“”\"«»]|\b(dice|dicono|ammette|rivela|spiega|racconta|intervista|parla|svela|confessa|promette|avverte|attacca|risponde|sottolinea|difende|chiarisce|ricorda)\b", re.I)
# tipo di dichiarazione, letto da titolo ed estratto: social (post, storie, messaggi sui social), intervista (interviste, conferenze stampa, podcast), dichiarazione (virgolette o verbi del "dire" nel titolo)
SOCIAL = re.compile(r"\b(sui social|sui suoi social|sui propri social|su instagram|su tiktok|su twitter|su facebook|nelle storie|nelle sue storie|storia su|messaggio sui social|un post|nuovo post|il post|post su|tweet|cinguett\w*|social network|sui social media|ha postato|ha pubblicato (?:una |un |su )|ha condiviso|su x|su ig|reel|stories|storie su)\b", re.I)
INTERVISTA = re.compile(r"\b(intervista|intervistato|intervistata|ai microfoni|conferenza stampa|ha raccontato|racconta|podcast|ospite a|a colloquio)\b", re.I)


def tipo_dichiarazione(titolo, estratto=""):
    if SOCIAL.search(titolo + " " + estratto):
        return "social"
    if INTERVISTA.search(titolo + " " + estratto):
        return "intervista"
    if CITAZIONE.search(titolo):
        return "dichiarazione"
    return None


# punteggio di interesse (campo "punteggio" in rassegna.json): il file resta in ordine di data, e' la pagina a ordinare per punteggio
ITALIANI = re.compile(r"\b(ferrari|antonelli|bagnaia|bezzecchi|marini|morbidelli|di giannantonio|dovizioso|rossi|vale|pecco|marco bezzecchi|aldeguer|fabio di giannantonio|ducati|monza|imola|mugello)\b", re.I)
ROUTINE = re.compile(r"\b(orari|programma|diretta tv|in tv|streaming|dove vedere|come vedere|palinsesto|ordine d'arrivo|classifica|risultati|griglia di partenza|tempi|prove libere|meteo|previsioni)\b", re.I)
PAROLE_VUOTE = {"della", "delle", "degli", "dello", "nella", "nelle", "sulla", "sulle", "dopo", "prima", "gran", "premio", "come", "sono", "senza", "tutti", "tutto", "anche", "questo", "questa", "essere", "dove", "cosa", "quando", "perche", "contro", "verso", "ancora", "nuovo", "nuova"}


def parole(titolo):
    return {w for w in re.findall(r"[a-zàèéìòù0-9]{4,}", titolo.lower()) if w not in PAROLE_VUOTE}


def assegna_punteggi(articoli, adesso=None):
    """Interesse: stessa storia su piu' testate (almeno 3 parole del titolo in comune), Ferrari/italiani, dichiarazioni, weekend di gara (ven-lun); meno per orari/programmi/risultati; calo con l'eta'."""
    adesso = adesso or datetime.now(timezone.utc)
    pw = [parole(a["titolo"]) for a in articoli]
    for i, a in enumerate(articoli):
        fonti = {a["fonte"]} | {b["fonte"] for j, b in enumerate(articoli) if j != i and len(pw[i] & pw[j]) >= 3}
        testo_a = a["titolo"] + " " + a["estratto"]
        punti = 10 * (len(fonti) - 1)
        if ITALIANI.search(testo_a):
            punti += 8
        if a["tipo"]:
            punti += {"social": 8, "intervista": 6, "dichiarazione": 5}[a["tipo"]]
        if ROUTINE.search(a["titolo"]):
            punti -= 12
        try:
            d = datetime.fromisoformat(a["pubblicato"])
            if d.weekday() in (4, 5, 6, 0):
                punti += 4
            punti -= min(30, (adesso - d).total_seconds() / 3600 / 4)
        except (TypeError, ValueError):
            punti -= 30
        a["punteggio"] = round(punti, 1)
        a["testate"] = len(fonti)


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
    for fonte, (url, serie) in FEEDS.items():
        try:
            voci = leggi_feed(url)
        except Exception as e:
            print(f"  {fonte}: feed non raggiungibile ({e}), salto")
            continue
        for e in voci[:MAX_PER_FEED]:
            titolo, link = testo(e["title"]), e["link"]
            if not titolo or not link.startswith("http"):
                continue
            articoli.append({"titolo": titolo, "estratto": estratto(e["summary"]), "fonte": fonte.strip(), "serie": serie_da_indirizzo(link, serie), "url": link, "pubblicato": data_iso(e["data"]), "tipo": tipo_dichiarazione(titolo, estratto(e["summary"])), "citazione": bool(tipo_dichiarazione(titolo, estratto(e["summary"])))})
        print(f"  {fonte}: {min(len(voci), MAX_PER_FEED)} articoli")
    if not articoli:
        print("Nessun feed raggiungibile: si lascia il file com'e'.")
        return
    articoli.sort(key=lambda a: a["pubblicato"] or "", reverse=True)
    articoli = articoli[:MAX_TOTALE]
    assegna_punteggi(articoli)
    print(f"  di cui con dichiarazioni: {sum(a['citazione'] for a in articoli)} (social {sum(a['tipo'] == 'social' for a in articoli)}, interviste {sum(a['tipo'] == 'intervista' for a in articoli)})")
    if "--prova" in sys.argv:
        for a in sorted(articoli, key=lambda x: -x["punteggio"])[:8]:
            print(f"- [{a['punteggio']}] {a['titolo']} [{a['fonte']}, {a['testate']} testate]\n  {a['estratto']}\n  {a['url']}")
        return
    FILE.write_text(json.dumps({"generato_il": datetime.now(timezone.utc).isoformat(timespec="seconds"), "articoli": articoli},
                               ensure_ascii=False, indent=1))
    print(f"Rassegna: {len(articoli)} articoli")


if __name__ == "__main__":
    main()
