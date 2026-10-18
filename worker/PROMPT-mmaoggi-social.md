# Prompt per la sessione di MMA Oggi (repository gr-build/mmaoggi-radar): avvisi sulle dichiarazioni social e comando /social

Incolla tutto il testo qui sotto, dalla riga «Lavora sul repository…» fino alla fine, in una sessione di Claude Code aperta su `gr-build/mmaoggi-radar`.

---

Lavora sul repository gr-build/mmaoggi-radar (bot Telegram di MMA Oggi: Cloudflare Worker `worker/bot-telegram.js` + workflow GitHub Actions + script Python). Parla con me in italiano, in modo semplice e diretto, senza introduzioni inutili. Se una richiesta è ambigua, chiedimi prima di fare.

## Cosa voglio (stesso sistema già fatto per GP Oggi, adattato all'MMA)

Le dichiarazioni dei lottatori sui social e le interviste sono i contenuti che fanno più visualizzazioni, e non voglio perdermele. Instagram, X e TikTok NON si possono leggere in modo affidabile (API chiuse o a pagamento, scraping che si blocca): non usare scraping dei social. Si lavora così:

### 1. Il radar riconosce le notizie che riportano un post social
- Nel radar (`radar.py` o dove si leggono i feed) ogni notizia ha un campo `tipo`: `social` (post, storie, messaggi sui social), `intervista` (interviste, conferenze stampa, podcast, ai microfoni), `dichiarazione` (virgolette o verbi del «dire» nel titolo), altrimenti vuoto. `citazione` è vero se `tipo` non è vuoto.
- Il tipo `social` si riconosce da titolo ed estratto con parole come: «sui social, su Instagram, su X, su TikTok, su Twitter, su Facebook, nelle storie, stories, reel, post, nuovo post, tweet, ha postato, ha pubblicato (un/una/su), ha condiviso, social network, sui social media» (in italiano e in inglese, perché le fonti MMA sono spesso inglesi: «took to Instagram», «on social media», «posted», «tweeted», «responded on X», «called out», «shared»).
- In `/radar` le notizie `social` stanno in cima con 📱, poi le interviste con 🎤, poi le dichiarazioni con 💬, poi le altre per data. Se il file pubblico delle notizie (`radar/notizie.json` o simile) non ha il campo `tipo`, aggiungilo.
- Aggiungi altre fonti ricche di dichiarazioni e social se mancano (siti MMA di news in inglese e italiano già usati dal radar o equivalenti con feed RSS verificati: controlla che il feed risponda prima di metterlo).

