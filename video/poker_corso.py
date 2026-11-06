"""Corso completo (tutorial da zero) «Quando chiamare: la matematica del Texas Hold'em»: regole e termini, teoria (probabilità, outs, equity, pot odds, implied odds, range),
sette mani svolte passo per passo con lo stesso metodo, errori comuni, riepilogo, quiz e glossario. Scritto per chi conosce poco il gioco.
Ogni numero è stato ricalcolato (vedi note nei commenti). Le percentuali tra scontri preflop sono valori indicativi arrotondati ("circa")."""
import copy
import re

from poker import (GLOS_COMPLETO, ODDS_BREVE, OUTS_BREVE, TAB_EQUITY, TAB_ODDS, TAB_OUTS, parla)

TIT = {}


class Sc:
    """Costruisce i beat di una scena: ogni b() aggiunge una frase parlata e lo stato che compare (righe della lavagna e sovrimpressioni si accumulano)."""

    def __init__(self, titolo, **base):
        self.t = titolo
        self.cur = dict(modo="tavolo", hero=[], board=[], pot=None, bet=None, vil="x", ev=[], lav=[], sov=[])
        self.cur.update(base)
        self.out = []

    def b(self, voce, lav=None, sov=None, reset=False, dopo=0.35, silenzio=0, **ov):
        st = copy.deepcopy(self.cur)
        if reset:
            st["lav"] = []
            st["sov"] = []
        if lav:
            st["lav"] += [lav] if isinstance(lav, tuple) else list(lav)
        if sov == "":
            st["sov"] = []
        elif sov:
            st["sov"] = (st["sov"] + [sov])[-3:]
        st.update(ov)
        self.cur = st
        self.out.append((self.t, copy.deepcopy(st), parla(voce) if voce else "", dopo, silenzio))
        return self

    def fine(self):
        if self.out:
            t, st, v, p, s = self.out[-1]
            self.out[-1] = (t, st, v, 1.3, s)
        return self.out


B1 = ["9h", "8h"]
BD = ["Kh", "7h", "2c", "4s"]
CUORI = [r + "h" for r in "AKQJT98765432"]


