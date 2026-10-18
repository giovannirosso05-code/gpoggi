"""Avviso su Telegram quando un pilota importante scrive o dice qualcosa sui social (riportato dalle testate).
Legge docs/data/rassegna.json (già aggiornato da build_news.py), manda un messaggio per ogni notizia nuova
di tipo "social" che nomina un pilota della lista, con il comando /n_<codice> per fare subito il video.
Stato: avvisi_social.json (indirizzi già avvisati). Alla prima esecuzione segna tutto come visto senza inviare."""
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

QUI = Path(__file__).parent
RASSEGNA = QUI / "docs" / "data" / "rassegna.json"
STATO = QUI / "avvisi_social.json"
ORE = 4  # solo notizie pubblicate nelle ultime ore
PILOTI = ["Leclerc", "Hamilton", "Antonelli", "Verstappen", "Norris", "Piastri", "Russell", "Alonso",
          "Marc Marquez", "Alex Marquez", "Bagnaia", "Bezzecchi", "Acosta", "Jorge Martin", "Di Giannantonio",
          "Morbidelli", "Quartararo", "Valentino Rossi", "Rossi", "Binder", "Mir"]
RE_PILOTI = re.compile(r"\b(" + "|".join(PILOTI) + r")\b", re.I)


def codice(url):
    return hashlib.sha256(url.encode()).hexdigest()[:10]


def main():
    art = json.loads(RASSEGNA.read_text(encoding="utf-8")).get("articoli", [])
    primo = not STATO.exists()
    visti = set(json.loads(STATO.read_text())) if not primo else set()
    limite = datetime.now(timezone.utc) - timedelta(hours=ORE)
    nuovi = []
    for a in art:
        if a["url"] in visti:
            continue
        visti.add(a["url"])
        if primo or a.get("tipo") != "social":
            continue
        try:
            if datetime.fromisoformat(a["pubblicato"]) < limite:
                continue
        except Exception:
            continue
        m = RE_PILOTI.search(a["titolo"] + " " + a.get("estratto", ""))
        if m:
            nuovi.append((a, m.group(1)))
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CANALE", "559225883")
    for a, nome in nuovi:
        testo = (f"📱 {nome} sui social\n\n{a['titolo']}\n{a['fonte']}\n\n{a.get('estratto', '')}\n\n"
                 f"Fai il video: /n_{codice(a['url'])}\nControlla prima la fonte: {a['url']}")
        if token:
            r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                              data={"chat_id": chat, "text": testo, "disable_web_page_preview": "true"}, timeout=30)
            print("Avviso", "inviato" if r.ok else f"errore {r.status_code}", "-", a["titolo"])
        else:
            print("[prova, nessun token]\n" + testo)
    STATO.write_text(json.dumps(sorted(visti)[-600:]), encoding="utf-8")
    print(f"Avvisi social: {len(nuovi)} nuovi ({'prima esecuzione, solo registrazione' if primo else 'ok'})")


if __name__ == "__main__":
    main()
