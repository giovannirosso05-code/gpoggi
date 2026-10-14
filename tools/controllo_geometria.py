"""Controllo di rigore geometrico del sito: apre ogni pagina a più larghezze (telefono, tablet, computer) e segnala
  1. scorrimento orizzontale della pagina o elementi che escono dallo schermo
  2. testi tagliati (puntini di sospensione o contenuto più largo della scatola)
  3. immagini rotte
  4. schede della stessa riga con altezze o allineamenti diversi (griglie di schede, podi, card)
  5. elementi che si sovrappongono dentro le card
Uso:  python3 tools/controllo_geometria.py [pagina.html ...] [--larghezze 360,390,768,1280]
Esce con codice 1 se trova errori: da lanciare prima di ogni pubblicazione del sito.
"""
import argparse, asyncio, json, subprocess, sys, time
from pathlib import Path
from playwright.async_api import async_playwright

DOCS = Path(__file__).resolve().parent.parent / "docs"
PORTA = 8771
GRIGLIE = [".driver-card", ".podio-home a", ".pross-card", ".hero2-lato", ".prono-col", ".ultima-gara", ".stat-card", ".card"]

JS = r"""
(griglie) => {
  const out = [];
  const W = document.documentElement.clientWidth;
  const nome = (e) => e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\s+/).slice(0, 2).join('.') : '');
  if (document.documentElement.scrollWidth > W + 1) out.push(['scroll-orizzontale', `la pagina è larga ${document.documentElement.scrollWidth}px su ${W}px`]);
  document.querySelectorAll('body *').forEach((e) => {
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    if (!r.width || !r.height || cs.visibility === 'hidden' || cs.display === 'none') return;
    if (e.closest('nav, .nav, .menu, .pills, .tabella-scroll, table, .scroll-x, [data-scroll], .gara-tabs, .tabs, .filtri, header')) return;
    // contenuti dentro un contenitore che scorre di lato di proposito (carosello di schede): non sono fuori schermo
    let sc = e.parentElement, inScorrimento = false;
    while (sc && sc !== document.body) { const o = getComputedStyle(sc).overflowX; if ((o === 'auto' || o === 'scroll') && sc.scrollWidth > sc.clientWidth + 1) { inScorrimento = true; break; } sc = sc.parentElement; }
    if (inScorrimento) return;
    if (r.right < -500) return;   // elementi nascosti di proposito fuori schermo (campi per l'accessibilità)
    if ((r.right > W + 1 || r.left < -1) && cs.position !== 'fixed' && !e.closest('[style*="overflow"]')) out.push(['fuori-schermo', nome(e) + ` ${Math.round(r.left)}→${Math.round(r.right)}`]);
    if (cs.textOverflow === 'ellipsis' && e.scrollWidth > e.clientWidth + 1) out.push(['testo-tagliato', nome(e) + ' «' + e.textContent.trim().slice(0, 40) + '»']);
    if (e.tagName === 'IMG' && e.complete && e.naturalWidth === 0 && e.src) out.push(['immagine-rotta', e.src.slice(-60)]);
  });
  // schede della stessa riga: stessa altezza e stessa posizione verticale
  griglie.forEach((sel) => {
    const els = [...document.querySelectorAll(sel)].filter((e) => e.getBoundingClientRect().width > 40 && getComputedStyle(e).display !== 'none');
    const righe = {};
    els.forEach((e) => { const y = Math.round(e.getBoundingClientRect().top / 4); (righe[y] = righe[y] || []).push(e); });
    Object.values(righe).forEach((riga) => {
      if (riga.length < 2) return;
      const alt = riga.map((e) => Math.round(e.getBoundingClientRect().height));
      const top = riga.map((e) => Math.round(e.getBoundingClientRect().top));
      if (Math.max(...alt) - Math.min(...alt) > 2) out.push(['altezze-diverse', `${sel}: ${alt.join(' / ')}px`]);
      if (Math.max(...top) - Math.min(...top) > 2) out.push(['non-allineate', `${sel}: top ${top.join(' / ')}`]);
      // all'interno: i testi corrispondenti devono stare alla stessa altezza (es. squadra e punti nelle schede pilota)
      const figli = riga.map((e) => [...e.querySelectorAll('.team, .numero, .tempo, .pross-timer, .pross-sess')].map((x) => Math.round(x.getBoundingClientRect().top - e.getBoundingClientRect().top)));
      const n = Math.min(...figli.map((f) => f.length));
      for (let i = 0; i < n; i++) { const v = figli.map((f) => f[i]); if (Math.max(...v) - Math.min(...v) > 2) out.push(['interno-disallineato', `${sel} elemento ${i + 1}: ${v.join(' / ')}px`]); }
    });
  });
  // sovrapposizioni tra testi fratelli dentro le card
  document.querySelectorAll('.hero2-lato, .driver-card-info, .pross-card, .ultima-gara').forEach((c) => {
    const f = [...c.children].filter((x) => x.getBoundingClientRect().height > 4 && getComputedStyle(x).position !== 'absolute');
    for (let i = 0; i < f.length - 1; i++) { const a = f[i].getBoundingClientRect(), b = f[i + 1].getBoundingClientRect(); if (a.bottom > b.top + 2 && a.top < b.bottom - 2 && a.left < b.right && b.left < a.right) out.push(['sovrapposti', nome(c) + ': ' + nome(f[i]) + ' e ' + nome(f[i + 1])]); }
  });
  return out;
}
"""


async def main():
    ap = argparse.ArgumentParser(); ap.add_argument("pagine", nargs="*"); ap.add_argument("--larghezze", default="360,390,768,1280")
    a = ap.parse_args()
    pagine = a.pagine or sorted(p.name for p in DOCS.glob("*.html") if p.name not in ("admin-gp-oggi.html", "formule.html"))
    larghezze = [int(x) for x in a.larghezze.split(",")]
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORTA)], cwd=DOCS, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    errori = 0
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(**({"executable_path": "/opt/pw-browsers/chromium"} if Path("/opt/pw-browsers/chromium").exists() else {}), args=["--no-sandbox"])
            for w in larghezze:
                pg = await b.new_page(viewport={"width": w, "height": 900})
                for n in pagine:
                    try:
                        await pg.goto(f"http://localhost:{PORTA}/{n}", wait_until="networkidle", timeout=40000); await pg.wait_for_timeout(900)
                        res = await pg.evaluate(JS, GRIGLIE)
                    except Exception as e:
                        res = [("errore-apertura", str(e)[:80])]
                    visti = set()
                    for tipo, det in res:
                        k = (tipo, det)
                        if k in visti: continue
                        visti.add(k); errori += 1
                        print(f"{w:>5}px  {n:<22} {tipo:<20} {det}")
                await pg.close()
            await b.close()
    finally:
        srv.terminate()
    print(f"\n{errori} segnalazioni su {len(pagine)} pagine x {len(larghezze)} larghezze")
    sys.exit(1 if errori else 0)


asyncio.run(main())
