"""Video "Chi sale sul podio?" in stile moderno (lo stesso dei video notizia: volto a tutto schermo, titolo a strisce, sottotitoli a parole, barra di avanzamento),
al posto delle vecchie schede ferme: il favorito con i suoi SÌ e NO, chi tenere d'occhio, la pole e l'invito a rispondere nei commenti.
Tutti i dati vengono dal sito (pronostici.json, gare, MotoGP) tramite auto_video.scene_previsione: nessun modello di linguaggio.
Niente «pronostico», voti, premi o soldi; il gioco del sito non si promuove (regole TikTok). Penalità in griglia solo da note con il loro Gran Premio.

Uso:  python3 previsioni_sub.py [auto|f1|motogp] [--invia] [--uscita FILE]
"""
import argparse, asyncio, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import auto_video as A  # noqa: E402
import notizia_sub as NS  # noqa: E402
import notizie_giorno as NG  # noqa: E402
import anteprima_gara as AG  # noqa: E402
import studio_gara as SG  # noqa: E402


def serie_prossima():
    pron = json.load(open(A.DATA / "pronostici.json"))
    ora = datetime.now(timezone.utc)
    cand = {k: pron[k]["gara"] for k in ("f1", "motogp") if pron.get(k) and pron[k].get("favoriti") and datetime.fromisoformat(pron[k]["gara"]) > ora}
    if not cand:
        raise SystemExit("nessuna gara in programma")
    return min(cand, key=cand.get)


def costruisci(chiave):
    """Scene del video dallo studio di GP Oggi (studio_gara.py): gara e pole non solo dalle ultime 5 gare, ma anche dal circuito, dalla moto/macchina e da chi ha vinto l'anno scorso."""
    st = SG.studio(chiave)
    S = "F1" if chiave == "f1" else "MotoGP"
    pron = json.load(open(A.DATA / "pronostici.json"))[chiave]
    nomi = NG.nomi_con_foto()
    gara = [r for r in st["gara"] if r["nome"] in nomi][:3]
    pole = [r for r in st["pole"] if r["nome"] in nomi]
    if len(gara) < 3 or not pole:
        raise SystemExit("meno di tre piloti con foto libera")
    luogo = re.sub(r"^(Gran Premio (degli|di|del|dello|della|d')\s*|GP )", "", pron["gp"]).strip()
    cogn = lambda n: n.split()[-1]
    a_ = lambda c: ("ad " if c[0] in "AEIOU" else "a ") + c
    extra = json.load(open(A.DATA / "foto-extra.json"))
    usate = {}

    def alt(n):
        """Foto in pista (macchina o moto) del pilota, se esiste una foto libera: cambia l'immagine rispetto al volto della scena del favorito."""
        chiavi = [k for k in extra.get(n, {}) if k.startswith("pista")]
        if not chiavi:
            return {}
        usate[n] = usate.get(n, -1) + 1
        return {"alt": chiavi[usate[n]]} if usate[n] < len(chiavi) else {}   # finite le foto in pista, si torna al volto

    chips = lambda r, k, n=3: [(m[0], m[1]) for m in r["motivi_" + k]][:n]
    voci = lambda r, k, n=2: [m[2] for m in r["motivi_" + k] if m[0] == "si"][:n]
    f0 = gara[0]
    titolo = f"{luogo}: chi sale sul podio?"
    scene = [{"foto": f0["nome"], "hook": True, "hook_titolo": titolo, "testo": titolo}]
    # prima statica: il tracciato, con chi ha vinto l'anno scorso
    gp = AG.paese_e_orari(chiave, pron)
    _, t_gara = AG.quando(pron["gara"])
    tr = AG.scheda_tracciato(chiave, pron, gp, t_gara)
    sc = st["scorso"]
    if tr:
        voce_tr = f"Ecco il tracciato di *{pron['circuito']}*."
        if sc.get("vincitore"):
            tr["box"][1] = [cogn(sc["vincitore"]), f"ha vinto qui nel {sc['anno']}"]
            voce_tr += f" L'anno scorso qui ha vinto *{sc['vincitore']}*."
        scene.append({"foto": f0["nome"], "pista": True, "tracciato": tr, "sub_top": 1440, "testo": voce_tr})
    # favorito
    no = next((m for m in f0["motivi_gara"] if m[0] == "no"), None)
    ch = [m for m in chips(f0, "gara") if m[0] == "si"][:3] + ([("no", no[1])] if no else [])
    voce = f"Per noi il favorito è *{cogn(f0['nome'])}*: " + ", ".join(voci(f0, "gara")) + "." + (f" Il dubbio: {no[2]}." if no else "")
    scene.append({"foto": f0["nome"], "nome": f0["nome"], "chips": ch, "sub_top": 1440, "testo": voce})
    # i due da tenere d'occhio
    for k, r in enumerate(gara[1:3]):
        v = voci(r, "gara")
        if not r["motivi_gara"] or not v:
            continue
        scene.append({"foto": r["nome"], "nome": r["nome"], "chips": chips(r, "gara"), "sub_top": 1440, "testo": (f"Occhio {a_(cogn(r['nome']))}: " if k == 0 else f"E {a_(cogn(r['nome']))}: ") + ", ".join(v) + ".", **alt(r["nome"])})
    # la pole, con chi l'ha presa l'anno scorso
    p0 = pole[0]
    ch_p = [(m[0], m[1]) for m in p0["motivi_pole"]][:3]
    pole_gia_detta = sc.get("pole") == p0["nome"]   # se è lui, il motivo c'è già
    if sc.get("pole") and not pole_gia_detta:
        ch_p.append(("info", f"Pole {sc['anno']}: {sc['pole']}"))
    vp = voci(p0, "pole")
    voce_p = f"E la pole? Per noi *{cogn(p0['nome'])}*" + (": " + ", ".join(vp) if vp else "") + "." + (f" L'anno scorso è stata di {cogn(sc['pole'])}." if sc.get("pole") and not pole_gia_detta else "")
    scene.append({"foto": p0["nome"], "nome": f"Pole: {p0['nome']}", "chips": ch_p[:4], "sub_top": 1440, "testo": voce_p, **alt(p0["nome"])})
    # seconda statica: il podio dei favoriti, disegnato (anche come immagine da pubblicare)
    podio = {"titolo": "Il podio dei favoriti", "sotto": pron["gp"],
             "righe": [{"pos": i + 1, "nome": r["nome"], "cognome": cogn(r["nome"]), "nota": r["costruttore"]} for i, r in enumerate(gara)]}
    scena_podio = {"foto": f0["nome"], "pista": True, "podio": podio, "sub_top": 1450,
                   "testo": f"Ecco il podio dei nostri favoriti: primo {cogn(gara[0]['nome'])}, secondo {cogn(gara[1]['nome'])}, terzo {cogn(gara[2]['nome'])}."}
    scene.append(scena_podio)
    spec = {"serie": S, "titolo_breve": luogo, "etichetta": "Chi sale sul podio", "fonte": "studio GP Oggi", "velocita": "+38%", "scene": scene,
            "finale": {"foto": f0["nome"], "domanda": "Chi sale sul podio secondo te?"}}
    icona, tag = ("🏁", "#f1 #formula1") if chiave == "f1" else ("🏍️", "#motogp")
    social = (f"{icona} {luogo}: chi sale sul podio? {icona}\n\n👑 Il nostro favorito: {f0['nome']}\n🎯 Pole? Per noi {p0['nome']}\n"
              + (f"🏆 L'anno scorso qui: vittoria di {sc['vincitore']}, pole di {sc['pole']}\n" if sc.get("vincitore") and sc.get("pole") else "")
              + f"\nLo studio guarda forma, circuito, {'macchina' if chiave == 'f1' else 'moto'} e risultati dell'anno scorso.\nE tu che dici? Dimmi la tua nei commenti 👇\n\n🔗 gpoggi.it\n\nOpinione basata sui numeri, non una certezza.\n\n#gpoggi {tag} #podio #previsioni")
    return spec, social, {"gp": pron["gp"]}, scena_podio


