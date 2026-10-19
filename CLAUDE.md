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

- Velocità voce: ogni voce è 3% più lenta di quella scritta nella scaletta (`RALLENTA` in notizia_sub.py, richiesta del gestore). Tra il gancio e "Seguici" nessuna pausa extra (come la frase subito successiva) e "Seguici" detto più lento del resto (+20%).

## Parlato: cosa non si dice mai a voce (richiesta del proprietario, 19 ottobre 2026)
- Mai la frase «è un'opinione/una valutazione basata sui numeri, non una certezza» detta dopo il favorito: chi ascolta non vuole saperlo. Resta solo scritta in didascalia (e in schermata finale se serve).
- Mai citare la fonte a voce («secondo Motorsport.com…»): chi ascolta lo trova brutto. La fonte si scrive in alto sullo schermo (`"fonte_alto": "Motorsport.com"` nella scena di `notizia_sub.py`, sotto la zona sicura y≥230) e in didascalia.

## Comando /gara (Telegram)
- `/gara` (e `/garaf1`, `/garamoto`) fa il video degli orari: tutti gli orari restano fermi a schermo, la voce li legge e dice il favorito (`video/orari_gp.py`, workflow «Orari prossima gara»), poi manda video e didascalia sul Telegram. Il vecchio video con circuito e notizie ora è `/anteprima`. Dopo ogni modifica a `worker/bot-telegram.js` il Worker su Cloudflare va ripubblicato a mano (vedi `worker/LEGGIMI.md`).

## Fatti (regola più importante)
- Mai errori su griglie, risultati, punti. Prima i documenti ufficiali FIA / API MotoGP, poi almeno due fonti.
- Una griglia di partenza si dà solo dopo il documento "Final Starting Grid" della FIA (penalità e partenze dalla pit lane arrivano dopo le qualifiche).
- Niente colpe senza una fonte; le dichiarazioni si attribuiscono e si riscrivono con parole nostre.
- Punti del mondiale ricalcolati da noi vanno dichiarati come tali.

## Rigore geometrico (sito e pagine social): nessun errore ammesso
- Prima di ogni pubblicazione del sito: `python3 tools/controllo_geometria.py` (apre ogni pagina a 360, 390, 768 e 1280 px e segnala scorrimento orizzontale, testi tagliati, immagini rotte, schede della stessa riga con altezze o allineamenti diversi, elementi sovrapposti). Deve dire 0 segnalazioni.
- Ogni elemento ripetuto (schede, podi, card, tabelle) ha la stessa misura e gli stessi allineamenti; niente testo che va a capo in modo diverso tra schede vicine (usare altezze minime).
- I social (Instagram e TikTok @gp.oggi) stanno in alto nella testata e in fondo a ogni pagina.
- Per i social: copertine e video nella zona sicura (testi tra y=230 e y=1650), titoli mai sopra il volto, stessa grafica per la stessa rubrica.

## TikTok: parole e contenuti da evitare (rimozione del 14 ottobre 2026 per «Servizi e beni regolamentati»)
- Mai «pronostico», «pronostici», «scommesse», «quote», «vota il tuo pronostico», premi, soldi, né la schermata del gioco del pronostico (ha il premio) in video, copertine, didascalie e hashtag. Usare «previsione» e le domande ai commenti.
- Non promuovere sui social il gioco «Pronostico del podio» del sito: per i giochi usare «Chi è il pilota?» e gli altri, senza premi.
- Se un video viene rimosso, presentare ricorso (180 giorni) e rifare la versione senza il contenuto sospetto.

## Rassegna della sera
- Mai titoli-domanda senza risposta ("perché X non è stato penalizzato?"): se la risposta esiste (come i freni di Antonelli a Singapore) il video senza risposta non ha senso. `rassegna_giornaliera.py` salta i titoli che finiscono con "?" e le frasi di estratto lasciate a metà. Notizie incrociate F1 / MotoGP; la fonte si scrive, non si dice.

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
- Niente orari di pubblicazione: né nei video né in didascalia (nessun «ogni lunedì alle 13/18»), così se il proprietario si dimentica di postare in orario non ci sono problemi (richiesta del 19 ottobre 2026).

## Pagella: regole del gancio e dell'ordine (ripetute dal proprietario)
- Il gancio non dice i voti e non parte mai dal pilota uomo della giornata (è già in copertina). In F1 si apre con Leclerc ("Un ottimo Leclerc fa felice una Ferrari non troppo sorridente") e subito dopo si parla di Hamilton: le due Ferrari si citano sempre, portano pubblico.
- In MotoGP il gancio è su chi ha preso un voto molto basso (es. "Bagnaia tra i peggiori del weekend"). Per i ritiri: se è una caduta, si dice caduto; se è un problema tecnico, "il voto va diviso tra lui e il team"; se la causa non è verificata non si dice niente sulla causa (mai "la causa non è chiara"). Le cause confermate si scrivono in `docs/data/pagella-note.json` (serie → gara → pilota → "caduta" | "tecnico").
- Le tabelle dei voti (copertina e schermata finale del video) vanno dal migliore a scendere; il video racconta dal voto più basso al più alto, il migliore per ultimo.
- Si dice sempre che i voti sono a scopo divertente e non vogliono offendere nessuno.
- Le chiusure dei voti si alternano ("Voto sette", "Per lui oggi sette e mezzo", "Si prende sei", "Gli diamo otto"): non ripetere sempre "voto".
- Non essere ridondante: niente frasi che ripetono posizioni o griglia già dette, niente avviso "a scopo divertente" a voce (resta scritto in didascalia, sito e schermata finale), niente "in fondo" per il migliore. Nelle tabelle niente numeri di posizione (sembrerebbe la classifica del mondiale) e si parla sempre di "pagella", mai di "classifica".
- Velocità della voce nei video pagella: +31% (5% più lenta di prima, su richiesta del proprietario).

## Foto dei video notizia: solo pertinenti, sempre controllabili
- Ogni scena mostra ciò di cui parla il suo testo: il pilota se il cognome è nella scena (F1: ritratto ESPN), altrimenti una foto ESPN il cui titolo ha parole del titolo della notizia, altrimenti il pilota più nominato nell'articolo. Mai volti a caso (un video su Horner con le foto di Sainz e Albon era sbagliato). Se non c'è nessuna foto pertinente il video non si fa (e arriva l'avviso).
- Prima della copertina e del video, su Telegram arriva un foglio con tutte le foto usate, una per scena, col titolo ESPN o il nome del pilota: si controlla prima di postare.
- Articolo corto o illeggibile: non si rinuncia. Si allunga con l'estratto del feed e con le altre testate che parlano della stessa storia (almeno 2 parole significative del titolo in comune). Solo se, anche così, restano meno di 350 caratteri il video non si fa.
- Nessuna foto ESPN che parli della notizia: si usa la foto dell'articolo stesso (og:image della pagina, credito alla testata) e, per le foto, solo gli articoli di altre testate che condividono almeno 3 parole del titolo; alternata al ritratto del pilota più nominato. Il foglio di controllo su Telegram dice sempre da dove viene ogni foto.
