"""Pubblica sul canale Telegram il riepilogo dell'ultima gara disputata, una sola volta per gara.

Legge i dati gia' scaricati in docs/data/ (nessuna notizia copiata da altri siti).
Variabili d'ambiente: TELEGRAM_BOT_TOKEN e TELEGRAM_CANALE (il codice numerico della chat con il bot, oppure @nomecanale).
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


def nuove_notizie(stato):
    """Titoli della rassegna stampa non ancora inviati (solo titolo, fonte e link). Alla prima volta si segnano tutti come gia' visti."""
    file = DATA / "rassegna.json"
    if not file.exists():
        return [], stato.get("visti", [])
    articoli = json.loads(file.read_text())["articoli"]
    visti = stato.get("visti")
    urls = [a["url"] for a in articoli]
    if visti is None:
        return [], urls
    nuovi = [a for a in articoli if a["url"] not in set(visti)][:5]
    return nuovi, (urls + visti)[:300]


def messaggio_moto():
    """Riepilogo dell'ultima gara MotoGP (podio, primi cinque della classifica) dai file motogp-ultima.json e motogp-classifica.json."""
    f = DATA / "motogp-ultima.json"
    if not f.exists():
        return None, None
    u = json.loads(f.read_text())
    ris = [r for r in u.get("risultati", []) if r.get("pos")][:3]
    if not ris:
        return None, None
    righe = [f"<b>MotoGP · {html.escape(u['nome'], quote=False)}</b>", html.escape(u.get("circuito") or "", quote=False), ""]
    for r in ris:
        dist = f" · {html.escape(r['tempo'])}" if r["pos"] == 1 and r.get("tempo") else (f" · +{html.escape(r['distacco'])}" if r.get("distacco") else "")
        righe.append(f"{r['pos']}° {html.escape(r['nome'], quote=False)} ({html.escape(r['moto'], quote=False)}){dist}")
    cf = DATA / "motogp-classifica.json"
    if cf.exists():
        righe += ["", "<b>Classifica piloti MotoGP</b>"]
        for p in json.loads(cf.read_text())["piloti"][:5]:
            righe.append(f"{p['pos']}. {html.escape(p['nome'], quote=False)} — {p['punti']:g}")
    righe += ["", f'<a href="{SITO}/motogp.html">Tutta la MotoGP</a>']
    return f"{u['nome']}:{u['data']}", "\n".join(righe)


def testo_notizia(a):
    return f'<b>[{html.escape(a.get("serie", "F1"))}] {html.escape(a["titolo"], quote=False)}</b>\n{html.escape(a["fonte"], quote=False)} · <a href="{html.escape(a["url"])}">Leggi</a>'


def invia(token, chat, testo):
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      data={"chat_id": chat, "text": testo, "parse_mode": "HTML", "disable_web_page_preview": "true"}, timeout=30)
    r.raise_for_status()


def main():
    prova = "--prova" in sys.argv
    g, s = ultima_gara()
    if not g:
        print("Nessuna gara disputata: niente da pubblicare.")
        return
    chiave = f"{g['id']}:{s['key']}"
    stato = json.loads(STATO.read_text()) if STATO.exists() else {}
    testo = messaggio(g, s)
    nuove, visti = nuove_notizie(stato)
    chiave_moto, testo_moto = messaggio_moto()
    if prova:
        print(testo)
        if testo_moto:
            print("\n" + testo_moto)
        for a in nuove or []:
            print("\n" + testo_notizia(a))
        return
    token, canale = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CANALE")
    if not token or not canale:
        print("Mancano TELEGRAM_BOT_TOKEN o TELEGRAM_CANALE: invio saltato.")
        return
    if stato.get("ultima") != chiave:
        invia(token, canale, testo)
        stato["ultima"] = chiave
        print("Report pubblicato:", chiave)
    if testo_moto and stato.get("ultima_moto") != chiave_moto:
        invia(token, canale, testo_moto)
        stato["ultima_moto"] = chiave_moto
        print("Report MotoGP pubblicato:", chiave_moto)
    if os.environ.get("TELEGRAM_MODALITA") != "privata":   # in chat privata le notizie arrivano dal sondaggio del giorno
        for a in nuove:
            invia(token, canale, testo_notizia(a))
    stato["visti"] = visti
    STATO.write_text(json.dumps(stato))
    print(f"Notizie inviate: {len(nuove)}")


if __name__ == "__main__":
    main()
