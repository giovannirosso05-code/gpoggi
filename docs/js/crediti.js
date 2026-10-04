import { renderHeader, renderFooter, fetchJSON, esc, credito } from "./common.js";

renderHeader("");
renderFooter();

const [roster, eventi, fm, mm, fs] = await Promise.all([fetchJSON("data/roster.json"), fetchJSON("data/events.json"), fetchJSON("data/foto-motogp.json").catch(() => ({})), fetchJSON("data/mappe-motogp.json").catch(() => ({})), fetchJSON("data/foto-storici.json").catch(() => [])]);
document.getElementById("crediti-piloti").innerHTML = roster.filter((p) => p.foto)
  .map((p) => `<li><strong>${esc(p.nome)}</strong> — ${credito(p.foto)}</li>`).join("");
document.getElementById("crediti-circuiti").innerHTML = eventi.filter((g) => g.mappa)
  .map((g) => `<li><strong>${esc(g.circuito)}</strong> — ${credito(g.mappa, "Mappa")}</li>`).join("");

const li = (nome, f, cosa) => `<li><strong>${esc(nome)}</strong> — ${credito(f, cosa)}</li>`;
document.getElementById("crediti-piloti").innerHTML += Object.entries(fm).filter(([k]) => k.startsWith("nome:")).map(([k, f]) => li(k.slice(5), f)).join("")
  + fs.map((p) => li(p.nome, p.foto)).join("");
document.getElementById("crediti-circuiti").innerHTML += Object.entries(mm).map(([n, f]) => li(n, f, "Mappa")).join("");
