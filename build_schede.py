"""Schede carriera dei piloti: numeri e biografia breve.

- F1 in pista oggi: gare, vittorie, podi, pole, giri veloci e titoli da Jolpica (Ergast); data e luogo di nascita.
- MotoGP/Moto2/Moto3 in pista oggi: nascita, altezza, peso, debutto e stagioni dal servizio pubblico del campionato.
- Biografia breve (2-3 frasi) dall'edizione italiana di Wikipedia (testo CC BY-SA 4.0), con il link alla voce, per i piloti
  di oggi e per quelli degli ultimi 20 anni di F1 e MotoGP. Se non si trova una voce chiara, la biografia manca: non si inventa niente.
Scrive docs/data/schede.json (chiavi: "f1:<numero>", "moto:<id>", "nome:<nome>") e usa schede_cache.json per non ripetere le richieste.
"""
import json
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

import build_motogp as bm

ROOT = Path(__file__).parent
DATA = ROOT / "docs" / "data"
CACHE = ROOT / "schede_cache.json"
H = {"User-Agent": "GPOggiBot/1.0 (+https://gpoggi.it; progetto non commerciale; giovannirosso05@gmail.com)"}
norm = lambda s: unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower().strip()
JOLPICA = "https://api.jolpi.ca/ergast/f1"
SOLO_CACHE = "--solo-cache" in sys.argv  # scrive il file con quello che e' gia' nella cache, senza nuove richieste


def get(url, **kw):
    for tentativo in range(5):
        time.sleep(0.5 + 3 * tentativo)
        r = requests.get(url, headers=H, timeout=30, **kw)
        if r.status_code != 429:
            return r
    raise requests.RequestException("troppe richieste")


def totale(percorso):
    r = get(f"{JOLPICA}/{percorso}.json", params={"limit": 1})
    r.raise_for_status()
    return int(r.json()["MRData"]["total"])


def jolpica_pilota(roster_p):
    """Numeri di carriera in F1. Il pilota si cerca per cognome tra quelli della stagione corrente."""
    anno = datetime.now(timezone.utc).year
    r = get(f"{JOLPICA}/{anno}/drivers.json", params={"limit": 100})
    r.raise_for_status()
    drivers = r.json()["MRData"]["DriverTable"]["Drivers"]
    d = next((x for x in drivers if x.get("code") == roster_p.get("acronimo")), None) or next((x for x in drivers if norm(x["familyName"]) == norm(roster_p["nome"].split()[-1])), None)
    if not d:
        return None
    i = d["driverId"]
    titoli = next((s["titoli"] for s in json.loads((DATA / "storici.json").read_text())["piloti"] if norm(s["nome"]) == norm(roster_p["nome"])), None)
    return {"nascita": d.get("dateOfBirth"), "nazionalita": d.get("nationality"), "titoli": titoli,
            "gare": totale(f"drivers/{i}/results"), "vittorie": totale(f"drivers/{i}/results/1"),
            "podi": sum(totale(f"drivers/{i}/results/{p}") for p in (1, 2, 3)),
            "pole": totale(f"drivers/{i}/qualifying/1"), "giri_veloci": totale(f"drivers/{i}/fastest/1/results")}


def wiki_it(nome):
    """Biografia breve dalla Wikipedia italiana; vuota se la voce non e' un pilota o e' ambigua."""
    alias = {"Sergio Perez": "Sergio Pérez", "Vitaly Petrov": "Vitalij Petrov"}
    base = alias.get(nome, nome)
    for titolo in (base, f"{base} (pilota)", f"{base} (pilota automobilistico)", f"{base} (pilota motociclistico)", f"{base} (motociclista)"):
        r = get("https://it.wikipedia.org/api/rest_v1/page/summary/" + quote(titolo.replace(" ", "_"), safe="_"))
        if r.status_code == 404:
            continue
        r.raise_for_status()
        d = r.json()
        desc = (d.get("description") or "").lower()
        if d.get("type") == "standard" and "pilota" in desc and d.get("extract"):
            frasi = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý])", d["extract"].strip())
            testo = " ".join(frasi[:3])
            return {"testo": testo, "descrizione": d.get("description"), "pagina": d["content_urls"]["desktop"]["page"]}
    return None


def moto_api(rid):
    try:
        d = bm.api(f"riders/{rid}")
    except requests.RequestException:
        return None
    anni = {}
    for c in d.get("career", []):
        anni.setdefault(c["season"], []).append({"categoria": (c.get("category") or {}).get("name", "").replace("™", ""), "team": (c.get("team") or {}).get("name") or c.get("sponsored_team"), "numero": c.get("number")})
    ph = d.get("physical_attributes") or {}
    return {"nascita": d.get("birth_date"), "luogo": ", ".join(x for x in (d.get("birth_city"), d.get("birth_country")) if x), "altezza": ph.get("height"), "peso": ph.get("weight"),
            "debutto": d.get("start_year"), "carriera": [{"anno": a, "classi": v} for a, v in sorted(anni.items())]}


def main():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    out = {}
    roster = json.loads((DATA / "roster.json").read_text())
    storici = json.loads((DATA / "storici.json").read_text())["piloti"]
    moto = json.loads((DATA / "motogp-piloti.json").read_text())
    arch = json.loads((DATA / "motogp-archivio.json").read_text())["anni"]
    anno = datetime.now(timezone.utc).year

    def passo(chiave, funzione, *a):
        if chiave in cache or SOLO_CACHE:
            return cache.get(chiave)
        try:
            cache[chiave] = funzione(*a)
        except requests.RequestException as e:
            print(f"  {chiave}: {e}, riprovo alla prossima esecuzione")
            return None
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
        print(chiave, "ok" if cache[chiave] else "nessun dato")
        return cache[chiave]

    # nomi per la biografia: oggi + ultimi 20 anni
    nomi = [p["nome"] for p in roster if p.get("nome")]
    nomi += [p["nome"] for p in storici if p["stagioni"][-1] >= anno - 20]
    nomi += [p["nome"] for p in moto.values() if p.get("nome")]
    vecchi = {}
    for s in arch:
        if s["anno"] > anno - 20:
            for r in s["classifica"]:
                if r.get("nome"):
                    vecchi[r["nome"]] = 1
    nomi += list(vecchi)
    for p in roster:
        if p.get("nome"):
            f1 = passo(f"f1:{p['numero']}", jolpica_pilota, p)
            if f1:
                out[f"f1:{p['numero']}"] = f1
    for i, p in moto.items():
        if p.get("categoria") in ("MotoGP", "Moto2", "Moto3"):
            rid = p.get("riders_id")
            m = passo(f"moto:{i}", moto_api, rid or i) if rid else None
            if m:
                out[f"moto:{i}"] = m
    for n in dict.fromkeys(nomi):
        w = passo(f"nome:{n}", wiki_it, n)
        if w:
            out[f"nome:{n}"] = w
    (DATA / "schede.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"Schede: {len(out)} voci")


if __name__ == "__main__":
    main()
