"""Video e copertina "Ferrari a Singapore: è il momento?" nello stile ultim'ora, con i ritratti ESPN (piloti) e quello libero di Vasseur.

  python3 ferrari_singapore.py uscita.mp4 copertina.png [--libero]

Senza --libero: ritratti ESPN in tuta per Leclerc e Hamilton (copyright ESPN, rischio accettato dal gestore).
Con --libero: solo foto con licenza libera di Wikimedia Commons (nessun rischio di copyright).
"""
import asyncio, json, sys
from pathlib import Path

QUI = Path(__file__).parent
sys.path.insert(0, str(QUI))
import copertina as C  # noqa: E402
import notizia_sub as N  # noqa: E402
import ritratti_espn as R  # noqa: E402

SITO = QUI.parent / "docs"
ROSSO_FERRARI = (214, 24, 32)
ESPN = "Foto: ESPN"
VAS = "Foto: Ferrari / Danyele · CC BY-SA 4.0 · Wikimedia Commons"
FAN = "Foto: Liauzh · CC BY-SA 4.0 · Wikimedia Commons"


def main(video, cop, libero=False):
    if libero:
        return main_libero(video, cop)
    lec = R.ritratto("Charles Leclerc", ROSSO_FERRARI)
    ham = R.ritratto("Lewis Hamilton", ROSSO_FERRARI)
    vas = R.ritratto_libero(SITO / "img/foto-extra/fr_d_ric_vasseur_ritratto.jpg", "vasseur")
    fan = R.ritratto_libero(SITO / "img/foto-extra/lewis_hamilton_fanzone2025.jpg", "hamilton_fan", larghezza=1080, y0=0)
    spec = {
        "serie": "F1", "titolo_breve": "Ferrari a Singapore: è il momento?", "fonte": "Motorsport.com", "velocita": "+38%",
        "scene": [
            {"foto": "Charles Leclerc", "foto_file": str(lec), "credito": ESPN, "hook": True, "hook_titolo": "Ferrari a Singapore: è il momento?",
             "testo": "[Ferrari] non vince da *7 gare*: l'ultima volta a Silverstone, a luglio. Ma a Singapore può essere l'occasione giusta."},
            {"foto": "Charles Leclerc", "foto_file": str(lec), "credito": ESPN, "nome": "CHARLES LECLERC",
             "testo": "La pista piace alla [Ferrari]: *niente lunghi rettilinei*, quindi il *deficit di potenza* del motore pesa meno."},
            {"foto": "Lewis Hamilton", "foto_file": str(ham), "credito": ESPN, "nome": "LEWIS HAMILTON",
             "testo": "In classifica la [Ferrari] è *seconda tra i costruttori*, con *58 punti* di vantaggio sulla McLaren."},
            {"foto": "Frédéric Vasseur", "foto_file": str(vas), "credito": VAS, "nome": "FRED VASSEUR",
             "testo": "Il team principal [Vasseur] frena: *«una delle gare più impegnative dell'anno»*. E dice che i distacchi tra le squadre sono *molto ridotti*."},
            {"foto": "Lewis Hamilton", "foto_file": str(fan), "credito": FAN,
             "testo": "L'ultima vittoria Ferrari qui è di *Sainz, nel 2023*. E questo è l'ultimo *weekend sprint* della stagione, con *una sola sessione di prove*."}],
        "finale": {"foto": "Charles Leclerc", "foto_file": str(lec), "credito": ESPN, "domanda": "E tu che dici? Può vincere la Ferrari a Singapore?"}}
    asyncio.run(N.genera(spec, video))
    # copertina: tre volti affiancati, più piccoli perché stiano nella striscia
    c1 = R.ritratto("Charles Leclerc", ROSSO_FERRARI, larghezza=700, centro_volto_y=560, sfx="_cop")
    c2 = R.ritratto("Lewis Hamilton", ROSSO_FERRARI, larghezza=700, centro_volto_y=560, sfx="_cop")
    c3 = R.ritratto_libero(SITO / "img/foto-extra/fr_d_ric_vasseur_ritratto.jpg", "vasseur_cop", larghezza=620, y0=345, fondo=(150, 14, 20))
    spec_cop = {"serie": "F1", "etichetta": "Ultim'ora", "titolo": ["FERRARI A SINGAPORE:", "È IL MOMENTO?"], "evidenzia": 1, "sottotitolo": "Non vince da 7 gare",
                "foto": [{"file": str(c1), "credito": "Foto: ESPN (Leclerc, Hamilton) · Ferrari/Danyele CC BY-SA 4.0, Wikimedia Commons (Vasseur)", "pos": "50% 0%"},
                         {"file": str(c2), "pos": "50% 0%"}, {"file": str(c3), "pos": "50% 0%"}]}
    asyncio.run(C.main(spec_cop, cop))


