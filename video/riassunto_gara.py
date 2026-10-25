"""Riassunto della gara di F1 appena finita, tutto dai dati del sito (risultati, griglia, classifica): niente cause inventate, niente frasi senza numeri.

Scene: gancio sul vincitore, podio disegnato, un pilota che ha reso più del previsto, uno che ha deluso (solo se i numeri lo dicono: partenza e arrivo),
il mondiale di chi lo guida e come può chiuderlo alla gara dopo (calcolo nostro sui punti rimasti: si dichiara).
Se la classifica del sito non è ancora aggiornata dopo la gara, i punti sono ricalcolati da noi e il video lo dice.

Uso:  python3 riassunto_gara.py [--bene "Charles Leclerc"] [--male "George Russell"] [--invia] [--uscita FILE]
"""
import argparse, asyncio, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notizia_sub as NS  # noqa: E402
import notizie_giorno as NG  # noqa: E402
import ritratti_espn as R  # noqa: E402

DATA = NS.DATA
PTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
UN = "zero uno due tre quattro cinque sei sette otto nove dieci undici dodici tredici quattordici quindici sedici diciassette diciotto diciannove venti".split()
ORD = {1: "primo", 2: "secondo", 3: "terzo", 4: "quarto", 5: "quinto", 6: "sesto", 7: "settimo", 8: "ottavo", 9: "nono", 10: "decimo", 11: "undicesimo", 12: "dodicesimo",
       13: "tredicesimo", 14: "quattordicesimo", 15: "quindicesimo", 16: "sedicesimo", 17: "diciassettesimo", 18: "diciottesimo", 19: "diciannovesimo", 20: "ventesimo"}
pp = lambda pos: PTS[pos - 1] if pos and 1 <= pos <= 10 else 0
cogn = lambda n: n.split()[-1]


def carica(ordine=None):
    """ordine: lista di nomi in ordine d'arrivo presa da testate autorevoli, usata quando i dati del sito non hanno ancora la gara (squadre dalle qualifiche)."""
    ora = datetime.now(timezone.utc).isoformat()
    eventi = json.load(open(DATA / "events.json"))
    passati = [g for g in eventi if g["inizio"] < ora]
    for g in sorted(passati, key=lambda g: g["inizio"], reverse=True):
        det = json.load(open(DATA / "gare" / f"{g['id']}.json"))
        gara = next((s for s in det["sessioni"] if s["tipo"] == "Race" and s.get("risultati")), None)
        if not gara and ordine and det["sessioni"]:
            qq = next((s for s in det["sessioni"] if s["tipo"] == "Qualifying"), {})
            team = {x["nome"]: x["team"] for x in (qq.get("risultati") or [])}
            gara = {"risultati": [{"pos": i + 1, "nome": n, "team": team.get(n, ""), "stato": None, "tempo": None} for i, n in enumerate(ordine)]}
        if gara:
            q = next((s for s in det["sessioni"] if s["tipo"] == "Qualifying"), {})
            griglia = {x["nome"]: x["pos"] for x in (q.get("risultati") or []) if x.get("pos")}
            prossimo = next((x for x in sorted(eventi, key=lambda x: x["inizio"]) if x["inizio"] > g["inizio"]), None)
            dopo = [x for x in eventi if x["inizio"] > g["inizio"]]
            return g, gara["risultati"], griglia, prossimo, dopo
    raise SystemExit("nessuna gara con risultati")


def punti_mondiale(g, ris):
    """Classifica piloti dopo la gara: quella del sito se è già aggiornata, altrimenti ricalcolata da noi (si dichiara)."""
    st = json.load(open(DATA / "standings.json"))
    pil = {p["nome"]: p["punti"] for p in st["piloti"]}
    if st.get("dopo") == g["nome"]:
        return pil, False
    return {n: pil.get(n, 0) + pp(next((x["pos"] for x in ris if x["nome"] == n), None)) for n in pil}, True


