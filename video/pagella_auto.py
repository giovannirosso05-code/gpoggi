"""Pagella del weekend, tutta automatica: dai voti di docs/data/pagella.json scrive scaletta, copertina e didascalia in video/spec/.
Uso:  python video/pagella_auto.py            (fa i weekend F1 e MotoGP non ancora fatti, ricordati in video/pagella_fatte.json)
      python video/pagella_auto.py --forza    (rifa anche quelli gia' fatti)
Il video lo genera poi il workflow "Video da spec" (voce, grafica, invio su Telegram).
Il gancio parte da chi ha preso un voto basso o e' stato corretto in negativo, mai dal migliore; poi i voti da sotto a sopra, il migliore per ultimo.
Ogni frase viene dai dati (posizioni, griglia, cronaca, correzioni dichiarate): niente cause inventate."""
import json
import subprocess
import sys
from pathlib import Path

QUI = Path(__file__).parent
DATA = QUI.parent / "docs" / "data"
ORD = ["", "primo", "secondo", "terzo", "quarto", "quinto", "sesto", "settimo", "ottavo", "nono", "decimo", "undicesimo", "dodicesimo", "tredicesimo",
       "quattordicesimo", "quindicesimo", "sedicesimo", "diciassettesimo", "diciottesimo", "diciannovesimo", "ventesimo", "ventunesimo", "ventiduesimo",
       "ventitreesimo", "ventiquattresimo", "venticinquesimo", "ventiseiesimo"]
NUM = ["zero", "uno", "due", "tre", "quattro", "cinque", "sei", "sette", "otto", "nove", "dieci"]
MOTO = {"Ducati": "e1251b", "Aprilia": "7b2c8f", "KTM": "f26a1b", "Yamaha": "1d4fa3", "Honda": "dcdce2"}
GENERICHE = ("ha chiuso dove era partito", "ha chiuso a un passo dalla posizione di partenza")
RIDONDANTI = ("ha recuperato", "ha guadagnato", "ha perso", "è stato costante", "è uscito nella sprint", "è mancato nella sprint", "non ha firmato", "ha vinto", "è salito sul podio")


def ordinale(n):
    return ORD[n] if n < len(ORD) else f"{n}º"


def voto_parole(v):
    return NUM[int(v)] + (" e mezzo" if v != int(v) else "")


def fmt(v):
    return str(v).replace(".0", "").replace(".", ",")


def cognome(r):
    c = r["nome"].split()[-1]
    return "Marc Marquez" if r["nome"] == "Marc Marquez" else ("Alex Marquez" if r["nome"] == "Alex Marquez" else c)


def breve(r):
    c = r["nome"].split()[-1]
    return r["nome"].split()[0][0] + ". Marquez" if c == "Marquez" else c


def frase_sessioni(r, sprint):
    q = f"{ordinale(r['q'])} in qualifica" if r["q"] else "senza tempo in qualifica"
    parti = [q]
    if sprint:
        parti.append(f"{ordinale(r['s'])} nella sprint" if r["s"] else "fuori nella sprint")
    if r["g"]:
        g = f"{ordinale(r['g'])} in gara"
        if r.get("griglia") and r["griglia"] != r["g"] and abs(r["griglia"] - r["g"]) >= 3:
            g += f", partendo {ordinale(r['griglia'])}"
        parti.append(g)
    else:
        parti.append(f"{verbo_ritiro(r)} al giro {r['ritiro_giro']}" if r.get("ritiro_giro") else f"{verbo_ritiro(r)} in gara")
    return ", ".join(parti[:-1]) + " e " + parti[-1]


def frase_sessioni_breve(r, sprint):
    if r["q"] == 1 and (not sprint or r["s"] == 1) and r["g"] == 1:
        return "ha vinto tutto"
    sorp = r.get("sorpassi", 0)
    if sorp >= 1:
        return f"con {'un sorpasso' if sorp == 1 else str(sorp) + ' sorpassi'}"
    return "costante dalla qualifica alla gara" if "è stato costante in tutte le sessioni" in r.get("perche", []) else "con punti pesanti"


def tripletta(r, sprint):
    if r["q"] == 1 and r["g"] == 1 and (not sprint or r["s"] == 1):
        return "Pole, sprint e gara: una tripletta." if sprint else "Pole e vittoria: un weekend perfetto."
    return ""


CHIUSURE = ["Voto *{v}*.", "Per lui oggi *{v}*.", "Si prende *{v}*.", "Gli diamo *{v}*.", "Voto *{v}*.", "Per lui oggi *{v}*."]


