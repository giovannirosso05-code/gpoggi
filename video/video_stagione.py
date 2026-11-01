"""Video lungo sulla stagione 2026 di Kimi Antonelli, campione del mondo (≈90 s). Tutti i numeri vengono dai risultati del sito (docs/data/gare) controllati a mano;
i fatti di contorno (primo italiano a vincere in Cina da vent'anni, più giovane leader di sempre in Giappone, Monza dal 19° posto, titolo con il terzo posto in Messico)
da più testate (Il Post, AGI, Virgilio, Sky Sport, ESPN, Fanpage, Il Messaggero). Foto ESPN di questa stagione (scaricate al momento, mai nel repository).
Uso:  python3 video_stagione.py [--invia] [--uscita FILE]"""
import argparse, asyncio, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bandiera as B  # noqa: E402
import notizia_sub as NS  # noqa: E402
import notizie_giorno as NG  # noqa: E402
import ritratti_espn as R  # noqa: E402

TR = B.QUI / "extra" / "trofeo-f1.jpg"
CRED = "Foto: ESPN · Trofeo: Raimond Spekking (CC BY-SA 4.0), Wikimedia Commons"
esp = lambda p: f"https://a.espncdn.com/photo/2026/{p}_1296x729_16-9.jpg"
K = "Kimi Antonelli"


