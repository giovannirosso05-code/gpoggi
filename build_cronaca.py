"""Cronaca giro per giro delle gare di F1, scritta dai dati OpenF1 (messaggi della direzione gara, posizioni, giri, pit stop).

Ogni voce è un fatto dei dati: via (con l'eventuale ritardo), safety car, incidenti e decisioni dei commissari, ritiri con il giro,
cambi al comando, pit stop dei primi, arrivo. Le cause dei ritiri non si scrivono se i dati non le riportano.
Scrive docs/data/cronaca/<id gara>.json. Con una sessione dal vivo OpenF1 risponde 401: in quel caso si salta senza errori.
"""
import bisect
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

DATA = Path(__file__).parent / "docs" / "data"
OUT = DATA / "cronaca"
H = {"User-Agent": "GPOggiBot/1.0 (+https://gpoggi.it; progetto non commerciale)"}
ROMA = ZoneInfo("Europe/Rome")
MOTIVI = {"CAUSING A COLLISION": "contatto", "FALSE START - MOVING BEFORE SIGNAL": "falsa partenza", "DRIVING ERRATICALLY": "guida irregolare", "UNSAFE RELEASE": "rilascio pericoloso",
          "TRACK LIMITS": "limiti della pista", "FORCING ANOTHER DRIVER OFF THE TRACK": "ha spinto un avversario fuori pista", "SPEEDING IN THE PIT LANE": "eccesso di velocità ai box"}


def get(percorso, **p):
    for t in range(4):
        time.sleep(0.4 + 2 * t)
        r = requests.get(f"https://api.openf1.org/v1/{percorso}", params=p, headers=H, timeout=60)
        if r.status_code == 429:
            continue
        r.raise_for_status()
        return r.json()
    raise requests.RequestException("troppe richieste")


def ora_it(iso):
    return datetime.fromisoformat(iso).astimezone(ROMA).strftime("%H:%M")


GRIGLIA = {}


