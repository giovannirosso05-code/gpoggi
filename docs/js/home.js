import { renderHeader, renderFooter, fetchJSON, esc, img, credito, intervalloWeekend, formattaData, formattaDataOra, punti, stemma, ND, erroreCaricamento } from "./common.js";

renderHeader("home");
renderFooter();

function hero(eventi, roster) {
  const ora = Date.now();
  const sessioni = eventi.flatMap((g) => g.sessioni.map((s) => ({ ...s, gp: g })))
    .filter((s) => new Date(s.fine).getTime() > ora)
    .sort((a, b) => new Date(a.inizio) - new Date(b.inizio));
  const leader = roster.find((p) => p.posizione === 1 && p.foto) || roster.find((p) => p.foto);
  if (leader) {
    document.getElementById("hero").style.setProperty("--foto", `url("${new URL(leader.foto.file_grande || leader.foto.grande || leader.foto.file || leader.foto.url, document.baseURI).href}")`);
    document.getElementById("hero-credito").innerHTML = `${esc(leader.nome)} · ` + credito(leader.foto);
  }
  const s = sessioni[0];
  if (!s) {
    document.getElementById("hero-kicker").textContent = "Stagione conclusa";
    return;
  }
  document.getElementById("hero-kicker").textContent = s.nome;
  document.getElementById("hero-titolo").textContent = s.gp.nome;
  document.getElementById("hero-sotto").innerHTML = `${esc(s.gp.circuito)}, ${esc(s.gp.paese)} · ${formattaDataOra(s.inizio)} · <a href="gara.html?id=${s.gp.id}">Programma del weekend</a>`;
  const inizio = new Date(s.inizio).getTime();
  const box = document.getElementById("hero-countdown");
  const tick = () => {
    const diff = inizio - Date.now();
    if (diff <= 0) {
      box.innerHTML = `<div><b>${Date.now() < new Date(s.fine).getTime() ? "In corso" : "Conclusa"}</b><span>${esc(s.nome)}</span></div>`;
      return;
    }
    const parti = [[Math.floor(diff / 864e5), "giorni"], [Math.floor(diff / 36e5) % 24, "ore"], [Math.floor(diff / 6e4) % 60, "minuti"], [Math.floor(diff / 1e3) % 60, "secondi"]];
    box.innerHTML = parti.map(([v, l]) => `<div><b>${String(v).padStart(2, "0")}</b><span>${l}</span></div>`).join("");
    setTimeout(tick, 1000);
  };
  tick();
}


function podio(g, foto) {
  const sess = [...g.sessioni].reverse().find((s) => s.tipo === "Race" && s.risultati && s.risultati.length);
  if (!sess) return "";
  const top = sess.risultati.filter((r) => r.pos && r.pos <= 3).sort((a, b) => a.pos - b.pos);
  return `<div class="ultima-gara">
    <div class="ultima-gara-testa">
      <div><span class="kicker">Ultima gara</span><h3>${esc(g.nome)}</h3></div>
      <div class="muted">${esc(g.circuito)}, ${esc(g.paese)} · <a href="gara.html?id=${g.id}" class="accent">Tutti i risultati</a></div>
    </div>
    <div class="podio-home">${top.map((r) => `<a href="pilota.html?n=${r.numero}" style="--team:#${esc(coloreTeam[r.team] || "8b8a92")}">
      <div class="posto">${r.pos}°</div>
      ${foto[r.numero] ? img(foto[r.numero], r.nome || "") : '<span class="vuota"></span>'}
      <strong>${esc(r.nome || "Pilota #" + r.numero)}</strong>
      <div>${stemma(r.team, coloreTeam[r.team])}</div>
      <div class="tempo">${r.tempo ? esc(r.tempo) : ND}</div>
    </a>`).join("")}</div>
  </div>`;
}

let coloreTeam = {};

try {
  const [roster, eventi, standings] = await Promise.all([fetchJSON("data/roster.json"), fetchJSON("data/events.json"), fetchJSON("data/standings.json")]);
  hero(eventi, roster);
  coloreTeam = Object.fromEntries(standings.costruttori.map((c) => [c.team, c.colore]));
  const foto = Object.fromEntries(roster.filter((p) => p.foto).map((p) => [p.numero, p.foto]));

  const ora = new Date();
  const passati = eventi.filter((g) => new Date(g.fine) < ora).reverse();
  for (const ev of passati.slice(0, 3)) {
    const g = await fetchJSON(`data/gare/${ev.id}.json`);
    const html = podio(g, foto);
    if (html) { document.getElementById("ultima-gara").innerHTML = html; break; }
  }

  document.getElementById("riassunto-nota").textContent = standings.dopo ? `Dopo il ${standings.dopo}` : "";
  document.getElementById("top-classifica").innerHTML = standings.piloti.length ? `<div class="table-wrap"><table class="results">
    <thead><tr><th>Pos</th><th>Pilota</th><th>Team</th><th>Punti</th></tr></thead>
    <tbody>${standings.piloti.slice(0, 10).map((p) => `<tr class="${p.posizione <= 3 ? "podio" : ""}"><td>${p.posizione}</td>
      <td><a class="cella-pilota" href="pilota.html?n=${p.numero}">${foto[p.numero] ? img(foto[p.numero], p.nome || "", "foto-mini") : '<span class="foto-mini"></span>'}<strong>${esc(p.nome || "Pilota #" + p.numero)}</strong></a></td>
      <td><span class="cella-team">${stemma(p.team, p.colore)}${esc(p.team || "")}</span></td><td><strong>${punti(p.punti)}</strong></td></tr>`).join("")}</tbody></table></div>` : `<p class="muted">Classifica non ancora disponibile.</p>`;

  document.getElementById("mini-costruttori").innerHTML = standings.costruttori.slice(0, 5).map((c) => `
    <li><a href="classifiche.html"><span class="pos">${c.posizione}</span>${stemma(c.team, c.colore)}<span>${esc(c.team)}</span><span class="pt">${punti(c.punti)}</span></a></li>`).join("");

  try {
    const report = await fetchJSON("data/report.json");
    document.getElementById("ultime-notizie").innerHTML = report.slice(0, 3).map((r) => `
      <a class="evento-widget-mini" href="notizie.html"><div>
        <div class="evento-widget-mini-nome">${esc(r.titolo)}</div>
        <div class="evento-widget-mini-data">${formattaData(r.data)}</div></div></a>`).join("");
  } catch (e) {}

  const prossimi = eventi.filter((g) => new Date(g.fine) > ora).slice(0, 3);
  document.getElementById("prossimi-mini").innerHTML = prossimi.length ? prossimi.map((g) => `
    <a class="evento-widget-mini" href="gara.html?id=${g.id}">
      ${g.mappa ? img(g.mappa, "Tracciato di " + g.circuito) : ""}
      <div><div class="evento-widget-mini-nome">${esc(g.nome)}</div>
      <div class="evento-widget-mini-data">${esc(g.circuito)} · ${intervalloWeekend(g)}</div></div>
    </a>`).join("") : `<p class="muted" style="font-size:12px">Nessun weekend in programma.</p>`;
} catch (e) {
  erroreCaricamento(document.getElementById("ultima-gara"));
}
