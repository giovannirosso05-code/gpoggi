import asyncio, ssl, subprocess, json, base64, sys
from pathlib import Path
import edge_tts, edge_tts.communicate as C
from playwright.sync_api import sync_playwright
C._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
D=Path(__file__).parent; L=D.parent/"logo"; DATA=Path("/home/user/F1-Site/docs/data")
RATE=sys.argv[1] if len(sys.argv)>1 else "+18%"
st=json.load(open(DATA/"standings.json")); col={c["team"]:c["colore"] for c in st["costruttori"]}
# Fatti presi da OpenF1: race_control (ritardo, safety car, episodi, indagini), weather (pioggia), risultati di gara
SEG=[
 dict(testo="Gran Premio del Bahrain, domenica quattro ottobre. Ecco cosa è successo.",
      html="<span class='kick'>Resoconto</span><h1 style='font-size:128px;margin-top:40px'>Gran<br>Premio<br>del Bahrain</h1><div class='sub'>Kuala Lumpur · 4 ottobre 2026</div>"),
 dict(testo="La gara è partita con un'ora e mezza di ritardo. Prima del via è piovuto, il rischio era del novanta per cento e la procedura è stata sospesa. Via previsto alle nove, ora italiana. Partenza alle dieci e trentatré.",
      html="<span class='kick'>Il via in ritardo</span><div class='voce'><b>09:00</b><span>orario previsto · ora italiana (15:00 a Kuala Lumpur)</span></div><div class='voce'><b class='r'>10:33</b><span>via effettivo · ora italiana (16:33 a Kuala Lumpur)</span></div><div class='nota'>Pioggia prima del via · rischio 90% · procedura sospesa</div>"),
 dict(testo="Vince Max Verstappen con la Red Bull, partendo dalla pole position. Secondo Kimi Antonelli, a due secondi e tre decimi. Terzo Lewis Hamilton con la Ferrari.",
      html=None),
 dict(testo="Giro sette: contatto tra Leclerc e Hulkenberg, nessuna penalità. Safety car dal giro nove al dodici. Giro quattordici: Bortoleto e Sainz si toccano, dieci secondi di penalità a Bortoleto. Seconda safety car dal quarantacinque al cinquantuno.",
      html="<span class='kick'>Gli episodi</span><div class='ev'><b>Giro 7</b><span>Contatto Leclerc – Hulkenberg, nessuna penalità</span></div><div class='ev'><b>Giro 9–12</b><span>Safety car</span></div><div class='ev'><b>Giro 14</b><span>Bortoleto – Sainz: 10 secondi di penalità a Bortoleto</span></div><div class='ev'><b>Giro 45–51</b><span>Safety car</span></div>"),
 dict(testo="Tre i ritirati: Russell, Albon e Bottas. Dopo la bandiera a scacchi restano sotto esame Albon, Hulkenberg e Norris.",
      html="<span class='kick'>Ritirati</span><h1 style='font-size:92px;margin:30px 0 50px;line-height:1.15'>Russell<br>Albon<br>Bottas</h1><div class='nota'>Sotto esame dopo la gara: Albon, Hulkenberg, Norris</div>"),
 dict(testo="Antonelli resta primo con trecentoventi punti, poi Russell con duecentotrentasei e Hamilton con duecentoquattordici. Tra i costruttori guida la Mercedes.",
      html=None),
 dict(testo="Questo era GP Oggi. Dati OpenF1, sito non ufficiale.",
      html="<div style='text-align:center;margin-top:120px;font-family:Oswald;font-weight:700;font-size:150px;line-height:1'>GP<span style='color:#e8352f'>OGGI</span></div><div class='sub' style='text-align:center'>Dati OpenF1 · sito non ufficiale</div>"),
]

import re as _re
ROSTER={p["numero"]:p for p in json.load(open(DATA/"roster.json"))}
def faccia(n,px,cls="faccia"):
    d=base64.b64encode((D/"volti"/f"{n}.jpg").read_bytes()).decode()
    return f"<img class='{cls}' style='width:{px}px;height:{px}px' src='data:image/jpeg;base64,{d}'>"
def _autore(a):
    a=_re.sub(r"Original:\s*","",a or ""); a=_re.sub(r";\s*Derivative work:\s*"," / ",a); return a.replace("Picture by ","").strip()
def crediti(nums):
    out=[]
    for n in nums:
        f=ROSTER[n]["foto"]; t=f"{_autore(f['autore'])} ({f['licenza']})"
        if t not in out: out.append(t)
    return "Foto Wikimedia Commons: "+" · ".join(out)
def cognome(n): return ROSTER[n]["nome"].split()[-1]
SURN=lambda n: ROSTER[n]["nome"].split(" ",1)[1] if " " in ROSTER[n]["nome"] else ROSTER[n]["nome"]

