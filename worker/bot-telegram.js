/**
 * Bot Telegram di GP Oggi (Gpoggibot), sempre sveglio: Cloudflare Worker (gratuito).
 */

const REPO_BASE = "giovannirosso05-code/gpoggi";
const CHAT_BASE = "559225883";
const BOT_BASE = "Gpoggibot";
const RAMO = "main";
const VERSIONE = "definitivo-assoluto 2026-10-18";
const ETA_MASSIMA_SECONDI = 600;

const COMANDI = {
  "/duevideo": ["video-automatici.yml", { cosa: "notizie-ora" }, "Due video di notizie scelte dal sistema, subito"],
  "/previsioni": ["video-automatici.yml", { cosa: "previsioni" }, "Video delle previsioni dei prossimi Gran Premi (F1 e MotoGP)"],
  "/gara": ["anteprima-gara.yml", { serie: "auto" }, "Video sulla prossima gara: orario, circuito, chi può vincere e le ultime notizie"],
  "/garaf1": ["anteprima-gara.yml", { serie: "f1" }, "Come /gara, ma per il prossimo Gran Premio di F1"],
  "/garamoto": ["anteprima-gara.yml", { serie: "motogp" }, "Come /gara, ma per la prossima gara MotoGP"],
  "/venerdi": ["video-venerdi.yml", null, "Video del venerdì: ricorda di votare il podio"],
  "/maratona": ["video-maratona.yml", null, "Tre video di notizie (la maratona)"],
  "/risultati": ["risultati-weekend.yml", null, "Risultati del weekend"],
  "/dati": ["update-data.yml", null, "Aggiorna tutti i dati del sito e rimanda i riepiloghi"],
};

const elenco = () => [
  "/sessione · Prossima sessione di F1 e MotoGP",
  "/sessionerisultati · Ultimi risultati di F1 e MotoGP",
  "/copertina · Una nuova copertina per l'ultimo video (o /copertina parola)",
  "/radar · Notizie divise per Formula 1 e MotoGP (interviste e dichiarazioni in cima)",
  "/rassegna · Rassegna stampa subito, scelta in automatico; oppure /rassegna e 2-6 parole (o codici /n_…) per sceglierla tu: la prima notizia è il gancio (per esempio /rassegna minardi norris ferrari horner)",
  "/coda · Controlla lo stato dei video in lavorazione o in coda su GitHub",
  ...Object.entries(COMANDI).map(([c, [, , d]]) => `${c} · ${d}`),
].join("\n");

const RASSEGNA_BASE = "https://gpoggi.it/data/rassegna.json";
const QUANTE_PER_SERIE = 10;
const ETA_PULSANTI_SECONDI = 6 * 3600;

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
const senzaPrefisso = (t) => pulito(String(t || "").replace(/^\s*(f1|formula 1|motogp|moto ?gp)\s*[|:–-]\s*/i, ""));
const norm = (t) => String(t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ").trim();
const parole = (a) => norm(senzaPrefisso(a.titolo)).split(" ").filter(Boolean);
const primaParola = (a) => parole(a)[0] || "";

const ORE24 = 24 * 3600 * 1000;
const ORE72 = 72 * 3600 * 1000;
const dataArt = (a) => Date.parse(a.pubblicato) || 0;
const piuRecentiPrima = (l) => l.slice().sort((x, y) => dataArt(y) - dataArt(x));
const delGiorno = (l) => piuRecentiPrima(l).filter((a) => Date.now() - dataArt(a) < ORE24);
const ultime72 = (l) => piuRecentiPrima(l).filter((a) => Date.now() - dataArt(a) < ORE72);

const CITAZ = /[“”"«»]|\b(dice|dicono|ammette|rivela|spiega|racconta|intervista|parla|svela|confessa|promette|avverte|attacca|risponde|sottolinea|difende|chiarisce|ricorda)\b/i;
const èCitazione = (a) => a.citazione === true || (a.citazione === undefined && CITAZ.test(a.titolo || ""));
const èMotoGP = (a) => /motogp|moto ?gp|moto2|moto3/i.test(String(a.serie || ""));
// 🎤 interviste, 📱 post sui social, 💬 altre dichiarazioni (il campo "tipo" lo scrive build_news.py)
const icona = (a) => (a.tipo === "social" ? "📱 " : a.tipo === "intervista" ? "🎤 " : èCitazione(a) ? "💬 " : "");

function importanza(a) {
  let punti = 0;
  if (èCitazione(a)) punti += 50;
  if (a.tipo === "social") punti += 15;
  else if (a.tipo === "intervista") punti += 10;
  punti += Math.max(0, 24 - (Date.now() - dataArt(a)) / 3600000);
  return punti;
}

const perImportanza = (l) => l.slice().sort((x, y) => importanza(y) - importanza(x) || dataArt(y) - dataArt(x));

// Le notizie di una serie: quelle delle ultime 72 ore per importanza (dichiarazioni in cima); se sono meno di QUANTE_PER_SERIE
// (per esempio la MotoGP in un weekend senza gara) si completa con le più recenti disponibili, mai una lista quasi vuota.
const NON_NOTIZIA = /\borari\b|\bpodcast\b/i;   // «GP Australia: orari Sky/Now e TV8», «WarmUp F1 Podcast»: non sono notizie su cui fare un video
function sceltaPerSerie(tutte, filtro) {
  const serie = tutte.filter((a) => filtro(a) && !NON_NOTIZIA.test(a.titolo || ""));
  let lista = perImportanza(ultime72(serie)).slice(0, QUANTE_PER_SERIE);
  if (lista.length < QUANTE_PER_SERIE) {
    const gia = new Set(lista.map((a) => a.url));
    lista = lista.concat(piuRecentiPrima(serie).filter((a) => !gia.has(a.url)).slice(0, QUANTE_PER_SERIE - lista.length));
  }
  return lista;
}

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
    url: [art.url, senzaPrefisso(art.titolo), pulito(art.fonte), èMotoGP(art) ? "MotoGP" : "F1"].join("|"),
  }, `video su "${senzaPrefisso(art.titolo).slice(0, 90)}"`);
}

