"""Pagine statiche «orari italiani» per ogni Gran Premio (F1 e MotoGP) + indice, per farsi trovare su Google.

Il testo sta già nell'HTML (non serve JavaScript): chi cerca «orari GP Singapore ora italiana» trova gli orari subito.
Legge docs/data/events.json (F1), docs/data/motogp.json (MotoGP, prossimi weekend) e docs/data/gare/<id>.json (podio dei GP già corsi).
Scrive docs/orari-f1-<paese>-2026.html, docs/orari-motogp-<paese>-2026.html e docs/orari-gp.html, e aggiorna docs/sitemap.xml.
Uso:  python build_pagine_gp.py
"""
import html
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

QUI = Path(__file__).parent
DOCS = QUI / "docs"
DATA = DOCS / "data"
ROMA = ZoneInfo("Europe/Rome")
SITO = "https://gpoggi.it"
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
esc = html.escape

# Diritti TV in Italia: scritto in modo generico e senza promettere orari (cambiano di gara in gara), con invito a controllare il palinsesto.
DOVE_F1 = ("Tutte le sessioni (prove libere, qualifiche, sprint e gara) sono in diretta su Sky Sport F1 e in streaming su NOW. "
           "In chiaro su TV8 vanno in diretta le sprint, mentre la gara della domenica è di solito in differita (con eccezioni, come il Gran Premio d'Italia a Monza). "
           "I palinsesti cambiano: prima del weekend controlla quello ufficiale di Sky e di TV8.")
DOVE_MOTO = ("Tutte le gare sono in diretta su Sky Sport MotoGP e in streaming su NOW. "
             "In chiaro su TV8 vanno in diretta le Sprint, mentre la gara della domenica è di solito in differita (con alcune eccezioni, come Mugello e Misano). "
             "I palinsesti cambiano: prima del weekend controlla quello ufficiale di Sky e di TV8.")


def slug(testo):
    t = unicodedata.normalize("NFKD", testo).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def roma(iso):
    return datetime.fromisoformat(iso).astimezone(ROMA)


def data_it(d, anno=True):
    return f"{d.day} {MESI[d.month - 1]}" + (f" {d.year}" if anno else "")


def breve(nome, serie):
    """«Gran Premio di Singapore» -> «GP di Singapore»; «GP Australia» resta così."""
    n = re.sub(r"^Gran Premio", "GP", nome)
    return n


def paese_chiave(nome):
    n = re.sub(r"^(Gran Premio|GP)\s+(d'|di |del |dell'|degli |della )?", "", nome, flags=re.I)
    return slug(n)


def righe_sessioni(sessioni):
    out = []
    for s in sessioni:
        if not s.get("inizio"):
            continue
        d = roma(s["inizio"])
        out.append(f"<tr><td>{GIORNI[d.weekday()].capitalize()} {d.day} {MESI[d.month - 1]}</td><td><strong>{d:%H:%M}</strong></td><td>{esc(s['nome'])}</td></tr>")
    return "\n".join(out)


def podio(id_gp):
    try:
        g = json.load(open(DATA / "gare" / f"{id_gp}.json"))
    except Exception:
        return None
    gara = next((s for s in g.get("sessioni", []) if s["nome"] == "Gara" and s.get("risultati")), None)
    if not gara:
        return None
    top = [r for r in gara["risultati"] if r.get("pos") in (1, 2, 3)]
    top.sort(key=lambda r: r["pos"])
    return top if len(top) == 3 else None


