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
- Pronunce: Russell = Rassel, Leclerc = Leclèr, Lawson = Lòson, Hadjar = Adgiàr, Martin = Martìn (`PRONUNCIA` in notizia_sub.py).
- Subito dopo il gancio (non solo alla fine: la fine non la ascolta nessuno) c'è "Seguici per altri contenuti come questo" (aggiunto da notizia_sub.py; "segui": false lo toglie).
- Chiudere con la riga sul canale e una domanda, seguita da "Dimmi la tua nei commenti" (detta dalla voce e scritta nella schermata finale). Anche in didascalia l'ultima riga prima del sito è la domanda + "Dimmi la tua nei commenti 👇".

- Velocità voce: ogni voce è 1,5% più lenta di quella scritta nella scaletta (`RALLENTA` in notizia_sub.py, richiesta del gestore). Pausa di circa 0,6 secondi tra il gancio e "Seguici".

## Fatti (regola più importante)
- Mai errori su griglie, risultati, punti. Prima i documenti ufficiali FIA / API MotoGP, poi almeno due fonti.
- Una griglia di partenza si dà solo dopo il documento "Final Starting Grid" della FIA (penalità e partenze dalla pit lane arrivano dopo le qualifiche).
- Niente colpe senza una fonte; le dichiarazioni si attribuiscono e si riscrivono con parole nostre.
- Punti del mondiale ricalcolati da noi vanno dichiarati come tali.

## Foto
- Solo foto libere (Wikimedia Commons CC BY / CC BY-SA, o altre CC verificate). Credito in ogni scena. Niente "NC", niente foto di agenzia.

## Foto da ESPN (scelta di rischio del gestore)
- Per mostrare macchine, circuiti e momenti di gara si possono usare foto di ESPN (il gestore lo ha deciso, 13 ottobre 2026). Nella scena: `"foto_url": "https://a.espncdn.com/photo/…_1296x729_16-9.jpg"` (si trovano con `site.api.espn.com/apis/site/v2/sports/racing/f1/news`): `notizia_sub.py` le scarica al momento in `video/_cache/` (mai nel repository né nel sito) e scrive "Foto: ESPN". Alternare volti, macchine e circuiti, non solo piloti.

## Segreti
- Mai chiedere né scrivere token in chat o nel repository.

## Consegna su Telegram
- Ogni video, copertina e didascalia fatti a mano vanno anche in `invio/` (es. `invio/nome.mp4`, `invio/nome.png`, `invio/nome.txt` con la didascalia): il workflow "Invio su Telegram" parte al push e li manda sul Telegram del proprietario, come fa il bot di MMA Oggi. I già inviati sono in `video/inviati.json`.
- Anche in chat si mandano con SendUserFile, ma la consegna su Telegram è quella che conta.
- I workflow dei video automatici avvisano su Telegram se falliscono. La chat è `559225883` (non è un segreto); il token è nei secret del repository (`TELEGRAM_BOT_TOKEN` o `TELEGRAM_TOKEN`), mai in chiaro.

## Video fatti a mano: generarli su GitHub
- La voce (edge-tts) dalla sandbox dà errore 403: i video a mano si generano su GitHub. Si mettono scaletta (`video/spec/nome.json`), copertina (`nome.png`) e didascalia (`nome.txt`) in `video/spec/`: il workflow "Video da spec" crea il video, lo copia in `invio/` con copertina e didascalia e li manda sul Telegram.
- Scena con tabella: `classifica.righe` accetta anche `voto` (al posto dei punti) e `nota`; `sub_top` per scena sposta i sottotitoli.

## Pagella (copertina)
- Sulla copertina il migliore è nel sigillo col voto grande; sotto, i voti in ordine decrescente: il secondo subito dopo il primo, poi gli altri a scendere (mai in ordine crescente). Nel video invece Verstappen/il migliore è l'ultimo.
- Se edge-tts dà 403 (succede anche su GitHub), `notizia_sub.py` passa da solo alla voce di riserva Piper (maschile, tempi delle parole stimati).

## Pagella automatica del lunedì
- `video/pagella_auto.py` costruisce da solo scaletta, copertina e didascalia dai voti (`docs/data/pagella.json`). Il workflow "Video da spec" parte ogni lunedì alle 09:07 UTC (11:07 italiane in estate): i video sono pronti per essere postati alle 13 (MotoGP) e alle 18 (F1), aggiorna i voti, prepara F1 e MotoGP dell'ultimo weekend e li manda sul Telegram. I weekend già fatti sono in `video/pagella_fatte.json`.
- Il gancio non parte mai dal migliore: parte da chi ha un voto molto basso o una correzione pesante in negativo (il più famoso), poi si va dai voti bassi ai più alti, il migliore per ultimo. I ritiri si commentano come ritiro (mai la causa, se non c'è una fonte).
- Le correzioni dichiarate si scrivono in `docs/data/pagella-correzioni.json`.
- Voce: se nei segreti del repository ci sono `AZURE_SPEECH_KEY` e `AZURE_SPEECH_REGION` si usa la voce ufficiale Azure (la stessa Diego di edge-tts, con i tempi veri); altrimenti edge-tts, poi le riserve Piper e Kokoro.
- Nei video si dice: "Ogni lunedì alle 13 la pagella della MotoGP, tornate sul profilo alle 18 per quella della F1" (e viceversa nel video F1); lo stesso orario è in didascalia.

## Pagella: regole del gancio e dell'ordine (ripetute dal proprietario)
- Il gancio non dice i voti e non parte mai dal pilota uomo della giornata (è già in copertina). In F1 si apre con Leclerc ("Un ottimo Leclerc fa felice una Ferrari non troppo sorridente") e subito dopo si parla di Hamilton: le due Ferrari si citano sempre, portano pubblico.
- In MotoGP il gancio è su chi ha preso un voto molto basso (es. "Bagnaia tra i peggiori del weekend"). Per i ritiri: se è una caduta, si dice caduto; se è un problema tecnico, "il voto va diviso tra lui e il team"; se la causa non è verificata non si dice niente sulla causa (mai "la causa non è chiara"). Le cause confermate si scrivono in `docs/data/pagella-note.json` (serie → gara → pilota → "caduta" | "tecnico").
- Le tabelle dei voti (copertina e schermata finale del video) vanno dal migliore a scendere; il video racconta dal voto più basso al più alto, il migliore per ultimo.
- Si dice sempre che i voti sono a scopo divertente e non vogliono offendere nessuno.
- Le chiusure dei voti si alternano ("Voto sette", "Per lui oggi sette e mezzo", "Si prende sei", "Gli diamo otto"): non ripetere sempre "voto".
- Non essere ridondante: niente frasi che ripetono posizioni o griglia già dette, niente avviso "a scopo divertente" a voce (resta scritto in didascalia, sito e schermata finale), niente "in fondo" per il migliore. Nelle tabelle niente numeri di posizione (sembrerebbe la classifica del mondiale) e si parla sempre di "pagella", mai di "classifica".
- Velocità della voce nei video pagella: +31% (5% più lenta di prima, su richiesta del proprietario).
