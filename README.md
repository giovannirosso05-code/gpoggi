# GP Oggi

Sito statico non ufficiale sulla Formula 1: piloti, classifiche, calendario e risultati per sessione. (HTML/CSS/JS vanilla, dati in JSON statici, aggiornamento via GitHub Actions).

Non affiliato a Formula 1, FIA o ai team. Nessun logo, immagine o font ufficiale.

## Dati

Fonte: [OpenF1](https://openf1.org) (API pubblica, dati di terzi non ufficiali).

```
python -m pip install -r requirements.txt
python scraper_f1.py [anno]     # scrive docs/data/ (la prima run ~2 min, poi usa cache/)
python -m http.server 8000 --directory docs
```

`scraper_f1.py` produce `roster.json`, `standings.json`, `events.json`, `meta.json`, `gare/<id>.json` e `piloti/<numero>.json`.

Foto dei piloti e mappe dei circuiti: `foto_wiki.py` le cerca su Wikipedia/Wikimedia Commons, accetta solo licenze libere (CC BY, CC BY-SA, CC0, OGL, pubblico dominio) e salva una copia in `docs/img/foto/`. Autore e licenza di ogni immagine sono mostrati sotto la foto e nella pagina `crediti.html` (obbligatorio per le licenze CC). Il logo è disegnato da zero: sorgente in `docs/img/logo-sorgente.svg`.
Se un dato manca nella fonte, il sito mostra «n.d.». Il workflow `.github/workflows/update-data.yml` rilancia lo scraper ogni 6 ore e committa `docs/data/`.

## Pubblicazione

GitHub Pages: Settings → Pages → branch `main`, cartella `/docs`. Nessun dominio personalizzato per ora (aggiungere `docs/CNAME` e i meta canonical/og:url quando c'è).
