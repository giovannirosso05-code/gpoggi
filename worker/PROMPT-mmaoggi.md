# Prompt per la sessione di MMA Oggi (repository gr-build/mmaoggi-radar)

Incolla tutto il testo qui sotto, dalla riga «Lavora sul repository…» fino alla fine, in una sessione di Claude Code aperta su `gr-build/mmaoggi-radar`.

---

Lavora sul repository gr-build/mmaoggi-radar (bot Telegram di MMA Oggi: Cloudflare Worker `worker/bot-telegram.js` + workflow GitHub Actions + script Python). Parla con me in italiano, in modo semplice e diretto, senza introduzioni inutili. Se una richiesta è ambigua, chiedimi prima di fare: interpretazioni sbagliate mi fanno perdere tempo.

## Cosa voglio (stesso sistema che abbiamo fatto per GP Oggi, adattato all'MMA)

Oggi `/video` sceglie le notizie da solo e `/notizie` manda il riepilogo. Voglio poter **scegliere io le notizie** su cui fare i video e la rassegna stampa, in automatico oppure a scelta. In particolare:

### 1. Elenco delle notizie con un comando per ognuna (`/radar`)
- `/radar` manda su Telegram le notizie delle ultime 24 ore (massimo 20, messaggi da 8 notizie per non farli tagliare), ognuna con: numero, `💬` davanti se contiene dichiarazioni dei lottatori (virgolette o verbi come «dice, ammette, rivela, spiega, attacca, risponde, sfida»), il titolo, la fonte, e sotto un comando toccabile `▶ /n_<codice>`.
- Il `<codice>` è l'inizio dello SHA-256 dell'indirizzo dell'articolo (primi 5 byte in esadecimale, 10 caratteri). Toccare `/n_<codice>` lancia **subito** il video proprio su quella notizia. NIENTE pulsanti inline con numeri: nel nostro bot non rispondevano (Telegram non li mandava al Worker), i comandi di testo funzionano sempre.
- Le notizie con `💬` stanno in cima alla lista (poi per data, la più recente prima). Mi servono molte più citazioni, interviste e frasi dei lottatori.
- `/video parola` (o `/video link`): se la parola trova più notizie, parte subito la prima (la più recente), senza chiedermi di scegliere. Il comando `/n_<codice>` serve per scegliere quella precisa.
- Il Worker deve leggere le notizie da un file JSON pubblico aggiornato dal radar (per esempio `radar/notizie.json` pubblicato su GitHub Pages o come file nel repo letto via raw.githubusercontent.com). Il Worker NON può leggere la cache di Actions. Ogni notizia: `titolo, fonte, url, pubblicato (ISO UTC), estratto, citazione (true/false)`. Se il radar già calcola questi dati (voto, gruppi), riusali; aggiungi solo il file.

