import { renderHeader, renderFooter, fetchJSON, esc, ICON_SEARCH, erroreCaricamento } from "./common.js";

renderHeader("classifiche");
renderFooter();
document.getElementById("search-icon").innerHTML = ICON_SEARCH;

const box = document.getElementById("storici-box");
let tutti = [], ordine = "titoli";
const intervallo = (a) => (a[0] === a[a.length - 1] ? String(a[0]) : `${a[0]}–${a[a.length - 1]}`);

function disegna() {
  const q = document.getElementById("cerca").value.trim().toLowerCase();
  let l = tutti.filter((p) => !q || [p.nome, p.naz, ...p.team].join(" ").toLowerCase().includes(q));
  const cmp = { titoli: (a, b) => b.titoli - a.titoli || b.vittorie - a.vittorie, vittorie: (a, b) => b.vittorie - a.vittorie, stagioni: (a, b) => b.stagioni.length - a.stagioni.length, nome: (a, b) => a.nome.localeCompare(b.nome, "it") }[ordine];
  l = l.sort((a, b) => cmp(a, b) || a.nome.localeCompare(b.nome, "it"));
  document.getElementById("conta").textContent = `(${l.length})`;
  box.innerHTML = `<div class="table-wrap"><table class="results"><thead><tr><th>Pilota</th><th>Paese</th><th>Titoli</th><th>Vittorie</th><th>Stagioni</th><th>Team</th></tr></thead><tbody>${
    l.slice(0, 300).map((p) => `<tr><td><a href="storico.html?id=${esc(p.id)}" class="link-nome"><strong>${esc(p.nome)}</strong></a></td><td>${esc(p.naz || "n.d.")}</td><td>${p.titoli ? "<b class='accent'>" + p.titoli + "</b>" : "–"}</td><td>${p.vittorie || "–"}</td>
      <td>${p.stagioni.length} <span class="muted">(${intervallo(p.stagioni)})</span></td><td class="team-lungo">${esc(p.team.slice(0, 4).join(", "))}${p.team.length > 4 ? "…" : ""}</td></tr>`).join("")
  }</tbody></table></div>${l.length > 300 ? `<p class="muted" style="font-size:13px">Mostrati i primi 300: restringi la ricerca per vedere gli altri.</p>` : ""}`;
}

try {
  tutti = (await fetchJSON("data/storici.json")).piloti;
  document.getElementById("cerca").addEventListener("input", disegna);
  document.getElementById("ordine").addEventListener("click", (e) => {
    const b = e.target.closest(".pill"); if (!b) return;
    ordine = b.dataset.o; document.querySelectorAll("#ordine .pill").forEach((x) => x.classList.toggle("active", x === b)); disegna();
  });
  disegna();
} catch (e) { erroreCaricamento(box); }