def scene():
    S = []

    # 1 ---------------------------------------------------------------- hook (senza carte: solo idee)
    s = Sc("Hook", modo="cartelli", testi=["Decidi con i numeri, non a sensazione"], n=1)
    s.b("Nel poker puoi prendere la decisione giusta e perdere lo stesso. E puoi prendere quella sbagliata e vincere. Per questo quasi tutti giocano a sensazione.")
    s.b("Chi vince nel lungo periodo fa un'altra cosa: confronta un prezzo con una probabilità. È un conto semplice, che dura pochi secondi.")
    s.b("In questo video lo imparerai da zero. Prima un po' di teoria, per capire come si ragiona. Poi le regole e le parole del poker, poi i calcoli, poi le mani una per una. Alla fine saprai decidere da solo.", sov="Prima la teoria, poi le mani")
    S += s.fine()

    # 1b --------------------------------------------------------------- teoria introduttiva (nessuna carta)
    s = Sc("Introduzione · Decisione e risultato", modo="cartelli", testi=["Decisione ≠ risultato", "Il poker è informazione incompleta", "Ogni scelta ha un prezzo"], n=1)
    s.b("Cominciamo dall'idea più importante, e non servono carte per capirla. Nel poker devi distinguere la decisione dal risultato.", sov="DECISIONE ≠ RISULTATO")
    s.b("Il poker è un gioco a informazione incompleta: non vedi le carte dell'avversario e non sai cosa uscirà. Quindi anche la scelta migliore può perdere, perché c'è la fortuna. Questa fortuna di breve periodo si chiama varianza.", n=2, sov="VARIANZA = la fortuna nel breve periodo")
    s.b("Una decisione si giudica da come si comporta se la ripeti mille volte, non da come va una volta sola. Se è giusta, alla lunga ti fa guadagnare, anche se stasera perdi.", n=3)
    S += s.fine()

    s = Sc("Introduzione · Prezzo contro probabilità", modo="cartelli", testi=["Prezzo: quanto devi pagare", "Premio: quanto puoi vincere", "Probabilità: quanto spesso vinci"], n=1)
    s.b("Ogni decisione di poker ha tre ingredienti. Il prezzo: quanto devi pagare per restare in gioco. Il premio: quanto puoi vincere. E la probabilità: quanto spesso vinci davvero.", sov="PREZZO · PREMIO · PROBABILITÀ")
    s.b("Facciamo un esempio senza carte. Paghi 10 fiches per tirare un dado. Se esce il 6, ricevi 60 fiches. Il 6 esce una volta su sei, quindi in media ricevi 60 diviso 6, cioè 10. Paghi 10 e in media riprendi 10: è un pareggio.", n=2, sov="1 su 6 × 60 = 10 → pareggio")
    s.b("Se il premio fosse 90, in media riprenderesti 15: ogni tiro ti farebbe guadagnare 5. Conviene. Se il premio fosse 30, in media riprenderesti 5: ogni tiro ti farebbe perdere 5. Non conviene.", n=3, sov="Premio 90: conviene · Premio 30: non conviene")
    s.b("Questo guadagno medio si chiama valore atteso, in inglese expected value. Una decisione è buona quando il valore atteso è positivo. Nel poker succede lo stesso: l'avversario punta, quello è il tuo prezzo; il piatto è il tuo premio; e la tua mano determina la probabilità.", sov="EXPECTED VALUE = guadagno medio nel lungo periodo")
    S += s.fine()

    s = Sc("Introduzione · Le tre domande", modo="scheda", passi=["Cosa ho? (le mie carte e i miei progetti)", "Cosa può avere lui? (il suo range)", "Quanto mi costa restare? (le pot odds)"], n=1, tabelle=False)
    s.b("In ogni mano ti farai tre domande, sempre le stesse. Prima: cosa ho? Cioè le tue carte e quello che possono diventare.", n=1)
    s.b("Seconda: cosa può avere lui? Non puoi saperlo, ma puoi stimare l'insieme delle sue mani possibili. Si chiama range.", n=2)
    s.b("Terza: quanto mi costa restare in gioco, rispetto a quanto posso vincere? Si chiama pot odds.", n=3)
    s.b("Ti spiego ognuna con calma, nell'ordine giusto. Prima le regole e le parole, così non ti perdi niente. Poi le carte e le probabilità. Solo dopo tutto questo, le mani vere.", sov="Prima la teoria, poi le mani")
    S += s.fine()

    # 2 ---------------------------------------------------------------- roadmap
    s = Sc("Cosa imparerai")
    passi = ["Parte 1 · Le regole e le parole del poker", "Parte 2 · La teoria: probabilità, outs, equity, pot odds", "Parte 3 · Capire la mano dell'avversario", "Parte 4 · Sette mani, passo per passo", "Parte 5 · Errori, riepilogo e quiz"]
    s.b("Il video è diviso in cinque parti.", modo="scheda", passi=passi, n=1, tabelle=False)
    s.b("Nella prima ripassiamo le regole e impariamo le parole inglesi del poker, una alla volta. Nella seconda arriva la teoria: probabilità, outs, equity e pot odds.", n=2)
    s.b("Nella terza impari a capire la mano dell'avversario: i range, le azioni, le dimensioni delle puntate.", n=3)
    s.b("Nella quarta applichiamo tutto a sette mani vere, con il conto fatto passo per passo. Nella quinta gli errori da evitare, un riepilogo da salvare e un quiz.", n=5)
    s.b("Il messaggio da portare a casa è uno solo: non esiste una percentuale fissa sopra cui giocare. La soglia la decide la puntata dell'avversario. Lo ripeteremo spesso.", sov="La soglia la decide la puntata dell'avversario")
    S += s.fine()

    # 3 ---------------------------------------------------------------- il gioco
    s = Sc("Parte 1 · Come funziona una mano", hero=B1)
    s.b("Il Texas Hold'em si gioca con un mazzo di 52 carte. Ogni giocatore riceve due carte coperte, solo sue. Poi sul tavolo vengono scoperte cinque carte comuni, che tutti possono usare.")
    s.b("Vince chi fa la migliore combinazione di cinque carte, scegliendo tra le sue due e le cinque del tavolo.")
    s.b("La mano si gioca in quattro fasi, e ogni fase ha un nome inglese. Preflop è la fase prima che esca qualsiasi carta comune: hai solo le tue due carte.", sov="PREFLOP = prima delle carte comuni")
    s.b("Flop sono le prime tre carte comuni, scoperte insieme.", board=["Kh", "7h", "2c"], sov="FLOP = le prime 3 carte comuni")
    s.b("Turn è la quarta carta comune.", board=BD, sov="TURN = la 4ª carta comune")
    s.b("River è la quinta e ultima.", board=BD + ["Qd"], sov="RIVER = la 5ª carta comune")
    s.b("L'insieme delle carte comuni si chiama board. Le fiches in gioco, al centro del tavolo, formano il pot, cioè il piatto.", pot=100, sov="BOARD = le carte comuni · POT = il piatto")
    s.b("Prima che le carte vengano date, due giocatori mettono nel piatto una puntata obbligatoria, i blind. Servono a far partire il gioco: senza qualcosa da vincere, nessuno avrebbe motivo di giocare.", sov="BLIND = puntata obbligatoria iniziale")
    s.b("Se alla fine sono ancora in due o più, si arriva allo showdown: i giocatori scoprono le carte e vince la combinazione migliore.", vil=["Ad", "Kc"], sov="SHOWDOWN = si scoprono le carte a fine mano")
    S += s.fine()

    # 4 ---------------------------------------------------------------- azioni
    s = Sc("Parte 1 · Le azioni", hero=B1, board=BD, pot=100)
    s.b("Quando tocca a te, hai a disposizione poche azioni, tutte con un nome inglese. Immagina il pot a 100 fiches.")
    s.b("Se nessuno ha ancora puntato, puoi fare bet, cioè puntare: metti fiches nel piatto. Oppure puoi fare check: passi la parola senza puntare, e resti in gioco.", bet=50, bet_t="BET", sov="BET = puntare · CHECK = passare")
    s.b("Da qui in poi chiamerò hero il giocatore che decide, cioè te, e villain l'avversario.", sov="HERO = tu · VILLAIN = l'avversario")
    s.b("Se il villain ha puntato 50, per restare in gioco devi fare call: pareggiare la sua puntata, quindi mettere anche tu 50. Oppure puoi fare raise: rilanciare, cioè pareggiare e aggiungere altre fiches, per costringere gli altri a pagare di più.", sov="CALL = pareggiare · RAISE = rilanciare")
    s.b("Se non vuoi pagare, fai fold: abbandoni la mano. Perdi le fiches che hai già messo, ma non ne perdi altre.", sov="FOLD = abbandonare la mano")
    s.b("All'estremo c'è l'all-in: punti tutte le fiches che hai davanti a te. Queste fiches si chiamano stack.", bet=100, bet_t="ALL-IN", sov="ALL-IN = puntare tutto · STACK = le tue fiches")
    s.b("In questo video parleremo quasi sempre di una sola scelta: il villain ha puntato e tu devi decidere tra call e fold. È la decisione più frequente al tavolo, ed è quella in cui la matematica aiuta di più.")
    S += s.fine()

    # 5 ---------------------------------------------------------------- combinazioni
    R = [("Scala reale", "10, J, Q, K, A dello stesso seme", ["Th", "Jh", "Qh", "Kh", "Ah"]), ("Scala colore", "cinque carte in scala dello stesso seme", ["4h", "5h", "6h", "7h", "8h"]),
         ("Poker", "quattro carte uguali", ["7s", "7h", "7d", "7c", "Ah"]), ("Full", "un tris e una coppia", ["Kd", "Kh", "Ks", "4c", "4d"]),
         ("Colore (flush)", "cinque carte dello stesso seme", ["As", "Js", "8s", "5s", "2s"]), ("Scala (straight)", "cinque carte consecutive", ["5s", "6h", "7d", "8c", "9s"]),
         ("Tris", "tre carte uguali", ["9s", "9h", "9d", "Kc", "4s"]), ("Doppia coppia", "due coppie", ["Qs", "Qh", "7d", "7c", "3s"]),
         ("Coppia", "due carte uguali", ["Ks", "Kh", "9d", "6c", "2s"]), ("Carta alta", "nessuna combinazione", ["As", "Jd", "8c", "5h", "2s"])]
    s = Sc("Parte 1 · Le combinazioni")
    s.b("Per decidere se una mano è buona devi conoscere le combinazioni. Le vediamo dalla più forte alla più debole.", modo="mani", righe=R, n=1)
    s.b("La scala reale batte tutto, poi la scala colore e il poker. Poi il full, cioè un tris più una coppia.", n=4)
    s.b("Il colore, in inglese flush, sono cinque carte dello stesso seme. La scala, in inglese straight, sono cinque carte consecutive. Questi due nomi ci serviranno spesso.", n=6, sov="FLUSH = colore · STRAIGHT = scala")
    s.b("Poi il tris, la doppia coppia, la coppia e infine la carta alta.", n=10)
    s.b("Se due giocatori hanno la stessa coppia, vince chi ha la carta laterale più alta. Si chiama kicker.", sov="KICKER = la carta laterale che decide a parità")
    S += s.fine()

    # 6 ---------------------------------------------------------------- draw
    s = Sc("Parte 1 · I progetti (draw)", hero=B1, board=["Kh", "7h", "2c"], ev=["Kh", "7h", "9h", "8h"])
    s.b("Quasi mai hai già la mano migliore. Molto più spesso hai una mano incompleta, che può migliorare con le carte che devono ancora uscire. Si chiama draw, cioè progetto.", sov="DRAW = progetto: mano incompleta che può migliorare")
    s.b("Qui hai 9♥8♥ e sul board ci sono K♥ e 7♥: hai quattro cuori e te ne manca uno per fare colore. È un flush draw, un progetto di colore.", sov="FLUSH DRAW = progetto di colore")
    s.b("L'altro progetto classico è lo straight draw, il progetto di scala. Hai 9♠8♦ e sul board 7♣ 6♥ 2♠. Ti serve un 10 oppure un 5: puoi completare la scala da entrambi i lati.", hero=["9s", "8d"], board=["7c", "6h", "2s"], ev=[], sov="STRAIGHT DRAW = progetto di scala")
    s.b("Questo si chiama open-ended: scala aperta da due lati.", sov="OPEN-ENDED = scala aperta da due lati")
    s.b("Se invece ti serve una sola carta precisa, per esempio un 7 con 9♠8♦ sul board 6♣ 5♥ 2♠, hai un gutshot: una scala interna.", board=["6c", "5h", "2s"], sov="GUTSHOT = scala interna, una sola carta")
    S += s.fine()

    # 7 ---------------------------------------------------------------- probabilità
    s = Sc("Parte 2 · La probabilità da zero", modo="mazzo", known=[], outs=[])
    s.b("Prima di contare le carte, ricordiamo cos'è una probabilità. Si calcola così: quante carte ti vanno bene, diviso quante carte possono uscire.")
    s.b("Un mazzo ha 52 carte. I cuori sono 13. Se peschi una carta a caso, la probabilità che sia un cuori è 13 diviso 52: un quarto, cioè 25%. In pratica, una volta su quattro.", outs=CUORI, lav=[("13 ÷ 52 = 25%", "y"), ("1 volta su 4", "g")])
    s.b("In una mano di poker però non peschi da un mazzo intero: alcune carte le vedi già. Le tue due e quelle sul board non possono più uscire, quindi le togli dal conto.", known=["9h", "8h", "Kh", "7h", "2c", "4s"], outs=[], reset=True)
    s.b("Al turn vedi sei carte: le tue 2 e le 4 del board. Restano 52 meno 6, cioè 46 carte che non vedi.", lav=("52 − 2 − 4 = 46", "y"))
    s.b("Tra queste 46 ci sono anche le due carte coperte dell'avversario. Tu non le conosci, quindi per te sono come carte ancora nel mazzo.", lav=("Carte che non vedi: 46", "w"))
    S += s.fine()

    # 8 ---------------------------------------------------------------- outs
    s = Sc("Parte 2 · Gli outs", modo="mazzo", known=["9h", "8h", "Kh", "7h", "2c", "4s"], outs=[])
    s.b("Ora possiamo definire gli outs: sono le carte ancora nel mazzo che migliorano la tua mano. Nel nostro caso, i cuori che restano.", outs=[c for c in CUORI if c not in ("9h", "8h", "Kh", "7h")], sov="OUTS = carte che migliorano la tua mano")
    s.b("Quanti sono? Un seme ha 13 carte. Quattro cuori li vedi già: due in mano e due sul board. 13 meno 4 fa 9. Hai 9 outs.", lav=[("13 − 4 = 9", "y"), ("9 OUTS", "g")])
    s.b("Con lo stesso metodo si contano tutti i progetti. Un flush draw vale 9 outs. Un open-ended, 8: servono 4 carte da un lato e 4 dall'altro.", modo="tabella", titolo="Gli outs dei progetti più comuni", testa=TAB_OUTS[0], righe=TAB_OUTS[1], n=2)
    s.b("Un gutshot vale 4 outs: la carta giusta è una sola, e ce ne sono quattro nel mazzo.", n=3)
    s.b("Un'overcard è una carta più alta di quelle sul board. Con A♠K♦ su un board 9♣ 6♥ 2♠, ogni asso o re ti dà la coppia più alta: 3 più 3, 6 outs.", n=4, sov="OVERCARD = carta più alta del board")
    s.b("Se hai una coppia in mano e cerchi il set, cioè il tris fatto con la tua coppia più una carta del board, ti restano solo 2 outs.", n=5, sov="SET = tris con coppia in mano")
    s.b("L'ultima riga è la più ricca: J♠T♠ su un board 9♠ 8♠ 2♦ ha un flush draw e un open-ended insieme. Sono 9 più 6, perché due carte erano già nel conto dei cuori: 15 outs. La useremo in una mano.", n=6)
    s.b("Attenzione agli outs sporchi, in inglese dirty outs: sono carte che ti migliorano ma possono dare all'avversario una mano ancora migliore. Se il board ha già una coppia, per esempio, un cuori che ti dà colore può dare a lui un full.", sov="DIRTY OUTS = outs che possono aiutare anche l'avversario")
    s.b("Quando hai dubbi, contali a metà oppure non contarli.")
    S += s.fine()

    # 9 ---------------------------------------------------------------- equity
    s = Sc("Parte 2 · Da outs a equity", hero=B1, board=BD, ev=["Kh", "7h", "9h", "8h"])
    s.b("Gli outs sono un conteggio. Serve una percentuale: si chiama equity ed è la percentuale di volte in cui vinci la mano se si arriva fino in fondo.", sov="EQUITY = % di volte che vinci la mano")
    s.b("Il calcolo esatto è semplice. Al turn restano 46 carte e 9 sono buone: 9 diviso 46 fa 19,6%. È la probabilità che il river sia un cuori.", lav=[("9 ÷ 46 = 19,6%", "y")])
    s.b("Al tavolo però non si fanno divisioni a mente. Si usa una scorciatoia: la regola del 2 e del 4. Se devi vedere una sola carta, moltiplichi gli outs per 2. 9 per 2 fa 18%, vicinissimo al 19,6% esatto.", lav=[("1 carta → outs × 2", "b"), ("9 × 2 = 18% (esatto 19,6%)", "y")], sov="Una carta da vedere → outs × 2")
    s.b("Perché funziona? Ogni carta del mazzo pesa circa il 2% di probabilità: uno diviso 46 fa 2,2%. Moltiplicare per 2 è un arrotondamento comodo.")
    s.b("Se invece sei al flop e vedrai sicuramente sia il turn sia il river, hai due carte da vedere e moltiplichi per 4. Con 9 outs fa 36%, e il valore esatto è 35%.", board=["Kh", "7h", "2c"], lav=[("2 carte → outs × 4", "b"), ("9 × 4 = 36% − 1 = 35%", "y")], sov="Due carte, solo se ALL-IN → outs × 4")
    s.b("Attenzione però a quel 'sicuramente': vuol dire che sei all-in. Se l'avversario può puntare di nuovo al turn, tu stai pagando per vedere una carta sola, e devi usare il 2. È l'errore più comune di tutti, e ci torneremo.")
    s.b("Ultima correzione: con più di 8 outs la regola del 4 esagera. Togli la differenza tra i tuoi outs e 8. Con 15 outs: 15 per 4 fa 60, meno 7, fa 53%. Il valore esatto è 54%.", lav=[("15 × 4 = 60 → 60 − 7 = 53%", "y"), ("esatto 54%", "g")], sov="Più di 8 outs → togli (outs − 8)")
    s.b("Ecco la tabella completa, con la stima rapida sempre accanto al valore esatto.", modo="tabella", titolo="Da outs a equity", testa=TAB_EQUITY[0], righe=TAB_EQUITY[1], n=4, sov="")
    S += s.fine()

    # 10 --------------------------------------------------------------- pot odds
    s = Sc("Parte 2 · Le pot odds", hero=B1, board=BD, pot=100, bet=50)
    s.b("Ora la seconda metà del problema: quanto ti costa vedere la carta. L'avversario ha puntato e, per restare in gioco, devi chiamare. La domanda è se il prezzo vale la pena.")
    s.b("È come un acquisto: per avere la possibilità di vincere un pot da 200 ne paghi 50. Le pot odds trasformano questo rapporto in una percentuale: la quota minima di volte in cui devi vincere perché il call non faccia perdere fiches nel lungo periodo.", sov="POT ODDS = % minima di vittoria che ti serve per chiamare")
    s.b("La formula è una sola: prendi quanto devi chiamare e dividilo per il pot totale dopo il tuo call. Cioè il pot di partenza, più la bet del villain, più il tuo call.", lav=("call ÷ (pot + bet + call)", "w"), sov="Equity richiesta = call ÷ (pot + bet + call)")
    s.b("Nel pot ci sono 100 fiches, il villain punta 50 e tu per chiamare ne metti 50. Il pot finale è 100 più 50 più 50: 200.", lav=("100 + 50 + 50 = 200", "y"))
    s.b("50 diviso 200 fa 25%. Ti serve vincere almeno una volta su quattro.", lav=("50 ÷ 200 = 25%", "g"))
    s.b("Perché proprio il 25% è il punto di pareggio? Guarda quattro call uguali. Ne perdi tre: perdi 50 fiches ciascuna, cioè 150. Ne vinci uno: guadagni il pot di 100 più la bet di 50 del villain, cioè 150. Fai pari.", lav=[("4 call: 3 persi = −150", "r"), ("1 vinto = +150", "g"), ("Pareggio → 25%", "y")])
    s.b("Non devi rifare il conto ogni volta: il risultato dipende solo da quanto è grande la bet rispetto al pot. Ecco i cinque casi più frequenti. Impara questa tabella a memoria: è metà del lavoro.", modo="tabella", titolo="Le pot odds dei cinque casi più comuni", testa=TAB_ODDS[0], righe=TAB_ODDS[1], n=5, sov="Più grande la bet, più equity ti serve")
    S += s.fine()

    # 11 --------------------------------------------------------------- regola
    s = Sc("Parte 2 · La regola decisionale")
    s.b("Ecco il cuore di tutto il video. Hai due numeri: la tua equity, cioè quanto spesso vinci, e l'equity richiesta dalle pot odds, cioè quanto spesso ti serve vincere.", modo="bilancia", incl=None)
    s.b("Se la prima è più alta della seconda, fai call.", incl="sx", sov="EQUITY > EQUITY RICHIESTA → CALL")
    s.b("Se è più bassa, fai fold.", incl="dx", sov="altrimenti → FOLD")
    s.b("Non esiste una percentuale fissa sopra cui giocare. La soglia la decide l'avversario con la sua bet: cambia la bet, cambia la soglia.", incl=None)
    s.b("C'è una sola eccezione importante, e te la spiego subito.")
    S += s.fine()

    # 12 --------------------------------------------------------------- implied odds
    s = Sc("Parte 2 · Le implied odds", hero=["5c", "5d"], board=[], pot=None, bet=30, bet_t="RILANCIO", stack="1000")
    s.b("A volte la regola dice fold, ma il call conviene lo stesso. Succede per le implied odds: le fiches extra che pensi di vincere nelle puntate successive, se completi il progetto.", sov="IMPLIED ODDS = fiches extra che vincerai dopo, se centri")
    s.b("Il motivo è semplice: il pot attuale non è l'unico che puoi vincere. Se centri la carta che ti serve, l'avversario può continuare a puntare, e tu vinci molto di più.")
    s.b("Funziona solo a due condizioni. La prima: il tuo progetto è nascosto, cioè se centri l'avversario non se ne accorge. La seconda: l'avversario ha molte fiches davanti, cioè uno stack grande.")
    s.b("L'esempio classico è il set mining: chiamare con una coppia piccola, sperando di fare set al flop. Lo vedremo in una mano.", sov="SET MINING = chiamare con coppia piccola per fare set")
    S += s.fine()

    # 13 --------------------------------------------------------------- range
    s = Sc("Parte 3 · Capire l'avversario: il range")
    s.b("Finora abbiamo contato carte come se le mani dell'avversario non esistessero. In effetti non le conosci. Ma puoi stimare l'insieme di tutte le mani che il villain potrebbe avere in quella situazione. Si chiama range, ed è la parte più importante del poker: dal prossimo capitolo impari a ragionarci passo per passo.", modo="tavolo", hero=["7s", "7h"], vil="x", sov="RANGE = tutte le mani che l'avversario può avere")
    s.b("I professionisti non pensano 'ha un asso': pensano 'ha una di queste venti mani'. Per capire perché conta, guarda come cambia l'equity al cambiare della mano avversaria. I valori sono indicativi e arrotondati.")
    RB = [(["7s", "7h"], ["Ad", "Kc"], 55), (["Ks", "Kh"], ["Qd", "Qc"], 82), (["Ac", "Qh"], ["As", "Kd"], 25)]
    s.b("Una coppia contro due overcard, per esempio 7♠7♥ contro A♦K♣, è quasi un testa o croce: circa 55 a 45 per la coppia.", modo="barre", righe=RB, n=1, sov="")
    s.b("Un overpair, cioè una coppia più alta contro una coppia più bassa: K♠K♥ contro Q♦Q♣, circa 82 a 18.", n=2, sov="OVERPAIR = coppia più alta della coppia avversaria")
    s.b("Una dominated hand è una mano dominata: A♣Q♥ contro A♠K♦. Avete lo stesso asso, ma il kicker di lui è più alto. Circa 25 a 75.", n=3, sov="DOMINATED HAND = stessa carta alta, l'altra peggiore")
    s.b("Lo stesso identico 7♠7♥, quindi, vale il 55% contro una mano e il 20% contro un'altra. La tua equity dipende da cosa ha lui: ecco perché dobbiamo imparare a capirlo.")
    S += s.fine()

    FAM = (["Famiglia di mani", "Esempio sul board K♥ 7♥ 2♣ 4♠", "Cosa fa"], [
        ["Mano fatta forte", "A♦K♣ (top pair) · 7♠7♦ (set)", "ha già vinto o quasi"], ["Mano media", "Q♦Q♣ (coppia sotto il re)", "ha valore, non vuole grosse puntate"],
        ["Progetto (draw)", "A♥Q♥ (colore) · 6♠5♠ (scala)", "può migliorare"], ["Aria", "J♦T♣ (niente)", "non ha nulla"]])
    s = Sc("Parte 3 · Passo 1: le famiglie di mani", hero=B1, board=BD, pot=100, bet=50)
    s.b("Come si ragiona su un range? Si parte dividendo le mani in famiglie. Prendiamo il nostro board, K♥ 7♥ 2♣ 4♠, e immaginiamo che il villain stia puntando.")
    s.b("Prima famiglia: le mani fatte forti. Per esempio A♦K♣, che ha la coppia di re con il kicker più alto. Si chiama top pair: la coppia con la carta più alta del board. Oppure 7♠7♦, che ha fatto set.", modo="tabella", titolo="Le famiglie di mani", testa=FAM[0], righe=FAM[1], n=1, sov="TOP PAIR = coppia con la carta più alta del board")
    s.b("Seconda famiglia: le mani medie, per esempio Q♦Q♣. Una coppia, ma sotto il re del board: ha valore, però non vuole giocare grossi piatti.", n=2)
    s.b("Terza: i progetti, i draw. A♥Q♥ ha un progetto di colore, 6♠5♠ un progetto di scala.", n=3)
    s.b("Quarta: l'aria, cioè mani che non hanno niente, per esempio J♦T♣. Un avversario può puntare anche con queste: si chiama bluff, puntare senza avere la mano per far foldare l'altro.", n=4, sov="BLUFF = puntare senza mano, per far foldare")
    s.b("Quando invece punta con una mano forte per farsi pagare da mani peggiori, si parla di value bet, una puntata di valore.", sov="VALUE BET = puntata per farsi pagare da mani peggiori")
    S += s.fine()

    s = Sc("Parte 3 · Passo 2: le azioni raccontano una storia", hero=B1, board=BD, pot=100, bet=50)
    s.b("Ogni azione dell'avversario toglie alcune mani dal suo range. È come un'indagine: ogni indizio restringe i sospettati.")
    s.b("Preflop il villain ha rilanciato. Chi rilancia di solito ha mani buone: quelle più deboli, come 7♣2♦, quasi mai.", lav=("Preflop: rilancia → mani buone", "w"))
    s.b("Al flop ha puntato: possono essere mani fatte, progetti, qualche bluff.", lav=("Flop: punta → fatte, progetti, bluff", "w"))
    s.b("Al turn punta ancora. Adesso restano soprattutto le mani che vogliono davvero continuare: chi aveva un bluff debole spesso si ferma qui.", lav=("Turn: punta ancora → più forte, o progetto che insiste", "y"))
    s.b("Se invece passa, cioè fa check, di solito non ha una mano molto forte. Ma attenzione: a volte è una trappola, finge debolezza per farti puntare.", lav=("Check → di solito debole, a volte trappola", "b"))
    s.b("Nessuna lettura è certa: sono indizi, non prove. Servono a spostare le probabilità, non a conoscere le carte.")
    S += s.fine()

    s = Sc("Parte 3 · Passo 3: la dimensione della bet", hero=B1, board=BD, pot=100, bet=33)
    s.b("Anche la grandezza della puntata è un indizio. Qui il villain punta 33, circa un terzo del pot.")
    s.b("Una bet piccola, di solito, viene da mani medie che vogliono solo vedere cosa fai, oppure da mani forti che vogliono farsi pagare da mani deboli.", lav=("Bet piccola → media, oppure value bet leggera", "w"))
    s.b("Ora il villain punta 100, cioè tutto il pot. Una bet grande è quasi sempre una di due cose: una mano molto forte che vuole incassare, oppure un bluff che vuole farti foldare.", bet=100, lav=("Bet grande → molto forte oppure bluff", "y"), sov="BET GRANDE = molto forte oppure bluff")
    s.b("E ricorda il legame con le pot odds: più la bet è grande, più equity ti serve. Con la bet da 100 ti serve il 33,3%.", lav=("Pot pieno → equity richiesta 33,3%", "b"))
    s.b("Quindi davanti a una bet grande chiediti: questo avversario ha davvero una mano così forte più spesso di quanto bluffa?")
    S += s.fine()

    VS = (["Mano del villain", "Cosa ha", "La tua equity (9♥8♥)"], [["A♦K♣", "top pair, coppia di re", "20,5%"], ["7♠7♦", "set di sette", "15,9%"], ["A♥Q♥", "colore con l'asso, ancora da fare", "13,6%"], ["6♠5♠", "progetto di scala", "77,3%"]])
    s = Sc("Parte 3 · Passo 4: la tua equity contro le sue mani", hero=B1, board=BD, pot=100, bet=50, ev=["Kh", "7h", "9h", "8h"])
    s.b("Rivediamo la nostra mano, 9♥8♥ sul board K♥ 7♥ 2♣ 4♠, al turn. Finora abbiamo usato 9 diviso 46, cioè abbiamo ipotizzato mani a caso. Ora contiamo contro mani precise: restano 44 carte, perché ne vediamo 6 e conosciamo le 2 del villain.", lav=("52 − 6 − 2 = 44", "w"))
    s.b("Contro A♦K♣, la coppia di re, hai il 20,5%. Ti servono i cuori: 9 carte su 44. È quasi come il nostro 19,6%.", modo="tabella", titolo="La tua equity contro mani precise", testa=VS[0], righe=VS[1], n=1, sov="")
    s.b("Contro il set di sette, 7♠7♦, scendi al 15,9%. Il 2♥ e il 4♥ ti darebbero colore, ma appaiano il board e gli darebbero il full: sono dirty outs. Restano 7 outs puliti, 7 su 44.", n=2, sov="DIRTY OUTS: 2♥ e 4♥ gli danno il full")
    s.b("Contro A♥Q♥, il colore con l'asso, scendi al 13,6%. Se esce un altro cuori vince lui, con il colore più alto. Ti salvi solo accoppiando un 9 o un 8: 6 carte su 44.", n=3)
    s.b("Contro 6♠5♠, un progetto di scala, sei tu il favorito: 77,3%. A lui servono 10 carte su 44, tra scale e coppie.", n=4)
    s.b("Guarda quanto cambia: da circa il 14% a circa il 77%, con la stessa identica mano. La tua equity dipende da cosa ha lui.", sov="")
    S += s.fine()

    s = Sc("Parte 3 · Passo 5: pesare il range", hero=B1, board=BD, pot=100, bet=50)
    s.b("Ora la domanda finale: quanto pesa ciascuna di queste mani? Facciamo un esempio semplificato: dai al villain dieci mani possibili, tutte ugualmente probabili. La tua equity totale è la media.")
    s.b("Primo avversario, prudente: punta solo con mani forti. Nel suo range ci sono 6 mani da top pair, 3 set e 1 colore con l'asso.", lav=("Prudente: 6 top pair · 3 set · 1 colore", "w"))
    s.b("Fai la media: 6 per 20,5, più 3 per 15,9, più 1 per 13,6, diviso 10. Fa circa 18,4%. Le pot odds chiedono il 25%: fold.", lav=[("(6×20,5 + 3×15,9 + 1×13,6) ÷ 10", "y"), ("= 18,4% < 25% → FOLD", "r")])
    s.b("Secondo avversario, aggressivo: punta anche con i progetti. Nel suo range ci sono 4 top pair, 2 set, 2 colori con l'asso e 2 scale aperte.", reset=True, lav=("Aggressivo: 4 top pair · 2 set · 2 colori · 2 scale", "w"))
    s.b("Media: 4 per 20,5, più 2 per 15,9, più 2 per 13,6, più 2 per 77,3, diviso 10. Fa circa 29,6%. Più del 25%: call.", lav=[("(4×20,5 + 2×15,9 + 2×13,6 + 2×77,3) ÷ 10", "y"), ("= 29,6% > 25% → CALL", "g")])
    s.b("Stessa mano, stessa bet, decisione opposta: è cambiato solo ciò che pensi che abbia. Questo è un esempio didattico, nel gioco vero non hai numeri così precisi. Ma il ragionamento è lo stesso: più progetti e bluff ci sono nel suo range, più il call diventa giusto.", sov="Più progetti e bluff nel suo range → più il call è giusto")
    s.b("Come si impara a stimare il range? Prima di decidere, fatti tre domande: che storia racconta la mano? Che dimensione ha la bet? Che tipo di giocatore ho davanti, prudente o aggressivo?")
    S += s.fine()

    # 14 --------------------------------------------------------------- metodo
    s = Sc("Il metodo completo")
    pas = ["Leggi l'avversario: che mani può avere?", "Conta gli outs", "Equity: outs × 2 (una carta) · × 4 (solo all-in)", "Equity richiesta = call ÷ (pot + bet + call)", "Equity > richiesta → CALL · altrimenti → FOLD"]
    s.b("Mettiamo tutto in fila. Il metodo completo ha cinque passi.", modo="scheda", passi=pas, n=1, tabelle=False)
    s.b("Passo zero: leggi l'avversario e immagina il suo range. Poi i quattro passi di calcolo: conta gli outs, trasformali in equity, calcola l'equity richiesta con le pot odds, confronta.", n=3)
    s.b("Nelle prossime sette mani useremo il conto standard, quello con gli outs, e ogni volta ti dirò quando la lettura dell'avversario potrebbe cambiare la decisione.", n=5)
    S += s.fine()

    # ---------------------------------------------------------------- mani
    def mano(t, hero, board, pot, bet, **kw):
        return Sc(t, hero=hero, board=board, pot=pot, bet=bet, **kw)

    s = mano("Mano 1 · Il flush draw al turn", B1, BD, 100, 50, ev=["Kh", "7h", "9h", "8h"])
    s.b("Mano uno. Hero ha 9♥8♥, il board è K♥ 7♥ 2♣ 4♠: siamo al turn. Il pot è 100 e il villain punta 50.")
    s.b("Primo passo, gli outs: 9 cuori. Perché non contiamo anche i 9 e gli 8? Perché una coppia di 9 o di 8 non batte un avversario che ha un re.", lav=("1) OUTS: 9 cuori", "w"))
    s.b("Secondo passo, l'equity: manca una sola carta, quindi 9 per 2, 18%. Il valore esatto è 19,6%.", lav=("2) EQUITY: 9 × 2 = 18% (esatto 19,6%)", "y"))
    s.b("Terzo passo, le pot odds: una bet di metà pot, quindi 25%.", lav=("3) POT ODDS: 50 ÷ 200 = 25%", "b"))
    s.b("Quarto passo, il confronto: 19,6 è meno di 25. La decisione corretta è fold.", lav=("4) 19,6% < 25% → FOLD", "r"), sov="19,6% < 25% → FOLD")
    s.b("È questa la risposta che sorprende: un progetto di colore, da solo, non giustifica un call di mezzo pot al turn.")
    S += s.fine()

    s = mano("Mano 2 · Stessa mano, bet diversa", B1, BD, 100, 25, ev=["Kh", "7h", "9h", "8h"])
    s.b("Stessa identica situazione: stesse carte, stesso board, stesso pot. Cambia una sola cosa: il villain punta 25 invece di 50.")
    s.b("La tua equity non è cambiata: sempre 19,6%.", lav=("Equity: 19,6%", "y"))
    s.b("Sono cambiate le pot odds: 25 diviso 150, cioè 100 più 25 più 25, fa 16,7%.", lav=("Pot odds: 25 ÷ 150 = 16,7%", "b"))
    s.b("Ora 19,6 è più di 16,7. La decisione corretta è call.", lav=("19,6% > 16,7% → CALL", "g"), sov="19,6% > 16,7% → CALL")
    s.b("Stessa mano, decisione opposta. È per questo che non esiste una percentuale magica: la soglia la sposta la bet dell'avversario.", sov="Stessa mano, bet diversa → decisione diversa")
    S += s.fine()

    s = mano("Mano 3 · Il gutshot e la trappola del × 4", ["9c", "8d"], ["Jh", "7s", "2c"], 90, 60, ev=["7s"])
    s.b("Mano tre. Hero ha 9♣8♦, il flop è J♥ 7♠ 2♣. Il pot è 90 e il villain punta 60, cioè due terzi del pot, e non è all-in.")
    s.b("Hai un gutshot: ti serve solo un 10 per fare scala, da 7 a J. Sono 4 outs.", lav=("1) OUTS: 4 (un 10)", "w"))
    s.b("Il villain non è all-in: se il turn non ti aiuta può puntare di nuovo. Quindi stai pagando per vedere una carta sola. Regola del 2: 4 per 2, 8%. Esatto: 4 diviso 47, cioè 8,5%.", lav=("2) EQUITY: 4 × 2 = 8% (esatto 8,5%)", "y"))
    s.b("Pot odds a due terzi del pot: 60 diviso 210, 28,6%. 8 contro 28: fold netto.", lav=[("3) POT ODDS: 60 ÷ 210 = 28,6%", "b"), ("4) 8% < 28,6% → FOLD", "r")])
    s.b("Ora la trappola. Cambiamo una sola carta del flop: J♥ T♠ 2♣. Adesso hai un open-ended: va bene una Q o un 7, 8 outs.", board=["Jh", "Ts", "2c"], ev=["Ts"], reset=True, lav=("OUTS: 8 (Q o 7)", "w"))
    s.b("Chi sbaglia fa così: 8 per 4, 32%. E 32 è più di 28,6, quindi chiama. Sbagliato.", lav=("8 × 4 = 32%  ✗", "r"))
    s.b("Non sei all-in: la carta che stai pagando è una sola. 8 per 2 fa 16%, esatto 17%. 17 contro 28,6: per la sola matematica è fold.", lav=[("8 × 2 = 16% (esatto 17%)", "y"), ("17% < 28,6% → FOLD", "r")], sov="NON sei all-in? → × 2, mai × 4")
    s.b("Al tavolo un call qui può avere senso per un altro motivo, le implied odds. Ma devi sapere che la stai pagando cara: non illuderti di avere il 32%.")
    S += s.fine()

    s = mano("Mano 4 · Due overcard", ["As", "Kd"], ["9c", "6h", "2s"], 100, 50, ev=[])
    s.b("Mano quattro. Hero ha A♠K♦, il flop è 9♣ 6♥ 2♠. Il pot è 100, il villain punta 50 e non è all-in.")
    s.b("Primo passo, gli outs: hai due overcard. Gli assi sono 3 e i re sono 3: 6 outs.", lav=("1) OUTS: 3 assi + 3 re = 6", "w"))
    s.b("Secondo passo: non sei all-in, quindi una carta sola. 6 per 2 fa 12%. Il valore esatto è 6 diviso 47, cioè 12,8%.", lav=("2) EQUITY: 6 × 2 = 12% (esatto 12,8%)", "y"))
    s.b("Terzo passo: 50 diviso 200, 25%. Quarto passo: 12 è molto meno di 25.", lav=[("3) POT ODDS: 50 ÷ 200 = 25%", "b"), ("4) 12% < 25% → FOLD", "r")], sov="12% < 25% → FOLD")
    s.b("La lezione: due overcard sembrano forti, ma da sole valgono pochi outs. Per chiamare una bet di mezzo pot servirebbe molto di più.")
    S += s.fine()

    s = Sc("Mano 5 · Il combo draw all-in", hero=["Js", "Ts"], board=["9s", "8s", "2d"], pot=100, bet=100, bet_t="ALL-IN")
    s.b("Mano cinque. Hero ha J♠T♠, il flop è 9♠ 8♠ 2♦. Il pot è 100 e il villain va all-in per 100, cioè una bet pari al pot. Supponiamo che abbia una coppia di assi: A♦A♣.", vil=["Ad", "Ac"])
    s.b("Primo passo, gli outs. Hai un flush draw: 9 picche. Hai anche un open-ended: ti servono una Q o un 7. Le Q e i 7 sono 8 carte, ma due sono picche e le hai già contate. Restano 6. 9 più 6 fa 15 outs.", lav=[("1) 9 picche + 6 della scala", "w"), ("OUTS: 9 + 6 = 15", "y")])
    s.b("Secondo passo. Qui puoi usare la regola del 4, perché sei all-in: vedrai sicuramente turn e river. 15 per 4 fa 60. Sopra gli 8 outs togli la differenza: 15 meno 8 fa 7. 60 meno 7: 53%. Il valore esatto è circa 54%.", lav=[("2) 15 × 4 = 60", "w"), ("60 − (15 − 8) = 53%", "y"), ("esatto ~54%", "g")], sov="All-in sul flop → × 4")
    s.b("Terzo passo: bet pari al pot, quindi 100 diviso 300, 33,3%. Quarto passo: 54 contro 33, call, senza esitare. Anzi, sei tu il favorito, anche se in questo momento non hai nemmeno una coppia.", lav=[("3) POT ODDS: 100 ÷ 300 = 33,3%", "b"), ("4) 54% > 33,3% → CALL", "g")], sov="54% > 33,3% → CALL (e sei favorito)")
    s.b("Una nota: se il villain avesse un set, per esempio 9-9, molti dei tuoi outs diventerebbero dirty outs, perché alcune carte che ti danno colore o scala gli darebbero il full. La tua equity scenderebbe molto.", vil=["9d", "9c"])
    S += s.fine()

    s = Sc("Mano 6 · Preflop all-in contro un range", hero=["7s", "7h"], board=[], pot=200, bet=400, bet_t="ALL-IN")
    s.b("Mano sei, preflop. Nel pot ci sono 200 fiches, il villain va all-in per 400 e hero ha 7♠7♥. Non ci sono outs da contare: ci serve l'equity contro le sue possibili mani.")
    s.b("Primo conto, le pot odds. Per chiamare metti 400. Pot finale: 200 più 400 più 400, 1000. 400 diviso 1000: ti serve il 40%.", lav=[("Call 400", "w"), ("200 + 400 + 400 = 1000", "y"), ("400 ÷ 1000 = 40%", "g")])
    s.b("Se il villain ha A-K, hai circa il 55%: call.", vil=["Ad", "Kc"], lav=("vs A-K: ~55% > 40% → CALL", "g"))
    s.b("Se ha Q-Q, hai circa il 20%: fold.", vil=["Qd", "Qc"], lav=("vs Q-Q: ~20% < 40% → FOLD", "r"))
    s.b("Il problema è che non sai cosa ha. Ed è qui che si vede la differenza tra chi gioca a sensazione e chi ragiona sul range: se pensi che l'avversario abbia più spesso mani come A-K che come Q-Q, il call è giusto; se pensi il contrario, no.", vil="x", sov="RANGE = tutte le mani che l'avversario può avere")
    S += s.fine()

    s = Sc("Mano 7 · Set mining e implied odds", hero=["5c", "5d"], board=[], pot=None, bet=30, bet_t="RILANCIO", stack="1000")
    s.b("Mano sette. Hero ha 5♣5♦. Il villain rilancia preflop a 30 e ha davanti a sé 1000 fiches di stack.")
    s.b("Una piccola coppia fa set al flop circa il 12% delle volte: una volta su 8,5. Se guardi solo il pot attuale, il call non conviene.", lav=("Set al flop: circa 12% (1 volta su 8,5)", "w"))
    s.b("Ma fai il conto su più mani. In 8,5 tentativi ne perdi 7,5, e ognuno ti costa 30 fiches: in tutto circa 225.", lav=("7,5 × 30 = circa 225 fiches", "r"))
    s.b("Per andare in pari ti basta vincere 225 fiches in più quella volta che centri. Con un avversario che ha 1000 fiches e una mano forte, è realistico.", lav=("Pareggio: vincere 225 in più", "y"))
    s.b("Nella pratica si usa una regola più prudente: chiama se le fiches che puoi ancora vincere sono almeno 15 o 20 volte il call. Più del minimo teorico, perché non sempre vieni pagato e a volte anche un set perde.", sov="Regola pratica: fiches vincibili ≥ 15-20 × il call")
    s.b("Qui 1000 diviso 30 fa circa 33 volte: call. Ma attenzione: se lo stack del villain fosse solo di 150, il call sarebbe sbagliato.", lav=("1000 ÷ 30 ≈ 33 volte > 15-20 → CALL", "g"))
    S += s.fine()

    # ---------------------------------------------------------------- errori
    s = Sc("Gli errori più comuni")
    s.b("Quattro errori costano più fiches di tutti gli altri. Uno: usare il × 4 quando non sei all-in. Paghi per una carta, non per due.", modo="cartelli", testi=["× 4 solo all-in", "Dirty outs = outs a metà", "Guarda la bet, non solo le tue carte", "Pensa al range, non a una mano"], n=1)
    s.b("Due: contare i dirty outs come se fossero puliti. Se una carta può aiutare anche l'avversario, il tuo out vale meno.", n=2)
    s.b("Tre: guardare solo le tue carte e non la dimensione della bet. La soglia la decide la bet.", n=3)
    s.b("Quattro: ragionare contro una mano sola. L'avversario non ha una mano: ha un range.", n=4)
    S += s.fine()

    # ---------------------------------------------------------------- riepilogo
    s = Sc("Riepilogo")
    s.b("Il metodo è sempre lo stesso, in quattro passi. Conta gli outs. Trasformali in equity: per 2 se vedi una carta, per 4 solo se sei all-in. Calcola l'equity richiesta con le pot odds. Confronta: se la tua equity è più alta, call.", modo="scheda", passi=pas, n=4, tabelle=True)
    s.b("Fai uno screenshot di questa schermata: è tutto quello che ti serve al tavolo.")
    S += s.fine()

    # ---------------------------------------------------------------- quiz
    s = Sc("Quiz")
    s.b("Tocca a te. Cinque mani: per ognuna metti in pausa, fai il conto con i quattro passi e decidi call o fold. Poi riparti e controlla.", hero=[], board=[], pot=None, bet=None, sov="Tocca a te")
    Q = [(["Qc", "Jd"], ["Ts", "9h", "3c", "2d"], 100, 100, "Hero Q♣J♦, board T♠ 9♥ 3♣ 2♦, al turn. Pot 100, il villain punta 100.",
          "Open-ended: servono un K o un 8, quindi 8 outs. Una carta da vedere: 8 × 2 = 16%, esatto 17,4%. Bet pari al pot: serve il 33,3%. FOLD.",
          [("OUTS: K o 8 = 8", "w"), ("8 × 2 = 16% (esatto 17,4%)", "y"), ("Pot odds: 100 ÷ 300 = 33,3%", "b"), ("16% < 33,3% → FOLD", "r")]),
         (["7d", "6d"], ["Qd", "Jd", "3c", "2s"], 200, 50, "Hero 7♦6♦, board Q♦ J♦ 3♣ 2♠, al turn. Pot 200, il villain punta 50.",
          "Flush draw: 9 outs. 9 × 2 = 18%, esatto 19,6%. Pot odds: 50 ÷ 300 = 16,7%. CALL.",
          [("OUTS: 9 quadri", "w"), ("9 × 2 = 18% (esatto 19,6%)", "y"), ("Pot odds: 50 ÷ 300 = 16,7%", "b"), ("18% > 16,7% → CALL", "g")]),
         (["8c", "7c"], ["Ac", "Jc", "4h"], 100, 50, "Hero 8♣7♣, board A♣ J♣ 4♥, al flop. Pot 100, il villain va all-in per 50 con una coppia d'assi senza fiori.",
          "Flush draw: 9 outs. All-in, quindi × 4: 36%, meno 1 uguale 35%, esatto 35%. Pot odds: 50 ÷ 200 = 25%. CALL.",
          [("OUTS: 9 fiori", "w"), ("All-in → 9 × 4 = 36% − 1 = 35%", "y"), ("Pot odds: 50 ÷ 200 = 25%", "b"), ("35% > 25% → CALL", "g")]),
         (["9s", "8s"], ["Ks", "6s", "2d"], 60, 40, "Hero 9♠8♠, board K♠ 6♠ 2♦, al flop. Pot 60, il villain punta 40 e non è all-in.",
          "Flush draw: 9 outs. Non sei all-in: una carta sola, 9 × 2 = 18%, esatto 19,1%. Pot odds: 40 ÷ 140 = 28,6%. FOLD.",
          [("OUTS: 9 picche", "w"), ("Non all-in → 9 × 2 = 18% (esatto 19,1%)", "y"), ("Pot odds: 40 ÷ 140 = 28,6%", "b"), ("18% < 28,6% → FOLD", "r")]),
         (["8h", "7h"], ["9h", "6d", "2h"], 120, 60, "Hero 8♥7♥, board 9♥ 6♦ 2♥, al flop. Pot 120, il villain va all-in per 60.",
          "Flush draw più open-ended: 9 cuori più 6 carte per la scala, 15 outs. All-in, quindi × 4 meno 7: 53%, esatto 54%. Pot odds: 60 ÷ 240 = 25%. CALL.",
          [("OUTS: 9 + 6 = 15", "w"), ("15 × 4 − 7 = 53% (esatto 54%)", "y"), ("Pot odds: 60 ÷ 240 = 25%", "b"), ("53% > 25% → CALL", "g")])]
    for hh, bb, pot, bet, dom, sol, righe in Q:
        base = dict(modo="tavolo", hero=hh, board=bb, pot=pot, bet=bet, vil="x", ev=[])
        s.cur.update(base)
        s.cur["lav"] = []
        s.b("Domanda. " + dom, sov="", dopo=0.4)
        s.b("", silenzio=6.0, dopo=0, pausa=True, sov="Metti in pausa e decidi: CALL o FOLD?")
        s.b("Soluzione. " + sol, lav=righe, sov="Soluzione", dopo=0.9, pausa=False)
    S += s.fine()

    # ---------------------------------------------------------------- chiusura
    s = Sc("Glossario e gioco responsabile")
    s.b("Ecco tutti i termini di oggi in una schermata: salvala.", modo="glossario", voci=GLOS_COMPLETO, n=len(GLOS_COMPLETO), tutti=True, sov="Salva questa schermata")
    s.b("Un'ultima cosa, la più importante. Questa matematica ti fa prendere decisioni migliori, ma non elimina la varianza, cioè la fortuna nel breve periodo. Puoi giocare perfettamente e perdere una mano, una sera, anche una settimana.", dopo=0.6)
    s.b("Gioca solo con soldi che puoi permetterti di perdere. Il poker è vietato ai minori di 18 anni. Se il gioco smette di essere un divertimento, chiedi aiuto: in Italia c'è il numero verde unico per le dipendenze dell'Istituto Superiore di Sanità, gratuito e anonimo: 800 940 789.", modo="chiusura")
    S += s.fine()
    return S


def beats_corso():
    out = scene()
    # varianza: nel glossario compare nel parlato come termine spiegato
    return out
