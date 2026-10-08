// Votazioni del pronostico: Cloudflare Worker + KV (gratuito). Non è ancora attivo: finché non lo pubblichi i voti restano nel browser.
//
// Come attivarlo:
//   1. Cloudflare → Workers & Pages → Create → Worker, incolla questo file.
//   2. Workers → Settings → Bindings → KV namespace: crea "VOTI" e collegalo al Worker con questo nome.
//   3. Copia l'indirizzo del Worker (https://voti.<nome>.workers.dev) in VOTI_URL, nel file docs/js/common.js.
//
// GET  ?gp=<chiave>              -> { voti: { "Nome Pilota": 12, ... } }
// POST { gp, scelta }            -> registra il voto e restituisce lo stesso conteggio.
// Un voto per indirizzo IP (conservato solo come impronta, per 7 giorni) e per gara: limite contro i voti ripetuti, non una garanzia.
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type" };
const json = (d, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { "Content-Type": "application/json", ...CORS } });
const impronta = async (t) => [...new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t)))].slice(0, 8).map((b) => b.toString(16).padStart(2, "0")).join("");

// Ora di partenza delle gare (file del sito, aggiornato a ogni giro dei dati): serve a chiudere i voti e a tenere nascosto il podio scelto fino al via.
let orariCache = { t: 0, v: null };
async function orariGara() {
  if (orariCache.v && Date.now() - orariCache.t < 300000) return orariCache.v;
  try { const r = await fetch("https://gpoggi.it/data/gara-orari.json", { cf: { cacheTtl: 300 } }); if (r.ok) orariCache = { t: Date.now(), v: await r.json() }; } catch (e) {}
  return orariCache.v || {};
}

// Email per il premio: si toglie il "+alias" e, per Gmail, i punti, così la stessa casella non conta due volte.
function normalizzaEmail(e) {
  const m = String(e || "").trim().toLowerCase().match(/^([^\s@]+)@([^\s@]+\.[^\s@]{2,})$/);
  if (!m || e.length > 80) return null;
  let [, loc, dom] = m;
  loc = loc.split("+")[0];
  if (dom === "googlemail.com") dom = "gmail.com";
  if (dom === "gmail.com") loc = loc.replace(/\./g, "");
  return loc ? loc + "@" + dom : null;
}

