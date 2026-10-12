# GP Oggi: regole fisse per video, copertine e didascalie

Decise con il proprietario del canale (TikTok @gp.oggi, sito gpoggi.it). Valgono per ogni video fatto a mano o in sessione.

## Didascalie
- Sempre in un riquadro di codice, con le righe a capo, pronte da incollare.
- Sempre la riga del sito prima degli hashtag: `🔗 gpoggi.it` (stessa riga delle didascalie automatiche; il link non è cliccabile, quello cliccabile sta nella bio). Vedi anche `video/didascalie.md`.
- Massimo 5 hashtag, `#gpoggi` per primo.
- Una frase forte in apertura, una domanda in chiusura, hashtag alla fine.
- Nessuna parola su premi o soldi.

## Copertine
- Volto grande a tutto schermo con titolo su due righe, sfondo colorato solo dietro le parole (`video/copertina.py`; rosso F1, blu MotoGP).
- Zona sicura: l'editor di TikTok taglia circa 200 px sopra e 190 sotto (1080x1920). Testi tra y=230 e y=1650.
- Se c'è un vincitore, foto sorridente se esiste una foto libera giusta. Mai foto con il cappellino di un altro podio (es. "2ND" di Zandvoort 2024).
- Mai modificare una foto per farle dire una cosa falsa.

## Video (`video/notizia_sub.py`)
- 25-35 s, gancio nel primo secondo (risultato forte, nome di un italiano se pertinente), schermo diviso (foto in pista sopra, volto sotto), pause corte.
- Pronunce: Hadjar = Adgiàr, Martin = Martìn (`PRONUNCIA` in notizia_sub.py).
- Chiudere con la riga sul canale e una domanda.

## Fatti (regola più importante)
- Mai errori su griglie, risultati, punti. Prima i documenti ufficiali FIA / API MotoGP, poi almeno due fonti.
- Una griglia di partenza si dà solo dopo il documento "Final Starting Grid" della FIA (penalità e partenze dalla pit lane arrivano dopo le qualifiche).
- Niente colpe senza una fonte; le dichiarazioni si attribuiscono e si riscrivono con parole nostre.
- Punti del mondiale ricalcolati da noi vanno dichiarati come tali.

## Foto
- Solo foto libere (Wikimedia Commons CC BY / CC BY-SA, o altre CC verificate). Credito in ogni scena. Niente "NC", niente foto di agenzia.

## Segreti
- Mai chiedere né scrivere token in chat o nel repository.

## Consegna su Telegram
- Ogni video, copertina e didascalia fatti a mano vanno anche in `invio/` (es. `invio/nome.mp4`, `invio/nome.png`, `invio/nome.txt` con la didascalia): il workflow "Invio su Telegram" parte al push e li manda sul Telegram del proprietario, come fa il bot di MMA Oggi. I già inviati sono in `video/inviati.json`.
- Anche in chat si mandano con SendUserFile, ma la consegna su Telegram è quella che conta.
- I workflow dei video automatici avvisano su Telegram se falliscono. La chat è `559225883` (non è un segreto); il token è nei secret del repository (`TELEGRAM_BOT_TOKEN` o `TELEGRAM_TOKEN`), mai in chiaro.
