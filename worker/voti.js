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

export default {
  async fetch(req, env) {
    if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
    const url = new URL(req.url);
    if (req.method === "GET" && url.pathname === "/pronostici") {
      // Tutti i pronostici del gioco "Pronostico del podio" (opzionale ?gp=ID): nome, podio e orario di invio dato dal server
      const gp = (url.searchParams.get("gp") || "").replace(/[^\w-]/g, "").slice(0, 40);
      const prefisso = gp ? `pron:${gp}:` : "pron:";
      const out = [];
      let cursor;
      for (let i = 0; i < 5; i++) {
        const r = await env.VOTI.list({ prefix: prefisso, cursor, limit: 1000 });
        for (const k of r.keys) if (k.metadata) out.push({ gp: k.name.split(":")[1], ...k.metadata });
        if (r.list_complete) break;
        cursor = r.cursor;
      }
      return json({ pronostici: out });
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
      const c = await req.json().catch(() => ({}));
      const gp = String(c.gp || "").replace(/[^\w-]/g, "").slice(0, 40), id = String(c.id || "").replace(/[^\w-]/g, "").slice(0, 40);
      const nick = String(c.nick || "").trim().replace(/\s+/g, " ");
      const podio = Array.isArray(c.podio) ? c.podio.map((x) => String(x).slice(0, 10)) : [];
      if (!gp || id.length < 8 || !/^[\p{L}\p{N} _.-]{3,16}$/u.test(nick) || podio.length !== 3 || new Set(podio).size !== 3) return json({ errore: "dati non validi" }, 400);
      const limite = `limite:pron:${await impronta((req.headers.get("CF-Connecting-IP") || "") + new Date().toISOString().slice(0, 10))}`;
      const n = Number((await env.VOTI.get(limite)) || 0);
      if (n >= 30) return json({ errore: "troppi invii oggi" }, 429);
      await env.VOTI.put(limite, String(n + 1), { expirationTtl: 86400 });
      const chiaveNome = `nick:${gp}:${nick.toLowerCase()}`;
      const occupato = await env.VOTI.get(chiaveNome);
      if (occupato && occupato !== id) return json({ errore: "nome già usato" }, 409);
      await env.VOTI.put(chiaveNome, id, { expirationTtl: 90 * 86400 });
      await env.VOTI.put(`pron:${gp}:${id}`, "1", { metadata: { nick, podio, ts: Date.now() }, expirationTtl: 90 * 86400 });
      return json({ ok: true });
    }
    if (url.pathname === "/consiglio") {
      // Consigli dei visitatori: solo testo, nessun dato personale. Massimo 3 al giorno per indirizzo; si leggono nel pannello KV di Cloudflare.
      const c = await req.json().catch(() => ({}));
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
    const { gp, scelta } = await req.json().catch(() => ({}));
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
