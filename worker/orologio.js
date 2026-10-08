// Orologio di GP Oggi: Cloudflare Worker (gratuito) che fa partire i video e i controlli a orario esatto.
// Perché: i giri programmati di GitHub Actions a volte non partono per ore (o non partono affatto). Qui c'è un solo
// orario ("ogni 15 minuti") e il Worker decide cosa lanciare guardando l'ora italiana, poi chiede a GitHub di avviare il lavoro.
//
// Come attivarlo (circa 10 minuti, una volta sola):
//   1. GitHub → Settings (del tuo profilo) → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token.
//      Repository access: "Only select repositories" → solo gpoggi. Permissions → Repository permissions → "Actions": Read and write.
//      Scadenza: 1 anno. Copia il token (inizia con github_pat_…).
//   2. Cloudflare → Workers & Pages → Create → Worker → nome "gpoggi-orologio" → Deploy → Edit code → incolla questo file → Deploy.
//   3. Worker → Settings → Variables and Secrets → Add → tipo "Secret": nome GH_TOKEN, valore il token del punto 1 (mai in chat, mai in un file).
//   4. Worker → Settings → Triggers → Cron Triggers → Add → "*/15 * * * *" (ogni 15 minuti, ora UTC).
//   5. (facoltativo, per provare) Secret CHIAVE con una parola a caso lunga: poi apri
//      https://gpoggi-orologio.<tuo-nome>.workers.dev/prova?k=CHIAVE&w=video-maratona.yml  e deve rispondere "ok 204".
// Quando funziona, i giri programmati di GitHub vanno spenti (altrimenti i video escono doppi): me lo dici e li tolgo io.

const REPO = "giovannirosso05-code/gpoggi";
const RAMO = "main";

// Cosa lanciare e quando: g = giorno (Mon…Sun), h = ora italiana (0-23), m = minuto (0, 15, 30, 45).
const REGOLE = [
  { nome: "notizie del giorno", file: "video-automatici.yml", inputs: { cosa: "notizie" }, quando: (g, h, m) => h === 12 && m === 0 },
  { nome: "pronostico del giovedì", file: "video-automatici.yml", inputs: { cosa: "previsioni" }, quando: (g, h, m) => g === "Thu" && h === 19 && m === 0 },
  { nome: "video del venerdì", file: "video-venerdi.yml", quando: (g, h, m) => g === "Fri" && h === 9 && m === 15 },
  // maratona: ogni due ore dalle 8 alle 22 (il flusso si spegne da solo alla sua scadenza)
  { nome: "maratona di notizie", file: "video-maratona.yml", quando: (g, h, m) => h >= 8 && h <= 22 && h % 2 === 0 && m === 15 },
  // risultati veloci: ogni 15 minuti da venerdì a domenica e il lunedì mattina; il flusso controlla da solo se è finita una sessione
  { nome: "risultati del weekend", file: "risultati-weekend.yml", quando: (g, h) => ["Fri", "Sat", "Sun"].includes(g) || (g === "Mon" && h <= 7) },
];

function oraItalia(ms) {
  const p = Object.fromEntries(new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Rome", weekday: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23" })
    .formatToParts(new Date(ms)).map((x) => [x.type, x.value]));
  return { g: p.weekday, h: Number(p.hour), m: Number(p.minute) };
}

async function lancia(env, file, inputs) {
  const r = await fetch(`https://api.github.com/repos/${REPO}/actions/workflows/${file}/dispatches`, {
    method: "POST",
    headers: { Authorization: `Bearer ${env.GH_TOKEN}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "gpoggi-orologio", "Content-Type": "application/json" },
    body: JSON.stringify({ ref: RAMO, ...(inputs ? { inputs } : {}) }),
  });
  return r.status;   // 204 = partito
}

export default {
  async scheduled(event, env, ctx) {
    const { g, h, m } = oraItalia(event.scheduledTime);
    for (const r of REGOLE) {
      if (!r.quando(g, h, m)) continue;
      ctx.waitUntil(lancia(env, r.file, r.inputs).then((s) => console.log(`${r.nome}: ${s}`)).catch((e) => console.log(`${r.nome}: errore ${e}`)));
    }
  },
  // prova a mano (solo se è impostata la chiave CHIAVE): /prova?k=CHIAVE&w=video-maratona.yml[&cosa=notizie]
  async fetch(req, env) {
    const u = new URL(req.url);
    if (u.pathname !== "/prova" || !env.CHIAVE || u.searchParams.get("k") !== env.CHIAVE) return new Response("non trovato", { status: 404 });
    const file = u.searchParams.get("w") || "";
    if (!REGOLE.some((r) => r.file === file)) return new Response("flusso non valido", { status: 400 });
    const cosa = u.searchParams.get("cosa");
    const s = await lancia(env, file, cosa ? { cosa } : undefined);
    return new Response(s === 204 ? "ok 204" : `errore ${s}`, { status: s === 204 ? 200 : 502 });
  },
};
