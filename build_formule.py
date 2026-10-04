"""Classifiche piloti e team di Formula 2 e Formula 3 da Wikipedia (testo CC BY-SA 4.0).

Non esiste una fonte gratuita con licenza per F2/F3: Wikipedia ha le tabelle di classifica della stagione, aggiornate dai volontari.
Si legge solo la tabella "Drivers' Championship standings", quella dei team e l'elenco iscritti (per abbinare pilota e team).
Scrive docs/data/f2.json e docs/data/f3.json. Prova in locale:  python build_formule.py --prova
"""
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DATA = Path(__file__).parent / "docs" / "data"
HEADERS = {"User-Agent": "GPOggiBot/1.0 (+https://gpoggi.it; progetto non commerciale)"}
CODICI = {"RET", "DNS", "DNQ", "DSQ", "DNP", "WD", "EX", "NC", "DNA", "DNPQ"}  # esiti di gara: la seconda riga di ogni team contiene i risultati del secondo pilota
SERIE = {"f2": ("FIA_Formula_2_Championship", "Formula 2"), "f3": ("FIA_Formula_3_Championship", "Formula 3")}


def pagina(titolo):
    for t in range(6):
        r = requests.get("https://en.wikipedia.org/w/api.php", params={"action": "parse", "page": titolo, "prop": "text", "format": "json", "formatversion": 2, "redirects": 1},
                         headers=HEADERS, timeout=60)
        if r.status_code == 200:
            return r.json()["parse"]["text"]
        time.sleep(8 * (t + 1))
    raise RuntimeError(f"Wikipedia non risponde per {titolo}")


def testo(c):
    for tag in c.find_all(["sup", "style"]):
        tag.decompose()
    return " ".join(c.get_text(" ", strip=True).split())


def tabella(soup, sezione):
    h = soup.find(id=sezione)
    return h.find_next("table", class_="wikitable") if h else None


def numero(s):
    m = re.search(r"-?\d+(?:[.,]\d+)?", s or "")
    return float(m.group(0).replace(",", ".")) if m else None


def squadre_piloti(soup):
    """Abbina ogni pilota ai suoi team leggendo la tabella degli iscritti (la cella del team ha rowspan)."""
    t = tabella(soup, "Entries")
    out, team = {}, None
    for r in (t.find_all("tr") if t else [])[1:]:
        celle = r.find_all(["th", "td"])
        if len(celle) >= 4:
            team = testo(celle[0]); pilota = testo(celle[2])
        elif len(celle) == 3 and team:
            pilota = testo(celle[1])
        else:
            continue
        if pilota and pilota.lower() not in ("tba", "driver", "driver name"):
            out.setdefault(pilota, [])
            if team not in out[pilota]:
                out[pilota].append(team)
    return out


def classifica_piloti(soup, team_di):
    t = tabella(soup, "Drivers'_Championship_standings")
    righe = []
    for r in (t.find_all("tr") if t else []):
        c = r.find_all(["th", "td"])
        if len(c) < 4:
            continue
        pos, nome, pt = testo(c[0]), testo(c[1]), numero(testo(c[-1]))
        if not (re.fullmatch(r"\d+|NC", pos) and pt is not None and re.search(r"[A-Za-z]", nome)):
            continue
        righe.append({"pos": int(pos) if pos.isdigit() else None, "nome": nome, "team": " / ".join(team_di.get(nome, [])) or None, "punti": pt})
    return righe


def classifica_team(soup):
    t = tabella(soup, "Teams'_Championship_standings")
    righe = []
    for r in (t.find_all("tr") if t else []):
        c = r.find_all(["th", "td"])
        if len(c) < 4:
            continue
        pos, nome, pt = testo(c[0]), testo(c[1]), numero(testo(c[-1]))
        if re.fullmatch(r"\d+", pos) and re.search(r"[A-Za-z]{3}", nome) and nome.upper() not in CODICI and pt is not None:
            righe.append({"pos": int(pos), "team": nome, "punti": pt})
    return righe


def main():
    anno = datetime.now(timezone.utc).year
    for chiave, (nome_pagina, nome) in SERIE.items():
        titolo = f"{anno}_{nome_pagina}"
        soup = BeautifulSoup(pagina(titolo), "lxml")
        piloti = classifica_piloti(soup, squadre_piloti(soup))
        team = classifica_team(soup)
        if not piloti:
            print(f"{nome}: tabella non trovata, file lasciato com'era")
            continue
        if "--prova" in sys.argv:
            print(nome, [(p["pos"], p["nome"], p["team"], p["punti"]) for p in piloti[:3]], [(t["pos"], t["team"], t["punti"]) for t in team[:2]])
            continue
        (DATA / f"{chiave}.json").write_text(json.dumps({
            "serie": nome, "anno": anno, "aggiornato": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "fonte": f"https://en.wikipedia.org/wiki/{titolo}", "licenza": "CC BY-SA 4.0", "piloti": piloti, "team": team}, ensure_ascii=False, indent=1))
        print(f"{nome}: {len(piloti)} piloti, {len(team)} team")


if __name__ == "__main__":
    main()