race=json.load(open(DATA/"gare/1308.json"))
gara=sorted([r for r in [s for s in race["sessioni"] if s["tipo"]=="Race"][0]["risultati"] if r.get("pos")],key=lambda r:r["pos"])
def riga(p,n,t,x,c="8b8a92"): return f"<div class='riga' style='border-left:14px solid #{c}'><div class='pos'>{p}</div><div><div class='nome'>{n}</div><div class='team'>{t}</div></div><div class='pt'>{x}</div></div>"
SEG[2]["html"]="<span class='kick'>Il podio</span><div style='margin-top:30px'>"+"".join(riga(f"{r['pos']}°",r['nome'],r['team'],r['distacco'] or r['tempo'],col.get(r['team'],'8b8a92')) for r in gara[:3])+"</div><div class='nota'>Pole position: Max Verstappen</div>"
SEG[5]["html"]="<span class='kick'>Classifica piloti</span><div class='sub' style='margin:10px 0'>Dopo il "+st['dopo']+"</div>"+"".join(riga(f"{p['posizione']}°",p['nome'],p['team'],f"{p['punti']:g}",p.get('colore') or '8b8a92') for p in st['piloti'][:3])+"<div class='sub' style='margin-top:40px'>Costruttori: <b style='color:#f2f1ee'>"+st['costruttori'][0]['team']+f" {st['costruttori'][0]['punti']:g}</b></div>"

def col_podio(r):
    n=r["numero"]; tm=col.get(r["team"],"8b8a92")
    nome=ROSTER[n]["nome"].split(" ",1)
    return f"<div class='colp' style='border-top:12px solid #{tm}'><div class='posto'>{r['pos']}°</div>{faccia(n,250)}<div class='nome2'>{nome[0]}<br>{nome[-1]}</div><div class='team'>{r['team']}</div><div class='gap'>{r['distacco'] or r['tempo']}</div></div>"
SEG[2]["html"]="<span class='kick'>Il podio</span><div class='cols'>"+"".join(col_podio(r) for r in gara[:3])+"</div><div class='nota'>Pole position: Max Verstappen</div>"
SEG[2]["cred"]=[r["numero"] for r in gara[:3]]
SEG[3]["html"]=("<span class='kick'>Gli episodi</span>"
 f"<div class='ev'><div><b>Giro 7</b><span>Contatto Leclerc – Hulkenberg, nessuna penalità</span></div><div class='fac2'>{faccia(16,120)}{faccia(27,120)}</div></div>"
 "<div class='ev'><div><b>Giro 9–12</b><span>Safety car</span></div></div>"
 f"<div class='ev'><div><b>Giro 14</b><span>Bortoleto – Sainz: 10 secondi di penalità a Bortoleto</span></div><div class='fac2'>{faccia(5,120)}{faccia(55,120)}</div></div>"
 "<div class='ev'><div><b>Giro 45–51</b><span>Safety car</span></div></div>")
SEG[3]["cred"]=[16,27,5,55]
SEG[4]["html"]=("<span class='kick'>Ritirati</span><div class='tre'>"+"".join(f"<div>{faccia(n,260)}<div class='nome2'>{cognome(n)}</div></div>" for n in (63,23,77))+"</div>"
 "<div class='nota'>Sotto esame dopo la gara</div><div class='tre piccoli'>"+"".join(f"<div>{faccia(n,140)}<div class='team'>{cognome(n)}</div></div>" for n in (23,27,1))+"</div>")
SEG[4]["cred"]=[63,23,77,27,1]
def riga_f(n,p,t,x,c): return f"<div class='riga' style='border-left:14px solid #{c}'>{faccia(n,140)}<div><div class='nome'>{ROSTER[n]['nome']}</div><div class='team'>{p}° · {t}</div></div><div class='pt'>{x}</div></div>"
SEG[5]["html"]="<span class='kick'>Classifica piloti</span><div class='sub' style='margin:10px 0'>Dopo il "+st['dopo']+"</div>"+"".join(riga_f(p['numero'],p['posizione'],p['team'],f"{p['punti']:g}",p.get('colore') or '8b8a92') for p in st['piloti'][:3])+"<div class='sub' style='margin-top:40px'>Costruttori: <b style='color:#f2f1ee'>"+st['costruttori'][0]['team']+f" {st['costruttori'][0]['punti']:g}</b></div>"
SEG[5]["cred"]=[p['numero'] for p in st['piloti'][:3]]
SEG[6]["cred"]=sorted({16,27,5,55,63,23,77,1,3,12,44})

