# GP Oggi

Sito statico non ufficiale su Formula 1, MotoGP, Formula 2 e Formula 3, in italiano (HTML/CSS/JS senza framework, dati in JSON statici, aggiornamento automatico con un file di istruzioni per GitHub Actions o GitLab).

Non affiliato a Formula 1, FIA, MotoGP, Dorna o ai team. Nessun logo, immagine o font ufficiale.

## Sezioni
Home con conto alla rovescia F1 e MotoGP, piloti, classifiche, calendario (con file .ics scaricabili), notizie (report di gara automatici e rassegna stampa con link alle fonti), giochi (quiz), MotoGP (MotoGP, Moto2, Moto3, schede pilota, archivio dal 1949), F2 e F3 (classifiche), archivio storico F1 dal 1950 con schede dei piloti.

## Dati e licenze
| Contenuto | Fonte | Note |
|---|---|---|
| F1 stagione in corso | OpenF1 | pensata per uso non commerciale; blocca le richieste durante le sessioni dal vivo (lo script salta il giro) |
| Archivio F1 dal 1950 | Jolpica F1 | CC BY-NC-SA 4.0, uso non commerciale |
| MotoGP: calendario, classifiche, risultati, archivio | servizio pubblico del campionato | non documentato, condizioni d'uso non trovate |
| F2 e F3 | Wikipedia | testo CC BY-SA 4.0 |
| Notizie | feed RSS pubblici (titolo, estratto breve e link alla fonte) | condizioni dei singoli siti da verificare |
| Foto piloti e mappe F1 | Wikimedia Commons | solo licenze libere; autore e licenza mostrati e in `crediti.html` |

Con pubblicità o guadagni serve un accordo scritto con i gestori delle fonti non commerciali.

## Script (cartella principale)
```
python -m pip install -r requirements.txt
python scraper_f1.py          # F1 stagione in corso: docs/data/, foto e mappe
python build_news.py          # rassegna stampa
python build_motogp.py        # MotoGP (calendario, classifiche, schede pilota)
python build_report_moto.py   # report di gara MotoGP dai dati del campionato (e cronaca giro per giro)
python build_cronaca.py       # cronaca giro per giro delle gare F1 (OpenF1: ritiri, safety car, incidenti, ritardi)
python build_pronostici.py    # pronostico F1 e MotoGP (indice da forma, classifica, circuito)
python foto_motogp.py         # foto dei piloti MotoGP/Moto2/Moto3 (Wikimedia); poi foto_motogp_openverse.py per quelli rimasti senza
python foto_circuiti_moto.py  # mappe dei circuiti MotoGP (Wikimedia Commons)
python build_schede.py        # schede carriera: numeri (Jolpica, MotoGP) e biografia breve (Wikipedia in italiano)
python build_formule.py       # classifiche F2 e F3
python build_calendari.py     # file .ics
python build_archivio.py      # archivio F1 dal 1950 (le stagioni già scaricate non si rifanno)
python build_motogp_archivio.py
python telegram_post.py --prova   # messaggio Telegram senza inviarlo
python -m http.server 8000 --directory docs
```
`.github/workflows/update-data.yml` esegue tutto ogni 6 ore (gli archivi solo il lunedì); `.gitlab-ci.yml` fa lo stesso su GitLab Pages. Telegram usa i segreti `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CANALE` (mai nei file).

## Pubblicazione
La cartella `docs` è il sito. Dominio: gpoggi.it (OVHcloud). Canonical, og:url e sitemap puntano a https://gpoggi.it/.
Per usare il dominio nudo su Cloudflare Pages i DNS vanno spostati a Cloudflare; con GitHub Pages bastano i record A e CNAME.

## Idee per i video
Vedi `video/IDEE.md`.

## Bot Telegram a comandi
`worker/bot-telegram.js` (Cloudflare Worker `gpoggi-bot`) riceve i comandi di Gpoggibot e lancia al volo i workflow di GitHub: istruzioni in `worker/LEGGIMI.md`.
