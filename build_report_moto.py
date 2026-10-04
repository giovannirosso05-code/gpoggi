"""Report di gara della MotoGP (e vincitori di Moto2 e Moto3), scritti dai dati del servizio pubblico del campionato.

Per ogni gara disputata del 2026: condizioni della pista, podio e distacco, pole, giro veloce (con numero del giro e record),
sprint del sabato e ritiri con il giro in cui si sono fermati. Non si scrive nessuna causa di caduta o guasto che i dati non riportano.
Scrive docs/data/motogp-report.json.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import build_motogp as bm

OUT = Path(__file__).parent / "docs" / "data" / "motogp-report.json"
OUT_GARE = Path(__file__).parent / "docs" / "data" / "motogp-gare.json"
PISTA = {"dry": "asciutta", "wet": "bagnata", "damp": "umida"}
CIELO = {"cloudy": "nuvoloso", "sunny": "soleggiato", "overcast": "coperto", "rain": "pioggia", "rainy": "pioggia", "clear": "sereno", "partly cloudy": "poco nuvoloso", "fog": "nebbia"}
ORDINALE = {1: "primo", 2: "secondo", 3: "terzo"}


def sec(g):
    try:
        return f"{float(g):.3f}".rstrip("0").rstrip(".").replace(".", ",")
    except (TypeError, ValueError):
        return None


def tempo_giro(t):
    """'01:43.041' -> '1:43.041'."""
    return t.lstrip("0").lstrip(":") if t else t


def classifica(sid):
    return bm.api_cache(f"results/session/{sid}/classification", test="false")


def righe(cl):
    return [{"pos": x.get("position"), "nome": x["rider"]["full_name"], "numero": x["rider"].get("number"), "team": x["team"]["name"], "moto": x["constructor"]["name"],
             "tempo": x.get("time"), "distacco": (x.get("gap") or {}).get("first"), "giri": x.get("total_laps"), "stato": x.get("status"), "punti": x.get("points")} for x in cl["classification"]]


def classifiche_evento(e, cat_ids):
    """Classifica completa della gara per MotoGP, Moto2 e Moto3, piu' la sprint della MotoGP."""
    out = {}
    for c, cid in cat_ids.items():
        if c not in ("MotoGP", "Moto2", "Moto3"):
            continue
        sess = bm.api_cache("results/sessions", eventUuid=e["id"], categoryUuid=cid)
        for tipo, chiave in (("RAC", c), ("SPR", c + " sprint")):
            q = next((x for x in sess if x["type"] == tipo), None)
            if q and (tipo == "RAC" or c == "MotoGP"):
                try:
                    out[chiave] = righe(classifica(q["id"]))
                except Exception:
                    pass
    return out


