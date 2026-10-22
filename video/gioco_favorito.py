"""Video "Chi è?" sul favorito per il podio del prossimo Gran Premio: la foto parte molto sgranata e si schiarisce, gli indizi arrivano uno alla volta
(categoria, età, nazionalità, forma recente) e l'ultimo dice che è tra i favoriti di GP Oggi per il podio. Si risponde nei commenti.
Tutti i dati vengono dal sito (pronostici.json, schede.json, roster/foto MotoGP): nessun testo scritto a mano, nessun modello di linguaggio.
Mai le parole «pronostico», «scommesse», «quote», premi o soldi (regole TikTok): si dice «favoriti per il podio».

Uso:  python3 gioco_favorito.py [auto|f1|motogp] [--pos 0|1|2] [--invia] [--uscita FILE]
auto = la gara che parte prima; --pos sceglie quale dei primi tre favoriti (di base il primo).
"""
import argparse, asyncio, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gioco as G  # noqa: E402


def scegli(serie, pos):
    pron = json.load(open(G.DATA / "pronostici.json"))
    ora = datetime.now(timezone.utc)
    cand = {k: pron[k] for k in ("f1", "motogp") if pron.get(k) and pron[k].get("favoriti") and datetime.fromisoformat(pron[k]["gara"]) > ora}
    if serie != "auto":
        if serie not in cand:
            raise SystemExit(f"nessuna gara in programma per {serie}")
        k = serie
    else:
        if not cand:
            raise SystemExit("nessuna gara in programma")
        k = min(cand, key=lambda x: cand[x]["gara"])
    return k, cand[k], cand[k]["favoriti"][pos]


def nome_gp_voce(gp):
    return gp.replace("GP ", "Gran Premio d'", 1) if gp.startswith("GP ") else gp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("serie", nargs="?", default="auto", choices=["auto", "f1", "motogp"])
    ap.add_argument("--pos", type=int, default=0, choices=[0, 1, 2])
    ap.add_argument("--invia", action="store_true")
    ap.add_argument("--uscita", type=Path, default=G.QUI / "gioco_favorito.mp4")
    a = ap.parse_args()
    k, p, fav = scegli(a.serie, a.pos)
    c = G.scegli_pilota("f1" if k == "f1" else "moto", fav["nome"])
    moto = k == "motogp"
    col = "#1f5fd1" if moto else "#e8352f"
    categoria, serie_voce = ("MotoGP", "MotoGP") if moto else ("Formula 1", "Formula uno")
    gp, gp_voce = p["gp"], nome_gp_voce(p["gp"])
    italiano = c["naz"] == "Italia"
    indizi = [("Categoria", categoria, f"Corre in {serie_voce}."),
              ("Nazionalità", c["naz"], f"Nazionalità: {c['naz']}."),
              ("Età", f"{c['eta']} anni", f"Ha {G.it(c['eta'])} anni.")]
    m = next((re.match(r"(\d+) vittori[ae] nelle ultime (\d+) gare", x) for x in fav.get("motivi", []) if re.match(r"(\d+) vittori[ae] nelle ultime (\d+) gare", x)), None)
    if m:
        n, tot = int(m.group(1)), int(m.group(2))
        indizi.append(("Forma", f"{n} vittorie su {tot} gare" if n != 1 else f"1 vittoria su {tot} gare",
                       f"Ha vinto {G.it(n)} delle ultime {G.it(tot)} gare." if n != 1 else f"Ha vinto una delle ultime {G.it(tot)} gare."))
    indizi.append(("Podio", gp.replace("Gran Premio degli ", "").replace("Gran Premio di ", "").replace("GP ", ""), f"Per GP Oggi è tra i favoriti per salire sul podio al {gp_voce}."))
    intro = (f"Un italiano è tra i favoriti per il podio al {gp_voce}! Sai dire chi è? " if italiano else f"Chi è tra i favoriti per il podio al {gp_voce}? Sai dire chi è? ") + "Seguici per altri giochi come questo."
    cred = f"Foto: {G.autore(c['foto']['autore'])} · {c['foto']['licenza']} · Wikimedia Commons"
    asyncio.run(G.monta(col, "CHI È?", f"Tra i favoriti per il <i>podio</i> · {gp}", G.livelli_pixel(G.immagine_pilota(c)), indizi, "il nome", cred, intro, a.uscita))
    tag = "#motogp" if moto else "#f1 #formula1"
    social = (f"{'Un italiano è tra i favoriti per il podio ' if italiano else 'Chi è tra i favoriti per il podio '}{('🇮🇹 ' if italiano else '')}{'🏍️' if moto else '🏁'}\n\n"
              f"{gp}: sai chi è? Scrivi il nome nei commenti 👇\n\nSeguici per la risposta e per altri giochi come questo.\n\n🔗 gpoggi.it\n\n#gpoggi {tag} #granpremio")
    json.dump({"tipo": "pilota", "risposta": c["nome"], "social": social}, open(str(a.uscita) + ".json", "w"), ensure_ascii=False)
    if a.invia:
        G.invia_telegram(a.uscita)


if __name__ == "__main__":
    main()
