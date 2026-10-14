"""Video "Chi è?" legato alla notizia del momento: chi guida il Mondiale di F1 (dati della classifica del sito) e invito a giocare gratis a «Chi è il pilota?» sul sito.

La foto parte molto sgranata e si schiarisce, gli indizi arrivano uno alla volta; l'ultimo (il primo posto nel Mondiale) rende la risposta facile per chi segue la F1:
si commenta per dire il nome. Se il leader è italiano, il gancio lo dice. Tutto dai dati del sito, nessun modello di linguaggio.
Uso:  python3 gioco_virale.py [--invia] [--uscita FILE]
"""
import argparse, asyncio, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gioco as G  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--invia", action="store_true")
    ap.add_argument("--uscita", type=Path, default=G.QUI / "gioco_virale.mp4")
    a = ap.parse_args()
    st = json.load(open(G.DATA / "standings.json"))
    capo = min(st["piloti"], key=lambda p: p["posizione"])
    c = G.scegli_pilota("f1", capo["nome"])
    punti = int(capo["punti"])
    italiano = c["naz"] == "Italia"
    indizi = [("Categoria", "Formula 1", "Corre in Formula uno."),
              ("Età", f"{c['eta']} anni", f"Ha {G.it(c['eta'])} anni."),
              ("Nazionalità", c["naz"], f"Nazionalità: {c['naz']}."),
              ("Mondiale", f"1° · {punti} punti", f"In classifica è primo, con {G.it(punti)} punti.")]
    intro = ("Un italiano guida il Mondiale di Formula uno! Sai dire chi è? " if italiano else "Chi guida il Mondiale di Formula uno? Sai dire chi è? ") + "Seguici per altri giochi come questo."
    cred = f"Foto: {G.autore(c['foto']['autore'])} · {c['foto']['licenza']} · Wikimedia Commons"
    asyncio.run(G.monta("#e8352f", "CHI È?", "Chi guida il <i>Mondiale</i> di Formula 1?", G.livelli_pixel(G.immagine_pilota(c)), indizi, "il nome", cred, intro, a.uscita,
                        fine_extra=" Gioca gratis a Chi è il pilota su G P Oggi punto it. Il link è in bio.", piede="Gioca gratis su gpoggi.it · link in bio"))
    social = (f"{'Un italiano guida il Mondiale di Formula 1 🇮🇹🏁' if italiano else 'Chi guida il Mondiale di Formula 1? 🏁'}\n\nSai chi è? Scrivi il nome nei commenti 👇\n\n"
              "Mandalo a un amico che segue la F1 e vediamo chi lo indovina per primo.\n\nGioca gratis a «Chi è il pilota?» sul sito: link in bio.\nSeguici per la risposta e per altri giochi.\n\n🔗 gpoggi.it\n\n#gpoggi #f1 #formula1 #indovinailpilota #mondiale")
    json.dump({"tipo": "pilota", "risposta": c["nome"], "social": social}, open(str(a.uscita) + ".json", "w"), ensure_ascii=False)
    if a.invia:
        G.invia_telegram(a.uscita)


if __name__ == "__main__":
    main()
