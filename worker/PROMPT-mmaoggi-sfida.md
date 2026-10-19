# Prompt per il sito di MMA Oggi: «Sfida del giorno» (5 domande)

Incolla tutto il testo qui sotto, dalla riga «Lavora sul sito…» in poi, in una sessione di Claude Code aperta sul repository del SITO di MMA Oggi (non sul bot). Il gioco esiste già su GP Oggi (repository `giovannirosso05-code/gpoggi`, file `docs/js/giochi.js`, `docs/giochi.html`, `docs/css/style.css`): se hai accesso, leggilo e adattalo.

---

Lavora sul sito di MMA Oggi (sito statico su GitHub Pages). Parla con me in italiano, semplice e diretto. Se una cosa è ambigua chiedimi prima. Nessun segreto in chat o nel repository.

## Cosa voglio: la «Sfida del giorno»
Una pagina `giochi.html` (con link nel menu e nel footer) con il gioco «Sfida del giorno»: **5 domande a risposta multipla con 4 opzioni, uguali per tutti, una nuova ogni giorno**, con la cultura generale degli ultimi anni di MMA (tutto in italiano, gratis, senza registrazione, senza account).

### Come funziona (copia il comportamento di GP Oggi)
- **Stesse domande per tutti:** un generatore con seme (PRNG tipo mulberry32 con seme dall'hash FNV-1a della stringa `"mmaoggi-" + data italiana AAAA-MM-GG`, fuso `Europe/Rome`). Mescolamenti e scelte delle domande usano quel generatore, quindi due persone nello stesso giorno vedono le stesse 5 domande e le stesse opzioni nello stesso ordine.
- **Numero della sfida:** «Sfida del giorno #N», con N = giorni dal giorno di lancio + 1 (il giorno di lancio è #1).
- **Struttura di una domanda:** titolo («Chi vinse la cintura dei pesi leggeri UFC nel 2022?»), un riquadro grande con il contesto in evidenza (anno, categoria di peso, nome), 4 pulsanti. Dopo il tocco: la risposta giusta diventa verde, quella sbagliata rossa, la giusta si evidenzia comunque, compare «Avanti →» (alla fine «Vedi il risultato»). Punteggio in alto («Punti: N», «3 di 5»). Credito foto sotto, se ci sono foto.
- **Fine:** punteggio grande («4/5»), le 5 caselle 🟩🟥 con gli esiti, titolo «Quante ne indovini su 5?», la serie di giorni di fila («🔥 3 giorni di fila · record 5»), il testo «Le domande sono uguali per tutti: sfida un amico e confrontate il risultato. Domani una nuova sfida.», pulsante «📲 Sfida un amico» e «Altri giochi».
- **Sfida un amico:** condivide con il menu del telefono (`navigator.share`) o, se non c'è, copia negli appunti questo testo (con il risultato vero): «🥊 MMA Oggi · Sfida del giorno #N\n4/5 🟩🟩🟥🟩🟩\n🔥 3 giorni di fila\nLe domande sono uguali per tutti: riesci a fare meglio?\n👉 https://<dominio>/giochi.html?sfida=1». Aprire `giochi.html?sfida=1` fa partire subito la sfida.
- **Una volta al giorno:** se ho già giocato oggi, si mostra direttamente il risultato di oggi (salvato nel browser con la chiave `sfida-AAAA-MM-GG`: punti ed esiti).
- **Serie di giorni di fila (sullo stesso dispositivo):** in `localStorage` chiave `sfida-serie` = `{ultimo, serie, migliore}`. Si aggiorna solo quando finisco la sfida: se `ultimo` è ieri la serie sale di 1, se è oggi non cambia, altrimenti riparte da 1. Tutti gli accessi a `localStorage` dentro try/catch (può essere bloccato o vuoto).
- **Dati:** niente domande scritte a mano a caso: le risposte vengono da file di dati del sito o da dati verificati (vedi sotto). Se non ci sono abbastanza dati per fare almeno 3 domande, messaggio «Non ci sono abbastanza dati per la sfida di oggi: riprova più tardi.»
- Nessun premio, nessun soldo, nessun pronostico, nessuna scommessa, nessuna quota: né nella pagina né nei testi di condivisione (TikTok ci ha rimosso un video per «Servizi e beni regolamentati»).

### Le 5 domande: mix (come in GP Oggi: cultura generale degli ultimi 10 anni)
Piano fisso di tipi, ruotando ogni giorno con il seme:
1. **Chi vinse un incontro importante / un titolo** negli ultimi 10 anni (es. «Chi vinse il titolo dei pesi medi UFC nel 2019?», «Chi ha battuto X all'evento UFC N?»).
2. **Chi è il campione attuale** di una categoria di peso (solo se il dato nel sito è aggiornato; altrimenti salta).
3. **Di quale paese è il lottatore X?** o **in quale categoria combatte?**
4. **Chi è questo lottatore?** (foto, se esiste una foto con licenza libera e il credito) oppure **chi ha fatto questa cosa?** (record, soprannome: «Chi è chiamato "The Notorious"?»).
5. Una domanda a rotazione tra: **soprannome**, **gesto tecnico/sottomissione famosa**, **quale organizzazione** (UFC, PFL, Oktagon, ONE…).
Le tre opzioni sbagliate arrivano dallo stesso gruppo (stessa categoria di peso, stesso periodo, stessa organizzazione), mai assurde. Ogni domanda ha UNA risposta giusta senza ambiguità: se due lottatori hanno lo stesso cognome vale solo il nome completo. Mai fatti non verificati: se un dato non è certo non si usa. Almeno la metà delle domande deve riguardare anche lottatori e organizzazioni che il sito già segue.

### Grafica
Stessa grafica del sito di MMA Oggi (colori, font, tema chiaro/scuro). Il rosso/arancione dei pulsanti principali acceso, non spento. Layout che funziona a 360 px di larghezza, senza scorrimento orizzontale, schede con la stessa altezza, testi mai tagliati. Prima di pubblicare controlla tutte le pagine nuove a 360, 390, 768 e 1280 px (se c'è `tools/controllo_geometria.py` usalo: deve dire 0 segnalazioni; se manca, fai uno screenshot con Playwright e guardalo davvero).

### SEO
Titolo della pagina «Giochi di MMA online gratis: quiz e sfida del giorno | MMA Oggi», descrizione di una frase con le parole «giochi», «MMA», «quiz», «gratis», canonical, og:title/description, link nel footer e nella sitemap, e una voce nel menu «Giochi».

## Come lavorare
- Prima leggi com'è fatto il sito (struttura, dati disponibili, come si caricano i dati), dimmi in poche righe cosa hai capito e quali dati userai per le domande, poi procedi. Chiedimi solo le scelte che dipendono da me (nome del gioco, quali organizzazioni includere).
- Prova tutto in locale: apri la pagina con Playwright, gioca le 5 domande, controlla che con la stessa data escano le stesse domande, che la serie di giorni funzioni (simulando ieri/oggi) e che non ci siano errori in console. Non dichiarare «fatto» ciò che non hai visto funzionare: dimmi cosa hai provato e cosa no.
- Quando hai finito, pubblica e dammi il link alla pagina e il link GitHub dei file cambiati.
