"""Griglia di partenza provvisoria della MotoGP, subito dopo le qualifiche (pagina Live).

Quando la Q2 del weekend in corso è finita e la gara non è ancora partita, scrive docs/data/motogp-griglia.json con l'ordine delle qualifiche
(prima la Q2, poi chi si è fermato in Q1). Le penalità in griglia NON sono incluse: la griglia ufficiale arriva dopo. Altrimenti il file resta vuoto ({}).
Niente cache: le sessioni cambiano mentre si svolgono.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import build_motogp as bm

OUT = Path(__file__).parent / "docs" / "data" / "motogp-griglia.json"


def tempo(t):
    return t.lstrip("0").lstrip(":") if t else t


def main():
    anno = datetime.now(timezone.utc).year
    stag = next(x for x in bm.api("results/seasons") if x["year"] == anno)["id"]
    cat = next(x["id"] for x in bm.api("results/categories", seasonUuid=stag) if x["name"].replace("™", "") == "MotoGP")
    eventi = sorted((e for e in bm.api("results/events", seasonUuid=stag) if not e.get("test") and e.get("status") != "FINISHED"), key=lambda e: e["date_start"])
    if not eventi:
        OUT.write_text("{}"); return
    e = eventi[0]
    sess = bm.api("results/sessions", eventUuid=e["id"], categoryUuid=cat)
    gara = next((q for q in sess if q["type"] == "RAC"), None)
    q2 = next((q for q in sess if q["type"] == "Q" and q.get("number") == 2), None)
    if not gara or gara.get("status") in ("FINISHED", "CANCELLED") or not q2 or q2.get("status") != "FINISHED":
        OUT.write_text("{}"); return
    righe, visti = [], set()
    for numero in (2, 1):
        q = next((x for x in sess if x["type"] == "Q" and x.get("number") == numero), None)
        if not q or q.get("status") != "FINISHED":
            continue
        for x in sorted((y for y in bm.api(f"results/session/{q['id']}/classification", test="false")["classification"] if y.get("position")), key=lambda y: y["position"]):
            if x["rider"]["id"] in visti:
                continue
            visti.add(x["rider"]["id"])
            righe.append({"pos": len(righe) + 1, "nome": x["rider"]["full_name"], "team": x["team"]["name"], "moto": x["constructor"]["name"],
                          "info": tempo((x.get("best_lap") or {}).get("time")), "da": f"Q{numero}"})
    if len(righe) < 10:
        OUT.write_text("{}"); return
    OUT.write_text(json.dumps({"gp": bm.nome_gp_moto(e.get("name"), (e.get("country") or {}).get("name")), "gara_inizio": gara["date"],
                               "aggiornato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "righe": righe}, ensure_ascii=False, indent=1))
    print("Griglia MotoGP:", len(righe), "piloti")


if __name__ == "__main__":
    main()