### 2. Avvisi automatici su Telegram per i lottatori importanti
- Nuovo workflow `avvisi-social.yml`: parte ogni mezz'ora (cron `7,37 5-22 * * *` in UTC va bene, GitHub può ritardare) e con `workflow_dispatch`; permessi `contents: write`; `concurrency` con `cancel-in-progress: false`.
- Passi: aggiorna le notizie (lo script del radar che scrive il file pubblico), poi `avvisi_social.py`, poi commit di `radar/notizie.json` (o il nome reale) e di `avvisi_social.json` con `git pull --rebase --autostash -X theirs origin main && git push`.
- `avvisi_social.py`: legge il file delle notizie; per ogni notizia nuova (indirizzo non in `avvisi_social.json`) con `tipo == "social"`, pubblicata nelle ultime 4 ore, che nomina un lottatore della LISTA, manda un messaggio Telegram con: «📱 <Nome> sui social», titolo, fonte, estratto, `Fai il video: /n_<codice>` (codice = primi 10 caratteri esadecimali dello SHA-256 dell'indirizzo, come nel Worker) e il link per controllare la fonte. Salva gli indirizzi già visti (ultimi 600). **Alla prima esecuzione registra tutto come già visto e NON invia niente.**
- LISTA dei lottatori importanti (modificabile, tienila in cima al file): mettici i nomi più cercati e seguiti: ad esempio McGregor, Jon Jones, Topuria, Makhachev, Islam, Pereira, Chimaev, Poirier, Adesanya, Du Plessis, Aspinall, Volkanovski, Pimblett, O'Malley, Usman, Edwards, Oliveira, Gaethje, Holloway, Strickland, Dricus, Costa, Whittaker, Sterling, Dvalishvili, Fiziev, Nurmagomedov, Cejudo, Ngannou, Miocic e i lottatori italiani della UFC o di Oktagon/Bellator/PFL che il radar già conosce. Usa i nomi con cui il radar già li identifica; se un cognome è ambiguo (due Nurmagomedov, due fratelli con lo stesso cognome) vale solo il nome completo.
- Il token Telegram è nel secret `TELEGRAM_TOKEN` (o `TELEGRAM_BOT_TOKEN`) del repository e la chat è la mia: usa gli stessi nomi di secret che usano già gli altri workflow. Mai scrivere token nel codice.
- NON mandarmi messaggi di prova: prova in locale con `--prova`/senza token (lo script stampa il messaggio invece di inviarlo) e dimmi cosa vedi.

### 3. Comando `/social`: video da un post social incollato a mano
- Quando vedo un post prima delle testate, scrivo al bot: `/social Topuria su Instagram: testo del post`. Il Worker riconosce il comando (anche con `@nomebot`), prende tutto il testo dopo `/social` (minimo 20 caratteri, massimo 3000; altrimenti risponde con un esempio) e lancia il workflow del video con `cosa: "social"` e il testo in un input (stesso input che usa già `notizia-scelta` per l'indirizzo, oppure uno nuovo `post`).
- Nel workflow passa il testo con una variabile d'ambiente (mai interpolato dentro lo script) e chiama lo script del video con `--post "$TESTO" --avvisa`.
- Lo script del video: se c'è `--post`, costruisce una «notizia» manuale: `url = "social:<hash del testo>"` (niente da scaricare: salta download dell'articolo, foto dell'articolo e notizie correlate), `fonte = "Post social di <Nome>"`, `titolo` = inizio del testo (max 90 caratteri), `estratto` = il testo, `manuale = true`. Il lottatore si ricava dal nome COMPLETO o dal cognome non ambiguo nel testo; se non c'è nessun lottatore noto, manda un avviso Telegram («Nel testo non trovo il nome di un lottatore. Riscrivi /social con il nome…») e si ferma.
- Il minimo di testo per fare il video è 40 caratteri (non i 350 degli articoli). Nel prompt per il modello che scrive il video aggiungi: «Questo NON è un articolo ma un POST SOCIAL scritto dal lottatore (testo incollato dal gestore). Attribuiscilo con chiarezza («ha scritto sui social», «nel suo post»), racconta solo ciò che c'è nel post, non aggiungere fatti, motivi o retroscena che non vi compaiono e non presentare come certo ciò che è solo una sua opinione.»
- La didascalia non mette il link dell'articolo (non esiste), solo titolo e fonte. Il resto (foglio foto di controllo, copertina, regole di pertinenza delle foto, voce) resta come oggi.
- Nel testo di `/start`/aiuto aggiungi la riga di `/social`.

## Regole che valgono sempre
1. Foto sempre pertinenti scena per scena; mai volti a caso; stesso cognome = ambiguità (vale solo il nome completo).
2. Non mandarmi niente senza che lo chieda: prova in locale, dimmi cosa vedi.
3. Fatti: niente accuse senza fonte; le dichiarazioni si attribuiscono e si riscrivono con parole nostre.
4. TikTok ci ha rimosso un video per «Servizi e beni regolamentati»: in video, copertine e didascalie evita pronostico/pronostici, scommesse, quote, premi, soldi.
5. Non cambiare voce, velocità o grafica che già funzionano.
6. Nessun segreto in chat o nel repository.

## Come lavorare
- Prima leggi `radar.py`, `video_notizie.py`, `worker/bot-telegram.js`, `worker/LEGGIMI.md` e i workflow esistenti, e dimmi in poche righe cosa hai capito. Poi procedi (non chiedermi conferma per i dettagli tecnici, solo per le scelte che dipendono da me, come la lista dei lottatori).
- Se hai accesso al repository `giovannirosso05-code/gpoggi` guardalo come riferimento già funzionante: `avvisi_social.py`, `.github/workflows/avvisi-social.yml`, `build_news.py` (`SOCIAL`, `tipo_dichiarazione`), `video/notizie_giorno.py` (`--post`) e `worker/bot-telegram.js` (comando `/social`). Adatta, non copiare alla cieca: qui i nomi sono lottatori e il testo dei video lo scrive Gemini come oggi.
- Controlla ciò che puoi in locale: `node --check` sul Worker, YAML dei workflow, riconoscimento del tipo `social` con notizie vere, riconoscimento del lottatore nel testo di `/social`. Non dichiarare «fatto» ciò che non hai visto funzionare: dimmi cosa hai provato e cosa no.
- Quando hai finito: aggiorna `worker/LEGGIMI.md` e la riga `VERSIONE` in cima al Worker, e dammi **il link GitHub al file `worker/bot-telegram.js`** (pagina `blob`, così premo «Copy raw file»). Poi dimmi i passi per aggiornare il Worker di MMA Oggi su Cloudflare (Edit code → incolla → Deploy → controlla la versione): il Worker di MMA Oggi è un altro da quello di GP Oggi, non incollare mai il codice nel Worker sbagliato.
