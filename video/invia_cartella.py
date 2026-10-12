"""Manda su Telegram i file messi nella cartella invio/ (video, copertine) con la didascalia da copiare.

Come funziona: si aggiungono al repository i file in invio/ (video .mp4, copertina .png/.jpg) e, per ognuno,
un file di testo con lo stesso nome e la didascalia (es. invio/hamilton.mp4 + invio/hamilton.txt). Il workflow
"Invio su Telegram" parte da solo al push, manda i file nuovi e ricorda in video/inviati.json quelli già mandati,
così non si ripete mai un invio. Stessi segreti degli altri workflow: TELEGRAM_BOT_TOKEN (o TELEGRAM_TOKEN)
e, se c'è, TELEGRAM_CANALE; altrimenti la tua chat privata.
Prova senza inviare: DRY=1 python video/invia_cartella.py
"""
import html
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CARTELLA = ROOT / "invio"
REGISTRO = ROOT / "video" / "inviati.json"
CHAT_BASE = "559225883"
VIDEO = (".mp4", ".mov", ".m4v")
FOTO = (".png", ".jpg", ".jpeg")


def tok_chat():
    tok = (os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN") or "").strip()
    chat = (os.environ.get("TELEGRAM_CANALE") or os.environ.get("TELEGRAM_CHAT_ID") or CHAT_BASE).strip()
    return tok, chat


def manda_file(tok, chat, percorso, didascalia=""):
    video = percorso.suffix.lower() in VIDEO
    metodo, campo = ("sendVideo", "video") if video else ("sendPhoto", "photo")
    extra = {"width": "1080", "height": "1920", "supports_streaming": "true"} if video else {}
    with open(percorso, "rb") as f:
        r = requests.post(f"https://api.telegram.org/bot{tok}/{metodo}", data={"chat_id": chat, "caption": didascalia[:1000], **extra}, files={campo: f}, timeout=300)
    if not r.ok:
        print(f"  Telegram ha rifiutato {percorso.name}: {r.status_code} {r.text[:200]}")
    return r.ok


def manda_testo(tok, chat, testo):
    r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", json={
        "chat_id": chat, "parse_mode": "HTML", "disable_web_page_preview": True,
        "text": ("✍️ <b>Didascalia</b> (tocca il testo per copiarlo)\n<pre>" + html.escape(testo) + "</pre>")[:4000]}, timeout=60)
    if not r.ok:
        print(f"  Telegram ha rifiutato la didascalia: {r.status_code} {r.text[:200]}")
    return r.ok


def main():
    dry = bool(os.environ.get("DRY"))
    tok, chat = tok_chat()
    if not tok and not dry:
        print("Token Telegram mancante (secret TELEGRAM_BOT_TOKEN o TELEGRAM_TOKEN): niente inviato.")
        sys.exit(1)
    fatti = json.loads(REGISTRO.read_text()) if REGISTRO.exists() else []
    nuovi = sorted((p for p in CARTELLA.glob("*") if p.suffix.lower() in VIDEO + FOTO and p.name not in fatti),
                   key=lambda p: (p.suffix.lower() not in VIDEO, p.name))   # prima i video, poi le copertine
    if not nuovi:
        print("Niente di nuovo da inviare.")
        return
    errori = 0
    testi_mandati = set()
    for p in nuovi:
        txt = p.with_suffix(".txt")
        didascalia = txt.read_text(encoding="utf-8").strip() if txt.exists() else ""
        print(("[prova] " if dry else "") + f"invio {p.name} ({p.stat().st_size // 1024} KB), didascalia: {'sì' if didascalia else 'no'}")
        if dry:
            continue
        ok = manda_file(tok, chat, p, didascalia if p.suffix.lower() in VIDEO else "")
        if ok and didascalia and p.suffix.lower() in VIDEO and txt.name not in testi_mandati:
            ok = manda_testo(tok, chat, didascalia) and ok
            testi_mandati.add(txt.name)
        if ok:
            fatti.append(p.name)
            REGISTRO.write_text(json.dumps(fatti, ensure_ascii=False, indent=1))
        else:
            errori += 1
    if errori:
        sys.exit(1)


if __name__ == "__main__":
    main()
