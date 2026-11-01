"""Video «Antonelli campione del mondo»: pronto in anticipo, si lancia SOLO a titolo confermato (workflow «Video campione»).
Graﬁche: bandiera italiana, raggi, coriandoli, trofeo del campionato (Commons CC BY-SA); ritratto ESPN. Nessun dato di gara: solo fatti che valgono se il titolo arriva a Città del Messico.
Uso:  python3 video_campione.py [--invia] [--uscita FILE]"""
import argparse, asyncio, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bandiera as B  # noqa: E402
import notizia_sub as NS  # noqa: E402
import notizie_giorno as NG  # noqa: E402
import ritratti_espn as R  # noqa: E402

EN = os.environ.get("GPOGGI_LINGUA", "it") == "en"   # versione inglese per il secondo account (stesso script, voce e scritte in inglese)
_ = lambda it, en: en if EN else it
FOTO = _("Foto", "Photo")
TR = B.QUI / "extra" / "trofeo-f1.jpg"
CRED = f"{FOTO}: ESPN · " + _("Trofeo", "Trophy") + ": Raimond Spekking (CC BY-SA 4.0), Wikimedia Commons"


def costruisci():
    c = R.CACHE
    c.mkdir(exist_ok=True)
    comp = lambda nome, **k: str(B.composizione("Kimi Antonelli", str(c / nome), **k))
    f1 = comp("camp_v1.jpg", trofeo=TR, larghezza=1450, px=-240, tr_x=880, tr_h=620, alza=0, conf=True, luce=True)
    f0 = comp("camp_v0.jpg", trofeo=TR, larghezza=1200, px=-170, tr_x=880, tr_h=520, alza=430, conf=True, luce=True)   # gancio: faccia alta, il titolo sta sotto il mento
    f2 = comp("camp_v2.jpg", trofeo=None, larghezza=1400, px=-160, alza=0, conf=True, luce=True)
    f3 = comp("camp_v3.jpg", trofeo=None, larghezza=1300, px=-110, alza=0, conf=True, luce=True)
    esp = lambda p: f"https://a.espncdn.com/photo/2026/{p}_1296x729_16-9.jpg"   # foto ESPN di questa stagione (scaricate al momento in video/_cache/, mai nel repository)
    sc = [
        {"foto": "Kimi Antonelli", "hook": True, "hook_titolo": _("Antonelli campione del mondo!", "Antonelli is world champion!"), "testo": _("*Antonelli* è *campione del mondo*!", "*Antonelli* is *world champion*!"), "foto_file": f0, "credito": CRED},
        {"foto": "Kimi Antonelli", "testo": _("A *vent'anni* è il più giovane di sempre: il record era di *Vettel*, a ventitré.", "At *twenty* he's the youngest champion ever: the record was *Vettel's*, at twenty-three."), "foto_url": esp("0805/r1697948"), "credito": f"{FOTO}: ESPN (Monaco 2026)"},
        {"foto": "Kimi Antonelli", "testo": _("Tutto è cominciato in *Cina*: prima pole e prima vittoria, la prima di un italiano in vent'anni.", "It all began in *China*: first pole and first win, the first for an Italian in twenty years."), "foto_file": f3, "credito": f"{FOTO}: ESPN", "fonte_alto": "Il Post"},
        {"foto": "Kimi Antonelli", "testo": _("A *Monza* ha vinto partendo dal *diciannovesimo* posto: a casa, un italiano non vinceva dal *millenovecentosessantasei*.", "At *Monza* he won starting *nineteenth*: no Italian had won the home race since *nineteen sixty-six*."), "foto_file": f2, "credito": f"{FOTO}: ESPN", "fonte_alto": "Sky Sport, ESPN"},
        {"foto": "Kimi Antonelli", "testo": _("Nove vittorie in diciotto gare, e un italiano sul tetto del mondo *settantatré anni* dopo *Ascari*.", "Nine wins in eighteen races, and an Italian on top of the world *seventy-three years* after *Ascari*."), "foto_url": esp("1026/r1736290"), "credito": f"{FOTO}: ESPN (Austin 2026)", "pausa": 0.2},
        {"foto": "Kimi Antonelli", "testo": _("Ha chiuso il conto a *Città del Messico*, con quattro gare d'anticipo.", "He clinched it in *Mexico City*, with four races to spare."), "foto_url": esp("1025/r1736157"), "credito": f"{FOTO}: ESPN (Austin 2026)"},
    ]
    spec = {"serie": "F1", "titolo_breve": _("Antonelli campione", "Antonelli champion"), "etichetta": _("Campione del mondo", "World champion"), "fonte": "GP Oggi", "velocita": "+38%", "segui": False, "scene": sc,
            "finale": {"foto": "Kimi Antonelli", "domanda": _("Qual è il momento che ricorderai di questa stagione?", "Which moment of this season will you remember?")}}
    social = (_("""🏆🇮🇹 ANTONELLI CAMPIONE DEL MONDO! 🇮🇹🏆

A 20 anni Kimi diventa il più giovane campione della storia della F1 (il record era di Vettel, a 23) e il primo italiano a vincere il Mondiale dopo Alberto Ascari, nel 1953. Dalla prima vittoria in Cina a Monza, vinta partendo dal 19° posto, fino al titolo a Città del Messico con quattro gare d'anticipo.

Qual è il momento che ricorderai di questa stagione? Dimmi la tua nei commenti 👇

Fonti: Il Post, Sky Sport, ESPN.
🔗 gpoggi.it

#gpoggi #f1 #antonelli #campione #formula1""", """🏆🇮🇹 ANTONELLI IS WORLD CHAMPION! 🇮🇹🏆

At 20, Kimi becomes the youngest champion in F1 history (the record was Vettel's, at 23) and the first Italian to win the title since Alberto Ascari in 1953. From his first win in China to Monza, won from 19th on the grid, to the title in Mexico City with four races to spare.

Which moment of this season will you remember? Tell us in the comments 👇

Sources: Il Post, Sky Sport, ESPN.
🔗 gpoggi.it

#gpoggi #f1 #antonelli #worldchampion #formula1"""))
    return spec, social