b64=lambda f: base64.b64encode((L/f).read_bytes()).decode()
CSS=f"""<style>
@font-face{{font-family:Oswald;font-weight:700;src:url(data:font/woff2;base64,{b64('oswald-latin-700-normal.woff2')})}}
@font-face{{font-family:Inter;font-weight:500;src:url(data:font/woff2;base64,{b64('inter-latin-500-normal.woff2')})}}
*{{box-sizing:border-box}}html,body{{margin:0}}
body{{width:1080px;height:1920px;background:#111115;color:#f2f1ee;font-family:Inter;position:relative;overflow:hidden}}
.barra{{position:absolute;left:0;right:0;top:0;height:20px;background:#e8352f}}
.piede{{position:absolute;left:0;right:0;bottom:70px;text-align:center;font-size:30px;color:#8f8e97;letter-spacing:.04em}}
.logo{{position:absolute;left:0;right:0;top:80px;text-align:center}} .logo svg{{width:520px;height:auto}}
.centro{{position:absolute;left:70px;right:70px;top:640px}}
h1{{font-family:Oswald;font-weight:700;text-transform:uppercase;margin:0;line-height:1.02}}
.kick{{font-family:Oswald;font-weight:700;font-size:44px;letter-spacing:.08em;color:#fff;background:#e8352f;display:inline-block;padding:6px 22px;text-transform:uppercase}}
.sub{{font-size:42px;color:#b6b5bd;margin-top:30px}}
.riga{{display:flex;align-items:center;gap:26px;padding:26px 0 26px 26px;border-bottom:2px solid #2f2f38}}
.pos{{font-family:Oswald;font-weight:700;font-size:80px;color:#e8352f;width:90px}}
.nome{{font-family:Oswald;font-weight:700;font-size:58px;text-transform:uppercase;line-height:1}}
.team{{font-size:32px;color:#b6b5bd;margin-top:6px}}
.pt{{margin-left:auto;font-family:Oswald;font-weight:700;font-size:60px}}
.voce{{margin-top:40px}} .voce b{{font-family:Oswald;font-weight:700;font-size:170px;line-height:1;display:block}} .voce b.r{{color:#e8352f}} .voce span{{font-size:38px;color:#b6b5bd}}
.nota{{margin-top:60px;font-size:40px;color:#b6b5bd;border-top:2px solid #2f2f38;padding-top:30px}}
.ev{{padding:26px 0;border-bottom:2px solid #2f2f38}} .ev b{{font-family:Oswald;font-weight:700;font-size:64px;color:#e8352f;display:block;text-transform:uppercase}} .ev span{{font-size:42px;line-height:1.3}}
.cols{{display:flex;gap:18px;margin-top:30px}}.colp{{flex:1;text-align:center;padding-top:18px;background:#1a1a20;border-radius:14px;padding-bottom:22px}}
.posto{{font-family:Oswald;font-weight:700;font-size:70px;color:#e8352f;line-height:1}}
.faccia{{border-radius:50%;object-fit:cover;display:block;margin:14px auto;border:6px solid #2f2f38}}
.nome2{{font-family:Oswald;font-weight:700;font-size:46px;text-transform:uppercase;line-height:1.05}}
.gap{{font-family:Oswald;font-weight:700;font-size:40px;margin-top:10px}}
.ev{{display:flex;align-items:center;justify-content:space-between;gap:20px}}.fac2{{display:flex;gap:10px;flex:none}}.fac2 .faccia{{margin:0;border-width:4px}}
.tre{{display:flex;justify-content:space-around;text-align:center;margin-top:30px}}.tre .faccia{{margin:0 auto 10px}}.tre.piccoli{{margin-top:20px}}.tre.piccoli .team{{font-size:30px}}
.cred{{position:absolute;left:70px;right:70px;bottom:130px;text-align:center;font-size:21px;line-height:1.35;color:#8f8e97}}
.riga .faccia{{margin:0;border-width:4px;flex:none}}
</style>"""
car=(L/"auto-gp-scuro.svg").read_text().replace('viewBox="0 0 512 512" width="512" height="512"','viewBox="6 96 500 320" width="520" height="333"')
def pagina(corpo,cred=None):
    c=f"<div class='cred'>{crediti(cred)}</div>" if cred else ""
    return f"<html><head>{CSS}</head><body><div class='barra'></div><div class='logo'>{car}</div><div class='centro'>{corpo}</div>{c}<div class='piede'>GP OGGI · sito non ufficiale · dati OpenF1</div></body></html>"
async def tts(i,t):
    await edge_tts.Communicate(t,"it-IT-DiegoNeural",rate=RATE).save(str(D/f"v{i}.mp3"))
async def tutte(): 
    for i,s in enumerate(SEG): await tts(i,s["testo"])
asyncio.run(tutte())
dur=[float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(D/f"v{i}.mp3")]).strip()) for i in range(len(SEG))]
print([round(d,1) for d in dur], "totale", round(sum(dur),1), "parole", sum(len(s["testo"].split()) for s in SEG))
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/opt/pw-browsers/chromium"); pg=b.new_page(viewport={"width":1080,"height":1920})
    for i,s in enumerate(SEG):
        pg.set_content(pagina(s["html"],s.get("cred"))); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(250); pg.screenshot(path=str(D/f"n{i}.png"))
json.dump(dur,open(D/"dur.json","w"))