def pagina(titolo, descr, h1, kicker, corpo, url, json_ld):
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>try{{var t=null,q=/[?&]tema=(light|dark)/.exec(location.search);if(q)t=q[1];try{{if(t)localStorage.setItem("tema",t);else t=localStorage.getItem("tema")}}catch(e){{}}if(!t){{var m=/(?:^|;)gpoggi-tema=(light|dark)/.exec(window.name);t=m&&m[1]}}document.documentElement.dataset.theme=t||"light"}}catch(e){{document.documentElement.dataset.theme="light"}}</script>
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" sizes="96x96" href="/img/favicon-96.png?v=3">
<link rel="icon" type="image/png" sizes="192x192" href="/img/favicon-192.png?v=3">
<link rel="apple-touch-icon" href="/img/apple-touch-icon.png?v=3">
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#f5f4f0">
<title>{esc(titolo)}</title>
<meta name="description" content="{esc(descr)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="GP Oggi">
<meta property="og:title" content="{esc(titolo)}">
<meta property="og:description" content="{esc(descr)}">
<meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600&family=Press+Start+2P&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css?v=129">
<!-- Statistiche senza cookie, Plausible -->
<script async src="https://plausible.io/js/pa-ZWqatc_5BB5FuQLCJYeLj.js"></script>
<script>window.plausible=window.plausible||function(){{(plausible.q=plausible.q||[]).push(arguments)}},plausible.init=plausible.init||function(i){{plausible.o=i||{{}}}};plausible.init()</script>
<link rel="canonical" href="{SITO}/{url}">
{('<script type="application/ld+json">' + json.dumps(json_ld, ensure_ascii=False) + '</script>') if json_ld else ''}
</head>
<body>

<header id="site-header" class="site-header"></header>

<div class="container">
  <main>
    <span class="kicker">{esc(kicker)}</span>
    <h1>{esc(h1)}</h1>
{corpo}
  </main>
</div>

<footer id="site-footer" class="site-footer"></footer>