def costruisci():
    c = R.CACHE
    c.mkdir(exist_ok=True)
    comp = lambda nome, **k: str(B.composizione(K, str(c / nome), **k))
    f0 = comp("stag_v0.jpg", trofeo=TR, larghezza=1200, px=-170, tr_x=880, tr_h=520, alza=430, conf=True, luce=True)
    f1 = comp("stag_v1.jpg", trofeo=None, larghezza=1400, px=-160, alza=0, conf=True, luce=True)
    f2 = comp("stag_v2.jpg", trofeo=TR, larghezza=1450, px=-240, tr_x=880, tr_h=620, alza=0, conf=True, luce=True)

    def S(testo, foto=None, chips=None, cred="Foto: ESPN", **k):
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
        S("*Antonelli* è *campione del mondo*: ecco la sua stagione, gara dopo gara.", f0, cred=CRED, hook=True, hook_titolo="Antonelli campione: la sua stagione"),
        S("Si comincia in *Australia*, con un secondo posto dietro *Russell*.", esp("0814/r1701692"), [("info", "Australia: 2° (vince Russell)")]),
        S("In *Cina* arrivano la prima pole e la prima vittoria: la prima di un italiano in vent'anni.", f1, [("si", "Cina: pole"), ("si", "Cina: prima vittoria in F1"), ("info", "Primo italiano a vincere da vent'anni")], fonte_alto="Il Post"),
        S("In *Giappone* vince ancora e diventa il più giovane leader del Mondiale di sempre.", f2, [("si", "Giappone: pole e vittoria"), ("info", "Più giovane leader di sempre: 19 anni")], cred=CRED, fonte_alto="AGI, Virgilio"),
        S("Poi *Miami*, *Canada* e *Monaco*: sono cinque vittorie di fila.", f2, [("si", "Cina · Giappone · Miami"), ("si", "Canada · Monaco"), ("info", "5 vittorie di fila")], cred=CRED),
        S("A *Monaco* festeggia con la bandiera italiana sulle spalle.", esp("0805/r1697948"), [("si", "Monaco: pole e vittoria")], cred="Foto: ESPN (Monaco 2026)"),
        S("L'estate si complica: ritiro a *Barcellona*, e in Gran Bretagna un quindicesimo posto dopo pole e vittoria nella sprint.", esp("1030/r1738641"), [("no", "Barcellona: ritiro"), ("si", "Gran Bretagna: pole e sprint vinta"), ("no", "Gara: 15°")]),
        S("Ma in *Belgio* torna a vincere, partendo dalla pole.", esp("1031/r1739070"), [("si", "Belgio: pole e vittoria")]),
        S("A *Monza* vince partendo dal *diciannovesimo* posto: a casa nessun italiano vinceva dal millenovecentosessantasei.", f1, [("info", "Partenza: 19°"), ("si", "Monza: vittoria"), ("info", "Primo italiano a Monza dal 1966")], fonte_alto="Sky Sport, ESPN"),
        S("Poi arrivano la *Spagna* e *Austin*: l'ottava e la nona vittoria.", esp("1026/r1736290"), [("si", "Spagna: vittoria"), ("si", "Austin: pole e vittoria"), ("info", "9 vittorie")], cred="Foto: ESPN (Austin 2026)"),
        S("Dopo la pausa i podi non mancano: terzo in *Austria*, terzo in *Ungheria*, secondo in *Olanda*.", esp("0819/r1703751"), [("si", "Austria: 3°"), ("si", "Ungheria: 3°"), ("si", "Olanda: 2°")]),
        S("A *Baku* è sedicesimo in qualifica e chiude la gara quinto, poi secondo in *Bahrain* e terzo a *Singapore*.", esp("0814/r1701692"), [("info", "Azerbaigian: qualifica 16°, gara 5°"), ("si", "Bahrain: 2°"), ("si", "Singapore: 3°")]),
        S("Il rivale più vicino è *Russell*: dopo Austin ha duecentoquarantadue punti, contro i trecentosessantacinque di Kimi.", esp("1031/r1738806"), [("info", "Antonelli: 365 punti"), ("info", "Russell: 242 punti")]),
        S("Il bilancio prima del Messico: *nove vittorie*, *sette pole* e *quindici podi* in diciotto gare.", esp("1023/r1735238"), [("si", "9 vittorie"), ("si", "7 pole"), ("si", "15 podi in 18 gare")]),
        S("Alla vigilia aveva raccontato di avere la *febbre*, ma ha voluto il titolo.", esp("1030/r1738641"), [("info", "Messico: Antonelli ha la febbre")], fonte_alto="Automoto.it"),
        S("A *Città del Messico* vince *Verstappen*, ma Kimi chiude terzo davanti a *Leclerc*: basta, è campione del mondo.", esp("1101/r1739242"), [("si", "Messico: 3° posto"), ("si", "Campione con 4 gare d'anticipo")], fonte_alto="Fanpage, Il Messaggero", cred="Foto: ESPN (Città del Messico 2026)"),
        S("A vent'anni è il più giovane campione di sempre: il record era di *Vettel*, a ventitré. E l'Italia, dopo *Ascari*, ha di nuovo un campione.", f2, cred=CRED, pausa=0.2),
    ]
    spec = {"serie": "F1", "titolo_breve": "La stagione di Antonelli", "etichetta": "Stagione 2026", "fonte": "GP Oggi", "velocita": "+38%", "segui": False, "scene": sc,
            "finale": {"foto": K, "domanda": "Qual è stato il momento più bello della stagione di Kimi?"}}
    social = ("🏆🇮🇹 LA STAGIONE DI KIMI ANTONELLI, GARA DOPO GARA 🇮🇹🏆\n\n"
              "Seconda in Australia, poi la prima pole e la prima vittoria in Cina. Cinque vittorie di fila fino a Monaco, il ritiro di Barcellona, la rimonta di Monza dal 19° posto, "
              "e il titolo a Città del Messico a 20 anni: il più giovane campione di sempre e il primo italiano dopo Ascari, nel 1953.\n"
              "Prima del Messico: 9 vittorie, 7 pole e 15 podi in 18 gare.\n\n"
              "Qual è stato il momento più bello della stagione di Kimi? Dimmi la tua nei commenti 👇\n\n"
              "Fonti: Il Post, AGI, Sky Sport, ESPN, Fanpage.\n🔗 gpoggi.it\n\n#gpoggi #f1 #antonelli #campionedelmondo #stagione")
    return spec, social


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--invia", action="store_true"); ap.add_argument("--uscita", type=Path, default=NS.QUI / "video_stagione.mp4")
    a = ap.parse_args()
    spec, social = costruisci()
    asyncio.run(NS.genera(spec, a.uscita))
    if a.invia:
        NG.telegram(a.uscita, "🏆 La stagione di Antonelli", social)


if __name__ == "__main__":
    main()
