"""Pubblica sul canale Telegram il riepilogo dell'ultima gara disputata, una sola volta per gara.

Legge i dati gia' scaricati in docs/data/ (nessuna notizia copiata da altri siti).
Variabili d'ambiente: TELEGRAM_BOT_TOKEN e TELEGRAM_CANALE (per esempio @nomecanale).
Uso:  python telegram_post.py --prova    (stampa il messaggio senza inviarlo)
"""
import html
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).parent
DATA = ROOT / "docs" / "data"
STATO = ROOT / "telegram_stato.json"
SITO = "https://gpoggi.it"


def ultima_gara():
    eventi = json.loads((DATA / "events.json").read_text())
    for ev in sorted(eventi, key=lambda e: e["fine"], reverse=True):
        scheda = json.loads((DATA / "gare" / f"{ev['id']}.json").read_text())
        for s in scheda["sessioni"]:
            if s.get("tipo") == "Race" and s.get("risultati"):
                return scheda, s
    return None, None


def messaggio(g, s):
    podio = [r for r in s["risultati"] if r.get("pos") and r["pos"] <= 3]
    righe = [f"<b>{html.escape(g['nome'], quote=False)}</b>", f"{html.escape(g['circuito'], quote=False)}, {html.escape(g['paese'], quote=False)}", ""]
    for r in sorted(podio, key=lambda r: r["pos"]):
        nome = html.escape(r.get("nome") or f"Pilota #{r['numero']}", quote=False)
        team = html.escape(r.get("team") or "n.d.", quote=False)
        tempo = f" · {html.escape(r['tempo'], quote=False)}" if r.get("tempo") else ""
        righe.append(f"{r['pos']}° {nome} ({team}){tempo}")
    st = json.loads((DATA / "standings.json").read_text())
    if st.get("piloti"):
        righe += ["", "<b>Classifica piloti</b>"]
        for p in st["piloti"][:5]:
            righe.append(f"{p['posizione']}. {html.escape(p.get('nome') or '#' + str(p['numero']))} — {p['punti']:g}")
    righe += ["", f'<a href="{SITO}/gara.html?id={g["id"]}">Tutti i risultati</a>']
    return "\n".join(righe)


def main():
    prova = "--prova" in sys.argv
    g, s = ultima_gara()
    if not g:
        print("Nessuna gara disputata: niente da pubblicare.")
        return
    chiave = f"{g['id']}:{s['key']}"
    stato = json.loads(STATO.read_text()) if STATO.exists() else {}
    testo = messaggio(g, s)
    if prova:
        print(testo)
        return
    if stato.get("ultima") == chiave:
        print("Gara gia' pubblicata:", chiave)
        return
    token, canale = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CANALE")
    if not token or not canale:
        print("Mancano TELEGRAM_BOT_TOKEN o TELEGRAM_CANALE: invio saltato.")
        return
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      data={"chat_id": canale, "text": testo, "parse_mode": "HTML", "disable_web_page_preview": "true"}, timeout=30)
    r.raise_for_status()
    STATO.write_text(json.dumps({"ultima": chiave}))
    print("Pubblicato:", chiave)


if __name__ == "__main__":
    main()
