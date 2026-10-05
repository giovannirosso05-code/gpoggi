"""Notizie del giorno sul tuo Telegram, da votare, e raccolta del voto.

Una volta al giorno (dalle 10 ora italiana) manda al bot il messaggio con le notizie piu' interessanti (solo titolo, fonte e link,
niente testi copiati) e un sondaggio: la notizia con piu' voti diventa il video del giorno. Ogni giro legge anche i voti dati
(poll_answer) e scrive la scelta in video/scelta.json, che si legge poi per preparare il video.

Variabili d'ambiente: TELEGRAM_BOT_TOKEN e TELEGRAM_CANALE (il numero della tua chat con il bot).
Uso:  python telegram_sondaggio.py --prova    (stampa cosa manderebbe senza inviare)
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).parent
STATO = ROOT / "telegram_sondaggi.json"
SCELTA = ROOT / "video" / "scelta.json"
RASSEGNA = ROOT / "docs" / "data" / "rassegna.json"
ROMA = ZoneInfo("Europe/Rome")
ORA_MINIMA = 10
QUANTE = 5


def api(token, metodo, **dati):
    r = requests.post(f"https://api.telegram.org/bot{token}/{metodo}", data=dati, timeout=30)
    r.raise_for_status()
    return r.json()["result"]


def taglia(testo, n):
    return testo if len(testo) <= n else testo[: n - 1].rstrip() + "…"


def candidate(stato):
    """Prime notizie non ancora proposte, alternando F1 e MotoGP quando possibile."""
    if not RASSEGNA.exists():
        return []
    viste = set(stato.get("proposte", []))
    nuove = [a for a in json.loads(RASSEGNA.read_text())["articoli"] if a["url"] not in viste]
    per_serie = {}
    for a in nuove:
        per_serie.setdefault(a.get("serie", "F1"), []).append(a)
    out = []
    while len(out) < QUANTE and any(per_serie.values()):
        for serie in list(per_serie):
            if per_serie[serie] and len(out) < QUANTE:
                out.append(per_serie[serie].pop(0))
    return out


def raccogli_voti(token, stato):
    """Legge i voti arrivati e aggiorna la scelta di ogni sondaggio."""
    ris = api(token, "getUpdates", offset=stato.get("offset", 0), allowed_updates=json.dumps(["poll_answer"]), timeout=0)
    for u in ris:
        stato["offset"] = u["update_id"] + 1
        pa = u.get("poll_answer")
        if not pa:
            continue
        sond = stato.get("sondaggi", {}).get(pa["poll_id"])
        if sond is not None:
            sond["voto"] = pa["option_ids"][0] if pa["option_ids"] else None   # None = voto ritirato
    # scelta: l'ultimo sondaggio che ha ricevuto un voto valido
    for pid, s in sorted(stato.get("sondaggi", {}).items(), key=lambda kv: kv[1]["data"], reverse=True):
        if s.get("voto") is not None:
            a = s["opzioni"][s["voto"]]
            SCELTA.parent.mkdir(exist_ok=True)
            SCELTA.write_text(json.dumps({"data": s["data"], **a}, ensure_ascii=False, indent=1))
            break


def main():
    prova = "--prova" in sys.argv
    stato = json.loads(STATO.read_text()) if STATO.exists() else {}
    ora = datetime.now(ROMA)
    oggi = ora.strftime("%Y-%m-%d")
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CANALE")
    if not prova and (not token or not chat):
        print("Mancano TELEGRAM_BOT_TOKEN o TELEGRAM_CANALE: sondaggio saltato.")
        return
    if not prova:
        raccogli_voti(token, stato)
    gia = stato.get("ultimo") == oggi
    cand = [] if gia or ora.hour < ORA_MINIMA else candidate(stato)
    if prova:
        for i, a in enumerate(candidate(stato), 1):
            print(f"{i}. [{a.get('serie', 'F1')}] {a['titolo']} ({a['fonte']})")
        return
    if len(cand) >= 2:
        righe = ["<b>Notizie del giorno</b>", "Vota qui sotto quella che vuoi in video.", ""]
        for i, a in enumerate(cand, 1):
            righe.append(f'{i}. [{a.get("serie", "F1")}] <a href="{a["url"]}">{a["titolo"].replace("<", "").replace(">", "")}</a> · {a["fonte"]}')
        api(token, "sendMessage", chat_id=chat, text="\n".join(righe), parse_mode="HTML", disable_web_page_preview="true")
        opzioni = [taglia(f'{i}. [{a.get("serie", "F1")}] {a["titolo"]}', 100) for i, a in enumerate(cand, 1)]
        sond = api(token, "sendPoll", chat_id=chat, question="Quale notizia facciamo in video?", options=json.dumps(opzioni, ensure_ascii=False), is_anonymous="false")
        stato.setdefault("sondaggi", {})[sond["poll"]["id"]] = {"data": oggi, "voto": None, "opzioni": [{"titolo": a["titolo"], "url": a["url"], "fonte": a["fonte"], "serie": a.get("serie", "F1")} for a in cand]}
        stato["proposte"] = ([a["url"] for a in cand] + stato.get("proposte", []))[:300]
        stato["ultimo"] = oggi
        print("Sondaggio inviato con", len(cand), "notizie")
    STATO.write_text(json.dumps(stato, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