def scena(r, sprint, alt, i=0):
    resto = [x for x in r.get("perche", []) if x not in GENERICHE and not x.startswith(RIDONDANTI)]
    if not r["g"]:
        resto = []   # il ritiro e' gia' nella frase delle sessioni
    extra = (resto[0][0].upper() + resto[0][1:] + ".") if resto else (frase_ritiro(r) if not r["g"] else "")
    if r.get("correzione"):
        extra += " " + r["motivo"][0].upper() + r["motivo"][1:] + "."
    testo = f"[{cognome(r)}]: {frase_sessioni(r, sprint)}. {extra} {CHIUSURE[i % len(CHIUSURE)].format(v=voto_parole(r['voto']))}".replace("  ", " ")
    return {"foto": r["nome"], **alt, "testo": testo}


def art(marca):
    return ("l'" if marca[0].upper() in "AEIOU" else "la ") + marca


def foto_gancio(nome):
    """Per il gancio una foto diversa dal solito: in tuta/maglia della squadra se c'e', altrimenti sorridente."""
    try:
        extra = json.load(open(DATA / "foto-extra.json")).get(nome, {})
    except Exception:
        return {}
    for k in ("ferrari", "tuta", "sorriso"):
        if k in extra:
            return {"alt": k}
    return {}


def marche_moto():
    try:
        tot = {}
        for p in json.load(open(DATA / "motogp-classifica.json"))["categorie"]["MotoGP"]:
            tot[p["moto"]] = tot.get(p["moto"], 0) + p["punti"]
        return tot
    except Exception:
        return {}


def vittorie_di_fila(serie, w, nome):
    """Quante gare consecutive ha vinto il pilota fino a questo weekend (dai risultati sul sito)."""
    vinc = []
    try:
        if serie == "f1":
            for f in (DATA / "gare").glob("*.json"):
                g = json.load(open(f))
                gara = next((x for x in g["sessioni"] if x["tipo"] == "Race" and x.get("risultati")), None)
                if gara:
                    vinc.append((gara["inizio"], gara["risultati"][0]["nome"]))
        else:
            for g in json.load(open(DATA / "motogp-gare.json")).values():
                c = g["classifiche"].get("MotoGP")
                if c:
                    vinc.append((g["data"], c[0]["nome"]))
    except Exception:
        return 0
    vinc.sort()
    n = 0
    for _, v in reversed([x for x in vinc if x[0][:10] <= w["data"][:10]]):
        if v != nome:
            break
        n += 1
    return n


def causa_ritiro(serie, gp_nome, nome):
    """'caduta', 'tecnico' o 'sconosciuta' (default): si scrive a mano in docs/data/pagella-note.json solo se c'e' una fonte."""
    try:
        return json.load(open(DATA / "pagella-note.json")).get(serie, {}).get(gp_nome, {}).get(nome, "sconosciuta")
    except Exception:
        return "sconosciuta"


def frase_ritiro(r):
    """Frase sul ritiro solo se la causa e' verificata (pagella-note.json); altrimenti non si dice niente."""
    c = r.get("causa", "sconosciuta")
    if c == "tecnico":
        return "Problema tecnico: il voto va diviso tra lui e il team."
    if c == "fisico":
        return "Si ritira per il dolore alla spalla."
    return ""


def verbo_ritiro(r):
    return "caduto" if r.get("causa") == "caduta" else "ritirato"


def prominenza(serie):
    try:
        if serie == "f1":
            return {p["nome"]: p["punti"] for p in json.load(open(DATA / "standings.json"))["piloti"]}
        return {p["nome"]: p["punti"] for p in json.load(open(DATA / "motogp-classifica.json"))["categorie"]["MotoGP"]}
    except Exception:
        return {}


def foto_pista(serie, nome):
    try:
        extra = json.load(open(DATA / "foto-extra.json")).get(nome, {})
    except Exception:
        return {}
    for k in ("pista", "pista_suzuka", "pista_cina", "pista_bahrain"):
        if k in extra:
            return {"alt": k, "pista": True}
    return {}