async function comandoCoda(env, chat) {
  const r = await fetch(`https://api.github.com/repos/${env.REPO || REPO_BASE}/actions/runs?per_page=5`, {
    headers: { Authorization: `Bearer ${env.GITHUB_TOKEN}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "gpoggi-bot" },
  });
  if (!r.ok) {
    await rispondi(env, chat, "⚠️ Non riesco a leggere lo stato della coda da GitHub al momento.");
    return;
  }
  const dati = await r.json();
  const esecuzioni = (dati.workflow_runs || []).slice(0, 4);
  if (!esecuzioni.length) {
    await rispondi(env, chat, "📭 Nessun lavoro recente su GitHub.");
    return;
  }
  const righe = esecuzioni.map(x => {
    const statoEmoji = x.status === "in_progress" ? "🔴 In corso" : x.status === "queued" ? "⏳ In coda" : x.conclusion === "success" ? "✅ Completato" : "❌ Fallito";
    return `${statoEmoji} · ${x.name} (${x.head_branch})`;
  });
  await rispondi(env, chat, `📊 Stato code GitHub:\n\n${righe.join("\n")}`);
}

async function formattaBlocco(titoloSezione, lista) {
  if (!lista.length) return `${titoloSezione}\nNessuna notizia recente.`;
  const cod = await Promise.all(lista.map((a) => codice(a.url)));
  const righe = lista.map((a, i) => `${i + 1}. ${icona(a)}${senzaPrefisso(a.titolo).slice(0, 90)} (${pulito(a.fonte)})\n   ▶ /n_${cod[i]}`);
  return `${titoloSezione}\n\n${righe.join("\n\n")}`;
}

async function mostraLista(env, chat) {
  const tutte = await notizie(env);
  if (!tutte.length) { await rispondi(env, chat, "Non trovo notizie al momento. Riprova tra poco."); return; }

  const listaF1 = sceltaPerSerie(tutte, (a) => !èMotoGP(a));
  const listaMoto = sceltaPerSerie(tutte, (a) => èMotoGP(a));

  const bloccoF1 = await formattaBlocco("🏎 FORMULA 1 · Ultime notizie (dichiarazioni e interviste in cima)", listaF1);
  const bloccoMoto = await formattaBlocco("🏍 MOTOGP · Ultime notizie (dichiarazioni e interviste in cima)", listaMoto);
  const istruzioni = "\n\n🎤 = intervista · 📱 = social · 💬 = dichiarazioni\n• Tocca ▶ sotto la notizia per il video singolo\n• Scrivi /rassegna per la rassegna stampa subito, oppure /rassegna e 2-6 parole per sceglierla tu (la prima notizia è il gancio)\n• Scrivi /coda per controllare lo stato dei video.";

  await invia(env, chat, bloccoF1);
  await invia(env, chat, bloccoMoto + istruzioni);
}

async function videoDa(env, chat, arg) {
  if (!norm(arg)) { await rispondi(env, chat, "Scrivi /notizia e la prima parola della notizia, per esempio /notizia norris. Per vedere le notizie scrivi /radar."); return; }
  const trovate = cerca(await notizie(env), arg);
  if (!trovate.length) { await rispondi(env, chat, `Non trovo nessuna notizia con «${norm(arg).split(" ")[0]}». Scrivi /radar per vedere l'elenco.`); return; }
  await lanciaNotizia(env, chat, trovate[0]);
}

async function copertinaDa(env, chat, arg) {
  let url = "";
  if (norm(arg)) {
    const t = cerca(await notizie(env), arg);
    if (!t.length) { await rispondi(env, chat, `Non trovo nessuna notizia con «${norm(arg).split(" ")[0]}». Scrivi /radar per vedere l'elenco.`); return; }
    const a = t[0];
    url = [a.url, senzaPrefisso(a.titolo), pulito(a.fonte), èMotoGP(a) ? "MotoGP" : "F1"].join("|");
  }
  await eseguiLancio(env, chat, "video-automatici.yml", { cosa: "copertina", url }, url ? "una nuova copertina per quella notizia" : "una nuova copertina per l'ultimo video");
}

// /rassegna [parole o codici]: la rassegna stampa subito. Senza parole la scelta è automatica; con le parole (o i codici /n_… del /radar)
// gli articoli li scegli tu (da 2 a 6) e il primo è il gancio.
async function rassegnaDa(env, chat, arg) {
  const token = String(arg || "").trim().split(/\s+/).filter(Boolean);
  const scelte = [];
  if (token.length) {
    const tutte = await notizie(env);
    for (const p of token) {
      const m = p.match(/^\/?n_([0-9a-f]{10})$/i);
      let a = null;
      if (m) { for (const x of tutte) if ((await codice(x.url)) === m[1].toLowerCase()) { a = x; break; } }
      else a = cerca(tutte, p)[0];
      if (!a) { await rispondi(env, chat, `Non trovo nessuna notizia con «${p}». Scrivi /radar per vedere l'elenco.`); return; }
      if (!scelte.some((s) => s.url === a.url)) scelte.push(a);
    }
    if (scelte.length < 2) { await rispondi(env, chat, "Per la rassegna scelta servono almeno 2 notizie diverse (o nessuna parola per la scelta automatica)."); return; }
    if (scelte.length > 6) scelte.length = 6;
  }
  await eseguiLancio(env, chat, "rassegna-sera.yml", { forza: "si", scelte: scelte.map((a) => a.url).join(" "), gancio: "" },
    scelte.length ? `rassegna con le ${scelte.length} notizie scelte (gancio: «${senzaPrefisso(scelte[0].titolo).slice(0, 60)}»)` : "rassegna stampa con scelta automatica");
}

async function videoDaCodice(env, chat, cod) {
  for (const a of await notizie(env)) if ((await codice(a.url)) === cod) { await lanciaNotizia(env, chat, a); return; }
  await rispondi(env, chat, "Quella notizia non è più nella lista. Scrivi di nuovo /radar.");
}

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

async function codaDi(env, file) {
  const r = await fetch(`https://api.github.com/repos/${env.REPO || REPO_BASE}/actions/workflows/${file}/runs?per_page=10`, {
    headers: { Authorization: `Bearer ${env.GITHUB_TOKEN}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "gpoggi-bot" },
  });
  if (!r.ok) return null;
  const attivi = ((await r.json()).workflow_runs || []).filter((x) => ["in_progress", "queued", "pending", "waiting", "requested"].includes(x.status));
  return { inLavoro: attivi.filter((x) => x.status === "in_progress").length, inAttesa: attivi.filter((x) => x.status !== "in_progress").length };
}

async function eseguiLancio(env, chat, file, inputs, descrizione) {
  let coda = null;
  if (file === "video-automatici.yml") {
    coda = await codaDi(env, file).catch(() => null);
    if (coda && coda.inAttesa >= 1) {
      await rispondi(env, chat, `⏳ Non lancio "${descrizione}": c'è già un video in lavorazione e uno in coda. Riscrivi il comando tra qualche minuto.`);
      return;
    }
  }
  const esito = await lancia(env, file, inputs);
  if (!esito.ok) { await rispondi(env, chat, `⚠️ Non sono riuscito a lanciare "${descrizione}" (GitHub ${esito.stato}).\n${esito.dettaglio}`); return; }
  await rispondi(env, chat, coda && coda.inLavoro >= 1
    ? `🕓 In coda: ${descrizione}. C'è un altro video in lavorazione: parte appena finisce.`
    : `✅ Lanciato: ${descrizione}. Arriva tra qualche minuto.`);
}

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

const normSess = (w) => (w.sessioni || []).map((x) => { const i = Date.parse(x.inizio), f = Date.parse(x.fine); return { nome: x.codice === "PR" ? "Practice" : x.nome, codice: x.codice, i, f: f > i ? f : i + 45 * 60000 }; }).sort((a, b) => a.i - b.i);

function bloccoSessione(icona, serie, weekend, adesso) {
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
const riga = (r, primo, giriVincitore) => {
  if (r.pos == null) return `– ${r.nome} · ritirato${r.giri ? ` dopo ${r.giri}${r.giri === 1 ? "giro" : "giri"}` : " al primo giro"}`;
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
  const f1 = await risultatiF1(env, adesso);
  const a = [`🏎 FORMULA 1${f1.gp ? ` · ${f1.gp}` : ""}`];
  if (f1.sessione) a.push(`Ultima sessione con risultati: ${f1.sessione.nome}`, ...f1.sessione.risultati.map((r, i) => riga(r, i === 0, f1.sessione.nome === "Gara" || f1.sessione.nome === "Sprint" ? (f1.sessione.risultati[0] || {}).giri : 0)));
  else a.push("Nessun risultato disponibile per questo weekend.");
  for (const x of f1.senza) { a.push(`⏳ ${x.nome}: finita alle ${soloOra(Date.parse(x.fine))}, risultati non ancora pubblicati dalla fonte.`); attesa = true; }
  if (f1.ultimaGara && !(f1.sessione && f1.sessione.nome === "Gara")) a.push(`🏁 Ultima gara: ${f1.ultimaGara.gp} · ${podio(f1.ultimaGara.rows)}`);

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

async function invia(env, chat, testoLungo) {
  let blocco = "";
  for (const r of testoLungo.split("\n")) {
    if (blocco.length + r.length + 1 > 3800) { await rispondi(env, chat, blocco); blocco = ""; }
    blocco += (blocco ? "\n" : "") + r;
  }
  if (blocco.trim()) await rispondi(env, chat, blocco);
}

const testo = (s, stato = 200) => new Response(s, { status: stato, headers: { "Content-Type": "text/plain; charset=utf-8" } });

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

export default {
  async fetch(req, env, ctx) {
    const u = new URL(req.url);
    if (req.method === "GET") {
      if (u.pathname === "/stato" || u.pathname === "/attiva") return servizio(req, env, u);
      return testo(`GP Oggi bot: ok · versione ${VERSIONE}`);
    }
    if (req.method !== "POST") return testo("non consentito", 405);
    if (!env.WEBHOOK_SECRET || !uguali(req.headers.get("X-Telegram-Bot-Api-Secret-Token"), env.WEBHOOK_SECRET)) return testo("non autorizzato", 401);
    const update = await req.json().catch(() => ({}));
    const msg = update.message;
    if (!msg || !msg.text) return testo("ok");
    if (String(msg.chat && msg.chat.id) !== String(env.CHAT_ID || CHAT_BASE)) return testo("ok");

    const lavoro = (async () => {
      if (Date.now() / 1000 - (msg.date || 0) > ETA_MASSIMA_SECONDI) return;
      const t = msg.text.trim();
      const comando = t.startsWith("/") ? t.split(/\s+/)[0].toLowerCase().split("@")[0] : "";

      const ses = comando.replace(/^\/sessioni/, "/sessione").replace(/^\/sessione_/, "/sessione");
      if (ses === "/sessione") { await comandoSessione(env, msg.chat.id); return; }
      if (ses === "/sessionerisultati") { await comandoRisultati(env, msg.chat.id); return; }
      if (comando === "/radar" || comando === "/notizie" || comando === "/scegli") { await mostraLista(env, msg.chat.id); return; }

      if (COMANDI[comando]) {
        const [file, inputs, descrizione] = COMANDI[comando];
        await eseguiLancio(env, msg.chat.id, file, inputs, descrizione);
        return;
      }

      if (comando === "/coda") {
        await comandoCoda(env, msg.chat.id);
        return;
      }

      const rs = comando.match(/^\/rassegna(?:_(.*))?$/);
      if (rs) { await rassegnaDa(env, msg.chat.id, rs[1] !== undefined ? rs[1].replace(/_/g, " ") : t.split(/\s+/).slice(1).join(" ")); return; }
      const cp = comando.match(/^\/copertina(?:_(.*))?$/);
      if (cp) { await copertinaDa(env, msg.chat.id, cp[1] !== undefined ? cp[1].replace(/_/g, " ") : t.split(/\s+/).slice(1).join(" ")); return; }
      const nc = comando.match(/^\/n_([0-9a-f]{10})$/);
      if (nc) { await videoDaCodice(env, msg.chat.id, nc[1]); return; }
      const nv = comando.match(/^\/(?:notizia|video)(?:_(.*))?$/);
      if (nv) {
        await videoDa(env, msg.chat.id, nv[1] !== undefined ? nv[1].replace(/_/g, " ") : t.split(/\s+/).slice(1).join(" "));
        return;
      }
      await rispondi(env, msg.chat.id, `Sono sveglio. Comandi:\n${elenco()}`);
    })();
    ctx.waitUntil(lavoro.catch((e) => { console.error(e); return rispondi(env, msg.chat.id, `⚠️ Qualcosa non ha funzionato: riprova tra poco.\n(${String(e && e.message || e).slice(0, 200)})`); }));
    return testo("ok");
  },
};
