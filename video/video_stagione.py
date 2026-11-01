"""Video lungo sulla stagione 2026 di Kimi Antonelli, campione del mondo (≈90 s). Tutti i numeri vengono dai risultati del sito (docs/data/gare) controllati a mano;
i fatti di contorno (primo italiano a vincere in Cina da vent'anni, più giovane leader di sempre in Giappone, Monza dal 19° posto, titolo con il terzo posto in Messico)
da più testate (Il Post, AGI, Virgilio, Sky Sport, ESPN, Fanpage, Il Messaggero). Foto ESPN di questa stagione (scaricate al momento, mai nel repository).
Uso:  python3 video_stagione.py [--invia] [--uscita FILE]"""
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
esp = lambda p: f"https://a.espncdn.com/photo/2026/{p}_1296x729_16-9.jpg"
K = "Kimi Antonelli"


def costruisci():
    c = R.CACHE
    c.mkdir(exist_ok=True)
    comp = lambda nome, **k: str(B.composizione(K, str(c / nome), **k))
    f0 = comp("stag_v0.jpg", trofeo=TR, larghezza=1200, px=-170, tr_x=880, tr_h=520, alza=430, conf=True, luce=True)
    f1 = comp("stag_v1.jpg", trofeo=None, larghezza=1400, px=-160, alza=0, conf=True, luce=True)
    f2 = comp("stag_v2.jpg", trofeo=TR, larghezza=1450, px=-240, tr_x=880, tr_h=620, alza=0, conf=True, luce=True)

    def S(testo, foto=None, chips=None, cred=None, **k):
        cred = cred or f"{FOTO}: ESPN"
        d = {"foto": K, "testo": testo, "credito": cred, **k}
        if foto and foto.startswith("http"):
            d["foto_url"] = foto
        elif foto:
            d["foto_file"] = foto
        if chips:
            d["chips"] = [tuple(x) for x in chips]
            d["sub_top"] = 1440
        return d

    sc = [
        S(_("*Antonelli* è *campione del mondo*: ecco la sua stagione, gara dopo gara.", "*Antonelli* is *world champion*: here is his season, race by race."), f0, cred=CRED, hook=True,
          hook_titolo=_("Clamorosa stagione di Kimi", "Kimi's incredible season")),
        S(_("Si comincia in *Australia*, con un secondo posto dietro *Russell*.", "It starts in *Australia*, with second place behind *Russell*."), esp("0814/r1701692"), [("info", _("Australia: 2° (vince Russell)", "Australia: 2nd (Russell wins)"))]),
        S(_("In *Cina* arrivano la prima pole e la prima vittoria: la prima di un italiano in vent'anni.", "In *China* come the first pole and the first win: the first for an Italian in twenty years."), f1,
          [("si", _("Cina: pole", "China: pole")), ("si", _("Cina: prima vittoria in F1", "China: first F1 win")), ("info", _("Primo italiano a vincere da vent'anni", "First Italian winner in twenty years"))], fonte_alto="Il Post"),
        S(_("In *Giappone* vince ancora e diventa il più giovane leader del Mondiale di sempre.", "In *Japan* he wins again and becomes the youngest championship leader ever."), f2,
          [("si", _("Giappone: pole e vittoria", "Japan: pole and win")), ("info", _("Più giovane leader di sempre: 19 anni", "Youngest leader ever: 19 years old"))], cred=CRED, fonte_alto="AGI, Virgilio"),
        S(_("Poi *Miami*, *Canada* e *Monaco*: sono cinque vittorie di fila.", "Then *Miami*, *Canada* and *Monaco*: that's five wins in a row."), f2,
          [("si", _("Cina · Giappone · Miami", "China · Japan · Miami")), ("si", _("Canada · Monaco", "Canada · Monaco")), ("info", _("5 vittorie di fila", "5 wins in a row"))], cred=CRED),
        S(_("A *Monaco* festeggia con la bandiera italiana sulle spalle.", "In *Monaco* he celebrates with the Italian flag on his shoulders."), esp("0805/r1697948"), [("si", _("Monaco: pole e vittoria", "Monaco: pole and win"))], cred=f"{FOTO}: ESPN (Monaco 2026)"),
        S(_("L'estate si complica: ritiro a *Barcellona*, e in Gran Bretagna un quindicesimo posto dopo pole e vittoria nella sprint.", "Summer gets tougher: a retirement in *Barcelona*, and in Britain a fifteenth place after pole and a sprint win."), esp("1030/r1738641"),
          [("no", _("Barcellona: ritiro", "Barcelona: retirement")), ("si", _("Gran Bretagna: pole e sprint vinta", "Britain: pole and sprint win")), ("no", _("Gara: 15°", "Race: 15th"))]),
        S(_("Ma in *Belgio* torna a vincere, partendo dalla pole.", "But in *Belgium* he wins again, from pole."), esp("1031/r1739070"), [("si", _("Belgio: pole e vittoria", "Belgium: pole and win"))]),
        S(_("A *Monza* vince partendo dal *diciannovesimo* posto: a casa nessun italiano vinceva dal millenovecentosessantasei.", "At *Monza* he wins starting *nineteenth*: no Italian had won the home race since nineteen sixty-six."), f1,
          [("info", _("Partenza: 19°", "Start: 19th")), ("si", _("Monza: vittoria", "Monza: win")), ("info", _("Primo italiano a Monza dal 1966", "First Italian winner at Monza since 1966"))], fonte_alto="Sky Sport, ESPN"),
        S(_("Poi arrivano la *Spagna* e *Austin*: l'ottava e la nona vittoria.", "Then *Spain* and *Austin*: win number eight and win number nine."), esp("1026/r1736290"),
          [("si", _("Spagna: vittoria", "Spain: win")), ("si", _("Austin: pole e vittoria", "Austin: pole and win")), ("info", _("9 vittorie", "9 wins"))], cred=f"{FOTO}: ESPN (Austin 2026)"),
        S(_("Dopo la pausa i podi non mancano: terzo in *Austria*, terzo in *Ungheria*, secondo in *Olanda*.", "The podiums keep coming: third in *Austria*, third in *Hungary*, second in the *Netherlands*."), esp("0819/r1703751"),
          [("si", _("Austria: 3°", "Austria: 3rd")), ("si", _("Ungheria: 3°", "Hungary: 3rd")), ("si", _("Olanda: 2°", "Netherlands: 2nd"))]),
        S(_("A *Baku* è sedicesimo in qualifica e chiude la gara quinto, poi secondo in *Bahrain* e terzo a *Singapore*.", "In *Baku* he qualifies sixteenth and finishes the race fifth, then second in *Bahrain* and third in *Singapore*."), esp("0814/r1701692"),
          [("info", _("Azerbaigian: qualifica 16°, gara 5°", "Azerbaijan: qualifying 16th, race 5th")), ("si", _("Bahrain: 2°", "Bahrain: 2nd")), ("si", _("Singapore: 3°", "Singapore: 3rd"))]),
        S(_("Il rivale più vicino è *Russell*: dopo Austin ha duecentoquarantadue punti, contro i trecentosessantacinque di Kimi.", "His closest rival is *Russell*: after Austin he has two hundred and forty-two points, against Kimi's three hundred and sixty-five."), esp("1031/r1738806"),
          [("info", _("Antonelli: 365 punti", "Antonelli: 365 points")), ("info", _("Russell: 242 punti", "Russell: 242 points"))]),
        S(_("Il bilancio prima del Messico: *nove vittorie*, *sette pole* e *quindici podi* in diciotto gare.", "The record before Mexico: *nine wins*, *seven poles* and *fifteen podiums* in eighteen races."), esp("1023/r1735238"),
          [("si", _("9 vittorie", "9 wins")), ("si", _("7 pole", "7 poles")), ("si", _("15 podi in 18 gare", "15 podiums in 18 races"))]),
        S(_("Alla vigilia aveva raccontato di avere la *febbre*, ma ha voluto il titolo.", "The day before, he said he had a *fever*, but he wanted the title anyway."), esp("1030/r1738641"), [("info", _("Messico: Antonelli ha la febbre", "Mexico: Antonelli has a fever"))], fonte_alto="Automoto.it"),
        S(_("A *Città del Messico* vince *Verstappen*, ma Kimi chiude terzo davanti a *Leclerc*: basta, è campione del mondo.", "In *Mexico City* *Verstappen* wins, but Kimi finishes third ahead of *Leclerc*: that's enough, he is world champion."), esp("1101/r1739242"),
          [("si", _("Messico: 3° posto", "Mexico: 3rd place")), ("si", _("Campione con 4 gare d'anticipo", "Champion with 4 races to spare"))], fonte_alto="Fanpage, Il Messaggero", cred=f"{FOTO}: ESPN ({_('Città del Messico', 'Mexico City')} 2026)"),
        S(_("A vent'anni è il più giovane campione di sempre: il record era di *Vettel*, a ventitré. E l'Italia, dopo *Ascari*, ha di nuovo un campione.", "At twenty he is the youngest champion ever: the record was *Vettel's*, at twenty-three. And Italy, after *Ascari*, has a champion again."), f2, cred=CRED, pausa=0.2),
    ]
    spec = {"serie": "F1", "titolo_breve": _("Clamorosa stagione di Kimi", "Kimi's incredible season"), "etichetta": _("Stagione 2026", "2026 season"), "fonte": "GP Oggi", "velocita": "+38%", "segui": False, "scene": sc,
            "finale": {"foto": K, "domanda": _("Qual è stato il momento più bello della stagione di Kimi?", "What was the best moment of Kimi's season?")}}
    social = _("""🏆🇮🇹 CLAMOROSA STAGIONE DI KIMI ANTONELLI, GARA DOPO GARA 🇮🇹🏆

Secondo in Australia, poi la prima pole e la prima vittoria in Cina. Cinque vittorie di fila fino a Monaco, il ritiro di Barcellona, la rimonta di Monza dal 19° posto, e il titolo a Città del Messico a 20 anni: il più giovane campione di sempre e il primo italiano dopo Ascari, nel 1953.
Prima del Messico: 9 vittorie, 7 pole e 15 podi in 18 gare.

Qual è stato il momento più bello della stagione di Kimi? Dimmi la tua nei commenti 👇

Fonti: Il Post, AGI, Sky Sport, ESPN, Fanpage.
🔗 gpoggi.it

#gpoggi #f1 #antonelli #campionedelmondo #stagione""", """🏆🇮🇹 KIMI ANTONELLI'S INCREDIBLE SEASON, RACE BY RACE 🇮🇹🏆

Second in Australia, then his first pole and first win in China. Five wins in a row up to Monaco, the Barcelona retirement, the Monza comeback from 19th on the grid, and the title in Mexico City at 20: the youngest champion ever and the first Italian since Ascari, in 1953.
Before Mexico: 9 wins, 7 poles and 15 podiums in 18 races.

What was the best moment of Kimi's season? Tell us in the comments 👇

Sources: Il Post, AGI, Sky Sport, ESPN, Fanpage.
🔗 gpoggi.it

#gpoggi #f1 #antonelli #worldchampion #season""")
    return spec, social


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--invia", action="store_true"); ap.add_argument("--uscita", type=Path, default=NS.QUI / "video_stagione.mp4")
    a = ap.parse_args()
    spec, social = costruisci()
    asyncio.run(NS.genera(spec, a.uscita))
    if a.invia:
        NG.telegram(a.uscita, _("🏆 Clamorosa stagione di Kimi", "🏆 Kimi's incredible season (EN)"), social)


if __name__ == "__main__":
    main()
