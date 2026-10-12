"""Video animato 'dalla griglia all'arrivo': i piloti scivolano dalla posizione di partenza a quella d'arrivo.
Solo grafica e dati nostri (griglia e risultati): nessuna foto, nessuna ripresa, quindi nessun problema di licenze.
Uso:  python animazione_rimonte.py f1|motogp uscita.mp4        (ultimo weekend in docs/data/pagella.json)
"""
import asyncio
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import notizia_sub as n
from playwright.async_api import async_playwright

W, H, FPS = n.W, n.H, 24
T_GRIGLIA, T_MOVE, T_DELTA, T_FINE = 1.2, 4.6, 7.6, 10.4   # secondi: griglia ferma, spostamento, frecce, chiusura


def dati(serie):
    w = json.load(open(n.DATA / "pagella.json"))[serie]
    righe = [r for r in w["righe"] if r.get("griglia")]
    righe.sort(key=lambda r: r["griglia"])
    ret = [r for r in righe if r["g"] is None]
    fin = sorted([r for r in righe if r["g"] is not None], key=lambda r: r["g"])
    arrivo = {r["nome"]: i for i, r in enumerate(fin + sorted(ret, key=lambda r: r["griglia"]))}
    MOTO = {"Ducati": "e1251b", "Aprilia": "7b2c8f", "KTM": "f26a1b", "Yamaha": "1d4fa3", "Honda": "dcdce2"}
    out = []
    for i, r in enumerate(righe):
        out.append({"nome": r["nome"].split()[-1] if r["nome"] != "Marc Marquez" and r["nome"] != "Alex Marquez" else r["nome"].split()[0][0] + ". Marquez",
                    "colore": r.get("colore") or MOTO.get(r.get("moto"), "888"), "da": i, "a": arrivo[r["nome"]], "g": r["g"], "griglia": r["griglia"],
                    "delta": (r["griglia"] - r["g"]) if r["g"] is not None else None})
    return w["nome"], out


