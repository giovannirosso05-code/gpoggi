"""Chiedi un voto su una notizia (pulsante "vota questa"), una volta al giorno intorno alle 14:00.

Sceglie una notizia dalla rassegna non ancora votata oggi, o la prima se tutte sono state toccate.
Manda un messaggio con il titolo e un pulsante: chi clicca vota quella notizia.
I voti si accumulano su Cloudflare KV e raggiungono 75 → il video.
Variabili: TELEGRAM_BOT_TOKEN, TELEGRAM_CANALE, VOTI_WORKER_URL (URL del Worker che gestisce i voti).
Uso: python telegram_vota.py [--prova]
"""
import html, json, os, sys, urllib.parse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROMA = ZoneInfo("Europe/Rome")
ROOT = Path(__file__).parent
RASSEGNA = ROOT / "docs" / "data" / "rassegna.json"
STATO = ROOT / "telegram_voti.json"

def api(token, metodo, **dati):
    r = requests.post(f"https://api.telegram.org/bot{token}/{metodo}", data=dati, timeout=30)
    r.raise_for_status()
    return r.json().get("result")

def main():
    prova = "--prova" in sys.argv
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_CANALE") or os.environ.get("TELEGRAM_CHAT_ID")
    worker_url = os.environ.get("VOTI_WORKER_URL") or "https://gpoggivotti.giovannirosso05.workers.dev"
    if not prova and (not token or not chat):
        print("Mancano TELEGRAM_BOT_TOKEN o TELEGRAM_CANALE: voto saltato.")
        return
    
    oggi = datetime.now(ROMA).strftime("%Y-%m-%d")
    stato = json.loads(STATO.read_text()) if STATO.exists() else {}
    
    if stato.get("ultimo") == oggi:
        print("Voto già mandato oggi.")
        return
    
    rass = json.loads(RASSEGNA.read_text())["articoli"]
    gia_toccate = set(stato.get("toccate", []))
    candidate = [a for a in rass if a["url"] not in gia_toccate]
    if not candidate:
        gia_toccate = set()
        candidate = rass[:5]
    
    a = candidate[0]
    gia_toccate.add(a["url"])
    
    txt = f"🏁 <b>Vota la notizia di oggi</b>\n\n<b>{html.escape(a['titolo'][:80])}</b>\n\n<i>{html.escape(a['fonte'])}</i>"
    callback = f"vota_{urllib.parse.quote(a['url'][:50], safe='')}"
    
    if prova:
        print(txt)
        print(f"Pulsante: Vota questa · callback: {callback}")
        return
    
    try:
        api(token, "sendMessage", chat_id=chat, text=txt, parse_mode="HTML",
            reply_markup=json.dumps({"inline_keyboard": [[{"text": "👍 Vota questa", "callback_data": callback}]]}))
        stato["ultimo"] = oggi
        stato["toccate"] = list(gia_toccate)
        STATO.write_text(json.dumps(stato, ensure_ascii=False, indent=1))
        print("Richiesta voto inviata.")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()
