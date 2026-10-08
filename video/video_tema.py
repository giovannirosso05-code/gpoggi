"""Video su un tema del momento (per esempio un dibattito tra piloti) da un file JSON in video/temi/, nello stesso stile dei video del pronostico.

  python video/video_tema.py video/temi/format_2027.json --uscita out.mp4

Ogni scena: titolo (testo grande), pilota (foto + etichetta + frase breve + righe) o cta. Si usano foto diverse per pilota.
Scrive anche OUT.txt con la didascalia. Le citazioni vanno tenute brevi e attribuite: niente testi copiati dagli articoli.
"""
import argparse, asyncio, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import auto_video as A  # noqa: E402


def cornice_piena(corpo, colore, foto=None, file_extra=None, credito=None):
    """Foto a tutto schermo: sfondo sfocato che riempie lo schermo + foto nitida a tutta larghezza, testo sopra una sfumatura in basso."""
    if file_extra:
        percorso = A.SITO / file_extra["file"]; cred = credito or ""
    elif foto:
        percorso = A.foto_file(foto); cred = f"Foto: {foto.get('autore', '')} · {foto.get('licenza', '')} · via Wikimedia Commons"
    else:
        return A.cornice(corpo, colore, None)
    uri = "data:image/jpeg;base64," + A.b64(percorso)
    stile = (f"<style>{A.CSS}.url{{color:{colore}}}"
             f".bg{{position:absolute;left:-80px;top:-80px;width:1240px;height:2080px;background:url({uri}) center/cover;filter:blur(38px) brightness(.5)}}"
             f".pic{{position:absolute;left:0;top:250px;width:1080px;display:block}}"
             f".sfum{{position:absolute;left:0;top:700px;width:1080px;height:1220px;background:linear-gradient(180deg,rgba(11,11,14,0) 0%,rgba(11,11,14,.78) 38%,#0b0b0e 66%)}}</style>")
    return (f"<!doctype html><meta charset=utf-8>{stile}<div class=bg></div><img class=pic src='{uri}'><div class=sfum></div>"
            f"<div class=logo><img src='data:image/png;base64,{A.b64(A.SITO / 'img/logo-wide-scuro.png')}'></div>{corpo}"
            f"<div class=cred style='top:1665px'>{A.esc(cred)}</div><div class=url>gpoggi.it</div><div class=avviso>Sito non ufficiale, non affiliato a Formula 1, FIA, MotoGP, Dorna o ai team</div>")


def scene_da_spec(spec):
    colore = A.BLU if spec.get("serie") == "MotoGP" else A.ROSSO
    chiave = "motogp" if spec.get("serie") == "MotoGP" else "f1"
    out = []
    n = len(spec["scene"])
    for i, s in enumerate(spec["scene"]):
        righe = "".join(f"<div style='font:500 44px Inter;color:#e8e8ee;padding:12px 0;border-bottom:2px solid #26262e'>{A.esc(r)}</div>" for r in s.get("righe", []))
        if s["tipo"] == "pilota":
            foto = A.foto_per_nome(s["pilota"], chiave)
            extra = s.get("foto_extra")
            pill = s.get("colore", colore)
            corpo = (f"<span class=pill style='top:1000px;background:{pill}'>{A.esc(s['etichetta'])}</span>"
                     f"<h1 style='position:absolute;left:70px;right:70px;top:1060px;margin:0;font:700 96px/1 Oswald;text-transform:uppercase'>{A.esc(s['pilota'])}</h1>"
                     f"<div style='position:absolute;left:70px;right:70px;top:1190px;font:700 58px/1.1 Oswald;color:#ffd21f'>{A.esc(s['frase'])}</div>"
                     f"<div style='position:absolute;left:70px;right:70px;top:1330px'>{righe}</div>")
            out.append((cornice_piena(corpo, colore, foto, extra, extra and extra.get("credito")), s["voce"]))
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
