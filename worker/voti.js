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
    if (req.method === "GET") {
      const gp = (url.searchParams.get("gp") || "").slice(0, 80);
      return json({ voti: JSON.parse((await env.VOTI.get("conteggio:" + gp)) || "{}") });
    }
    if (req.method !== "POST") return json({ errore: "metodo non consentito" }, 405);
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
