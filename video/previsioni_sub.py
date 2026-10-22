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


def serie_prossima():
    pron = json.load(open(A.DATA / "pronostici.json"))
    ora = datetime.now(timezone.utc)
    cand = {k: pron[k]["gara"] for k in ("f1", "motogp") if pron.get(k) and pron[k].get("favoriti") and datetime.fromisoformat(pron[k]["gara"]) > ora}
    if not cand:
        raise SystemExit("nessuna gara in programma")
    return min(cand, key=cand.get)


def costruisci(chiave):
    if not A.scene_previsione(chiave):
        raise SystemExit("nessuna previsione disponibile")
    d = A.DATI_PREV[chiave]
    S = "F1" if chiave == "f1" else "MotoGP"
    luogo = re.sub(r"^(Gran Premio (degli|di|del|dello|della|d')\s*|GP )", "", d["gp"]).strip()
    nome_f, chips_f, voce1 = d["fav"]
    extra = json.load(open(A.DATA / "foto-extra.json"))
    usate = {}

    def alt(n):
        """Foto in pista (macchina o moto) del pilota, se esiste una foto libera: cambia l'immagine rispetto al volto della scena del favorito."""
        chiavi = [k for k in extra.get(n, {}) if k.startswith("pista")]
        if not chiavi:
            return {}
        usate[n] = usate.get(n, -1) + 1
        return {"alt": chiavi[usate[n]]} if usate[n] < len(chiavi) else {}   # finite le foto in pista, si torna al volto
    titolo = f"{luogo}: chi sale sul podio?"
    scene = [{"foto": nome_f, "hook": True, "hook_titolo": titolo, "testo": titolo}]
    pron = json.load(open(A.DATA / "pronostici.json"))[chiave]
    gp = AG.paese_e_orari(chiave, pron)
    _, t_gara = AG.quando(pron["gara"])
    tr = AG.scheda_tracciato(chiave, pron, gp, t_gara)
    if tr:   # prima statica: la mappa del circuito
        scene.append({"foto": nome_f, "pista": True, "tracciato": tr, "sub_top": 1440, "testo": f"Ecco il tracciato di *{pron['circuito']}*."})
    scene.append({"foto": nome_f, "nome": nome_f, "chips": chips_f, "sub_top": 1440, "testo": voce1.split("? ", 1)[-1]})
    for nome, motivi, voce in d["rivali"]:
        scene.append({"foto": nome, "nome": nome, "chips": [("info", m) for m in motivi], "sub_top": 1440, "testo": voce, **alt(nome)})
    pole = d.get("pole")
    if pole:
        fav_pole, occhio, ordine, voce3 = pole
        scene.append({"foto": fav_pole, "nome": f"Pole: {fav_pole}", "chips": [("info", f"{n}: {c} pole nelle ultime 5 qualifiche") for n, c in ordine[:3]], "sub_top": 1440,
                      "testo": voce3, **alt(fav_pole)})
    # seconda statica: il podio dei favoriti, disegnato (anche come immagine da pubblicare)
    top3 = [f for f in pron["favoriti"] if f["nome"] in NG.nomi_con_foto()][:3]
    podio = None
    if len(top3) == 3:
        podio = {"titolo": "Il podio dei favoriti", "sotto": pron["gp"],
                 "righe": [{"pos": i + 1, "nome": f["nome"], "cognome": f["nome"].split()[-1], "nota": f"indice {f['indice']}"} for i, f in enumerate(top3)]}
        scene.append({"foto": top3[0]["nome"], "pista": True, "podio": podio, "sub_top": 1450,
                      "testo": f"Ecco il podio dei nostri favoriti: primo {top3[0]['nome'].split()[-1]}, secondo {top3[1]['nome'].split()[-1]}, terzo {top3[2]['nome'].split()[-1]}."})
    spec = {"serie": S, "titolo_breve": luogo, "etichetta": "Chi sale sul podio", "fonte": "dati GP Oggi", "velocita": "+38%", "scene": scene,
            "finale": {"foto": nome_f, "domanda": "Chi sale sul podio secondo te?"}}
    icona, tag = ("🏁", "#f1 #formula1") if chiave == "f1" else ("🏍️", "#motogp")
    pole_riga = (f"🎯 Pole? Per noi {pole[0]}" + (f", ma occhio a {pole[1]}" if pole[1] else "") + "\n") if pole else ""
    social = (f"{icona} {luogo}: chi sale sul podio? {icona}\n\n👑 Il nostro favorito: {nome_f}\n{pole_riga}\n"
              f"E tu che dici? Dimmi la tua nei commenti 👇\n\n🔗 gpoggi.it\n\nOpinione basata sui numeri, non una certezza.\n\n#gpoggi {tag} #podio #previsioni")
    return spec, social, d, (scene[-1] if podio else None)


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
