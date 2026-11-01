"""Grafiche pronte per «Antonelli campione del mondo» (da pubblicare SOLO a titolo confermato): copertina, record di età, primo italiano dopo Ascari.
Uso: python3 grafica_campione.py cartella_uscita/   (foto ESPN: i file restano fuori dal repository)"""
import sys, asyncio, base64
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import notizia_sub as n, copertina as C, bandiera as B
OUT = (sys.argv[1] if len(sys.argv) > 1 else '/tmp/campione/').rstrip('/') + '/'
logo = n.b64(n.SITO / "img/logo-wide-scuro.png")
TR = B.QUI / "extra" / "trofeo-f1.jpg"

def pagina(comp, pill, righe, sotto=None, credito="Foto: ESPN · Trofeo: Raimond Spekking, CC BY-SA 4.0"):
    foto = base64.b64encode(open(comp, "rb").read()).decode()
    strisce = "".join(f'<div class="s {k}" style="top:{y}px;font-size:{px}px"><span>{t}</span></div>' for k, t, y, px in righe)
    sot = f'<div class=sotto>{sotto}</div>' if sotto else ''
    return f"""<!doctype html><meta charset=utf-8><style>{n.CSS_FONT}
html,body{{margin:0;width:{n.W}px;height:{n.H}px;overflow:hidden;position:relative;background:#06100f;font-family:Oswald,sans-serif}}
.f{{position:absolute;inset:0;background:url(data:image/jpeg;base64,{foto}) center/cover}}
.logo{{position:absolute;left:50%;margin-left:-170px;top:245px;width:340px;z-index:6}}
.pill{{position:absolute;left:0;right:0;top:1600px;text-align:center;z-index:6}}
.pill span{{display:inline-block;background:#06100f;color:#ffc400;font:700 40px Oswald;letter-spacing:.14em;text-transform:uppercase;padding:6px 26px;border:3px solid #ffc400;border-radius:10px}}
.s{{position:absolute;left:0;right:0;text-align:center;font-family:Oswald;font-weight:700;text-transform:uppercase;line-height:1;z-index:6}}
.s span{{display:inline-block;padding:2px 28px 8px}}
.r span{{background:#e8352f;color:#fff}} .w span{{background:#fff;color:#0b0b0e}} .g span{{background:#ffc400;color:#1a1300;box-shadow:0 0 40px rgba(255,196,0,.55)}} .v span{{background:#009246;color:#fff}}
.sotto{{position:absolute;left:0;right:0;top:1640px;text-align:center;font:600 34px Inter;color:#fff;text-shadow:0 2px 8px #000;z-index:6;padding:0 80px}}
.cred{{position:absolute;right:36px;bottom:110px;font:500 20px Inter;color:rgba(255,255,255,.85);z-index:7}}
</style><div class=f></div><img class=logo src="data:image/png;base64,{logo}">{"<div class=pill><span>"+pill+"</span></div>" if pill else ""}{strisce}{sot}<div class=cred>{credito}</div>"""

async def fai(nome, comp, pill, righe, sotto=None, credito="Foto: ESPN · Trofeo: Raimond Spekking, CC BY-SA 4.0"):
    await C.scatta(pagina(comp, pill, righe, sotto, credito), OUT + nome)

async def main():
    # 1 copertina campione: faccia grande + trofeo + coriandoli e raggi
    B.composizione("Kimi Antonelli", OUT + "c1.jpg", TR, larghezza=1650, px=-300, tr_x=880, tr_h=640, conf=True, luce=True)
    await fai("antonelli-campione-copertina.png", OUT + "c1.jpg", "Campione del mondo 2026",
              [("w", "Antonelli", 1150, 120), ("g", "Campione", 1282, 118), ("r", "del mondo", 1424, 100)])
    # 2 il più giovane di sempre
    B.composizione("Kimi Antonelli", OUT + "c2.jpg", None, larghezza=1700, px=-310, conf=True, luce=True)
    await fai("antonelli-piu-giovane.png", OUT + "c2.jpg", None,
              [("g", "Il più giovane", 1150, 108), ("r", "campione di sempre", 1290, 86)],
              "Aveva 20 anni: il precedente record era di Vettel, a 23", credito="Foto: ESPN")
    # 3 italiano dopo 73 anni
    B.composizione("Kimi Antonelli", OUT + "c3.jpg", TR, larghezza=1650, px=-300, tr_x=880, tr_h=640, conf=True, luce=True)
    await fai("antonelli-italiano-dopo-73-anni.png", OUT + "c3.jpg", None,
              [("v", "Un italiano", 1150, 108), ("w", "campione del mondo", 1285, 84), ("r", "dopo 73 anni", 1415, 100)],
              "L'ultimo era stato Alberto Ascari, nel 1953")
asyncio.run(main())
