"""Video sulla pole del GP appena qualificato. I fatti (tempi e distacchi) vengono da testate autorevoli e sono scritti in video/pole_messico.json
(finché i dati ufficiali del sito non hanno la qualifica). Ritratti ESPN, tabella dei primi sei, nessun dato dedotto da noi tranne «gli basta un nono posto».
Uso:  python3 pole_gp.py video/pole_messico.json [--invia] [--uscita FILE]"""
import argparse, asyncio, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notizia_sub as NS  # noqa: E402
import notizie_giorno as NG  # noqa: E402
import ritratti_espn as R  # noqa: E402

cogn = lambda n: n.split()[-1]


def costruisci(f):
    colori = {p["nome"]: p.get("colore", "e8352f") for p in json.load(open(NS.DATA / "roster.json"))}
    rgb = lambda n: tuple(int(colori.get(n, "e8352f")[i:i + 2], 16) for i in (0, 2, 4))

    def espn(n):
        try:
            return {"foto_file": str(R.ritratto(n, rgb(n))), "credito": "Foto: ESPN"}
        except (SystemExit, Exception) as e:
            print(f"  ritratto ESPN non disponibile per {n}: {e}")
            return {}

    top = f["classifica"]
    p1, p2, p3 = top[0], top[1], top[2]
    fa = f["fonte"]
    scene = [{"foto": p1["nome"], "hook": True, "hook_titolo": f"{cogn(p1['nome'])} in pole a {f['gp']}!", "testo": f"*{cogn(p1['nome'])}* in pole a {f['gp']}! {f['gancio']}", "fonte_alto": fa, **espn(p1["nome"])}]
    for t in f["scene"]:
        n = t["pilota"]
        scene.append({"foto": n, "nome": n, "testo": t["testo"], "fonte_alto": fa, **({"chips": [tuple(c) for c in t["chips"]]} if t.get("chips") else {}), "sub_top": 1440 if t.get("chips") else None, **espn(n)})
        scene[-1] = {k: v for k, v in scene[-1].items() if v is not None}
    righe = [("si" if r["pos"] == 1 else "info", f"{r['pos']}. {cogn(r['nome'])} {r['nota']}") for r in top[:6]]
    scene.append({"foto": p1["nome"], "nome": "Qualifiche: i primi sei", "chips": righe, "sub_top": 1650, "testo": f["testo_tabella"], "fonte_alto": fa, **espn(p1["nome"])})
    spec = {"serie": "F1", "titolo_breve": f"Pole {f['gp']}", "etichetta": "Qualifiche", "fonte": fa, "velocita": "+38%", "scene": scene,
            "finale": {"foto": p1["nome"], "domanda": f["domanda"]}}
    return spec, f["didascalia"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fatti", type=Path); ap.add_argument("--invia", action="store_true"); ap.add_argument("--uscita", type=Path, default=NS.QUI / "pole_gp.mp4")
    a = ap.parse_args()
    spec, social = costruisci(json.load(open(a.fatti)))
    for s in spec["scene"]:
        print(" *", s.get("hook_titolo") or s.get("nome") or "(tabella)", "|", s["testo"])
    asyncio.run(NS.genera(spec, a.uscita))
    if a.invia:
        NG.telegram(a.uscita, f"🏁 Pole {spec['titolo_breve']}", social)


if __name__ == "__main__":
    main()