def report_evento(e, cat_ids):
    nome_gp = bm.nome_gp_moto(e.get("name"), (e.get("circuit") or {}).get("country"))
    sess = bm.api_cache("results/sessions", eventUuid=e["id"], categoryUuid=cat_ids["MotoGP"])
    rac = next((q for q in sess if q["type"] == "RAC"), None)
    if not rac:
        return None
    cl = classifica(rac["id"])
    arrivati = [x for x in cl["classification"] if x.get("position")]
    if len(arrivati) < 3:
        return None
    top = arrivati[:3]
    giri = max((x.get("total_laps") or 0) for x in cl["classification"])
    par = []
    cond = rac.get("condition") or {}
    parti = []
    if cond.get("track"):
        parti.append(f"pista {PISTA.get(cond['track'].lower(), cond['track'].lower())}")
    if cond.get("weather"):
        parti.append(f"cielo {CIELO.get(cond['weather'].lower(), cond['weather'].lower())}")
    if cond.get("air"):
        parti.append(f"aria a {cond['air'].replace('º', '°')}")
    if cond.get("ground"):
        parti.append(f"asfalto a {cond['ground'].replace('º', '°')}")
    gap2 = sec((top[1].get("gap") or {}).get("first"))
    riga = (f"{top[0]['rider']['full_name']} ({top[0]['constructor']['name']}) vince il {nome_gp} di MotoGP"
            f"{f' con {gap2} secondi di vantaggio su' if gap2 else ' davanti a'} {top[1]['rider']['full_name']}; terzo {top[2]['rider']['full_name']}.")
    if parti:
        riga += " Condizioni: " + ", ".join(parti) + "."
    par.append(riga)
    # pole e giro veloce
    pole = next((r for r in cl.get("records", []) if r["type"] == "poleLap"), None)
    if pole:
        par.append(f"Pole position di {pole['rider']['full_name']} con {tempo_giro(pole['bestLap']['time'])}" + (", nuovo record della pista." if pole.get("isNewRecord") else "."))
    veloce = next((r for r in cl.get("records", []) if r["type"] == "fastestLap"), None)
    if veloce:
        s = f"Giro più veloce in gara: {veloce['rider']['full_name']}, {tempo_giro(veloce['bestLap']['time'])}"
        if veloce["bestLap"].get("number"):
            s += f" al giro {veloce['bestLap']['number']} di {giri}"
        if veloce.get("speed"):
            s += f" ({veloce['speed'].replace('.', ',')} km/h di media)"
        s += ", nuovo record del giro in gara." if veloce.get("isNewRecord") else "."
        par.append(s)
    # sprint
    spr = next((q for q in sess if q["type"] == "SPR"), None)
    if spr:
        s3 = [x for x in classifica(spr["id"])["classification"] if x.get("position")][:3]
        if len(s3) == 3:
            par.append(f"Sprint del sabato: vince {s3[0]['rider']['full_name']} ({s3[0]['constructor']['name']}), davanti a {s3[1]['rider']['full_name']} e {s3[2]['rider']['full_name']}.")
    # ritiri: chi non ha finito, con i giri fatti
    fuori = [x for x in cl["classification"] if not x.get("position") and (x.get("total_laps") or 0) < giri]
    if fuori:
        elenco = ", ".join(f"{x['rider']['full_name']} (giri completati: {x.get('total_laps') or 0} su {giri})" for x in sorted(fuori, key=lambda x: -(x.get("total_laps") or 0)))
        par.append(f"Ritirati: {elenco}.")
    # Moto2 e Moto3
    altri = []
    for c in ("Moto2", "Moto3"):
        try:
            s = bm.api_cache("results/sessions", eventUuid=e["id"], categoryUuid=cat_ids[c])
            r = next(q for q in s if q["type"] == "RAC")
            v = next(x for x in classifica(r["id"])["classification"] if x.get("position") == 1)
            altri.append(f"{c}: {v['rider']['full_name']} ({v['constructor']['name']})")
        except (StopIteration, KeyError):
            pass
    if altri:
        par.append("Vincitori delle altre classi: " + "; ".join(altri) + ".")
    # cronaca giro per giro: i dati del campionato dicono chi si e' fermato e a che giro, il giro veloce e il vincitore
    cr = [{"giro": 1, "tipo": "via", "testo": "Via della gara" + (f" con {', '.join(parti)}" if parti else "") + "."}]
    for x in sorted(fuori, key=lambda x: (x.get("total_laps") or 0)) if fuori else []:
        cr.append({"giro": (x.get("total_laps") or 0) + 1, "tipo": "ritiro", "testo": f"{x['rider']['full_name']} si ritira ({x.get('total_laps') or 0} giri completati su {giri})."})
    if veloce and veloce["bestLap"].get("number"):
        cr.append({"giro": veloce["bestLap"]["number"], "tipo": "giro", "testo": f"Giro più veloce: {veloce['rider']['full_name']}, {tempo_giro(veloce['bestLap']['time'])}" + (", nuovo record in gara." if veloce.get("isNewRecord") else ".")})
    cr.append({"giro": giri, "tipo": "arrivo", "testo": f"Bandiera a scacchi: vince {top[0]['rider']['full_name']} ({top[0]['constructor']['name']}), davanti a {top[1]['rider']['full_name']} e {top[2]['rider']['full_name']}."})
    cr.sort(key=lambda c: c["giro"])
    GARE[nome_gp] = {"nome": nome_gp, "circuito": (e.get("circuit") or {}).get("name"), "data": e["date_end"], "classifiche": classifiche_evento(e, cat_ids), "cronaca": cr}
    return {"gp": nome_gp, "circuito": (e.get("circuit") or {}).get("name"), "data": e["date_end"], "titolo": f"{top[0]['rider']['full_name']} vince il {nome_gp}", "paragrafi": par}


GARE = {}


def main():
    anno = datetime.now(timezone.utc).year
    stagione = next(x for x in bm.api("results/seasons") if x["year"] == anno)["id"]
    cat_ids = {x["name"].replace("™", ""): x["id"] for x in bm.api("results/categories", seasonUuid=stagione)}
    eventi = sorted((e for e in bm.api("results/events", seasonUuid=stagione, isFinished="true") if not e.get("test")), key=lambda e: e["date_start"])
    out = [r for r in (report_evento(e, cat_ids) for e in eventi) if r]
    out.sort(key=lambda r: r["data"], reverse=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    OUT_GARE.write_text(json.dumps(GARE, ensure_ascii=False))
    print(f"Report MotoGP: {len(out)}")


if __name__ == "__main__":
    main()
