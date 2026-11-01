"""Video «Antonelli campione del mondo»: pronto in anticipo, si lancia SOLO a titolo confermato (workflow «Video campione»).
Graﬁche: bandiera italiana, raggi, coriandoli, trofeo del campionato (Commons CC BY-SA); ritratto ESPN. Nessun dato di gara: solo fatti che valgono se il titolo arriva a Città del Messico.
Uso:  python3 video_campione.py [--invia] [--uscita FILE]"""
import argparse, asyncio, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bandiera as B  # noqa: E402
import notizia_sub as NS  # noqa: E402
import notizie_giorno as NG  # noqa: E402
import ritratti_espn as R  # noqa: E402

TR = B.QUI / "extra" / "trofeo-f1.jpg"
CRED = "Foto: ESPN · Trofeo: Raimond Spekking (CC BY-SA 4.0), Wikimedia Commons"


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
        {"foto": "Kimi Antonelli", "hook": True, "hook_titolo": "Antonelli campione del mondo!", "testo": "*Antonelli* è *campione del mondo*!", "foto_file": f0, "credito": CRED},
        {"foto": "Kimi Antonelli", "testo": "A *vent'anni* è il più giovane campione di sempre: il record era di *Vettel*, a ventitré.", "foto_url": esp("0805/r1697948"), "credito": "Foto: ESPN (Monaco 2026)"},
        {"foto": "Kimi Antonelli", "testo": "Un italiano sul tetto del mondo, *settantatré anni* dopo *Ascari*.", "foto_url": esp("1026/r1736290"), "credito": "Foto: ESPN (Austin 2026)", "pausa": 0.2},
        {"foto": "Kimi Antonelli", "testo": "Ha chiuso il conto a *Città del Messico*, con quattro gare d'anticipo.", "foto_url": esp("1025/r1736108"), "credito": "Foto: ESPN (Austin 2026)"},
        {"foto": "Kimi Antonelli", "testo": "Una stagione da *incorniciare*, e adesso tutta l'*Italia* è con lui.", "foto_file": f2, "credito": "Foto: ESPN"},
    ]
    spec = {"serie": "F1", "titolo_breve": "Antonelli campione", "etichetta": "Campione del mondo", "fonte": "GP Oggi", "velocita": "+38%", "segui": False, "scene": sc,
            "finale": {"foto": "Kimi Antonelli", "domanda": "Qual è il momento che ricorderai di questa stagione?"}}
    social = ("🏆🇮🇹 ANTONELLI CAMPIONE DEL MONDO! 🇮🇹🏆\n\nA 20 anni è il più giovane campione di sempre (il record era di Vettel, a 23) e il primo italiano a vincere il Mondiale dopo Ascari, nel 1953.\n\n"
              "Qual è il momento che ricorderai di questa stagione? Dimmi la tua nei commenti 👇\n\n🔗 gpoggi.it\n\n#gpoggi #f1 #antonelli #campione #formula1")
    return spec, social


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--invia", action="store_true"); ap.add_argument("--uscita", type=Path, default=NS.QUI / "video_campione.mp4")
    a = ap.parse_args()
    spec, social = costruisci()
    asyncio.run(NS.genera(spec, a.uscita))
    if a.invia:
        NG.telegram(a.uscita, "🏆 Antonelli campione del mondo", social)


if __name__ == "__main__":
    main()
