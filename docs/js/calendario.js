import { renderHeader, renderFooter, fetchJSON } from "./common.js";

renderHeader("gare");
renderFooter();

try {
  const [eventi, moto] = await Promise.all([fetchJSON("data/events.json"), fetchJSON("data/motogp.json")]);
  const nf = eventi.reduce((n, g) => n + g.sessioni.length, 0), nm = moto.weekend.reduce((n, w) => n + w.sessioni.length, 0);
  document.getElementById("n-f1").textContent = `${eventi.length} weekend, ${nf} sessioni.`;
  document.getElementById("n-moto").textContent = `${moto.weekend.length} weekend da disputare, ${nm} sessioni.`;
  document.getElementById("n-tutto").textContent = `${nf + nm} sessioni in un solo calendario.`;
} catch (e) {}
