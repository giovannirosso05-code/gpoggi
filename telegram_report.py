"""Report di fine giornata: le ultime 5 notizie con i voti accumulati (0-75).

Legge i voti da Cloudflare KV (chiave voti:<url>) e mostra una barra per ogni notizia.
Se una raggiunge 75 voti, quella diventa il video di domani.
Variabili: TELEGRAM_BOT_TOKEN, TELEGRAM_CANALE, VOTI_WORKER_URL.
Uso: python telegram_report.py [--prova]
"""
import html, json, os, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROMA = ZoneInfo("Europe/Rome")
ROOT = Path(__file__).parent
RASSEGNA = ROOT / "docs" / "data" / "rassegna.json"
SCELTA = ROOT / "video" / "scelta.json"

def api(token, metodo, **dati):
    r = requests.post(f"https://api.telegram.org/bot{token}/{metodo}", data=dati, timeout=30)
    r.raise_for_status()
    return r.json().get("result")

def barra(voti, max_v=75):
    """Barra di testo: ▮▮▮▯▯ (XX/75)"""
    pieni = min(voti, max_v)
    barre = int(pieni * 5 / max_v)
    vuoti = 5 - barre
    return "▮" * barre + "▯" * vuoti

def main():
    prova = "--prova" in sys.argv
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_CANALE") or os.environ.get("TELEGRAM_CHAT_ID")
    worker_url = os.environ.get("VOTI_WORKER_URL") or "https://gpoggivotti.giovannirosso05.workers.dev"
    
    if not prova and (not token or not chat):
        print("Mancano TELEGRAM_BOT_TOKEN o TELEGRAM_CANALE: report saltato.")
        return
    
    try:
        rass = json.loads(RASSEGNA.read_text())["articoli"][:5]
    except Exception as e:
        print(f"Errore lettura rassegna: {e}")
        return
    
    notizie = []
    vincente = None
    max_voti = -1
    
    for a in rass:
        try:
            v = int(requests.get(f"{worker_url}?voti={a['url']}", timeout=10).json().get("voti", 0))
        except Exception:
            v = 0
        
        notizie.append((a, v))
        if v > max_voti:
            max_voti = v
            if v >= 75:
                vincente = a
    
    righe = [f"🏁 <b>GP Oggi · Report voti</b> ({datetime.now(ROMA).strftime('%d/%m')})"]
    for a, v in notizie:
        vin = " 🎯" if a == vincente else ""
        righe.append(f'{barra(v)} <b>{v}</b> · [{a["serie"]}] <a href="{a["url"]}">{html.escape(a["titolo"][:60])}</a>{vin}')
    
    if vincente:
        righe.append(f"\n✅ Questa sarà il video di domani!")
        SCELTA.parent.mkdir(exist_ok=True)
        SCELTA.write_text(json.dumps({"data": datetime.now(ROMA).strftime("%Y-%m-%d"), **vincente}, ensure_ascii=False, indent=1))
    else:
        righe.append(f"\nVoti accumulati. Chi raggiunge 75 vince il video.")
    
    righe.append("https://gpoggi.it")
    
    if prova:
        print("\n".join(righe))
        return
    
    api(token, "sendMessage", chat_id=chat, text="\n".join(righe), parse_mode="HTML",
        disable_web_page_preview="true", disable_notification="true")
    print("Report inviato.")

if __name__ == "__main__":
    main()
