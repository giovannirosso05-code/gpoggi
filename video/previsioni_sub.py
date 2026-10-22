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
    alt = lambda n: {}   # sempre la foto più recente del sito (la foto alternativa di Marquez è del 2022)
    titolo = f"{luogo}: chi sale sul podio?"
    scene = [{"foto": nome_f, "hook": True, "hook_titolo": titolo, "testo": titolo, **alt(nome_f)},
             {"foto": nome_f, "nome": nome_f, "chips": chips_f, "sub_top": 1440, "testo": voce1.split("? ", 1)[-1], **alt(nome_f)}]
    for nome, motivi, voce in d["rivali"]:
        scene.append({"foto": nome, "nome": nome, "chips": [("info", m) for m in motivi], "sub_top": 1440, "testo": voce, **alt(nome)})
    pole = d.get("pole")
    if pole:
        fav_pole, occhio, ordine, voce3 = pole
        scene.append({"foto": fav_pole, "nome": f"Pole: {fav_pole}", "chips": [("info", f"{n}: {c} pole nelle ultime 5 qualifiche") for n, c in ordine[:3]], "sub_top": 1440,
                      "testo": voce3, **alt(fav_pole)})
    spec = {"serie": S, "titolo_breve": luogo, "etichetta": "Chi sale sul podio", "fonte": "dati GP Oggi", "velocita": "+38%", "scene": scene,
            "finale": {"foto": nome_f, "domanda": "Chi sale sul podio secondo te?"}}
    icona, tag = ("🏁", "#f1 #formula1") if chiave == "f1" else ("🏍️", "#motogp")
    pole_riga = (f"🎯 Pole? Per noi {pole[0]}" + (f", ma occhio a {pole[1]}" if pole[1] else "") + "\n") if pole else ""
    social = (f"{icona} {luogo}: chi sale sul podio? {icona}\n\n👑 Il nostro favorito: {nome_f}\n{pole_riga}\n"
              f"E tu che dici? Dimmi la tua nei commenti 👇\n\n🔗 gpoggi.it\n\nOpinione basata sui numeri, non una certezza.\n\n#gpoggi {tag} #podio #previsioni")
    return spec, social, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("serie", nargs="?", default="auto", choices=["auto", "f1", "motogp"])
    ap.add_argument("--invia", action="store_true")
    ap.add_argument("--uscita", type=Path, default=A.QUI / "previsioni_sub.mp4")
    a = ap.parse_args()
    chiave = serie_prossima() if a.serie == "auto" else a.serie
    spec, social, d = costruisci(chiave)
    asyncio.run(NS.genera(spec, a.uscita))
    if a.invia:
        NG.telegram(a.uscita, f"🏁 {d['gp']}: chi sale sul podio?", social)


if __name__ == "__main__":
    main()
