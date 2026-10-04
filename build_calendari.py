"""Calendari scaricabili (.ics) con F1 e MotoGP: docs/calendario/{f1,motogp,tutto}.ics.

Gli orari sono in UTC: l'app del calendario li mostra nel fuso di chi li apre (in Italia, ora italiana).
Per abbonarsi e ricevere gli aggiornamenti: webcal://gpoggi.it/calendario/f1.ics (serve il sito pubblicato).
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "docs" / "data"
OUT = ROOT / "docs" / "calendario"


def utc(s):
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def fmt(d):
    return d.strftime("%Y%m%dT%H%M%SZ")


def esc(t):
    return str(t).replace("\\", "\\\\").replace(";", "\;").replace(",", "\\,").replace("\n", "\\n")


def piega(riga):
    """RFC 5545: righe lunghe al massimo 75 byte, il resto va a capo con uno spazio."""
    b, out = riga.encode(), []
    while len(b) > 75:
        taglio = 75
        while (b[taglio] & 0xC0) == 0x80:  # non spezzare un carattere UTF-8
            taglio -= 1
        out.append(b[:taglio].decode())
        b = b[taglio:]
        b = b" " + b
    out.append(b.decode())
    return "\r\n".join(out)


def evento(uid, serie, sessione, gp, luogo, inizio, fine, nota=""):
    if fine <= inizio:
        fine = inizio + timedelta(hours=1)
        nota = "Durata indicativa di un'ora. " + nota
    righe = ["BEGIN:VEVENT", f"UID:{uid}@gpoggi.it", f"DTSTAMP:{fmt(datetime.now(timezone.utc))}", f"DTSTART:{fmt(inizio)}", f"DTEND:{fmt(fine)}",
             f"SUMMARY:{esc(f'{serie} · {sessione} · {gp}')}", f"LOCATION:{esc(luogo)}",
             f"DESCRIPTION:{esc((nota + 'Calendario di GP Oggi, sito non ufficiale.').strip())}",
             "BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{esc(f'{serie}: {sessione} tra 15 minuti')}", "TRIGGER:-PT15M", "END:VALARM", "END:VEVENT"]
    return righe


def calendario(nome, eventi):
    righe = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//GP Oggi//Calendario//IT", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             f"X-WR-CALNAME:{esc(nome)}", "X-WR-TIMEZONE:Europe/Rome", "REFRESH-INTERVAL;VALUE=DURATION:PT6H"]
    for e in eventi:
        righe += e
    righe.append("END:VCALENDAR")
    return "\r\n".join(piega(r) for r in righe) + "\r\n"


def main():
    f1, moto = [], []
    for g in json.loads((DATA / "events.json").read_text()):
        for s in g["sessioni"]:
            f1.append(evento(f"f1-{g['id']}-{s['tipo'].replace(' ', '')}", "F1", s["nome"], g["nome"], f"{g['circuito']}, {g['paese']}", utc(s["inizio"]), utc(s["fine"])))
    mf = DATA / "motogp.json"
    if mf.exists():
        for w in json.loads(mf.read_text())["weekend"]:
            for s in w["sessioni"]:
                moto.append(evento(f"motogp-{w['nome'].replace(' ', '')}-{s['codice']}", "MotoGP", s["nome"], w["nome"], f"{w['circuito']}, {w['paese']}", utc(s["inizio"]), utc(s["fine"])))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "f1.ics").write_text(calendario("F1 · GP Oggi", f1), newline="")
    (OUT / "motogp.ics").write_text(calendario("MotoGP · GP Oggi", moto), newline="")
    (OUT / "tutto.ics").write_text(calendario("F1 e MotoGP · GP Oggi", f1 + moto), newline="")
    print(f"Calendari: {len(f1)} sessioni F1, {len(moto)} sessioni MotoGP")


if __name__ == "__main__":
    main()