export default {
  async fetch(req, env) {
    if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
    const url = new URL(req.url);
    if (req.method === "GET" && url.pathname === "/pronostici") {
      // Tutti i pronostici del gioco "Pronostico del podio" (opzionale ?gp=ID): nome, podio e orario di invio dato dal server
      const gp = (url.searchParams.get("gp") || "").replace(/[^\w-]/g, "").slice(0, 40);
      const prefisso = gp ? `pron:${gp}:` : "pron:";
      const out = [];
      const orari = await orariGara();
      let cursor;
      for (let i = 0; i < 5; i++) {
        const r = await env.VOTI.list({ prefix: prefisso, cursor, limit: 1000 });
        for (const k of r.keys) {
          if (!k.metadata) continue;
          const gara = k.name.split(":")[1], via = orari[gara] ? Date.parse(orari[gara]) : null;
          // prima della partenza il podio scelto non si vede: restano nickname e orario del voto
          if (via && Date.now() >= via) { const { h, ...pubblico } = k.metadata; out.push({ gp: gara, ...pubblico }); }
          else out.push({ gp: gara, nick: k.metadata.nick, ts: k.metadata.ts });
        }
        if (r.list_complete) break;
        cursor = r.cursor;
      }
      return json({ pronostici: out });
    }
    if (req.method === "GET" && url.pathname === "/sospetti") {
      // Solo per chi gestisce il sito: nickname collegati tra loro (stessa connessione o stesso dispositivo). Serve il segreto ADMIN_KEY impostato in Cloudflare.
      if (!env.ADMIN_KEY || url.searchParams.get("k") !== env.ADMIN_KEY) return new Response("non trovato", { status: 404 });
      const perConn = {}, perDisp = {};
      let cursor;
      for (let i = 0; i < 10; i++) {
        const r = await env.VOTI.list({ prefix: "pron:", cursor, limit: 1000 });
        for (const k of r.keys) {
          if (!k.metadata) continue;
          const [, gp, id] = k.name.split(":");
          if (k.metadata.h) ((perConn[k.metadata.h] ||= {})[k.metadata.nick] ||= new Set()).add(gp);
          ((perDisp[id] ||= {})[k.metadata.nick] ||= new Set()).add(gp);
        }
        if (r.list_complete) break;
        cursor = r.cursor;
      }
      const raggruppa = (m, tipo) => Object.entries(m).filter(([, n]) => Object.keys(n).length >= 2).map(([chiave, n]) => ({ tipo, chiave, nickname: Object.entries(n).map(([nick, g]) => ({ nick, gare: g.size })) }));
      return json({ sospetti: [...raggruppa(perDisp, "stesso dispositivo"), ...raggruppa(perConn, "stessa connessione")] });
    }
    if (req.method === "GET" && url.pathname === "/vincitore") {
      // Solo per chi gestisce il sito: email salvata per un nickname (serve ADMIN_KEY). Uso: /vincitore?k=CHIAVE&nick=NICKNAME
      if (!env.ADMIN_KEY || url.searchParams.get("k") !== env.ADMIN_KEY) return new Response("non trovato", { status: 404 });
      const cerca = (url.searchParams.get("nick") || "").trim().toLowerCase();
      const trovati = {};
      let cursor;
      for (let i = 0; i < 10; i++) {
        const r = await env.VOTI.list({ prefix: "pron:", cursor, limit: 1000 });
        for (const k of r.keys) {
          if (!k.metadata || String(k.metadata.nick).toLowerCase() !== cerca) continue;
          const id = k.name.split(":")[2];
          trovati[id] = (await env.VOTI.get(`mail:${id}`)) || null;
        }
        if (r.list_complete) break;
        cursor = r.cursor;
      }
      return json({ nickname: cerca, email: Object.entries(trovati).map(([id, email]) => ({ id, email })) });
    }
    if (req.method === "GET" && url.pathname === "/svincola") {
      // Solo per chi gestisce il sito: libera un'email dal giocatore a cui è collegata (per chi ha perso il codice). Uso: /svincola?k=CHIAVE&email=INDIRIZZO
      if (!env.ADMIN_KEY || url.searchParams.get("k") !== env.ADMIN_KEY) return new Response("non trovato", { status: 404 });
      const em = normalizzaEmail(url.searchParams.get("email"));
      if (!em) return json({ errore: "email non valida" }, 400);
      await env.VOTI.delete(`mailacc:${await impronta(em)}`);
      return json({ ok: true, email: em });
    }
    if (req.method === "GET" && url.pathname === "/valutazione") {
      // Voto medio del sito (da 1 a 5 stelle): { media, voti }
      const a = JSON.parse((await env.VOTI.get("valutazione:totale")) || "{}");
      return json({ media: a.n ? Math.round((a.somma / a.n) * 10) / 10 : null, voti: a.n || 0 });
    }
    if (req.method === "GET" && url.pathname === "/consiglio") return json({ consigli: true });   // il sito lo usa per sapere se il modulo dei consigli funziona
    if (req.method === "GET") {
      const voti_url = url.searchParams.get("voti");
      if (voti_url) {
        // Voti accumulati per una notizia (report giornaliero)
        const chiave = `voti:${voti_url}`;
        const n = parseInt(await env.VOTI.get(chiave) || "0");
        return json({ voti: n, url: voti_url });
      }
      const gp = (url.searchParams.get("gp") || "").slice(0, 80);
      return json({ voti: JSON.parse((await env.VOTI.get("conteggio:" + gp)) || "{}") });
    }
    if (req.method !== "POST") return json({ errore: "metodo non consentito" }, 405);

    // Callback di Telegram: vota_<url_encoded>
    const body = await req.json().catch(() => ({}));
    if (body.callback_query && body.callback_query.data && body.callback_query.data.startsWith("vota_")) {
      const voti_url = decodeURIComponent(body.callback_query.data.slice(5));
      const chiave = `voti:${voti_url}`;
      let count = parseInt(await env.VOTI.get(chiave) || "0") + 1;
      await env.VOTI.put(chiave, String(count), { expirationTtl: 30 * 86400 });
      const botToken = env.TELEGRAM_BOT_TOKEN;
      if (botToken && body.callback_query.id) {
        const msg = count >= 75 ? "✅ Voto registrato! Questa notizia è il video di domani." : `✅ Voto registrato (${count}/75)`;
        fetch(`https://api.telegram.org/bot${botToken}/answerCallbackQuery`, {
          method: "POST",
          body: JSON.stringify({ callback_query_id: body.callback_query.id, text: msg, show_alert: false }),
          headers: { "Content-Type": "application/json" }
        }).catch(() => {});
      }
      return json({ ok: true, voti: count });
    }

    if (url.pathname === "/pronostico") {
      const c = body;
      const gp = String(c.gp || "").replace(/[^\w-]/g, "").slice(0, 40), id = String(c.id || "").replace(/[^\w-]/g, "").slice(0, 40);
      const nick = String(c.nick || "").trim().replace(/\s+/g, " ");
      const podio = Array.isArray(c.podio) ? c.podio.map((x) => String(x).slice(0, 10)) : [];
      if (!gp || id.length < 8 || !/^[\p{L}\p{N} _.-]{3,16}$/u.test(nick) || podio.length !== 3 || new Set(podio).size !== 3) return json({ errore: "dati non validi" }, 400);
      const via = (await orariGara())[gp];
      if (via && Date.now() >= Date.parse(via)) return json({ errore: "votazioni chiuse" }, 403);
      const emailNorm = c.email ? normalizzaEmail(c.email) : null;
      if (c.email && !emailNorm) return json({ errore: "email non valida" }, 400);
      if (emailNorm) {
        // una email = un solo giocatore: se è già collegata a un altro codice, non se ne crea un secondo
        const usata = await env.VOTI.get(`mailacc:${await impronta(emailNorm)}`);
        if (usata && usata !== id) return json({ errore: "email gia collegata a un altro giocatore" }, 409);
      }
      const limite = `limite:pron:${await impronta((req.headers.get("CF-Connecting-IP") || "") + new Date().toISOString().slice(0, 10))}`;
      const n = Number((await env.VOTI.get(limite)) || 0);
      if (n >= 30) return json({ errore: "troppi invii oggi" }, 429);
      await env.VOTI.put(limite, String(n + 1), { expirationTtl: 86400 });
      const chiaveNome = `nick:${gp}:${nick.toLowerCase()}`;
      const occupato = await env.VOTI.get(chiaveNome);
      if (occupato && occupato !== id) return json({ errore: "nome già usato" }, 409);
      await env.VOTI.put(chiaveNome, id, { expirationTtl: 90 * 86400 });
      if (emailNorm) {
        await env.VOTI.put(`mailacc:${await impronta(emailNorm)}`, id, { expirationTtl: 400 * 86400 });
        await env.VOTI.put(`mail:${id}`, emailNorm, { expirationTtl: 400 * 86400 });
      }
      const h = (await impronta((req.headers.get("CF-Connecting-IP") || "") + "|pron")).slice(0, 8);
      await env.VOTI.put(`pron:${gp}:${id}`, "1", { metadata: { nick, podio, ts: Date.now(), h }, expirationTtl: 90 * 86400 });
      return json({ ok: true });
    }
    if (url.pathname === "/valutazione") {
      // Un voto per dispositivo (id casuale conservato nel browser); chi cambia idea sostituisce il voto precedente. Nessun dato personale.
      const c = body;
      const id = String(c.id || "").replace(/[^\w-]/g, "").slice(0, 40), stelle = Math.round(Number(c.stelle));
      if (id.length < 8 || !(stelle >= 1 && stelle <= 5)) return json({ errore: "dati non validi" }, 400);
      const limite = `limite:val:${await impronta((req.headers.get("CF-Connecting-IP") || "") + new Date().toISOString().slice(0, 10))}`;
      const n = Number((await env.VOTI.get(limite)) || 0);
      if (n >= 20) return json({ errore: "troppi voti oggi" }, 429);
      await env.VOTI.put(limite, String(n + 1), { expirationTtl: 86400 });
      const prima = Number((await env.VOTI.get(`valutazione:${id}`)) || 0);
      const a = JSON.parse((await env.VOTI.get("valutazione:totale")) || "{}");
      a.somma = (a.somma || 0) - prima + stelle; a.n = (a.n || 0) + (prima ? 0 : 1);
      await env.VOTI.put(`valutazione:${id}`, String(stelle));
      await env.VOTI.put("valutazione:totale", JSON.stringify(a));
      return json({ media: Math.round((a.somma / a.n) * 10) / 10, voti: a.n });
    }
    if (url.pathname === "/consiglio") {
      // Consigli dei visitatori: solo testo, nessun dato personale. Massimo 3 al giorno per indirizzo; si leggono nel pannello KV di Cloudflare.
      const c = body;
      const testo = typeof c.testo === "string" ? c.testo.trim().slice(0, 600) : "";
      const tipo = ["funzione", "errore", "altro"].includes(c.tipo) ? c.tipo : "altro";
      if (testo.length < 5 || c.sito) return json({ errore: "testo troppo corto" }, 400);
      const chiave = `limite:consiglio:${await impronta((req.headers.get("CF-Connecting-IP") || "") + new Date().toISOString().slice(0, 10))}`;
      const n = Number((await env.VOTI.get(chiave)) || 0);
      if (n >= 3) return json({ errore: "troppi consigli oggi" }, 429);
      await env.VOTI.put(chiave, String(n + 1), { expirationTtl: 86400 });
      await env.VOTI.put(`consiglio:${new Date().toISOString()}:${Math.random().toString(36).slice(2, 6)}`, JSON.stringify({ tipo, testo }), { expirationTtl: 90 * 86400 });
      return json({ ok: true });
    }
    const { gp, scelta } = body;
    if (typeof gp !== "string" || typeof scelta !== "string" || !gp || !scelta || gp.length > 80 || scelta.length > 60) return json({ errore: "dati non validi" }, 400);
    const chiaveIp = `ip:${gp}:${await impronta(req.headers.get("CF-Connecting-IP") || "")}`;
    const conteggio = JSON.parse((await env.VOTI.get("conteggio:" + gp)) || "{}");
    if (!(await env.VOTI.get(chiaveIp))) {
      conteggio[scelta] = (conteggio[scelta] || 0) + 1;
      await env.VOTI.put("conteggio:" + gp, JSON.stringify(conteggio));
      await env.VOTI.put(chiaveIp, "1", { expirationTtl: 7 * 86400 });
    }
    return json({ voti: conteggio });
  },
};