async def png_podio(spec, scena, uscita):
    """La grafica del podio come immagine 1080x1920, da pubblicare anche da sola."""
    from playwright.async_api import async_playwright
    cred = NS.prepara_scena(scena)
    fb = NS.b64(NS.file_foto(NS.trova_foto(scena["foto"], scena.get("alt"))))
    async with async_playwright() as p:
        b = await p.chromium.launch(**({"executable_path": "/opt/pw-browsers/chromium"} if Path("/opt/pw-browsers/chromium").exists() else {}), args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": NS.W, "height": NS.H})
        await pg.set_content(NS.pagina(spec, {**scena, "sub_top": 1500}, fb, cred, 0.0, sub=[]))
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=str(uscita))
        await b.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("serie", nargs="?", default="auto", choices=["auto", "f1", "motogp"])
    ap.add_argument("--invia", action="store_true")
    ap.add_argument("--uscita", type=Path, default=A.QUI / "previsioni_sub.mp4")
    a = ap.parse_args()
    chiave = serie_prossima() if a.serie == "auto" else a.serie
    spec, social, d, scena_podio = costruisci(chiave)
    asyncio.run(NS.genera(spec, a.uscita))
    if scena_podio:
        asyncio.run(png_podio(spec, scena_podio, a.uscita.with_suffix(".png")))
    if a.invia:
        NG.telegram(a.uscita, f"🏁 {d['gp']}: chi sale sul podio?", social)


if __name__ == "__main__":
    main()