<script type="module">
import {{ renderHeader, renderFooter }} from "./js/common.js";
renderHeader("gare");
renderFooter();
</script>
</body>
</html>
"""


def pagina_gp(ev, serie):
    nome = breve(ev["nome"], serie)
    sess = [s for s in ev["sessioni"] if s.get("inizio")]
    gara = next((s for s in sess if s["nome"] == "Gara"), sess[-1] if sess else None)
    if not gara:
        return None
    anno = roma(gara["inizio"]).year
    d_gara = roma(gara["inizio"])
    etichetta = "F1" if serie == "f1" else "MotoGP"
    prefisso = "orari-f1" if serie == "f1" else "orari-motogp"
    file = f"{prefisso}-{paese_chiave(ev['nome'])}-{anno}.html"
    inizio = roma(sess[0]["inizio"])
    titolo = f"{etichetta} {nome} {anno}: orari italiani, dove vederlo e risultati | GP Oggi"
    descr = (f"{nome} {anno} di {etichetta}: tutti gli orari in ora italiana (prove, qualifiche"
             f"{', sprint' if any('print' in s['nome'] for s in sess) else ''} e gara), dove vederlo in TV e in streaming, e il podio.")
    luogo = ev.get("circuito") or ""
    localita = ev.get("localita") or ev.get("paese") or ""
    p = podio(ev.get("id")) if serie == "f1" else None
    paese = ev.get("paese") or ""
    if serie == "f1":
        citta = localita or luogo
        dove = f"a {esc(citta)}" + (f" ({esc(paese)})" if paese and paese not in citta else "")
    else:
        dove = f"sul circuito {esc(luogo)}" + (f" ({esc(paese)})" if paese and paese not in luogo else "")
    corpo = [f'    <p>Il {esc(nome)} di {etichetta} {anno} si corre {dove}. '
             f'La gara parte <strong>{GIORNI[d_gara.weekday()]} {data_it(d_gara, False)} alle {d_gara:%H:%M}</strong> (ora italiana). Il weekend inizia {GIORNI[inizio.weekday()]} {data_it(inizio, False)}.</p>',
             '    <h2>Orari in ora italiana</h2>',
             f'    <div class="table-wrap"><table class="results"><thead><tr><th>Giorno</th><th>Ora</th><th>Sessione</th></tr></thead><tbody>\n{righe_sessioni(sess)}\n    </tbody></table></div>',
             '    <p class="muted">Gli orari sono quelli ufficiali convertiti in ora italiana (Europa/Roma) e possono cambiare: li aggiorniamo ogni 6 ore circa.</p>',
             '    <h2>Dove vederlo in TV e in streaming</h2>',
             f'    <p>{esc(DOVE_F1 if serie == "f1" else DOVE_MOTO)}</p>']
    if p:
        corpo += [f'    <h2>Podio del {esc(nome)} {anno}</h2>',
                  '    <ol>' + "".join(f'<li><strong>{esc(r["nome"])}</strong> ({esc(r["team"])}){(", " + esc(r["tempo"])) if r.get("tempo") and r["pos"] == 1 else ""}</li>' for r in p) + '</ol>']
    if serie == "f1":
        corpo.append(f'    <p><a class="accent" href="gara.html?id={ev["id"]}">Risultati completi e programma del weekend →</a> · <a class="accent" href="pagella.html">Pagella dei piloti →</a> · <a class="accent" href="orari-gp.html">Tutti gli orari →</a></p>')
    else:
        corpo.append('    <p><a class="accent" href="motogp.html">Classifica e risultati MotoGP →</a> · <a class="accent" href="pagella.html">Pagella dei piloti →</a> · <a class="accent" href="orari-gp.html">Tutti gli orari →</a></p>')
    ld = {"@context": "https://schema.org", "@type": "SportsEvent", "name": f"{nome} {anno} ({etichetta})", "startDate": sess[0]["inizio"], "endDate": gara.get("fine") or gara["inizio"],
          "location": {"@type": "Place", "name": luogo or localita, "address": ev.get("paese") or localita}, "sport": "Motorsport", "url": f"{SITO}/{file}"}
    h1 = f"{etichetta} {nome} {anno}: orari italiani"
    kicker = f"{etichetta} · {data_it(inizio, False)} – {data_it(d_gara, False)}"
    return file, pagina(titolo, descr, h1, kicker, "\n".join(corpo), file, ld), (d_gara, etichetta, nome, file)


def main():
    voci = []
    for ev in json.load(open(DATA / "events.json")):
        r = pagina_gp(ev, "f1")
        if r:
            voci.append(r)
    try:
        for w in json.load(open(DATA / "motogp.json"))["weekend"]:
            r = pagina_gp({"nome": w["nome"], "circuito": w.get("circuito"), "paese": w.get("paese"), "sessioni": w.get("sessioni", [])}, "motogp")
            if r:
                voci.append(r)
    except Exception as e:
        print("MotoGP non incluso:", e)
    for file, testo, _ in voci:
        (DOCS / file).write_text(testo, encoding="utf-8")
    # indice
    ora = datetime.now(ROMA)
    voci.sort(key=lambda v: v[2][0])
    prossimi = [v for v in voci if v[2][0] >= ora]
    passati = [v for v in voci if v[2][0] < ora]
    def lista(vs):
        return "<ul>" + "".join(f'<li><a class="accent" href="{f}">{esc(n)} ({e})</a> — gara {GIORNI[d.weekday()]} {data_it(d, False)} alle {d:%H:%M}</li>' for (f, _, (d, e, n, f2)) in [(v[0], v[1], v[2]) for v in vs]) + "</ul>"
    corpo = ['    <p>Tutti gli orari dei Gran Premi di Formula 1 e MotoGP in ora italiana, con dove vederli in TV e in streaming. Scegli il weekend:</p>',
             '    <h2>Prossimi Gran Premi</h2>', lista(prossimi) if prossimi else '    <p class="muted">Nessun weekend in programma.</p>',
             '    <h2>Già corsi</h2>', lista(passati[::-1])]
    (DOCS / "orari-gp.html").write_text(pagina("Orari GP F1 e MotoGP in ora italiana: calendario e dove vederli | GP Oggi",
                                               "Orari di tutti i Gran Premi di Formula 1 e MotoGP in ora italiana: prove, qualifiche, sprint e gara, e dove vederli in TV e in streaming.",
                                               "Orari dei GP in ora italiana", "Formula 1 e MotoGP", "\n".join(corpo), "orari-gp.html", None), encoding="utf-8")
    # sitemap: si tolgono le vecchie voci «orari-» e si aggiungono le nuove
    sm = DOCS / "sitemap.xml"
    s = sm.read_text(encoding="utf-8")
    s = re.sub(r"\s*<url><loc>https://gpoggi\.it/orari-[^<]*</loc></url>", "", s)
    nuove = "".join(f"\n  <url><loc>{SITO}/{f}</loc></url>" for f in ["orari-gp.html"] + [v[0] for v in voci])
    s = s.replace("</urlset>", nuove.lstrip("\n") + "\n</urlset>")
    sm.write_text(s, encoding="utf-8")
    print(f"Pagine orari: {len(voci)} + indice")


if __name__ == "__main__":
    main()
