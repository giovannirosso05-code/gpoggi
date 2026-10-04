# Video di resoconto: idee da usare nei prossimi video

Il primo video (Gran Premio del Bahrain, 4 ottobre 2026) è stato fatto con `voce_resoconto.py`:
voce sintetica italiana (edge-tts, voce it-IT-DiegoNeural), schermate 1080x1920 renderizzate con
Playwright e montaggio con ffmpeg. Gli orari vanno sempre dati anche in ora italiana (Europe/Rome).
Le foto dei piloti vengono da `docs/img/foto/` (Wikimedia Commons): nel video va sempre scritto
autore e licenza. I percorsi nello script puntano alla cartella di lavoro e vanno adattati.

## Cosa raccontare (solo cose verificabili dai dati OpenF1)
- Ritardo di partenza: `race_control` (DELAYED START, RACE WILL START AT ...), confrontato con `date_start` della sessione.
- Pioggia: `weather` (campo rainfall) e messaggi `race_control` (RISK OF RAIN, TRACK SURFACE SLIPPERY).
- Safety car / VSC: `race_control` categoria SafetyCar, con numero di giro.
- Incidenti e penalità: `race_control` (INCIDENT ... NOTED, PENALTY, UNDER INVESTIGATION).
- Chi ha guadagnato e perso posizioni: endpoint `position` (ultima posizione prima del via contro la classifica finale).
- Ritiri con il giro: `giri` completati nel risultato di gara (stato RIT).
- Un pilota in zona podio che si ferma nel finale: serie `position` del pilota.

## Esempio dal Bahrain (da riusare come traccia)
- Russell: partito 7°, 2° al primo giro, sul podio per quasi tutta la gara, poi fermo al giro 50 su 55.
- Lindblad da 22° a 10°, Colapinto da 21° a 13°.
- Albon ritirato al giro 42, Bottas all'8°.

## Da non fare
- Non scrivere la causa di un ritiro o commenti sulle gomme se non c'è una fonte verificabile.
- Non usare foto senza credito in video.