def pagina(serie, gp, piloti):
    col = "#1f5fd1" if serie == "motogp" else "#e8352f"
    logo = (n.QUI / "logo" / ("moto-gp-scuro.svg" if serie == "motogp" else "auto-gp-scuro.svg")).read_text().replace('width="512" height="512"', 'width="150" height="150"', 1)
    gp_breve = gp.replace("Gran Premio d'", "").replace("Gran Premio di ", "").replace("Gran Premio del ", "").replace("Gran Premio dell'", "").replace("GP ", "").upper()
    return f"""<!doctype html><meta charset=utf-8><style>{n.CSS_FONT}
*{{box-sizing:border-box}} html,body{{margin:0;width:{W}px;height:{H}px;background:#0b0b0e;color:#fff;font-family:Inter,sans-serif;overflow:hidden;position:relative}}
.titolo{{position:absolute;left:60px;top:230px;font:700 74px/1 Oswald;text-transform:uppercase}}
.sotto{{position:absolute;left:60px;top:315px;font:700 40px Oswald;letter-spacing:.06em;text-transform:uppercase;color:#ffd21f}}
.logo{{position:absolute;right:50px;top:200px;width:150px;height:150px}}
.riga{{position:absolute;left:50px;right:50px;height:56px;display:flex;align-items:center;gap:16px;background:#1b1b21;border-radius:10px;padding:0 18px;font:600 36px Oswald;text-transform:uppercase;will-change:transform}}
.riga .p{{width:50px;text-align:right;color:rgba(255,255,255,.65)}} .riga .b{{width:12px;height:36px;border-radius:4px}}
.riga .nm{{flex:1}} .riga .d{{font-size:32px;min-width:120px;text-align:right}}
.su{{color:#4ade80}} .giu{{color:#ff6b6b}} .rit{{color:rgba(255,255,255,.5);font-size:26px}}
.fine{{position:absolute;inset:0;background:rgba(11,11,14,.985);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:30px;opacity:0}}
.fine .u{{font:700 64px Oswald;color:{col};letter-spacing:.04em}} .fine .t{{font:600 44px/1.15 Oswald;text-align:center;text-transform:uppercase;padding:0 80px}}
.nota{{position:absolute;left:50px;right:50px;bottom:60px;font:500 22px Inter;color:rgba(255,255,255,.6);text-align:center}}
</style>
<div class=titolo id=ti>La griglia</div><div class=sotto id=so>{gp_breve}</div><div class=logo>{logo}</div><div id=lista></div>
<div class=nota>Posizioni di partenza e di arrivo ufficiali. Elaborazione GP Oggi · gpoggi.it</div>
<div class=fine id=fine><div class=t>Chi ha recuperato di più?</div><div class=t style="color:#ffd21f;font-size:52px" id=top></div><div class=u>gpoggi.it</div></div>
<script>
const P={json.dumps(piloti, ensure_ascii=False)}; const Y0=400, RH=62;
const lista=document.getElementById('lista');
P.forEach((p,i)=>{{const d=document.createElement('div');d.className='riga';d.innerHTML=`<span class=p></span><span class=b style="background:#${{p.colore}}"></span><span class=nm>${{p.nome}}</span><span class=d></span>`;lista.appendChild(d);p.el=d;}});
const ease=x=>x<0?0:x>1?1:x*x*(3-2*x);
const best=[...P].filter(p=>p.delta!==null).sort((a,b)=>b.delta-a.delta)[0];
document.getElementById("top").textContent=best?`${{best.nome}}: dal ${{best.griglia}}° al ${{best.g}}° (+${{best.delta}})`:"";
function render(t){{
  const k=ease((t-{T_GRIGLIA})/({T_MOVE}-{T_GRIGLIA}));
  document.getElementById('ti').textContent=t<{T_GRIGLIA}+0.6?'La griglia':(t<{T_MOVE}?'La gara':'L\\'arrivo');
  P.forEach(p=>{{
    const pos=p.da+(p.a-p.da)*k; p.el.style.transform=`translateY(${{Y0+pos*RH}}px)`; p.el.style.top='0px'; p.el.style.zIndex=100+(p.delta===null?-50:p.delta);
    const num=k<0.5?p.da+1:p.a+1; p.el.querySelector('.p').textContent=(k>=0.5&&p.g===null)?'':num;
    const d=p.el.querySelector('.d');
    if(t>={T_MOVE}){{ const a=ease((t-{T_MOVE})/0.5);
      d.style.opacity=a; d.className='d '+(p.g===null?'rit':(p.delta>0?'su':(p.delta<0?'giu':'')));
      d.textContent=p.g===null?'RIT':(p.delta>0?'▲ '+p.delta:(p.delta<0?'▼ '+(-p.delta):'='));
      if(p.g===null) p.el.style.opacity=1-0.5*a;
      if(best&&p===best&&t>={T_DELTA}){{const s=1+0.05*Math.sin((t-{T_DELTA})*8);p.el.style.transform+=` scale(${{s}})`;p.el.style.background='rgba(74,222,128,.28)';}}
    }} else {{ d.textContent=''; }}
  }});
  document.getElementById('fine').style.opacity=ease((t-{T_DELTA}-1.4)/0.6);
}}
render(0);
</script>"""


async def main():
    serie = sys.argv[1] if len(sys.argv) > 1 else "f1"
    uscita = sys.argv[2] if len(sys.argv) > 2 else f"animazione_{serie}.mp4"
    gp, piloti = dati(serie)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        async with async_playwright() as p:
            b = await p.chromium.launch(**({"executable_path": "/opt/pw-browsers/chromium"} if Path("/opt/pw-browsers/chromium").exists() else {}), args=["--no-sandbox"])
            pg = await b.new_page(viewport={"width": W, "height": H})
            await pg.set_content(pagina(serie, gp, piloti)); await pg.wait_for_timeout(500)
            tot = int(T_FINE * FPS)
            for i in range(tot):
                await pg.evaluate(f"render({i / FPS})")
                await pg.screenshot(path=str(tmp / f"f{i:04d}.png"))
            await b.close()
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(tmp / "f%04d.png"), "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                        "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", uscita], check=True)
    print("Fatto:", uscita)


if __name__ == "__main__":
    asyncio.run(main())
