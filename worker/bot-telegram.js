/**
 * Bot Telegram di GP Oggi (Gpoggibot), sempre sveglio: Cloudflare Worker (gratuito).
 *
 * Telegram chiama questo indirizzo appena scrivi un comando (webhook); il Worker lancia al volo
 * il workflow giusto su GitHub e risponde subito in chat. Stesso schema del bot di MMA Oggi.
 * È un Worker separato dagli altri (gpoggivotti, gpoggi-orologio): non ne usa le variabili.
 *
 * Variabili da impostare su Cloudflare (Settings -> Variables and Secrets), tipo "Secret":
 *   TELEGRAM_TOKEN   token del bot Gpoggibot (BotFather)
 *   GITHUB_TOKEN     token GitHub "fine-grained", solo repository gpoggi, permesso Actions: Read and write
 *   WEBHOOK_SECRET   una parola lunga a caso inventata da te (Telegram la rimanda a ogni messaggio)
 * Variabili di testo (non segrete, hanno già un valore di base):
 *   CHAT_ID          chat autorizzata: chiunque altro viene ignorato in silenzio
 *   REPO             repository dei workflow (di base giovannirosso05-code/gpoggi)
 *   BOT_USERNAME     nome del bot che questo Worker può attivare (di base Gpoggibot): protegge dal token sbagliato
 *
 * Pagine di servizio (per te, con la parola segreta; i token non compaiono mai):
 *   /stato?k=PAROLA     dice di che bot si tratta e che webhook c'è adesso (non cambia niente)
 *   /attiva?k=PAROLA    imposta il webhook, solo se il bot è Gpoggibot e non c'è già un webhook di altri
 *                       (con &forza=1 sostituisce un webhook esistente: solo se sai cosa c'è)
 */

const REPO_BASE = "giovannirosso05-code/gpoggi";
const CHAT_BASE = "559225883";          // la tua chat privata (la stessa del bot di MMA Oggi: un id utente vale per tutti i bot)
const BOT_BASE = "Gpoggibot";
const RAMO = "main";
const ETA_MASSIMA_SECONDI = 600;        // un comando più vecchio di 10 minuti non si esegue (Telegram può ripetere gli invii dopo un guasto)

// comando -> [file del workflow, input del workflow o null, descrizione]
const COMANDI = {
  "/notizie": ["video-automatici.yml", { cosa: "notizie-ora" }, "Due video di notizie raccontate, subito"],
  "/previsioni": ["video-automatici.yml", { cosa: "previsioni" }, "Video delle previsioni dei prossimi Gran Premi (F1 e MotoGP)"],
  "/venerdi": ["video-venerdi.yml", null, "Video del venerdì: ricorda di votare il podio"],
  "/maratona": ["video-maratona.yml", null, "Tre video di notizie (la maratona, attiva fino all'11 ottobre)"],
  "/risultati": ["risultati-weekend.yml", null, "Risultati del weekend (solo se una sessione è finita da meno di 4 ore)"],
  "/dati": ["update-data.yml", null, "Aggiorna tutti i dati del sito e rimanda i riepiloghi"],
};

const elenco = () => Object.entries(COMANDI).map(([c, [, , d]]) => `${c} · ${d}`).join("\n");

// confronto che non si ferma al primo carattere diverso (la parola segreta non si indovina dai tempi)
function uguali(a, b) {
  a = String(a ?? ""); b = String(b ?? "");
  let d = a.length ^ b.length;
  for (let i = 0; i < Math.max(a.length, b.length); i++) d |= (a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0);
  return d === 0;
}

const tg = (env, metodo, corpo) =>
  fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/${metodo}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corpo || {}),
  }).then((r) => r.json().catch(() => ({ ok: false })));

const rispondi = (env, chatId, testo) => tg(env, "sendMessage", { chat_id: chatId, text: testo, disable_web_page_preview: true });

async function lancia(env, file, inputs) {
  const r = await fetch(`https://api.github.com/repos/${env.REPO || REPO_BASE}/actions/workflows/${file}/dispatches`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "gpoggi-bot",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ ref: RAMO, ...(inputs ? { inputs } : {}) }),
  });
  return { ok: r.status === 204, stato: r.status, dettaglio: r.status === 204 ? "" : (await r.text()).slice(0, 200) };
}

const testo = (s, stato = 200) => new Response(s, { status: stato, headers: { "Content-Type": "text/plain; charset=utf-8" } });

