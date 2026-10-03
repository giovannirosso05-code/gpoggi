# F1 Oggi

Sito statico dedicato alla Formula 1 — database piloti, gare, confronti e statistiche.

**⚠️ Non ufficiale, non affiliato a Formula 1 o FIA.** Vedi [chi-siamo.html](docs/chi-siamo.html) per il disclaimer completo.

Parallelo a **[MMA Oggi](https://mmaoggi.it/)** — stessa struttura e stack, contenuti diversi.

## Stack

- **Frontend:** HTML/CSS/JS puro (no framework)
- **Design:** Palette scura editoriale, font Oswald (titoli) + Inter (testo)
- **Dati:** OpenF1 API (pubblica, gratuita, tempo reale)
- **Hosting:** GitHub Pages (sito statico in `docs/`)
- **Build:** Python genera JSON da OpenF1 → sito carica e visualizza

## Come avviare in locale

```bash
pip install -r requirements.txt
python scraper_f1.py           # scarica da OpenF1 → cache/
python build_data.py           # genera docs/data/
python -m http.server 8000 --directory docs
```

Apri `http://localhost:8000`.

## Architettura

```
scraper_f1.py    → scarica piloti, team, gare da OpenF1 → cache/*.json
build_data.py    → genera JSON statici in docs/data/
docs/            → sito vero (HTML/CSS/JS)
```

### Flusso dati

1. **scraper_f1.py** chiama OpenF1 API, salva raw JSON in `cache/`
2. **build_data.py** legge cache, genera `docs/data/roster.json` e `docs/data/events.json`
3. **Frontend JS** carica i JSON, renderizza liste e confronti
4. **GitHub Pages** serve il sito statico — nessun server Python in produzione

## Pagine

- `index.html` — Home, roster piloti, filtri
- `gare.html` — Calendario gare (prossime e passate)
- `confronto.html` — Confronto tra due piloti
- `chi-siamo.html` — Disclaimer non ufficiale
- Segnaposti per: schede pilota, schede gara, news

## Pubblicare online

### GitHub Pages

1. Crea un repository pubblico (altrimenti GitHub Pages gratis non funziona)
2. Settings → Pages → Source: Deploy from branch → Branch: `main`, cartella: `/docs` → Save
3. Dopo un minuto il sito è live su `https://<user>.github.io/F1-Site/`

### Dominio personalizzato

1. Compra il dominio da un registrar (es. Register.it, Namecheap)
2. Nel registrar, imposta i record DNS puntando a GitHub Pages:
   - `A` record: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `CNAME` (opzionale, alternativa a A): `<user>.github.io`
3. In GitHub, Settings → Pages → Custom domain → inserisci il dominio → Save
4. Aggiungi il dominio in `docs/CNAME`:
   ```
   tuodominio.it
   ```

## OpenF1 API

- **Base URL:** `https://api.openf1.org/v1`
- **Rate limit:** 10 req/sec
- **Endpoints principali:**
  - `/seasons` → anni disponibili
  - `/drivers?season_year=2024` → piloti
  - `/teams?season_year=2024` → team
  - `/meetings?season_year=2024` → gare
  - `/sessions?meeting_key=...` → sessioni (FP1, Q, R, ecc.)

**Documentazione:** https://openf1.org/

## Roadmap (non implementato)

1. **Schede dettaglio pilota** — biografia, foto, record completo
2. **Schede dettaglio gara** — risultati sessione per sessione
3. **Classifiche** — costruttori e piloti (in tempo reale se OpenF1 le fornisce)
4. **Statistiche avanzate** — tempi giro, settori, comparativi
5. **News** — feed RSS riscritti in italiano (come FightItalia)
6. **Light mode** — supporto tema chiaro (CSS già ha le variabili)

## SEO e meta tag

- Meta tag Open Graph statici per home/pagine
- JSON-LD (schema.org) per pagine dettaglio (quando implementate)
- Sitemap XML + robots.txt
- Analytics: Plausible.io (privacy-first, no cookie)

## Legale

Vedi [docs/chi-siamo.html](docs/chi-siamo.html) per il disclaimer completo.

**Tl;dr:** Questo è un sito fan non ufficiale. Formula 1, F1, e i relativi loghi sono proprietà di Formula 1 World Championship Limited. Usiamo dati pubblici da OpenF1 solo per scopi informativi.

## Contatti / Issues

Se trovi bug o hai suggerimenti, apri un issue su GitHub.

---

**Basato su:** [FightItalia](https://github.com/gr-build/fightitalia) — stesso branding, stessa struttura, stesso stack, diversi contenuti.
