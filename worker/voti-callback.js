/**
 * Handler callback per i pulsanti Telegram.
 * POST /telegram con {update_id, callback_query: {id, from, message, data}}
 * data = "vota_<url_encoded_url>" → incrementa il voto su KV e risponde "✅ Voto registrato (XX/75)"
 */
export default {
  async fetch(req, env) {
    if (req.method !== "POST") return new Response("OK", {status: 200});
    try {
      const upd = await req.json();
      const cb = upd.callback_query;
      if (!cb || !cb.data.startsWith("vota_")) return new Response("OK", {status: 200});
      
      const url = decodeURIComponent(cb.data.slice(5));
      const key = `voti:${url}`;
      let voti = parseInt(await env.VOTI.get(key) || "0") + 1;
      await env.VOTI.put(key, String(voti), {expirationTtl: 30*86400});
      
      const msg = voti >= 75 ? "✅ Voto registrato! Questa notizia è il video di domani." : `✅ Voto registrato (${voti}/75)`;
      const botToken = env.TELEGRAM_BOT_TOKEN;
      if (botToken && cb.id) {
        await fetch(`https://api.telegram.org/bot${botToken}/answerCallbackQuery`, {
          method: "POST",
          body: JSON.stringify({callback_query_id: cb.id, text: msg, show_alert: false}),
          headers: {"Content-Type": "application/json"}
        });
      }
      return new Response(JSON.stringify({ok: true}), {status: 200});
    } catch (e) {
      console.error(e);
      return new Response(JSON.stringify({ok: false, error: e.message}), {status: 500});
    }
  }
};