def main_libero(video, cop):
    ex = SITO / "img/foto-extra"
    lec = R.ritratto_libero(ex / "charles_leclerc_ferrari.jpg", "lec_libero", y0=0)
    fan = R.ritratto_libero(ex / "lewis_hamilton_fanzone2025.jpg", "hamilton_fan", y0=0)
    vas = R.ritratto_libero(ex / "fr_d_ric_vasseur_ritratto.jpg", "vasseur")
    aut = R.ritratto_libero(ex / "lewis_hamilton_giappone2025.jpg", "hamilton_auto", y0=420)
    c_lec = "Foto: Gilzetbase · CC BY-SA 4.0 · Wikimedia Commons"
    spec = {
        "serie": "F1", "titolo_breve": "Ferrari a Singapore: è il momento?", "fonte": "Motorsport.com", "velocita": "+38%",
        "scene": [
            {"foto": "Charles Leclerc", "foto_file": str(lec), "credito": c_lec, "hook": True, "hook_titolo": "Ferrari a Singapore: è il momento?",
             "testo": "[Ferrari] non vince da *7 gare*: l'ultima volta a Silverstone, a luglio. Ma a Singapore può essere l'occasione giusta."},
            {"foto": "Charles Leclerc", "foto_file": str(lec), "credito": c_lec, "nome": "CHARLES LECLERC",
             "testo": "La pista piace alla [Ferrari]: *niente lunghi rettilinei*, quindi il *deficit di potenza* del motore pesa meno."},
            {"foto": "Lewis Hamilton", "foto_file": str(fan), "credito": FAN, "nome": "LEWIS HAMILTON",
             "testo": "In classifica la [Ferrari] è *seconda tra i costruttori*, con *58 punti* di vantaggio sulla McLaren."},
            {"foto": "Frédéric Vasseur", "foto_file": str(vas), "credito": VAS, "nome": "FRED VASSEUR",
             "testo": "Il team principal [Vasseur] frena: *«una delle gare più impegnative dell'anno»*. E dice che i distacchi tra le squadre sono *molto ridotti*."},
            {"foto": "Lewis Hamilton", "foto_file": str(aut), "credito": "Foto: Liauzh · CC BY-SA 4.0 · Wikimedia Commons",
             "testo": "L'ultima vittoria Ferrari qui è di *Sainz, nel 2023*. E questo è l'ultimo *weekend sprint* della stagione, con *una sola sessione di prove*."}],
        "finale": {"foto": "Charles Leclerc", "foto_file": str(lec), "credito": c_lec, "domanda": "E tu che dici? Può vincere la Ferrari a Singapore?"}}
    asyncio.run(N.genera(spec, video))
    c1 = R.ritratto_libero(ex / "charles_leclerc_ferrari.jpg", "lec_cop", larghezza=720, y0=60, fondo=(150, 14, 20))
    c2 = R.ritratto_libero(ex / "lewis_hamilton_fanzone2025.jpg", "ham_cop", larghezza=720, y0=60, fondo=(150, 14, 20))
    c3 = R.ritratto_libero(ex / "fr_d_ric_vasseur_ritratto.jpg", "vasseur_cop", larghezza=620, y0=345, fondo=(150, 14, 20))
    spec_cop = {"serie": "F1", "etichetta": "Ultim'ora", "titolo": ["FERRARI A SINGAPORE:", "È IL MOMENTO?"], "evidenzia": 1, "sottotitolo": "Non vince da 7 gare",
                "foto": [{"file": str(c1), "credito": "Foto: Wikimedia Commons (Gilzetbase, Liauzh, Ferrari/Danyele) · CC BY-SA 4.0", "pos": "50% 0%"},
                         {"file": str(c2), "pos": "50% 0%"}, {"file": str(c3), "pos": "50% 0%"}]}
    asyncio.run(C.main(spec_cop, cop))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], "--libero" in sys.argv)
