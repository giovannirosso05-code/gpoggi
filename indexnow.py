"""Avvisa Bing e gli altri motori IndexNow delle pagine nuove o cambiate (max 10000 per invio).
Uso: python indexnow.py --file=cambiati.txt  (elenco dei file cambiati, uno per riga)
     python indexnow.py --tutte    (tutte le pagine statiche SEO, una tantum)
La chiave è pubblica: il file docs/<chiave>.txt la contiene e ne prova la proprietà."""
import json, sys, urllib.request
from pathlib import Path

HOST = "gpoggi.it"
KEY = "c36e0287aeb3289ba061da8704b2d9b1"
DOCS = Path(__file__).parent / "docs"
PREFISSI = ("classifica-", "calendario-", "pilota-f1-", "pilota-motogp-", "giochi-", "piloti-", "orari-", "pagella-", "pagelle-")


def pagine(modo):
    if modo == "--tutte":
        return sorted(f.name for f in DOCS.glob("*.html") if f.name.startswith(PREFISSI))
    lista = Path(modo.split("=", 1)[1]) if modo.startswith("--file=") else None
    out = lista.read_text().split() if lista and lista.exists() else []
    return sorted(Path(f).name for f in out if f.endswith(".html") and Path(f).parent.name == "docs")


def main():
    elenco = pagine(sys.argv[1] if len(sys.argv) > 1 else "--tutte")
    if not elenco:
        print("IndexNow: nessuna pagina da segnalare")
        return
    urls = [f"https://{HOST}/{f}" for f in elenco][:10000]
    corpo = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"https://{HOST}/{KEY}.txt", "urlList": urls}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=corpo, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"IndexNow: {len(urls)} pagine segnalate (risposta {r.status})")
    except Exception as e:
        print(f"IndexNow: errore {e}")


if __name__ == "__main__":
    main()