def costruisci(serie, w):
    sprint, righe = w["sprint"], w["righe"]
    gp = w["nome"].replace("Gran Premio d'", "").replace("Gran Premio di ", "").replace("Gran Premio del ", "").replace("Gran Premio dell'", "").replace("GP ", "")
    gp_art = w["nome"].replace("Gran Premio", "Gran Premio").replace("GP ", "GP ")
    punti = prominenza(serie)
    for r in righe:
        r["causa"] = causa_ritiro(serie, w["nome"], r["nome"])
    asc = sorted(righe, key=lambda r: (r["voto_esatto"], -(punti.get(r["nome"], 0))))
    migliore = righe[0]
    scelti = []

    def aggiungi(r):
        if r and r not in scelti and r is not migliore:
            scelti.append(r)
    basso = asc[0]
    noti_bassi = [r for r in asc if r["voto"] <= 4.5]
    noto = max(noti_bassi, key=lambda r: punti.get(r["nome"], 0)) if noti_bassi else None
    forti = [r for r in righe if r.get("correzione", 0) <= -1]
    neg = max(forti, key=lambda r: punti.get(r["nome"], 0)) if forti else None
    sale = sorted((r for r in righe if r["g"] and r.get("griglia")), key=lambda r: r["griglia"] - r["g"], reverse=True)
    perde = min((r for r in righe if r["g"] and r.get("griglia")), key=lambda r: r["g"] - r["griglia"] if False else r["griglia"] - r["g"], default=None)
    # chi sceglie il gancio: il piu' famoso tra chi ha un voto molto basso o una correzione pesante in negativo (mai il migliore)
    cand = [r for r in (neg, noto) if r]
    prot = max(cand, key=lambda r: punti.get(r["nome"], 0)) if cand else basso
    protagonisti = sorted((r for r in righe if r is not migliore), key=lambda r: -punti.get(r["nome"], 0))[:2]
    rosse = [r for r in righe if serie == "f1" and r.get("team") == "Ferrari" and r is not migliore]   # le due Ferrari si citano sempre: portano pubblico
    for r in (*rosse, *protagonisti, *righe[1:3], basso, prot, neg, noto, sale[0] if sale and sale[0]["griglia"] - sale[0]["g"] >= 6 else None,
              perde if perde and perde["griglia"] - perde["g"] <= -3 else None, *[x for x in righe if x.get("correzione")], *righe[1:3]):
        aggiungi(r)
    scelti = sorted(scelti[:6], key=lambda r: r["voto_esatto"])
    ferrari = max((r for r in righe if r.get("team") == "Ferrari" and r["voto"] >= 8), key=lambda r: r["voto_esatto"], default=None) if serie == "f1" else None
    if ferrari:   # in Italia la Ferrari attira: si apre elogiando il suo migliore (mai il migliore assoluto della pagella)
        prot = ferrari
        aggiungi(ferrari)
        scelti = sorted(([ferrari] + [r for r in scelti if r is not ferrari])[:6], key=lambda r: r["voto_esatto"])
        compagno = next((r for r in righe if r.get("team") == "Ferrari" and r is not ferrari and r["voto"] <= 6.5), None)
        gara = f"{ordinale(ferrari['g'])} in gara" + (f", partendo {ordinale(ferrari['griglia'])}" if ferrari.get("griglia") and ferrari["griglia"] != ferrari["g"] else "")
        gancio = (f"Un ottimo [{cognome(ferrari)}] fa felice una Ferrari non troppo sorridente." if compagno else f"Un ottimo [{cognome(ferrari)}] fa felice la Ferrari.")
        hook_titolo = f"Un ottimo {breve(ferrari)}"
    elif prot is neg:
        gancio = f"[{cognome(prot)}] {voto_parole(prot['voto'])} in pagella. {neg['motivo'][0].upper() + neg['motivo'][1:]}. Ma il voto più basso del weekend è un altro."
    else:
        if prot is migliore:
            prot = basso
        ragione = f"{'è caduto' if prot.get('causa') == 'caduta' else 'si è ritirato'} al giro {prot['ritiro_giro']}" if (not prot["g"] and prot.get("ritiro_giro")) else next((x for x in prot.get("perche", []) if x not in GENERICHE), "")
        gancio = f"[{cognome(prot)}] tra i peggiori del weekend" + (f": {ragione}" if ragione else "") + "." + ((" " + frase_ritiro(prot)) if (not prot["g"] and frase_ritiro(prot)) else "")
        hook_titolo = f"{breve(prot)} tra i peggiori"
    hook_titolo = locals().get("hook_titolo") or f"{breve(prot)} {fmt(prot['voto'])} in pagella"
    righe_tab = [r for r in asc if r in scelti or r is migliore]
    for r in sorted(righe[:4], key=lambda r: -r["voto_esatto"]):
        pass
    coloreriga = lambda r: r.get("colore") or MOTO.get(r.get("moto"), "888888")
    tab = {"titolo": "I nostri voti", "righe": [{"pos": "", "colore": coloreriga(r), "nome": breve(r), "voto": fmt(r["voto"]), "nota": " "} for i, r in enumerate(sorted(set(map(id, righe_tab)) and righe_tab, key=lambda r: -r["voto_esatto"]))]}
    scene = [{"foto": prot["nome"], **foto_gancio(prot["nome"]), "hook": True, "hook_titolo": hook_titolo, "testo": gancio}]
    if ferrari:   # dopo il gancio si parla subito dell'altra Ferrari
        c2 = next((r for r in scelti if r.get("team") == "Ferrari" and r is not ferrari), None)
        if c2:
            scelti = [c2] + [r for r in scelti if r is not c2]
    for r in scelti:
        scene.append(scena(r, sprint, foto_pista(serie, r["nome"]), len(scene) - 1))
    fila = vittorie_di_fila(serie, w, migliore["nome"])
    ripetuta = {2: "Seconda vittoria di fila", 3: "Terza vittoria di fila"}.get(fila, f"{fila}ª vittoria di fila" if fila > 3 else "")
    lode = f" {ripetuta}: una prova da applausi." if ripetuta else " Una prova da applausi."
    pista = foto_pista(serie, migliore["nome"])
    if migliore["nome"] == "Marco Bezzecchi":
        pista["volto_alt"] = "sorriso"
    top = {"foto": migliore["nome"], **pista,
           "testo": f"E poi il migliore: [{cognome(migliore)}]. {tripletta(migliore, sprint) or (frase_sessioni(migliore, sprint)[0].upper() + frase_sessioni(migliore, sprint)[1:] + '.')}{lode} Voto *{voto_parole(migliore['voto'])}*."}
    scene.append(top)
    scene.append({"foto": migliore["nome"], "pista": True, "classifica": tab, "sub_top": 1360, "testo": "Ecco la pagella completa."})
    ser = "F1" if serie == "f1" else "MotoGP"
    return {"serie": ser, "titolo_breve": f"{gp}: la pagella", "fonte": "risultati ufficiali, calcolo GP Oggi", "velocita": "+31%", "scene": scene,
            "finale": {"foto": migliore["nome"], "domanda": f"Che voto dai tu a {gp}?"}}, migliore, gp, basso


