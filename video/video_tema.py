"""Video su un tema del momento (per esempio un dibattito tra piloti) da un file JSON in video/temi/, nello stesso stile dei video del pronostico.

  python video/video_tema.py video/temi/format_2027.json --uscita out.mp4

Ogni scena: titolo (testo grande), pilota (foto + etichetta + frase breve + righe) o cta. Si usano foto diverse per pilota.
Scrive anche OUT.txt con la didascalia. Le citazioni vanno tenute brevi e attribuite: niente testi copiati dagli articoli.
"""
import argparse, asyncio, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import auto_video as A  # noqa: E402


def scene_da_spec(spec):
    colore = A.BLU if spec.get("serie") == "MotoGP" else A.ROSSO
    chiave = "motogp" if spec.get("serie") == "MotoGP" else "f1"
    out = []
    n = len(spec["scene"])
    for i, s in enumerate(spec["scene"]):
        righe = "".join(f"<div style='font:500 44px Inter;color:#e8e8ee;padding:12px 0;border-bottom:2px solid #26262e'>{A.esc(r)}</div>" for r in s.get("righe", []))
        if s["tipo"] == "pilota":
            foto = A.foto_per_nome(s["pilota"], chiave)
            pill = s.get("colore", colore)
            corpo = (f"<span class=pill style='top:780px;background:{pill}'>{A.esc(s['etichetta'])}</span>"
                     f"<h1 style='position:absolute;left:70px;right:70px;top:840px;margin:0;font:700 96px/1 Oswald;text-transform:uppercase'>{A.esc(s['pilota'])}</h1>"
                     f"<div style='position:absolute;left:70px;right:70px;top:970px;font:700 58px/1.1 Oswald;color:#ffd21f'>{A.esc(s['frase'])}</div>"
                     f"<div style='position:absolute;left:70px;right:70px;top:1110px'>{righe}</div>")
            out.append((A.cornice(corpo, colore, foto), s["voce"]))
        elif s["tipo"] == "titolo":
            corpo = (f"<span class=pill style='top:430px;background:{colore}'>{A.esc(s['etichetta'])}</span>"
                     f"<h1 style='position:absolute;left:70px;right:70px;top:500px;margin:0;font:700 120px/1.02 Oswald;text-transform:uppercase'>{A.esc(s['titolo'])}</h1>"
                     f"<div style='position:absolute;left:70px;right:70px;top:1000px'>{righe}</div>"
                     f"<div style='position:absolute;left:70px;right:70px;top:1500px;font:500 28px Inter;color:#8a8a96'>Fonti: {A.esc(spec.get('fonti', ''))}</div>")
            out.append((A.cornice(corpo, colore, None), s["voce"]))
        else:
            corpo = (f"<div style='position:absolute;left:70px;right:70px;top:420px;text-align:center;font:700 170px/1 Oswald;text-transform:uppercase'>{A.esc(s['titolo'])}</div>"
                     f"<div style='position:absolute;left:70px;right:70px;top:760px'>{righe}</div>"
                     f"<div style='position:absolute;left:90px;right:90px;top:1180px;text-align:center;background:{colore};border-radius:28px;padding:34px 20px;font:700 60px/1.1 Oswald;text-transform:uppercase'>Vota il podio di Mandalika<br>su gpoggi.it</div>")
            out.append((A.cornice(corpo, colore, None), s["voce"]))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("spec", type=Path); ap.add_argument("--uscita", type=Path, default=Path(__file__).parent / "tema.mp4")
    a = ap.parse_args(); spec = json.load(open(a.spec))
    Path(str(a.uscita) + ".txt").write_text(spec.get("didascalia", ""), encoding="utf-8")
    asyncio.run(A.componi(scene_da_spec(spec), a.uscita, A.VELOCITA_NOTIZIE, rapido=True)); print("Video:", a.uscita)
