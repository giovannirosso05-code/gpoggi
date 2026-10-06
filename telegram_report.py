"""Report di fine giornata sul tuo Telegram: le ultime notizie con i voti ricevuti nel sondaggio del giorno.

Chiude il sondaggio di oggi (stopPoll: cosi' i voti si leggono senza getUpdates), poi manda un solo messaggio con le notizie
(titolo, fonte, link) e accanto a ciascuna i voti. Se oggi non c'e' stato un sondaggio, elenca solo le ultime notizie.
Variabili: TELEGRAM_BOT_TOKEN e TELEGRAM_CANALE.   Uso: python telegram_report.py [--prova]
"""
import html
import json
import os
import sys
from datetime import datetime

import requests

import telegram_sondaggio as S


def main():
    prova = "--prova" in sys.argv
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_CANALE") or os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Mancano TELEGRAM_BOT_TOKEN o TELEGRAM_CANALE: report saltato.")
        return
    oggi = datetime.now(S.ROMA).strftime("%Y-%m-%d")
    stato = json.loads(S.STATO.read_text()) if S.STATO.exists() else {}
    sond = next((s for s in stato.get("sondaggi", {}).values() if s["data"] == oggi), None)
    voti = {}
    if sond and sond.get("message_id"):
        try:
            if sond.get("chiuso"):
                raise requests.RequestException("gia' chiuso")
            poll = S.api(token, "stopPoll", chat_id=chat, message_id=sond["message_id"])
            sond["chiuso"] = True
            for a, o in zip(sond["opzioni"], poll["options"]):
                voti[a["url"]] = o["voter_count"]
            if sum(voti.values()):
                best = max(sond["opzioni"], key=lambda a: voti[a["url"]])
                S.SCELTA.parent.mkdir(exist_ok=True)
                S.SCELTA.write_text(json.dumps({"data": oggi, "voti": list(voti.values()), **best}, ensure_ascii=False, indent=1))
        except requests.RequestException as e:
            print("  voti non letti:", e)
    if sond:
        notizie = sond["opzioni"]
    else:
        notizie = [{"titolo": a["titolo"], "url": a["url"], "fonte": a["fonte"], "serie": a.get("serie", "F1")} for a in json.loads(S.RASSEGNA.read_text())["articoli"][:5]]
    righe = [f"🏁 <b>GP Oggi · Report di fine giornata</b> ({datetime.now(S.ROMA).strftime('%d/%m')})", ""]
    for i, a in enumerate(notizie, 1):
        v = voti.get(a["url"])
        voto = f" — <b>{v} vot{'o' if v == 1 else 'i'}</b>" if v is not None else ""
        righe.append(f'{i}. [{a["serie"]}] <a href="{a["url"]}">{html.escape(a["titolo"])}</a> · {html.escape(a["fonte"])}{voto}')
    if sond and not sum(voti.values()):
        righe += ["", "Oggi nessun voto: la prossima notizia in video sarà scelta in ordine."]
    elif voti:
        righe += ["", "Vince la più votata: sarà il prossimo video."]
    righe += ["", "Tutto su https://gpoggi.it"]
    if prova:
        print("\n".join(righe))
        return
    S.api(token, "sendMessage", chat_id=chat, text="\n".join(righe), parse_mode="HTML", disable_web_page_preview="true", disable_notification="true")
    S.STATO.write_text(json.dumps(stato, ensure_ascii=False, indent=1))
    print("Report inviato.")


if __name__ == "__main__":
    main()