def didascalia(serie, gp, migliore, basso, prot_nome):
    tag = "#f1" if serie == "f1" else "#motogp"
    return (f"La pagella di {gp}, studiata da noi 📝\n\n{migliore['nome']} {fmt(migliore['voto'])} è l'uomo del weekend, ma il voto più basso è {basso['nome']} ({fmt(basso['voto'])}).\n\n"
            f"Voti a scopo divertente, senza offendere nessuno. Sei d'accordo? Dimmi la tua nei commenti 👇\n\n🔗 gpoggi.it\n\n#gpoggi {tag} #{''.join(c for c in gp.lower() if c.isalnum())} #pagella")


def main():
    forza = "--forza" in sys.argv
    fatte_f = QUI / "pagella_fatte.json"
    fatte = json.load(open(fatte_f)) if fatte_f.exists() else []
    P = json.load(open(DATA / "pagella.json"))
    (QUI / "spec").mkdir(exist_ok=True)
    nuovi = []
    for serie in ("f1", "motogp"):
        w = P.get(serie)
        if not w:
            continue
        chiave = f"{serie}:{w['nome']}:{w['data'][:10]}"
        if chiave in fatte and not forza:
            print("gia' fatta:", chiave); continue
        spec, migliore, gp, basso = costruisci(serie, w)
        nome = f"pagella-{serie}-{''.join(c for c in gp.lower() if c.isalnum())}"
        (QUI / "spec" / f"{nome}.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1))
        (QUI / "spec" / f"{nome}.txt").write_text(didascalia(serie, gp, migliore, basso, None))
        alt = ["--alt", "sorriso"] if migliore["nome"] == "Marco Bezzecchi" else []
        subprocess.run([sys.executable, str(QUI / "copertina_pagella.py"), serie, str(QUI / "spec" / f"{nome}.png"), *alt], check=True, cwd=QUI)
        nuovi.append(chiave); print("scritta:", nome)
    if nuovi:
        fatte_f.write_text(json.dumps(fatte + nuovi, indent=1))


if __name__ == "__main__":
    main()