### 2. Rassegna stampa: automatica o scelta da me (`/rassegna`)
- `/rassegna` manda subito la rassegna con scelta automatica.
- `/rassegna parola1 parola2 parola3 parola4` (da 2 a 6 parole, oppure codici `/n_…`): usa quelle notizie, e **la prima è il gancio** (apre il video con il titolo grande e la voce che dice il titolo; poi una frase in più dall'estratto; poi «Questa e altre N notizie nella rassegna stampa di MMA Oggi»; poi le altre).
- Per il workflow `rassegna-serale.yml` aggiungi gli input `scelte` (indirizzi separati da spazio, vuoto = automatica) e `gancio` (titolo grande, vuoto = ricavato dal titolo). Nel passo di lancio passali con variabili d'ambiente (mai interpolati nel testo dello script) e un array bash.
- File `rassegna_forzata.json` (per un giorno preciso): `{"giorno": "AAAA-MM-GG", "gancio_url": "...", "gancio_titolo": "titolo grande", "gancio_articolo_titolo": "titolo originale", "gancio_fonte": "..."}`. Se per oggi esiste, quell'articolo apre la rassegna automatica (gli altri si scelgono come sempre, escludendo le storie simili). Il Worker non lo tocca: lo scrivo io quando mi serve.
- Una rassegna chiesta a mano (`--forza` o `--scelte`) **non** segna «fatta oggi» e non «consuma» le notizie: quella automatica delle 21:30 parte comunque.
- Regole di selezione della rassegna automatica:
  - solo notizie di OGGI (dalla mezzanotte italiana); se ne restano meno di n+2 si allarga a 30 ore;
  - mai notizie già usate in una rassegna precedente (salva gli indirizzi usati, ultimi 80) né già raccontate in un video né la stessa storia di un'altra testata (confronto delle parole del titolo);
  - niente titoli-domanda senza risposta (che finiscono con «?»);
  - le notizie con dichiarazioni dei lottatori hanno punteggio in più;
  - alternare, se ha senso, UFC e altre organizzazioni/fonti come già fa il radar.
- Alla fine manda **due copertine** (due versioni, con foto diverse, per scegliere), poi il video.

### 3. Copertina su richiesta (`/copertina`)
- Ogni video notizia arriva su Telegram **con la sua copertina inviata prima** (foto grande a tutto schermo + titolo su righe corte in riquadri colorati; zona sicura TikTok: testi tra y=230 e y=1650 su 1080x1920).
- `/copertina` crea una nuova copertina per l'ultimo video; `/copertina parola` per la notizia con quella parola. A ogni richiesta una foto diversa (contatore nello stato: 1 di N, 2 di N…). La didascalia dice quale opzione è: «Copertina 2 di 6: foto di …. Non ti piace? Riscrivi /copertina per la prossima.»
- Le opzioni devono essere solo **pertinenti**: foto del lottatore citato nel titolo, altre foto dello stesso lottatore, foto il cui titolo di fonte parla della notizia. Se non ce n'è nessuna: messaggio «non ho una foto pertinente», non una foto a caso.
- Titolo della copertina automatico: prima frase del titolo (senza prefisso, virgolette e «?»), massimo 8 parole / 44 caratteri / 4 righe da 14 caratteri al massimo, mai chiusa da una parolina (in, di, il, la, che, è…).

## Regole che ci hanno fatto sbagliare (da rispettare)

1. **Foto sempre pertinenti scena per scena.** Ogni scena mostra ciò di cui parla il suo testo: il lottatore se il cognome è nel testo della scena, altrimenti una foto il cui titolo parla della notizia, altrimenti il lottatore più nominato nell'articolo. MAI volti a caso: un video su un manager con le foto di sei lottatori diversi era sbagliato. Se non c'è nessuna foto pertinente il video non si fa e mi arriva un avviso.
2. **Stesso cognome = ambiguità.** Se due lottatori hanno lo stesso cognome (es. due Marquez nella MotoGP, in MMA succede spesso: fratelli, omonimi) vale solo il nome completo; il cognome da solo non sceglie nessuno dei due.
3. **Foglio di controllo prima del video.** Prima della copertina e del video mandami su Telegram un'immagine con tutte le foto usate, una per scena, con sotto il titolo della fonte o il nome del lottatore e la frase della scena, così le controllo prima di postare.
4. **Non mandarmi niente senza che lo chieda.** Non lanciare workflow che inviano su Telegram per «provare», se non ti ho chiesto di inviare. Prova in locale (`--prova`, anteprime, screenshot) e dimmi cosa vedi. Se devo vedere un video vero su Telegram, chiedimelo prima.
5. **Fatti.** Mai errori su risultati, record, categorie di peso, date. Se non sei sicuro lo dici, non lo scrivi. Niente colpe o accuse senza fonte; le dichiarazioni si attribuiscono («secondo …») con parole nostre, non si copiano gli articoli (nessuna sequenza di 6 parole uguale alla fonte). La fonte si scrive in sovraimpressione, non si dice a voce.
6. **TikTok ci ha rimosso un video per «Servizi e beni regolamentati»** (parlava di pronostici con premio). In video, copertine e didascalie evita: pronostico/pronostici, scommesse, quote, premi, soldi. Usa «previsione» e domande ai commenti.
7. **Didascalie**: in un riquadro di codice, `#mmaoggi` per primo, massimo 5 hashtag, riga del sito prima degli hashtag, una domanda in chiusura («Dimmi la tua nei commenti 👇»). Nessuna parola su premi o soldi.
8. **I cron di GitHub Actions saltano o ritardano di ore.** Per la rassegna serale metti più tentativi (21:23, 21:38, 21:53, 22:23, 22:38, 22:53, 23:23, 23:53 italiane, in UTC per ora legale e solare) e finestra fino alle 23:59, con il segno «già fatta oggi» che evita i doppioni (ma non segnarlo per le prove a mano).
9. **Voce e video**: restano come sono oggi (Azure con le riserve). Non cambiare voce, velocità o grafica che già funzionano.

## Come lavorare

- Prima leggi `radar.py`, `video_notizie.py`, `rassegna_serale.py`, `rassegna_curata.py`, `worker/bot-telegram.js`, `worker/LEGGIMI.md` e i workflow `video-notizie.yml`, `rassegna-serale.yml`, `rassegna-curata.yml`. Dimmi in poche righe cosa hai capito e cosa cambieresti, poi procedi (non chiedermi conferma per i dettagli tecnici, solo per le scelte che dipendono da me).
- Se hai accesso al repository `giovannirosso05-code/gpoggi` guardalo come riferimento già funzionante: `worker/bot-telegram.js` (comandi `/radar`, `/n_<codice>`, `/rassegna`, `/copertina`, `codice()`, `cerca()`), `video/notizie_giorno.py` (`pilota_citato`, `foto_pertinenti`, `foglio_foto`, `opzioni_copertina`, `copertina_su_richiesta`, `titolo_copertina`) e `video/rassegna_giornaliera.py` (`scegli_rassegna`, `articoli_da_url`, `leggi_forzata`, gancio). Adatta, non copiare alla cieca: qui i nomi sono lottatori, le fonti sono quelle del radar, il testo dei video lo scrive Gemini come oggi.
- Controlla ogni cosa che puoi provare in locale (sintassi del Worker con `node --check`, YAML dei workflow, selezione delle notizie con dati veri, copertine in PNG che guardi davvero). Non dichiarare «fatto» ciò che non hai visto funzionare: dimmi cosa hai provato e cosa no.
- Nessun segreto in chat o nel repository (`TELEGRAM_TOKEN`, `GITHUB_TOKEN`, `WEBHOOK_SECRET`, `GEMINI_API_KEY`, chiavi Azure): si inseriscono solo nelle impostazioni di Cloudflare o nei secret di GitHub.
- Quando hai finito: aggiorna `worker/LEGGIMI.md` (elenco comandi) e la riga di versione in cima al Worker (`VERSIONE`, visibile aprendo l'indirizzo del Worker con il browser) e dammi **il link GitHub al file `worker/bot-telegram.js`** (pagina `blob`, così premo «Copy raw file»): copiare da chat non funziona bene. Poi dimmi i passi per aggiornare il Worker di MMA Oggi su Cloudflare (Edit code → incolla → Deploy → controlla la versione): attenzione, il Worker di MMA Oggi è un altro da quello di GP Oggi, non incollare mai il codice nel Worker sbagliato.
