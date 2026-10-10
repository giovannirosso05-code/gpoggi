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
 *   /attiva?k=PAROLA    imposta (o aggiorna) il webhook, solo se il bot è Gpoggibot e non c'è già un webhook di altri
 *                       (con &forza=1 sostituisce un webhook esistente: solo se sai cosa c'è)
 */

const REPO_BASE = "giovannirosso05-code/gpoggi";
const CHAT_BASE = "559225883";          // la tua chat privata (la stessa del bot di MMA Oggi: un id utente vale per tutti i bot)
const BOT_BASE = "Gpoggibot";
const RAMO = "main";
const VERSIONE = "radar-notizia-2 live-1 2026-10-10";   // si legge aprendo l'indirizzo del Worker: serve a controllare che il codice pubblicato sia l'ultimo
const ETA_MASSIMA_SECONDI = 600;        // un comando più vecchio di 10 minuti non si esegue (Telegram può ripetere gli invii dopo un guasto)

// comando -> [file del workflow, input del workflow o null, descrizione]
const COMANDI = {
  "/duevideo": ["video-automatici.yml", { cosa: "notizie-ora" }, "Due video di notizie scelte dal sistema, subito"],
  "/previsioni": ["video-automatici.yml", { cosa: "previsioni" }, "Video delle previsioni dei prossimi Gran Premi (F1 e MotoGP)"],
  "/venerdi": ["video-venerdi.yml", null, "Video del venerdì: ricorda di votare il podio"],
  "/maratona": ["video-maratona.yml", null, "Tre video di notizie (la maratona, attiva fino all'11 ottobre)"],
  "/risultati": ["risultati-weekend.yml", null, "Risultati del weekend (escono appena la sessione è finita, fino a 4 ore dopo)"],
  "/dati": ["update-data.yml", null, "Aggiorna tutti i dati del sito e rimanda i riepiloghi"],
};

const elenco = () => [
  "/sessione · Prossima sessione di F1 e MotoGP: quando e cosa c'è",
  "/sessionerisultati · Ultimi risultati di F1 e MotoGP",
  "/radar · Tutte le ultime notizie: poi scrivi /notizia e la prima parola per averne il video (per esempio /notizia norris)",
  ...Object.entries(COMANDI).map(([c, [, , d]]) => `${c} · ${d}`),
].join("\n");

const RASSEGNA_BASE = "https://gpoggi.it/data/rassegna.json";
const QUANTE = 20;                        // notizie mostrate da /radar
const ETA_PULSANTI_SECONDI = 6 * 3600;    // i pulsanti restano buoni 6 ore (la lista cambia, la notizia si ritrova dal suo codice)

// codice breve di una notizia (i pulsanti di Telegram portano al massimo 64 caratteri)
async function codice(url) {
  const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(url));
  return [...new Uint8Array(h)].slice(0, 5).map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function notizie(env) {
  const r = await fetch(env.RASSEGNA_URL || RASSEGNA_BASE, { headers: { "User-Agent": "gpoggi-bot" } });
  if (!r.ok) throw new Error(`rassegna ${r.status}`);
  return (await r.json()).articoli || [];
}

const pulito = (t) => String(t || "").replace(/[|\n\r]+/g, " ").replace(/\s+/g, " ").trim();

// "F1 | Rebus Mercedes: ..." -> "Rebus Mercedes: ..." (il prefisso F1/MotoGP non conta come prima parola)
const senzaPrefisso = (t) => pulito(String(t || "").replace(/^\s*(f1|formula 1|motogp|moto ?gp)\s*[|:–-]\s*/i, ""));
const norm = (t) => String(t || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ").trim();
const parole = (a) => norm(senzaPrefisso(a.titolo)).split(" ").filter(Boolean);
const primaParola = (a) => parole(a)[0] || "";

const ORE24 = 24 * 3600 * 1000;
const dataArt = (a) => Date.parse(a.pubblicato) || 0;
const piuRecentiPrima = (l) => l.slice().sort((x, y) => dataArt(y) - dataArt(x));
const delGiorno = (l) => piuRecentiPrima(l).filter((a) => Date.now() - dataArt(a) < ORE24);

// notizie che corrispondono alla parola scritta: prima la prima parola del titolo (tra quelle del giorno), poi la prima parola tra tutte, poi una parola qualsiasi
function cerca(tutte, arg) {
  const p = norm(arg).split(" ")[0];
  if (!p) return [];
  const giorno = delGiorno(tutte), ord = piuRecentiPrima(tutte);
  const livelli = [
    giorno.filter((a) => primaParola(a) === p),
    ord.filter((a) => primaParola(a) === p),
    ord.filter((a) => parole(a).includes(p) || (p.length >= 4 && parole(a).some((w) => w.startsWith(p)))),
  ];
  return livelli.find((l) => l.length) || [];
}

async function lanciaNotizia(env, chat, art) {
  await eseguiLancio(env, chat, "video-automatici.yml", {
    cosa: "notizia-scelta",
    url: [art.url, senzaPrefisso(art.titolo), pulito(art.fonte), art.serie === "MotoGP" ? "MotoGP" : "F1"].join("|"),
  }, `video su "${senzaPrefisso(art.titolo).slice(0, 90)}"`);
}

async function tastieraDi(lista) {
  const righe = await Promise.all(lista.map(async (a, i) => ({ n: i + 1, c: await codice(a.url) })));
  const tastiera = [];
  for (let i = 0; i < righe.length; i += 5) tastiera.push(righe.slice(i, i + 5).map(({ n, c }) => ({ text: String(n), callback_data: `n:${c}` })));
  return tastiera;
}

async function mostraLista(env, chat) {
  const tutte = await notizie(env);
  let lista = delGiorno(tutte), intestazione = "📰 Le ultime notizie (ultime 24 ore)";
  if (!lista.length) { lista = piuRecentiPrima(tutte); intestazione = "📰 Niente di nuovo nelle ultime 24 ore: ecco le più recenti"; }
  lista = lista.slice(0, QUANTE);
  if (!lista.length) { await rispondi(env, chat, "Non trovo notizie al momento. Riprova tra poco."); return; }
  const righe = lista.map((a, i) => `${i + 1}. [${a.serie}] ${senzaPrefisso(a.titolo).slice(0, 90)} (${pulito(a.fonte)})\n   ▶ /notizia_${primaParola(a) || "x"}`);
  const PEZZO = 8;   // notizie per messaggio (Telegram taglia i messaggi lunghi)
  for (let i = 0; i < righe.length; i += PEZZO) {
    const primo = i === 0, ultimo = i + PEZZO >= righe.length;
    await tg(env, "sendMessage", {
      chat_id: chat,
      text: `${primo ? intestazione + "\n\n" : ""}${righe.slice(i, i + PEZZO).join("\n\n")}${ultimo ? `\n\nPer il video tocca il comando sotto la notizia, oppure scrivi /notizia e la prima parola (per esempio /notizia ${primaParola(lista[0]) || "norris"}). Puoi anche toccare un numero qui sotto.` : ""}`,
      ...(ultimo ? { reply_markup: { inline_keyboard: await tastieraDi(lista) } } : {}),
      disable_web_page_preview: true,
    });
  }
}

async function videoDa(env, chat, arg) {
  if (!norm(arg)) { await rispondi(env, chat, "Scrivi /notizia e la prima parola della notizia, per esempio /notizia norris. Per vedere le notizie scrivi /radar."); return; }
  const trovate = cerca(await notizie(env), arg);
  if (!trovate.length) { await rispondi(env, chat, `Non trovo nessuna notizia con «${norm(arg).split(" ")[0]}». Scrivi /radar per vedere l'elenco.`); return; }
  if (trovate.length === 1) { await lanciaNotizia(env, chat, trovate[0]); return; }
  const lista = trovate.slice(0, 5);
  await tg(env, "sendMessage", {
    chat_id: chat,
    text: `Ci sono più notizie con «${norm(arg).split(" ")[0]}». Tocca il numero giusto:\n\n${lista.map((a, i) => `${i + 1}. [${a.serie}] ${senzaPrefisso(a.titolo).slice(0, 90)} (${pulito(a.fonte)})`).join("\n")}`,
    reply_markup: { inline_keyboard: await tastieraDi(lista) },
    disable_web_page_preview: true,
  });
}

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

// Quanti lavori di questo flusso sono in corso o in attesa. GitHub tiene un solo lavoro in corso e uno solo in attesa:
// un terzo cancellerebbe quello in attesa, e il bot direbbe "Lanciato" per un video che non esce mai.
async function codaDi(env, file) {
  const r = await fetch(`https://api.github.com/repos/${env.REPO || REPO_BASE}/actions/workflows/${file}/runs?per_page=10`, {
    headers: { Authorization: `Bearer ${env.GITHUB_TOKEN}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "gpoggi-bot" },
  });
  if (!r.ok) return null;   // non riesco a controllare: si lancia lo stesso
  const attivi = ((await r.json()).workflow_runs || []).filter((x) => ["in_progress", "queued", "pending", "waiting", "requested"].includes(x.status));
  return { inLavoro: attivi.filter((x) => x.status === "in_progress").length, inAttesa: attivi.filter((x) => x.status !== "in_progress").length };
}

// lancia il flusso e risponde in chat con l'esito vero (anche "in coda" o "occupato")
async function eseguiLancio(env, chat, file, inputs, descrizione) {
  let coda = null;
  if (file === "video-automatici.yml") {
    coda = await codaDi(env, file).catch(() => null);
    if (coda && coda.inAttesa >= 1) {
      await rispondi(env, chat, `⏳ Non lancio "${descrizione}": c'è già un video in lavorazione e uno in coda. Riscrivi il comando tra qualche minuto, altrimenti andrebbe perso.`);
      return;
    }
  }
  const esito = await lancia(env, file, inputs);
  if (!esito.ok) { await rispondi(env, chat, `⚠️ Non sono riuscito a lanciare "${descrizione}" (GitHub ${esito.stato}).\n${esito.dettaglio}`); return; }
  await rispondi(env, chat, coda && coda.inLavoro >= 1
    ? `🕓 In coda: ${descrizione}. C'è un altro video in lavorazione: parte appena finisce, poi arriva tra qualche minuto.`
    : `✅ Lanciato: ${descrizione}. Arriva tra qualche minuto.`);
}

// ---------- /sessione e /sessionerisultati: orari e risultati letti dai dati del sito ----------
const DATI_BASE = "https://gpoggi.it/data";
const FUSO = "Europe/Rome";
const ORE4 = 4 * 3600 * 1000;

async function dato(env, nome) {
  const r = await fetch(`${env.DATI_URL || DATI_BASE}/${nome}`, { headers: { "User-Agent": "gpoggi-bot" }, cf: { cacheTtl: 60 } });
  if (!r.ok) throw new Error(`dato ${nome}: ${r.status}`);
  return r.json();
}

function quando(ms) {
  const p = Object.fromEntries(new Intl.DateTimeFormat("it-IT", { timeZone: FUSO, weekday: "long", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit", hourCycle: "h23" })
    .formatToParts(new Date(ms)).map((x) => [x.type, x.value]));
  return `${p.weekday} ${p.day} ${p.month} alle ${p.hour}:${p.minute}`;
}
const soloOra = (ms) => new Intl.DateTimeFormat("it-IT", { timeZone: FUSO, hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(new Date(ms));
function fra(ms) {
  const m = Math.max(1, Math.round(ms / 60000));
  if (m < 60) return `tra ${m} min`;
  const h = Math.floor(m / 60);
  if (h < 24) return `tra ${h} h${m % 60 ? ` ${m % 60} min` : ""}`;
  return `tra ${Math.floor(h / 24)} g${h % 24 ? ` ${h % 24} h` : ""}`;
}

// sessioni normalizzate di un weekend: durata di 45 minuti se la fonte non indica la fine (sprint e gara della MotoGP)
const normSess = (w) => (w.sessioni || []).map((x) => { const i = Date.parse(x.inizio), f = Date.parse(x.fine); return { nome: x.codice === "PR" ? "Practice" : x.nome, codice: x.codice, i, f: f > i ? f : i + 45 * 60000 }; }).sort((a, b) => a.i - b.i);

function bloccoSessione(icona, serie, weekend, adesso) {
  // il primo weekend che ha ancora una sessione non finita
  const w = weekend.map((x) => ({ nome: x.nome, sess: normSess(x) })).sort((a, b) => (a.sess[0]?.i || 0) - (b.sess[0]?.i || 0)).find((x) => x.sess.some((s) => s.f > adesso));
  if (!w) return `${icona} ${serie}\nNessuna sessione in programma.`;
  const righe = [`${icona} ${serie} · ${w.nome}`];
  const corso = w.sess.find((s) => s.i <= adesso && adesso < s.f);
  const prossime = w.sess.filter((s) => s.i > adesso);
  if (corso) righe.push(`🔴 In corso: ${corso.nome} (finisce alle ${soloOra(corso.f)})`);
  if (prossime.length) {
    righe.push(`▶ Prossima: ${prossime[0].nome}, ${quando(prossime[0].i)} (${fra(prossime[0].i - adesso)})`);
    if (prossime.length > 1) righe.push("Poi:", ...prossime.slice(1).map((s) => `• ${s.nome}, ${quando(s.i)}`));
  }
  return righe.join("\n");
}

async function comandoSessione(env, chat) {
  const adesso = Date.now();
  const [ev, mg] = await Promise.all([dato(env, "events.json"), dato(env, "motogp.json")]);
  await rispondi(env, chat, `${bloccoSessione("🏎", "FORMULA 1", ev, adesso)}\n\n${bloccoSessione("🏍", "MOTOGP", mg.weekend || [], adesso)}\n\nOrari italiani.`);
}

const TEMPO = (r, primo) => (primo ? r.tempo : (r.distacco && r.distacco !== "0.000" ? (String(r.distacco).startsWith("+") ? r.distacco : `+${r.distacco}`) : r.tempo)) || r.stato || "";
// una riga di classifica: chi non ha posizione è ritirato; chi ha fatto meno giri del vincitore è doppiato
const riga = (r, primo, giriVincitore) => {
  if (r.pos == null) return `– ${r.nome} · ritirato${r.giri ? ` dopo ${r.giri} ${r.giri === 1 ? "giro" : "giri"}` : " al primo giro"}`;
  const indietro = giriVincitore && r.giri && r.giri < giriVincitore ? ` · -${giriVincitore - r.giri} ${giriVincitore - r.giri === 1 ? "giro" : "giri"}` : "";
  return `${r.pos}. ${r.nome}${indietro || (TEMPO(r, primo) ? ` · ${TEMPO(r, primo)}` : "")}`;
};
const podio = (rows) => (rows || []).slice(0, 3).map((r) => `${r.pos}. ${r.nome}`).join(" · ");

async function risultatiF1(env, adesso) {
  const ev = (await dato(env, "events.json")).slice().sort((a, b) => Date.parse(a.inizio) - Date.parse(b.inizio)).filter((e) => Date.parse(e.inizio) <= adesso);
  let sessione = null, gp = "", senza = [], ultimaGara = null;
  for (let k = ev.length - 1; k >= 0 && k >= ev.length - 4; k--) {
    const d = await dato(env, `gare/${ev[k].id}.json`);
    const fatte = (d.sessioni || []).filter((x) => Date.parse(x.fine) <= adesso).sort((a, b) => Date.parse(b.fine) - Date.parse(a.fine));
    if (!sessione) {
      const c = fatte.find((x) => (x.risultati || []).length);
      if (c) { sessione = c; gp = d.nome; senza = fatte.filter((x) => !(x.risultati || []).length && Date.parse(x.fine) > Date.parse(c.fine) && adesso - Date.parse(x.fine) < ORE4); }
      else { gp = gp || d.nome; senza = senza.concat(fatte.filter((x) => adesso - Date.parse(x.fine) < ORE4)); }
    }
    const gara = fatte.find((x) => x.nome === "Gara" && (x.risultati || []).length);
    if (gara && !ultimaGara) ultimaGara = { gp: d.nome, rows: gara.risultati };
    if (sessione && ultimaGara) break;
  }
  return { sessione, gp, senza, ultimaGara };
}

async function comandoRisultati(env, chat) {
  const adesso = Date.now();
  let attesa = false;
  // ---------- Formula 1: ultima sessione con risultati (tutti i piloti) e podio dell'ultima gara
  const f1 = await risultatiF1(env, adesso);
  const a = [`🏎 FORMULA 1${f1.gp ? ` · ${f1.gp}` : ""}`];
  if (f1.sessione) a.push(`Ultima sessione con risultati: ${f1.sessione.nome}`, ...f1.sessione.risultati.map((r, i) => riga(r, i === 0, f1.sessione.nome === "Gara" || f1.sessione.nome === "Sprint" ? (f1.sessione.risultati[0] || {}).giri : 0)));
  else a.push("Nessun risultato disponibile per questo weekend.");
  for (const x of f1.senza) { a.push(`⏳ ${x.nome}: finita alle ${soloOra(Date.parse(x.fine))}, risultati non ancora pubblicati dalla fonte.`); attesa = true; }
  if (f1.ultimaGara && !(f1.sessione && f1.sessione.nome === "Gara")) a.push(`🏁 Ultima gara: ${f1.ultimaGara.gp} · ${podio(f1.ultimaGara.rows)}`);

  // ---------- MotoGP: ultima sessione del weekend in corso (se ce n'è) e ultimo GP concluso
  const [mg, cal, ms] = await Promise.all([dato(env, "motogp-gare.json"), dato(env, "motogp.json").catch(() => ({ weekend: [] })), dato(env, "motogp-sessioni.json").catch(() => null)]);
  const b = [];
  const corrente = (cal.weekend || []).map((x) => ({ nome: x.nome, sess: (x.sessioni || []).map((q) => ({ ...q, ...normSess({ sessioni: [q] })[0] })) }))
    .find((x) => x.sess.some((q) => q.i <= adesso) && x.sess.some((q) => q.f > adesso));
  if (corrente) {
    const dati = ms && (ms.weekend || []).find((w) => w.nome === corrente.nome);
    const conRis = (dati && dati.sessioni) || [];
    const ultima = conRis[conRis.length - 1];
    b.push(`🏍 MOTOGP · ${corrente.nome}`);
    if (ultima) b.push(`Ultima sessione con risultati: ${ultima.nome}`, ...ultima.risultati.map((r, i) => riga(r, i === 0, ultima.codice === "RAC" || ultima.codice === "SPR" ? (ultima.risultati[0] || {}).giri : 0)));
    else b.push("Nessuna sessione di questo weekend ha ancora risultati.");
    for (const q of corrente.sess) {
      if (q.f <= adesso && adesso - q.f < ORE4 && !conRis.some((x) => x.codice === q.codice)) { b.push(`⏳ ${NOME_MOTO[q.codice] || q.nome}: finita alle ${soloOra(q.f)}, risultati non ancora pubblicati dalla fonte.`); attesa = true; }
    }
    b.push("");
  }
  const gareM = Object.values(mg).filter((g) => g.classifiche && (g.classifiche.MotoGP || []).length).sort((x, y) => String(y.data).localeCompare(String(x.data)));
  if (gareM.length) {
    const g = gareM[0], cl = g.classifiche, tutti = [...(cl.MotoGP || []), ...(cl["MotoGP sprint"] || [])];
    const per = (num) => (tutti.find((r) => r.numero === num) || {}).nome;
    const [aa, mm, gg] = String(g.data).split("-").map(Number);
    const dataIt = new Intl.DateTimeFormat("it-IT", { timeZone: "UTC", day: "numeric", month: "long" }).format(new Date(Date.UTC(aa, mm - 1, gg)));
    b.push(`🏁 MotoGP · ultimo GP: ${g.nome} (${dataIt})`, "Gara", ...(cl.MotoGP || []).map((r, i) => riga(r, i === 0, (cl.MotoGP[0] || {}).giri)));
    if ((cl["MotoGP sprint"] || []).length) b.push("", "Sprint", ...cl["MotoGP sprint"].map((r) => (r.pos == null ? `– ${r.nome} · ritirato` : `${r.pos}. ${r.nome}`)));
    if (per(g.pole)) b.push("", `Pole: ${per(g.pole)}`);
    if (per(g.giro_veloce)) b.push(`Giro veloce: ${per(g.giro_veloce)}`);
  } else if (!corrente) b.push("🏍 MOTOGP\nNessun risultato disponibile.");

  // ---------- se manca il risultato di una sessione finita da poco, si lancia l'aggiornamento (una volta sola)
  if (attesa) {
    const coda = await codaDi(env, "risultati-weekend.yml").catch(() => null);
    if (coda && (coda.inLavoro || coda.inAttesa)) b.push("", "🔄 L'aggiornamento dei risultati è già in corso: riscrivi il comando tra qualche minuto.");
    else {
      const e = await lancia(env, "risultati-weekend.yml", null);
      b.push("", e.ok ? "🔄 Ho lanciato l'aggiornamento dei risultati: riscrivi il comando tra 5-6 minuti." : `⚠️ Non sono riuscito a lanciare l'aggiornamento (GitHub ${e.stato}).`);
    }
  }
  b.push("", "Classifiche complete su gpoggi.it");
  await invia(env, chat, a.join("\n"));
  await invia(env, chat, b.join("\n"));
}

const NOME_MOTO = { FP1: "Prove libere 1", PR: "Practice", FP2: "Prove libere 2", Q1: "Qualifiche 1", Q2: "Qualifiche 2", SPR: "Sprint", WUP: "Warm up", RAC: "Gara" };

// manda un testo lungo in più messaggi, spezzando sulle righe (Telegram accetta al massimo 4096 caratteri per messaggio)
async function invia(env, chat, testoLungo) {
  let blocco = "";
  for (const r of testoLungo.split("\n")) {
    if (blocco.length + r.length + 1 > 3800) { await rispondi(env, chat, blocco); blocco = ""; }
    blocco += (blocco ? "\n" : "") + r;
  }
  if (blocco.trim()) await rispondi(env, chat, blocco);
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
  if (info.url === mio && (info.allowed_updates || []).includes("callback_query")) return testo(`${righe.join("\n")}\n\nGià attivo: non serve rifarlo.`);
  if (info.url && info.url !== mio && u.searchParams.get("forza") !== "1") {
    return testo(`${righe.join("\n")}\n\nFERMO: c'è già un webhook di qualcun altro. Se è proprio da sostituire, aggiungi &forza=1 all'indirizzo.`, 409);
  }
  const r = await tg(env, "setWebhook", { url: mio, secret_token: env.WEBHOOK_SECRET, allowed_updates: ["message", "callback_query"] });
  return testo(r.ok ? `${righe.join("\n")}\n\nFatto: webhook attivato su ${mio}\nOra scrivi /start al bot.` : `Telegram ha rifiutato: ${r.description || "errore sconosciuto"}`, r.ok ? 200 : 502);
}

// tocco di un numero in /radar: ritrova la notizia dal codice e lancia il video su quella
function pulsante(cb, env, ctx) {
  const chat = cb.message && cb.message.chat && cb.message.chat.id;
  if (String(chat) !== String(env.CHAT_ID || CHAT_BASE)) return testo("ok");   // altri: ignorati in silenzio
  if (!String(cb.data || "").startsWith("n:")) return testo("ok");             // pulsanti di altri messaggi (es. "vota_"): non sono nostri
  const lavoro = (async () => {
    if (Date.now() / 1000 - (cb.message.date || 0) > ETA_PULSANTI_SECONDI) {
      await tg(env, "answerCallbackQuery", { callback_query_id: cb.id, text: "Lista vecchia: scrivi di nuovo /radar" });
      return;
    }
    await tg(env, "answerCallbackQuery", { callback_query_id: cb.id, text: "Lancio…" });
    const cod = cb.data.slice(2);
    let trovata = null;
    for (const a of await notizie(env)) if ((await codice(a.url)) === cod) { trovata = a; break; }
    if (!trovata) { await rispondi(env, chat, "Quella notizia non è più nella lista. Scrivi di nuovo /radar."); return; }
    await lanciaNotizia(env, chat, trovata);
  })();
  ctx.waitUntil(lavoro.catch((e) => console.error(e)));
  return testo("ok");
}

// Tempi dal vivo della MotoGP per la scheda Live del sito: il Worker li legge dalla fonte ufficiale e li ripassa con CORS aperto.
// Lo schema non è documentato: si restituisce in forma difensiva; con ?raw=1 si vede il testo originale.
const LIVE_MOTO = "https://api.motogp.pulselive.com/motogp/v1/timing-gateway/livetiming-lite";
async function liveMoto(u) {
  const CORS = { "Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=3" };
  try {
    const r = await fetch(LIVE_MOTO, { headers: { Accept: "application/json" } });
    const t = await r.text();
    if (u.searchParams.get("raw")) return new Response(t, { status: r.status, headers: { ...CORS, "Content-Type": "application/json; charset=utf-8" } });
    if (!r.ok) return new Response(JSON.stringify({ ok: false, stato: r.status }), { headers: { ...CORS, "Content-Type": "application/json" } });
    let d; try { d = JSON.parse(t); } catch { d = null; }
    const grezzo = d && (d.lead_riders || d.riders || d.classification || d.rider_list || d.data || d);
    const lista = Array.isArray(grezzo) ? grezzo : (grezzo && typeof grezzo === "object" ? Object.values(grezzo) : []);
    const piloti = lista.filter((x) => x && typeof x === "object").map((x, i) => ({
      pos: Number(x.pos ?? x.position ?? x.rider_position ?? i + 1) || i + 1,
      numero: x.rider_number ?? x.number ?? x.num ?? null,
      nome: x.rider_name ? [x.rider_name, x.rider_surname].filter(Boolean).join(" ") : (x.name ?? x.rider ?? null),
      team: x.team_name ?? x.team ?? null,
      tempo: x.lap_time ?? x.last_lap_time ?? x.best_lap_time ?? x.time ?? null,
      distacco: x.gap_first ?? x.gap ?? x.gap_to_leader ?? null,
    }));
    const testa = (d && typeof d === "object" && !Array.isArray(d)) ? d : {};
    return new Response(JSON.stringify({ ok: piloti.length > 0, sessione: testa.session_name ?? testa.session ?? testa.category ?? null, giri: testa.lap ?? testa.current_lap ?? null, bandiera: testa.flag ?? testa.session_status ?? null, piloti }), { headers: { ...CORS, "Content-Type": "application/json; charset=utf-8" } });
  } catch (e) {
    return new Response(JSON.stringify({ ok: false, errore: String(e && e.message || e).slice(0, 120) }), { headers: { ...CORS, "Content-Type": "application/json" } });
  }
}

export default {
  async fetch(req, env, ctx) {
    const u = new URL(req.url);
    if (req.method === "GET") {
      if (u.pathname === "/live/motogp") return liveMoto(u);
      if (u.pathname === "/stato" || u.pathname === "/attiva") return servizio(req, env, u);
      return testo(`GP Oggi bot: ok · versione ${VERSIONE}`);
    }
    if (req.method !== "POST") return testo("non consentito", 405);
    // Solo Telegram, che conosce la parola segreta, può farci eseguire qualcosa.
    if (!env.WEBHOOK_SECRET || !uguali(req.headers.get("X-Telegram-Bot-Api-Secret-Token"), env.WEBHOOK_SECRET)) return testo("non autorizzato", 401);
    const update = await req.json().catch(() => ({}));
    if (update.callback_query) return pulsante(update.callback_query, env, ctx);
    const msg = update.message;
    if (!msg || !msg.text) return testo("ok");
    if (String(msg.chat && msg.chat.id) !== String(env.CHAT_ID || CHAT_BASE)) return testo("ok"); // chiunque altro: ignorato in silenzio

    const lavoro = (async () => {
      if (Date.now() / 1000 - (msg.date || 0) > ETA_MASSIMA_SECONDI) return;
      const t = msg.text.trim();
      const comando = t.startsWith("/") ? t.split(/\s+/)[0].toLowerCase().split("@")[0] : "";
      // /sessione, /sessioni, /sessionerisultati, /sessionirisultati, /sessione_risultati: stessi due comandi, con o senza plurale
      const ses = comando.replace(/^\/sessioni/, "/sessione").replace(/^\/sessione_/, "/sessione");
      if (ses === "/sessione") { await comandoSessione(env, msg.chat.id); return; }
      if (ses === "/sessionerisultati") { await comandoRisultati(env, msg.chat.id); return; }
      if (comando === "/radar" || comando === "/notizie" || comando === "/scegli") { await mostraLista(env, msg.chat.id); return; }
      const nv = comando.match(/^\/(?:notizia|video)(?:_(.*))?$/);   // /notizia norris, /notizia_norris (toccabile); /video resta come alias
      if (nv) {
        await videoDa(env, msg.chat.id, nv[1] !== undefined ? nv[1].replace(/_/g, " ") : t.split(/\s+/).slice(1).join(" "));
        return;
      }
      if (!COMANDI[comando]) {
        await rispondi(env, msg.chat.id, `Sono sveglio. Scrivi uno di questi comandi:\n${elenco()}\n\n/aiuto · mostra questo elenco`);
        return;
      }
      const [file, inputs, descrizione] = COMANDI[comando];
      await eseguiLancio(env, msg.chat.id, file, inputs, descrizione);
    })();
    // Risponde subito a Telegram e finisce il lavoro in coda: Telegram non aspetta e non ripete l'invio.
    ctx.waitUntil(lavoro.catch((e) => { console.error(e); return rispondi(env, msg.chat.id, `⚠️ Qualcosa non ha funzionato: riprova tra poco.\n(${String(e && e.message || e).slice(0, 200)})`); }));
    return testo("ok");
  },
};