def vittorie(g, vinc):
    """Vittorie stagionali (dai risultati del sito + la gara appena finita): servono allo spareggio a pari punti."""
    w = {}
    for f in (DATA / "gare").glob("*.json"):
        d = json.load(open(f))
        if str(d.get("id", f.stem)) == str(g["id"]):
            continue
        for ses in d["sessioni"]:
            if ses["tipo"] == "Race" and ses.get("risultati"):
                r = sorted((x for x in ses["risultati"] if x.get("pos")), key=lambda x: x["pos"])
                if r:
                    w[r[0]["nome"]] = w.get(r[0]["nome"], 0) + 1
    w[vinc] = w.get(vinc, 0) + 1
    return w


def scenario(punti, leader, n_dopo, vitt=None):
    """Come può chiudere il titolo alla gara dopo, con 25 punti a gara nelle gare ancora rimaste (nessuna sprint nel calendario): dict con il necessario per la voce."""
    resto = 25 * (n_dopo - 1)   # punti ancora in palio dopo la prossima gara
    rivali = sorted(((n, p) for n, p in punti.items() if n != leader), key=lambda x: -x[1])
    out = {"resto": resto, "rivali": []}
    for n, p in rivali[:3]:
        L = punti[leader] - p
        out["rivali"].append({"nome": n, "L": L, "chiuso_gia": L > 25 + resto})
    r0 = out["rivali"][0]
    # vincendo (25 punti), il rivale più vicino al massimo secondo (18): chiude se 25 - 18 > resto - L
    r0["basta_vincere"] = all(25 - 18 > resto - x["L"] for x in out["rivali"])
    # punti massimi concessi al rivale più vicino se Antonelli vince: a - r > resto - L
    r_max = 25 - (resto - r0["L"]) - 1
    r0["punti_max_rivale"] = r_max
    # posizione minima che chiude il titolo alla prossima gara anche se il rivale vince (25): L - 25 + punti > resto
    # pari punti: vale lo spareggio per vittorie (il rivale vince tutte le gare rimaste, compresa la prossima)
    vitt = vitt or {}
    def basta(pos):
        for x in out["rivali"]:
            d = x["L"] - 25 + pp(pos) - resto
            if d > 0:
                continue
            if d == 0 and vitt and vitt.get(leader, 0) + (1 if pos == 1 else 0) > vitt.get(x["nome"], 0) + n_dopo:
                continue
            return False
        return True
    r0["pos_basta"] = max((pos for pos in range(1, 23) if basta(pos)), default=None)
    r0["pos_min_rivale"] = next((pos for pos in range(1, 23) if pp(pos) <= r_max), 11) if r_max >= 0 else None
    return out


def descr(nome, ris, griglia):
    r = next((x for x in ris if x["nome"] == nome), None)
    if not r:
        return None
    return {"pos": r["pos"], "griglia": griglia.get(nome), "stato": r.get("stato"), "team": r["team"], "tempo": r.get("tempo")}