def cronaca(g):
    r = next(s for s in g["sessioni"] if s["tipo"] == "Race")
    k, ris = r["key"], [x for x in (r.get("risultati") or [])]
    if not ris:
        return None
    nome = {x["numero"]: x["nome"] for x in ris}
    acr = {x["acronimo"]: x["nome"] for x in ris if x.get("acronimo")}
    cogn = lambda n: (n or "pilota").split()[-1] if n else "pilota"
    giri_tot = max((x["giri"] or 0) for x in ris)
    rc, pit, pos, laps = get("race_control", session_key=k), get("pit", session_key=k), get("position", session_key=k), get("laps", session_key=k)
    inizio_lap = {}
    for l in laps:
        if l.get("date_start"):
            inizio_lap.setdefault(l["driver_number"], []).append((l["date_start"], l["lap_number"]))
    for v in inizio_lap.values():
        v.sort()
    def giro_a(num, data):
        v = inizio_lap.get(num)
        if not v:
            return None
        i = bisect.bisect_right([d for d, _ in v], data) - 1
        return v[max(i, 0)][1]
    ev = []
    add = lambda giro, tipo, testo, ordine=0: ev.append({"giro": giro, "tipo": tipo, "testo": testo, "o": ordine})

    # partenza: ritardo rispetto all'orario previsto, pioggia
    primo = min((d for v in inizio_lap.values() for d, n in v if n == 1), default=None)
    previsto = r["inizio"]
    riga = "Parte la gara"
    if primo:
        ritardo = (datetime.fromisoformat(primo) - datetime.fromisoformat(previsto)).total_seconds() / 60
        riga += f" alle {ora_it(primo)} (ora italiana)"
        if ritardo >= 10:
            h, m = divmod(int(round(ritardo)), 60)
            riga += f", con {f'{h}h ' if h else ''}{m} minuti di ritardo sull'orario previsto delle {ora_it(previsto)}"
    pioggia = next((re.search(r"(\d+)%", x["message"]).group(1) for x in rc if "RISK OF RAIN" in x["message"]), None)
    sospesa = any("STARTING PROCEDURE SUSPENDED" in x["message"] for x in rc)
    if sospesa:
        riga += ". Procedura di partenza sospesa prima del via"
    if pioggia:
        riga += f"; rischio pioggia indicato al {pioggia}%"
    add(1, "via", riga + ".", -1)

    # primo giro: chi guadagna di piu' rispetto alla griglia
    griglia = {}
    if pos and primo:
        for p in pos:
            if p["date"] <= primo:
                griglia[p["driver_number"]] = p["position"]
        fine1 = {}
        for n, v in inizio_lap.items():
            t2 = next((d for d, ln in v if ln == 2), None)
            if t2:
                c = [p for p in pos if p["driver_number"] == n and p["date"] <= t2]
                if c:
                    fine1[n] = c[-1]["position"]
        mov = sorted(((griglia[n] - fine1[n], n) for n in fine1 if n in griglia), reverse=True)[:2]
        mov = [(d, n) for d, n in mov if d >= 3]
        if mov:
            add(1, "sorpasso", "Primo giro: " + "; ".join(f"{cogn(nome.get(n))} risale dal {griglia[n]}° al {fine1[n]}° posto" for d, n in mov) + ".", 1)

    # messaggi della direzione gara
    def nomi(testo):
        trovati = re.findall(r"\((\w{3})\)", testo)
        return " e ".join(cogn(acr.get(a, a)) for a in trovati) or "pilota"
    def motivo(testo):
        for en, it in MOTIVI.items():
            if en in testo:
                return it
        return None
    visti = set()
    # incidenti con due vetture: nomi per riferimento orario, per collegare le penalita' al contatto
    contatti = {}
    for x in rc:
        mt = re.search(r"INCIDENT INVOLVING CARS \d+ \((\w{3})\) AND \d+ \((\w{3})\) NOTED.*\((\d\d:\d\d:\d\d)\)", x["message"])
        if mt:
            contatti[mt.group(3)] = (mt.group(1), mt.group(2))
    for x in rc:
        m, lap, cat = x["message"].strip(), x.get("lap_number") or 1, x["category"]
        if cat == "SafetyCar":
            t = {"SAFETY CAR DEPLOYED": ("safety", "**Safety car in pista.**"), "SAFETY CAR IN THIS LAP": ("safety", "La safety car rientra ai box: si riparte."), "VSC DEPLOYED": ("safety", "**Virtual safety car.**"),
                 "VSC ENDING": ("safety", "Termina la virtual safety car.")}.get(m)
            if t and (t[1], lap) not in visti:
                visti.add((t[1], lap)); add(lap, t[0], t[1], 2)
        elif cat == "Flag" and x.get("flag") == "RED":
            add(lap, "safety", "**Bandiera rossa: gara sospesa.**", 2)
        elif cat == "Other" and re.search(r"INCIDENT INVOLVING CARS", m) and "FIA STEWARDS" not in m and "NOTED" in m and "AND" in m:
            mt = motivo(m)
            if mt in (None, "contatto"):
                add(lap, "incidente", f"**Incidente tra {nomi(m)}.**", 3)
        elif m.startswith("FIA STEWARDS:") and re.search(r"TIME PENALTY FOR", m) and "SERVED" not in m:
            s2 = re.search(r"(\d+) SECOND", m)
            rif = re.search(r"\((\d\d:\d\d:\d\d)\)\s*$", m)
            chi = re.search(r"\((\w{3})\)", m)
            altro = None
            if rif and chi and rif.group(1) in contatti:
                altro = next((a for a in contatti[rif.group(1)] if a != chi.group(1)), None)
            mt = motivo(m)
            motivo_txt = f" per il contatto con {cogn(acr.get(altro, altro))}" if altro else (f" ({mt})" if mt else "")
            add(lap, "penalita", f"**Penalità di {s2.group(1) if s2 else 'alcuni'} secondi a {nomi(m)}**{motivo_txt}.", 4)

    # ritiri col giro in cui si sono fermati
    for x in ris:
        if x.get("stato") == "RIT" and x["giri"] is not None and x["giri"] < giri_tot:
            add(x["giri"] + 1, "ritiro", f"**{x['nome']} si ritira** ({x['giri']} giri completati su {giri_tot}).", 5)

    # cambi al comando e pit stop dei primi sei
    if pos:
        capo, ultimo = None, None
        for p in sorted(pos, key=lambda p: p["date"]):
            if p["position"] != 1 or (primo and p["date"] < primo):
                continue
            if capo is not None and p["driver_number"] != capo:
                lap = giro_a(p["driver_number"], p["date"])
                if lap and lap > 1 and (lap, p["driver_number"]) != ultimo:
                    add(lap, "comando", f"**{cogn(nome.get(p['driver_number']))} passa al comando.**", 6)
                    ultimo = (lap, p["driver_number"])
            capo = p["driver_number"]
    # sorpassi nelle prime cinque posizioni (esclusi pit stop, safety car e ritiri)
    if pos:
        sc = set()
        aperta = None
        for x in sorted(rc, key=lambda x: x["date"]):
            if x["category"] == "SafetyCar":
                if x["message"].strip() in ("SAFETY CAR DEPLOYED", "VSC DEPLOYED"):
                    aperta = x.get("lap_number") or 1
                elif aperta is not None and x["message"].strip() in ("SAFETY CAR IN THIS LAP", "VSC ENDING"):
                    sc.update(range(aperta, (x.get("lap_number") or aperta) + 2)); aperta = None
        if aperta is not None:
            sc.update(range(aperta, giri_tot + 1))
        sta_ai_box = {(p["driver_number"], p["lap_number"] + d) for p in pit if p.get("lap_number") for d in (-1, 0, 1)}
        ritirati = {x["numero"]: (x["giri"] or 0) for x in ris if x.get("stato") == "RIT"}
        tiene = {}
        gia = set()
        for p in sorted(pos, key=lambda p: p["date"]):
            n, nuova = p["driver_number"], p["position"]
            if primo and p["date"] < primo:
                tiene[nuova] = n
                continue
            precedente = next((q for q, d in tiene.items() if d == n), None)
            passato = tiene.get(nuova)
            if precedente is not None and precedente > nuova:
                tiene.pop(precedente, None)
            tiene[nuova] = n
            if nuova <= 5 and precedente is not None and precedente > nuova and passato and passato != n:
                lap = giro_a(n, p["date"])
                if not lap or lap <= 1 or lap in sc or (passato, lap) in sta_ai_box or (n, lap) in sta_ai_box or passato in ritirati and ritirati[passato] <= lap:
                    continue
                if nuova == 1 or (lap, n, passato) in gia:
                    continue  # i cambi al comando sono gia' nella cronaca
                gia.add((lap, n, passato))
                add(lap, "sorpasso", f"**{cogn(nome.get(n))} supera {cogn(nome.get(passato))}** e sale al {nuova}° posto.", 6)
    primi = {x["numero"] for x in ris if x.get("pos") and x["pos"] <= 6}
    per_giro = {}
    for p in pit:
        if p["driver_number"] in primi and p.get("lap_number") and p["lap_number"] > 1 and (p.get("pit_duration") or 0) < 60:
            per_giro.setdefault(p["lap_number"], []).append(cogn(nome.get(p["driver_number"])))
    for lap, lista in per_giro.items():
        add(lap, "pit", ("Ai box: " if len(lista) > 1 else "Ai box: ") + ", ".join(lista) + ".", 7)

    top = sorted((x for x in ris if x.get("pos")), key=lambda x: x["pos"])[:3]
    if len(top) == 3:
        add(giri_tot, "arrivo", f"**Bandiera a scacchi: vince {top[0]['nome']}** ({top[0]['team']}), davanti a {top[1]['nome']} e {top[2]['nome']}.", 9)
    ev.sort(key=lambda e: (e["giro"], e["o"]))
    GRIGLIA.clear()
    GRIGLIA.update({str(n): p for n, p in (griglia or {}).items()})
    return [{"giro": e["giro"], "tipo": e["tipo"], "testo": e["testo"]} for e in ev], giri_tot


def main():
    OUT.mkdir(exist_ok=True)
    eventi = json.loads((DATA / "events.json").read_text())
    ora = datetime.now(timezone.utc).isoformat()
    for e in eventi:
        if e["fine"] > ora:
            continue
        f = OUT / f"{e['id']}.json"
        if f.exists() and f.stat().st_size > 50:
            continue
        g = json.loads((DATA / "gare" / f"{e['id']}.json").read_text())
        try:
            r = cronaca(g)
        except requests.RequestException as ex:
            print(f"  {e['nome']}: dati non disponibili ({ex})")
            continue
        if r:
            f.write_text(json.dumps({"giri": r[1], "griglia": dict(GRIGLIA), "voci": r[0]}, ensure_ascii=False, indent=1))
            print(f"{e['nome']}: {len(r[0])} voci")


if __name__ == "__main__":
    main()
