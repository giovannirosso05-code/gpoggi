"""Cerca su Wikimedia Commons foto alternative (licenza libera) dei piloti per non ripetere sempre la stessa nei video.

  python3 foto_extra.py cerca "Francesco Bagnaia" "Jorge Martin" …     scarica anteprime e metadati in foto_extra_lavoro/ (con foglio contatti)
  python3 foto_extra.py scegli "Francesco Bagnaia" 3 7 --nome ritratto …  copia le foto scelte in docs/img/foto-extra/ e le registra in docs/data/foto-extra.json

Le foto si scelgono guardando il foglio contatti: il titolo del file non basta a sapere se si vede il volto.
"""
import hashlib, json, re, shutil, sys, time, unicodedata
from pathlib import Path

import requests
from PIL import Image, ImageDraw

import foto_wiki as fw

ROOT = Path(__file__).parent
LAVORO = ROOT / "foto_extra_lavoro"
EXTRA = ROOT / "docs" / "data" / "foto-extra.json"
norm = lambda s: unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()
ESCLUDI = re.compile(r"\b(and|with|vs|leading|chasing|duel|panigale|bike|car|livery|engine|helmet)\b", re.I)


def api(**p):
    for t in range(4):
        r = requests.get("https://commons.wikimedia.org/w/api.php", params={"format": "json", **p}, headers=fw.HEADERS, timeout=30)
        if r.status_code == 200:
            return r.json()
        time.sleep(10 + 10 * t)
    return {}


def cerca(nome, extra=()):
    cogn = norm(nome).split()[-1]
    titoli = []
    for q in (nome, f"{nome} 2025", f"{nome} press conference", *extra):
        for x in api(action="query", list="search", srsearch=q, srnamespace=6, srlimit=40).get("query", {}).get("search", []):
            t = x["title"]
            if cogn in norm(t) and not ESCLUDI.search(t) and t not in titoli and t.lower().endswith((".jpg", ".jpeg")):
                titoli.append(t)
        time.sleep(2)
    out = []
    for t in titoli[:14]:
        try:
            info = fw._info_file(t.replace("File:", ""), 500)
        except requests.RequestException:
            time.sleep(8); continue
        if not info:
            continue
        r = requests.get(info["url"], headers=fw.HEADERS, timeout=60)
        if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image/"):
            time.sleep(5); continue
        f = LAVORO / (hashlib.md5(t.encode()).hexdigest()[:8] + ".jpg"); f.write_bytes(r.content)
        out.append({"file": f.name, "titolo": t.replace("File:", ""), **info})
        time.sleep(2.5)
    return out


def foglio(nome, lista):
    th = []
    for e in lista:
        im = Image.open(LAVORO / e["file"]).convert("RGB"); im.thumbnail((330, 330)); th.append(im)
    righe = (len(th) + 3) // 4
    s = Image.new("RGB", (4 * 340, max(1, righe) * 340), (20, 20, 20)); d = ImageDraw.Draw(s)
    for i, im in enumerate(th):
        x, y = (i % 4) * 340, (i // 4) * 340; s.paste(im, (x, y)); d.rectangle((x, y, x + 34, y + 22), fill=(0, 0, 0)); d.text((x + 6, y + 4), str(i), fill=(255, 255, 0))
    s.save(LAVORO / f"foglio_{norm(nome).replace(' ', '_')}.jpg")


def main():
    LAVORO.mkdir(exist_ok=True)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "cerca":
        extra = [a[4:] for a in args if a.startswith("--q=")]  # ricerche in più: --q="Lewis Hamilton Ferrari 2025"
        for nome in [a for a in args if not a.startswith("--q=")]:
            lista = cerca(nome, extra)
            (LAVORO / f"{norm(nome).replace(' ', '_')}.json").write_text(json.dumps(lista, ensure_ascii=False, indent=1))
            if lista:
                foglio(nome, lista)
            print(nome, len(lista), "foto")
    elif cmd == "scegli":
        nome = args[0]; nomi = args[1:]
        lista = json.loads((LAVORO / f"{norm(nome).replace(' ', '_')}.json").read_text())
        extra = json.loads(EXTRA.read_text()) if EXTRA.exists() else {}
        chiave = nome.replace("á", "a").replace("é", "e")
        for coppia in nomi:  # indice:nome, per esempio 3:ritratto
            i, etichetta = coppia.split(":"); e = lista[int(i)]
            grande = requests.get(e["grande"], headers=fw.HEADERS, timeout=60); grande.raise_for_status()
            dest = ROOT / "docs" / "img" / "foto-extra" / f"{norm(nome).replace(' ', '_')}_{etichetta}.jpg"
            dest.write_bytes(grande.content)
            extra.setdefault(chiave, {})[etichetta] = {"file": f"img/foto-extra/{dest.name}", "autore": re.sub(r"Original:\s*", "", e["autore"]), "licenza": e["licenza"], "pagina": e["pagina"], "titolo": e["titolo"]}
            time.sleep(3)
        EXTRA.write_text(json.dumps(extra, ensure_ascii=False, indent=1)); print("ok")


if __name__ == "__main__":
    main()