def costruisci(bene, male, ordine=None):
    g, ris, griglia, prossimo, dopo = carica(ordine)
    ris = sorted((x for x in ris if x.get("pos")), key=lambda x: x["pos"])
    luogo = g["circuito"]
    vinc = ris[0]
    punti, ricalcolati = punti_mondiale(g, ris)
    leader = max(punti, key=punti.get)
    colori = {p["nome"]: tuple(int(p["colore"][i:i + 2], 16) for i in (0, 2, 4)) for p in json.load(open(DATA / "roster.json")) if p.get("colore")}

    def espn(n):
        try:
            return {"foto_file": str(R.ritratto(n, colori.get(n, (232, 53, 47)))), "credito": "Foto: ESPN"}
        except (SystemExit, Exception) as e:
            print(f"  ritratto ESPN non disponibile per {n}: {e}")
            return {}

    def tondo(n):
        e = espn(n)
        if not e:
            return {}
        from PIL import Image
        im = Image.open(e["foto_file"]).convert("RGB"); w, h = im.size
        f = Path(e["foto_file"]).with_name(Path(e["foto_file"]).stem + "_tondo.jpg")
        im.crop((int(w * 0.12), 90, int(w * 0.88), 90 + int(w * 0.76))).resize((600, 600)).save(f, "JPEG", quality=90)
        return {"file": str(f), "credito": "ESPN"}

    titolo = f"{luogo}: vince {cogn(vinc['nome'])}!"
    scene = [{"foto": vinc["nome"], "hook": True, "hook_titolo": titolo, "testo": titolo, **espn(vinc["nome"])}]
    # podio
    podio = {"titolo": f"Il podio: {g['nome']}", "sotto": f"Partenza di {cogn(vinc['nome'])}: {griglia.get(vinc['nome'], '—')}°",
             "righe": [{"pos": r["pos"], "nome": r["nome"], "cognome": cogn(r["nome"]), "nota": r["team"], **tondo(r["nome"])} for r in ris[:3]]}
    voce_p = f"Ecco il podio: primo {cogn(ris[0]['nome'])}, secondo {cogn(ris[1]['nome'])}, terzo {cogn(ris[2]['nome'])}."
    scene.append({"foto": vinc["nome"], "pista": True, "podio": podio, "sub_top": 1450, "testo": voce_p})
    # chi ha reso di più, chi ha deluso
    res = {}
    for n, ruolo in ((bene, "bene"), (male, "male")):
        d = descr(n, ris, griglia)
        if not d:
            continue
        res[ruolo] = d
        part = d["griglia"]
        ch = []
        if d["pos"]:
            ch.append(("si" if ruolo == "bene" else "no", f"Partito {part}°, arrivato {d['pos']}°" if part else f"Arrivato {d['pos']}°"))
            if part and d["pos"] != part:
                ch.append(("si" if d["pos"] < part else "no", f"{'Guadagna' if d['pos'] < part else 'Perde'} {abs(part - d['pos'])} {'posizione' if abs(part - d['pos']) == 1 else 'posizioni'}"))
        guad = (part - d["pos"]) if part and d["pos"] else 0
        if ruolo == "bene" and not (d["pos"] and (d["pos"] <= 3 or guad >= 2)):
            print(f"  ATTENZIONE: {n} non ha avuto una gara da 'grande' (partito {part}, arrivato {d['pos']}): la frase è neutra")
            attacco = "Gara di"
        elif ruolo == "male" and not (guad <= -2 or (d["stato"] and str(d["stato"]).lower() not in ("finished", "classified", "+1 lap"))):
            print(f"  ATTENZIONE: {n} non ha deluso nei numeri (partito {part}, arrivato {d['pos']}): la frase è neutra")
            attacco = "Gara di"
        else:
            attacco = "Un grande" if ruolo == "bene" else "Weekend difficile per"
        voce = (f"{attacco} *{cogn(n)}*: " +
                (f"partito {ORD.get(part, str(part) + '°')}, arriva {ORD.get(d['pos'], str(d['pos']) + '°')}" if part else f"arriva {ORD.get(d['pos'], str(d['pos']) + '°')}") + ".")
        scene.append({"foto": n, "nome": n, "chips": ch, "sub_top": 1440, "testo": voce, **espn(n)})
    # il mondiale
    sc = scenario(punti, leader, len(dopo), vittorie(g, vinc['nome']))
    r0 = sc["rivali"][0]
    ch_m = [("si", f"{leader}: {punti[leader]:g} punti{' · calcolo GP Oggi' if ricalcolati else ''}"), ("info", f"+{r0['L']:g} su {cogn(r0['nome'])}")]
    # con punti ricalcolati da noi niente numeri a voce (la dichiarazione resta scritta nelle chips e in didascalia)
    voce_m = (f"Nel mondiale {cogn(leader)} è sempre primo." if ricalcolati else f"Nel mondiale {cogn(leader)} è primo con {punti[leader]:g} punti, {r0['L']:g} su {cogn(r0['nome'])}.")
    scene.append({"foto": leader, "nome": leader, "chips": ch_m, "sub_top": 1440, "testo": voce_m, **espn(leader)})
    if prossimo:
        nome_p = re.sub(r"^Gran Premio (di|del|dello|della|degli|d')\s*", "", prossimo["nome"])
        if r0["chiuso_gia"]:
            frase = f"Il titolo è già suo."
            ch_t = [("si", "Titolo già matematico")]
        elif r0["pos_basta"] is not None and r0["pos_basta"] > 1:
            frase = f"A {nome_p} gli basta un {ORD.get(r0['pos_basta'], str(r0['pos_basta']) + '°')} posto per essere campione del mondo."
            ch_t = [("si", f"{r0['pos_basta']}° posto a {nome_p} e il titolo è suo"), ("info", "Calcolo GP Oggi: punti rimasti e vittorie")]
        elif r0["basta_vincere"]:
            frase = f"Se vince a {nome_p}, è campione del mondo con quattro gare d'anticipo."
            ch_t = [("si", f"Vince a {nome_p}: campione già lì")]
        elif r0["punti_max_rivale"] is not None and r0["punti_max_rivale"] >= 0:
            frase = (f"A {nome_p} lo chiude se vince e {cogn(r0['nome'])} non fa più di {r0['punti_max_rivale']} punti, cioè non arriva più avanti del {ORD.get(r0['pos_min_rivale'], str(r0['pos_min_rivale']) + '°')} posto.")
            ch_t = [("info", f"Vince e {cogn(r0['nome'])} ≤ {r0['pos_min_rivale']}° posto: campione")]
        else:
            frase = f"A {nome_p} non può ancora chiudere il titolo."
            ch_t = [("info", f"Non ancora a {nome_p}")]
        scene.append({"foto": leader, "nome": f"Il titolo a {nome_p}", "chips": ch_t, "sub_top": 1440, "testo": frase, **espn(leader)})
    spec = {"serie": "F1", "titolo_breve": luogo, "etichetta": "Riassunto gara", "fonte": "risultati ufficiali, calcoli GP Oggi", "velocita": "+38%", "scene": scene,
            "finale": {"foto": vinc["nome"], "domanda": f"{cogn(leader)} campione già a {nome_p}?" if prossimo else "Che ne pensi della gara?"}}
    social = (f"🏁 {luogo}: vince {vinc['nome']}! 🏆\n\n" + (f"👏 {bene}: partito {res['bene']['griglia']}°, arrivato {res['bene']['pos']}°\n" if "bene" in res and res["bene"]["griglia"] else "")
              + (f"😬 {male}: partito {res['male']['griglia']}°, arrivato {res['male']['pos']}°\n" if "male" in res and res["male"]["griglia"] else "")
              + f"📊 {leader} è primo nel mondiale con {punti[leader]:g} punti{' (calcolo GP Oggi)' if ricalcolati else ''}\n\n"
              + f"E tu che dici? Dimmi la tua nei commenti 👇\n\n🔗 gpoggi.it\n\n#gpoggi #f1 #formula1 #{re.sub(r'[^a-z]', '', luogo.lower())}")
    return spec, social, res, sc, punti, ricalcolati, g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bene", default="Charles Leclerc"); ap.add_argument("--male", default="George Russell")
    ap.add_argument("--ordine", type=Path, help="file JSON con i nomi in ordine d'arrivo (da testate autorevoli)")
    ap.add_argument("--prova", action="store_true", help="stampa i fatti e le scene senza fare il video")
    ap.add_argument("--invia", action="store_true"); ap.add_argument("--uscita", type=Path, default=NS.QUI / "riassunto_gara.mp4")
    a = ap.parse_args()
    spec, social, res, sc, punti, ricalcolati, g = costruisci(a.bene, a.male, json.load(open(a.ordine)) if a.ordine else None)
    print("Risultati:", json.dumps(res, ensure_ascii=False), "\nScenario:", json.dumps(sc, ensure_ascii=False), "\nRicalcolati:", ricalcolati)
    for s in spec["scene"]:
        print(" *", {k: v for k, v in s.items() if k in ("hook_titolo", "nome", "chips", "testo")})
    print(social)
    if a.prova:
        return
    asyncio.run(NS.genera(spec, a.uscita))
    if a.invia:
        NG.telegram(a.uscita, f"🏁 {g['nome']}: riassunto", social)


if __name__ == "__main__":
    main()
