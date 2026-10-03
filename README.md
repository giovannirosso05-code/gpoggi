# F1 Oggi

Sito statico non ufficiale sulla Formula 1: piloti, classifiche, calendario e risultati per sessione. Stessa impronta di MMA Oggi (HTML/CSS/JS vanilla, dati in JSON statici, aggiornamento via GitHub Actions).

Non affiliato a Formula 1, FIA o ai team. Nessun logo, immagine o font ufficiale.

## Dati

Fonte: [OpenF1](https://openf1.org) (API pubblica, dati di terzi non ufficiali).

```
python -m pip install -r requirements.txt
python scraper_f1.py [anno]     # scrive docs/data/ (la prima run ~2 min, poi usa cache/)
python -m http.server 8000 --directory docs
```

`scraper_f1.py` produce `roster.json`, `standings.json`, `events.json`, `meta.json` e `gare/<id>.json`.
Se un dato manca nella fonte, il sito mostra «n.d.». Il workflow `.github/workflows/update-data.yml` rilancia lo scraper ogni 6 ore e committa `docs/data/`.

## Pubblicazione

GitHub Pages: Settings → Pages → branch `main`, cartella `/docs`. Nessun dominio personalizzato per ora (aggiungere `docs/CNAME` e i meta canonical/og:url quando c'è).
