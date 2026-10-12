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
        parti.append(f"ritirato al giro {r['ritiro_giro']}" if r.get("ritiro_giro") else "ritirato in gara")
    return ", ".join(parti[:-1]) + " e " + parti[-1]


def scena(r, sprint, alt):
    resto = [x for x in r.get("perche", []) if x not in GENERICHE]
    if not r["g"]:
        resto = []   # il ritiro e' gia' nella frase delle sessioni
    extra = (resto[0][0].upper() + resto[0][1:] + ".") if resto else ("Il ritiro pesa sul voto complessivo del weekend." if not r["g"] else "")
    if r.get("correzione"):
        extra += " " + r["motivo"][0].upper() + r["motivo"][1:] + "."
    testo = f"[{cognome(r)}]: {frase_sessioni(r, sprint)}. {extra} Voto *{voto_parole(r['voto'])}*.".replace("  ", " ")
    return {"foto": r["nome"], **alt, "testo": testo}


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
    for r in (basso, prot, neg, noto, sale[0] if sale and sale[0]["griglia"] - sale[0]["g"] >= 6 else None,
              perde if perde and perde["griglia"] - perde["g"] <= -3 else None, *[x for x in righe if x.get("correzione")], *righe[1:3]):
        aggiungi(r)
    scelti = sorted(scelti[:5], key=lambda r: r["voto_esatto"])
    if prot is neg:
        gancio = f"[{cognome(prot)}] {voto_parole(prot['voto'])} in pagella. {neg['motivo'][0].upper() + neg['motivo'][1:]}. Ma il voto più basso del weekend è un altro."
    else:
        ragione = f"si è ritirato al giro {prot['ritiro_giro']}" if (not prot["g"] and prot.get("ritiro_giro")) else next((x for x in prot.get("perche", []) if x not in GENERICHE), "")
        gancio = f"[{cognome(prot)}] {voto_parole(prot['voto'])} in pagella" + (f": {ragione}" if ragione else "") + ". " + (
            "Ma c'è chi ha preso ancora meno." if prot is not basso else "Nessuno ha fatto peggio.")
    hook_titolo = f"{breve(prot)} {fmt(prot['voto'])} in pagella"
    righe_tab = [r for r in asc if r in scelti or r is migliore]
    for r in sorted(righe[:4], key=lambda r: -r["voto_esatto"]):
        pass
    coloreriga = lambda r: r.get("colore") or MOTO.get(r.get("moto"), "888888")
    tab = {"titolo": f"Pagella: {gp}", "righe": [{"pos": i + 1, "colore": coloreriga(r), "nome": breve(r), "voto": fmt(r["voto"]), "nota": " "} for i, r in enumerate(sorted(set(map(id, righe_tab)) and righe_tab, key=lambda r: r["voto_esatto"]))]}
    scene = [{"foto": prot["nome"], "hook": True, "hook_titolo": hook_titolo, "testo": gancio}]
    for r in scelti:
        scene.append(scena(r, sprint, foto_pista(serie, r["nome"])))
    top = scena(migliore, sprint, {})
    top["testo"] = f"E poi il migliore: [{cognome(migliore)}]. {frase_sessioni(migliore, sprint)[0].upper() + frase_sessioni(migliore, sprint)[1:]}. Voto *{voto_parole(migliore['voto'])}*, è l'uomo del weekend."
    top.update({"pista": True, "classifica": tab, "sub_top": 1360})
    scene.append(top)
    ser = "F1" if serie == "f1" else "MotoGP"
    return {"serie": ser, "titolo_breve": f"{gp}: la pagella", "fonte": "risultati ufficiali, calcolo GP Oggi", "velocita": "+30%", "scene": scene,
            "finale": {"foto": migliore["nome"], "domanda": f"Che voto dai tu a {gp}?"}}, migliore, gp, basso


def didascalia(serie, gp, migliore, basso, prot_nome):
    tag = "#f1" if serie == "f1" else "#motogp"
    return (f"La pagella di {gp}, studiata da noi 📝\n\n{migliore['nome']} {fmt(migliore['voto'])} è l'uomo del weekend, ma il voto più basso è {basso['nome']} ({fmt(basso['voto'])}).\n\n"
            f"Sei d'accordo coi nostri voti? Dimmi la tua nei commenti 👇\n\n🔗 gpoggi.it\n\n#gpoggi {tag} #{''.join(c for c in gp.lower() if c.isalnum())} #pagella")


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
