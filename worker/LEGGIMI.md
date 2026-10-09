# Bot Telegram di GP Oggi sempre sveglio

Quando scrivi un comando a **Gpoggibot**, il bot lancia subito il lavoro su GitHub e ti risponde.
Niente più attese. È gratis.

## I comandi
| Comando | Cosa fa |
|---|---|
| `/scegli` | Ti mostra le 8 notizie più recenti con i numeri: tocchi il numero e il bot fa il video su quella |
| `/notizie` | Due video di notizie raccontate, scelte dal sistema, subito |
| `/previsioni` | Video delle previsioni dei prossimi Gran Premi (F1 e MotoGP) |
| `/venerdi` | Video del venerdì: ricorda di votare il podio |
| `/maratona` | Tre video di notizie (la maratona, attiva fino all'11 ottobre) |
| `/risultati` | Risultati del weekend: escono appena la sessione è finita, fino a 4 ore dopo (oltre le 4 ore si chiede a Claude) |
| `/dati` | Aggiorna tutti i dati del sito e rimanda i riepiloghi |
| `/start` o `/aiuto` | Mostra questo elenco |

## Regola d'oro
**Mai scrivere token o password in chat con me.** Li incolli solo nei campi di Cloudflare e di GitHub.

## Passi per te (uno alla volta, scrivi "fatto" a Claude dopo ogni gruppo)

### A. Il token di GitHub
1. Apri GitHub → clicca la tua foto in alto a destra → **Settings**.
2. In basso a sinistra: **Developer settings** → **Personal access tokens** → **Fine-grained tokens**.
3. Premi **Generate new token**.
4. Nome: `gpoggi-bot`. Scadenza: 1 anno.
5. **Resource owner**: `giovannirosso05-code`.
6. **Repository access** → **Only select repositories** → scegli solo `gpoggi`.
7. **Permissions** → **Repository permissions** → **Actions** → **Read and write**.
8. Premi **Generate token** e **tieni aperta la pagina** (il token si vede una volta sola).

### B. Il Worker su Cloudflare
1. Cloudflare → **Workers & Pages** → **Create** → **Create Worker**.
2. Nome: `gpoggi-bot` → **Deploy**.
3. **Edit code** → cancella tutto → incolla il contenuto di `worker/bot-telegram.js` → **Deploy**.

### C. Le tre parole segrete (Worker → Settings → Variables and Secrets → Add)
Per ognuna scegli il tipo **Secret**:
1. Nome `TELEGRAM_TOKEN` → il token di Gpoggibot (Telegram → BotFather → `/mybots` → Gpoggibot → API Token).
2. Nome `GITHUB_TOKEN` → il token del passo A.
3. Nome `WEBHOOK_SECRET` → una parola lunga a caso inventata da te (30 lettere e numeri). Segnatela da qualche parte, ti serve tra poco.

Premi **Deploy** quando Cloudflare lo chiede.

### D. Controllo e accensione (dal browser, senza token)
Ti serve l'indirizzo del Worker (in alto nella pagina, tipo `https://gpoggi-bot.TUONOME.workers.dev`).
1. Apri l'indirizzo: deve comparire `GP Oggi bot: ok`.
2. Apri `INDIRIZZO/stato?k=LA_TUA_PAROLA_SEGRETA`. Deve dire `Bot del token: @Gpoggibot`.
   Se dice un altro nome, **fermati** e dillo a Claude: hai messo il token sbagliato.
3. Se c'è scritto `Webhook attuale: (nessuno)`, apri `INDIRIZZO/attiva?k=LA_TUA_PAROLA_SEGRETA`.
   Deve dire `Fatto: webhook attivato`.
   Se invece c'è già un webhook, la pagina si ferma e non cambia niente: dillo a Claude.
4. Scrivi `/start` a Gpoggibot: deve rispondere subito con l'elenco.

## Se qualcosa non va
- **Il bot non risponde a /start**: apri `INDIRIZZO/stato?k=...` e guarda "Ultimo errore di Telegram". Se non è scritto niente, controlla la variabile `CHAT_ID` (di base è la tua chat privata).
- **"Non sono riuscito a lanciare ... (GitHub 403)"**: il token GitHub non ha il permesso Actions: Read and write sul repository `gpoggi`, oppure è scaduto. Rifai il passo A.
- **"GitHub 404"**: nome del repository o del file sbagliato: dillo a Claude.
- Un comando più vecchio di 10 minuti viene ignorato apposta.
- Per tornare indietro: apri `https://api.telegram.org/botTOKEN/deleteWebhook` solo se sai cosa fai, oppure chiedi a Claude.

## Dopo un aggiornamento del codice
Se Claude cambia `bot-telegram.js`: Cloudflare → `gpoggi-bot` → **Edit code** → cancella tutto → incolla il nuovo file → **Deploy**. Se serve, Claude ti dice di riaprire `INDIRIZZO/attiva?k=LA_TUA_PAROLA` (non fa danni: aggiorna solo il collegamento con Telegram).