def titolo_matematico():
    """True solo se la classifica del sito, dopo il GP di Città del Messico, dà Antonelli campione con le gare rimaste (spareggio per vittorie compreso).
    False se i dati non sono ancora aggiornati dopo la gara: allora serve --forza, dopo aver controllato due testate."""
    import json
    st = json.load(open(NS.DATA / "standings.json"))
    if "Messico" not in (st.get("dopo") or ""):
        return False
    punti = sorted(((p["punti"], p["nome"]) for p in st["piloti"]), reverse=True)
    (p1, n1), (p2, n2) = punti[0], punti[1]
    ev = json.load(open(NS.DATA / "events.json"))
    from datetime import datetime, timezone
    resto = 25 * len([g for g in ev if g["inizio"] > datetime.now(timezone.utc).isoformat()])
    vitt = {}
    for f in (NS.DATA / "gare").glob("*.json"):
        for ses in json.load(open(f))["sessioni"]:
            if ses["tipo"] == "Race" and ses.get("risultati"):
                v = sorted((x for x in ses["risultati"] if x.get("pos")), key=lambda x: x["pos"])
                if v:
                    vitt[v[0]["nome"]] = vitt.get(v[0]["nome"], 0) + 1
    return n1 == "Kimi Antonelli" and (p1 - p2 > resto or (p1 - p2 == resto and vitt.get(n1, 0) > vitt.get(n2, 0) + len([g for g in ev if g["inizio"] > datetime.now(timezone.utc).isoformat()])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--invia", action="store_true"); ap.add_argument("--forza", action="store_true", help="salta il controllo dei dati (solo dopo aver visto il titolo su due testate)"); ap.add_argument("--uscita", type=Path, default=NS.QUI / "video_campione.mp4")
    a = ap.parse_args()
    if not a.forza and not titolo_matematico():
        raise SystemExit("Antonelli non risulta campione nei dati del sito (o i dati non sono aggiornati dopo la gara): niente video. Controlla due testate e rilancia con --forza.")
    spec, social = costruisci()
    asyncio.run(NS.genera(spec, a.uscita))
    if a.invia:
        NG.telegram(a.uscita, _("🏆 Antonelli campione del mondo", "🏆 Antonelli world champion (EN)"), social)


if __name__ == "__main__":
    main()
