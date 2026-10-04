"""Archivio storico della classe regina del motomondiale (500cc e MotoGP) dal 1949: classifica finale di ogni stagione.

Stesso servizio pubblico usato per il calendario MotoGP, uso non commerciale. Scrive docs/data/motogp-archivio.json.
Le stagioni gia' scaricate restano in cache: si rifa solo l'anno appena concluso.
"""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).parent
CACHE = ROOT / "cache" / "motogp-archivio"
BASE = "https://api.motogp.pulselive.com/motogp/v1"
H = {"User-Agent": "GPOggiBot/1.0 (+https://gpoggi.it; progetto non commerciale)"}
PREMIER = ("motogp", "500cc", "500", "premier")


def get(percorso, **p):
    f = CACHE / (hashlib.md5(f"{percorso}{sorted(p.items())}".encode()).hexdigest() + ".json")
    if f.exists():
        return json.loads(f.read_text())
    for t in range(6):
        time.sleep(0.35)
        r = requests.get(f"{BASE}/{percorso}", params=p, headers=H, timeout=40)
        if r.status_code == 200:
            CACHE.mkdir(parents=True, exist_ok=True)
            f.write_text(r.text)
            return r.json()
        if r.status_code == 429:
            time.sleep(5 * (t + 1))
            continue
        r.raise_for_status()
    raise RuntimeError(percorso)


def main():
    corrente = datetime.now(timezone.utc).year
    anni = []
    for s in sorted(get("results/seasons"), key=lambda x: x["year"], reverse=True):
        if s["year"] >= corrente:
            continue
        try:
            cats = get("results/categories", seasonUuid=s["id"])
            cat = next((c for c in cats if c["name"].lower().replace("\\u2122", "").strip() in PREMIER), None) or (cats[0] if cats else None)
            if not cat:
                continue
            cl = get("results/standings", seasonUuid=s["id"], categoryUuid=cat["id"]).get("classification") or []
        except Exception as e:
            print(s["year"], "saltata:", e)
            continue
        righe = []
        for x in cl:
            r = x.get("rider") or {}
            righe.append({"pos": x.get("position"), "nome": r.get("full_name"), "paese": (r.get("country") or {}).get("name"), "team": (x.get("team") or {}).get("name"),
                          "moto": (x.get("constructor") or {}).get("name"), "punti": x.get("points"), "vittorie": x.get("race_wins")})
        if righe:
            anni.append({"anno": s["year"], "classe": cat["name"].replace("\\u2122", "").strip(), "classifica": righe})
            print(s["year"], cat["name"], len(righe))
    (ROOT / "docs" / "data" / "motogp-archivio.json").write_text(json.dumps({"anni": anni}, ensure_ascii=False, separators=(",", ":")))
    print(f"Archivio MotoGP: {len(anni)} stagioni")


if __name__ == "__main__":
    main()
