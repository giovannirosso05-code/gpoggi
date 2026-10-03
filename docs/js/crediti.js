import { renderHeader, renderFooter, fetchJSON, esc, credito } from "./common.js";

renderHeader("");
renderFooter();

const [roster, eventi] = await Promise.all([fetchJSON("data/roster.json"), fetchJSON("data/events.json")]);
document.getElementById("crediti-piloti").innerHTML = roster.filter((p) => p.foto)
  .map((p) => `<li><strong>${esc(p.nome)}</strong> — ${credito(p.foto)}</li>`).join("");
document.getElementById("crediti-circuiti").innerHTML = eventi.filter((g) => g.mappa)
  .map((g) => `<li><strong>${esc(g.circuito)}</strong> — ${credito(g.mappa, "Mappa")}</li>`).join("");