// /stato e /attiva: servono a te, per accendere il bot senza mai scrivere il token da nessuna parte
async function servizio(req, env, u) {
  if (!env.WEBHOOK_SECRET || !uguali(u.searchParams.get("k"), env.WEBHOOK_SECRET)) return testo("non autorizzato", 401);
  if (!env.TELEGRAM_TOKEN) return testo("Manca la variabile TELEGRAM_TOKEN sul Worker.", 500);
  const me = await tg(env, "getMe");
  if (!me.ok) return testo("Telegram non riconosce TELEGRAM_TOKEN (token sbagliato o scaduto). Non ho cambiato niente.", 502);
  const nome = me.result.username;
  const atteso = env.BOT_USERNAME || BOT_BASE;
  const info = (await tg(env, "getWebhookInfo")).result || {};
  const mio = `${u.origin}/`;
  const righe = [
    `Bot del token: @${nome}`,
    `Bot atteso: @${atteso}`,
    `Webhook attuale: ${info.url || "(nessuno)"}`,
    `Messaggi in attesa: ${info.pending_update_count ?? "?"}`,
    ...(info.last_error_message ? [`Ultimo errore di Telegram: ${info.last_error_message}`] : []),
  ];
  if (u.pathname === "/stato") return testo(righe.join("\n"));

  // /attiva
  if (String(nome).toLowerCase() !== String(atteso).toLowerCase()) {
    return testo(`${righe.join("\n")}\n\nFERMO: il token non è del bot @${atteso}. Non ho cambiato niente.`, 409);
  }
  if (info.url === mio) return testo(`${righe.join("\n")}\n\nGià attivo: non serve rifarlo.`);
  if (info.url && u.searchParams.get("forza") !== "1") {
    return testo(`${righe.join("\n")}\n\nFERMO: c'è già un webhook di qualcun altro. Se è proprio da sostituire, aggiungi &forza=1 all'indirizzo.`, 409);
  }
  const r = await tg(env, "setWebhook", { url: mio, secret_token: env.WEBHOOK_SECRET, allowed_updates: ["message"] });
  return testo(r.ok ? `${righe.join("\n")}\n\nFatto: webhook attivato su ${mio}\nOra scrivi /start al bot.` : `Telegram ha rifiutato: ${r.description || "errore sconosciuto"}`, r.ok ? 200 : 502);
}

export default {
  async fetch(req, env, ctx) {
    const u = new URL(req.url);
    if (req.method === "GET") {
      if (u.pathname === "/stato" || u.pathname === "/attiva") return servizio(req, env, u);
      return testo("GP Oggi bot: ok");
    }
    if (req.method !== "POST") return testo("non consentito", 405);
    // Solo Telegram, che conosce la parola segreta, può farci eseguire qualcosa.
    if (!env.WEBHOOK_SECRET || !uguali(req.headers.get("X-Telegram-Bot-Api-Secret-Token"), env.WEBHOOK_SECRET)) return testo("non autorizzato", 401);
    const update = await req.json().catch(() => ({}));
    const msg = update.message;
    if (!msg || !msg.text) return testo("ok");
    if (String(msg.chat && msg.chat.id) !== String(env.CHAT_ID || CHAT_BASE)) return testo("ok"); // chiunque altro: ignorato in silenzio

    const lavoro = (async () => {
      if (Date.now() / 1000 - (msg.date || 0) > ETA_MASSIMA_SECONDI) return;
      const t = msg.text.trim();
      const comando = t.startsWith("/") ? t.split(/\s+/)[0].toLowerCase().split("@")[0] : "";
      if (!COMANDI[comando]) {
        await rispondi(env, msg.chat.id, `Sono sveglio. Scrivi uno di questi comandi:\n${elenco()}\n\n/aiuto · mostra questo elenco`);
        return;
      }
      const [file, inputs, descrizione] = COMANDI[comando];
      const esito = await lancia(env, file, inputs);
      await rispondi(
        env,
        msg.chat.id,
        esito.ok
          ? `✅ Lanciato: ${descrizione}. Arriva tra qualche minuto.`
          : `⚠️ Non sono riuscito a lanciare "${descrizione}" (GitHub ${esito.stato}).\n${esito.dettaglio}`
      );
    })();
    // Risponde subito a Telegram e finisce il lavoro in coda: Telegram non aspetta e non ripete l'invio.
    ctx.waitUntil(lavoro.catch((e) => console.error(e)));
    return testo("ok");
  },
};
