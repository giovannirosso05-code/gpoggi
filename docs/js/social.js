import { renderHeader, renderFooter } from "./common.js";

renderHeader("social");
renderFooter();

const SITO = "https://gpoggi.it";
const esito = document.getElementById("soc-esito");
document.getElementById("soc-condividi").addEventListener("click", async () => {
  if (navigator.share) { try { await navigator.share({ title: "GP Oggi", text: "Formula 1 e MotoGP, tutto in un posto", url: SITO }); } catch (e) {} return; }
  copia();
});
document.getElementById("soc-copia").addEventListener("click", copia);
async function copia() {
  try { await navigator.clipboard.writeText(SITO); esito.textContent = "Link copiato: " + SITO; }
  catch (e) { esito.textContent = "Copia il link a mano: " + SITO; }
}
