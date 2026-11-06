"""Video pratico «Chiamare o lasciare: il conto da fare a mente» (circa 12-14 minuti).
Frasi corte e discorsive, voce più lenta, solo il necessario: quali calcoli fare, come si applicano e come ragionare mano per mano.
Tutti i numeri sono gli stessi già ricalcolati con enumerazione esatta per il corso lungo (vedi poker_corso.py)."""
from poker import TAB_ODDS, TAB_OUTS
from poker_corso import Sc

B1 = ["9h", "8h"]
BD = ["Kh", "7h", "2c", "4s"]


class P(Sc):
    """Come Sc, ma con pause più lunghe tra una frase e l'altra."""

    def b(self, voce, lav=None, sov=None, reset=False, dopo=0.7, silenzio=0, **ov):
        return super().b(voce, lav=lav, sov=sov, reset=reset, dopo=dopo, silenzio=silenzio, **ov)


TERMINI = [("Call / Fold", "pagare per restare / lasciare la mano"), ("Bet", "la puntata dell'avversario, il prezzo da pagare"),
           ("Pot", "il piatto: le fiches già in gioco"), ("Draw", "progetto: ti manca una carta per fare mano"),
           ("Outs", "le carte che ti completano il progetto"), ("Equity", "quante volte su cento vinci"),
           ("Pot odds", "quante volte su cento ti serve vincere"), ("All-in", "puntare tutte le proprie fiches")]


def scene():
    S = []

    # 1 ---- gancio, senza carte
    s = P("Gancio", modo="cartelli", testi=["Quanto vinco? Quanto pago?"], n=1)
    s.b("Il tuo avversario punta. Tu hai un progetto, ti manca una carta. Paghi o lasci?")
    s.b("Quasi tutti rispondono a sensazione. Ti faccio vedere il conto che fanno i giocatori bravi. Dura cinque secondi e si fa a mente.", sov="Il conto da fare a mente")
    S += s.fine()

    # 2 ---- idea
    s = P("L'idea in una frase", modo="cartelli", testi=["Quanto spesso vinco?", "Quanto mi serve vincere?", "Il primo è più alto? Pago."], n=1)
    s.b("L'idea è una sola. Ti chiedi due cose. La prima: quante volte su cento vinco questa mano? La seconda: quante volte su cento mi serve vincere, per pareggiare il prezzo che devo pagare?", sov="Due numeri da confrontare")
    s.b("Se vinci più spesso di quanto ti serve, paghi. Se vinci meno, lasci.", n=3, sov="Il primo numero più alto → CALL")
    s.b("Tutto il video serve a trovare questi due numeri in fretta. Poi li usiamo in cinque situazioni vere.")
    S += s.fine()

    # 3 ---- parole
    s = P("Le otto parole", modo="glossario", voci=TERMINI, n=1)
    s.b("Prima le parole. Sono poche, e le usiamo sempre. Call è pagare per restare in gioco. Fold è lasciare la mano.", n=1)
    s.b("Bet è la puntata dell'avversario: è il prezzo che devi pagare. Pot è il piatto, le fiches già in gioco.", n=3)
    s.b("Draw è un progetto: hai quasi una mano forte, ti manca una carta. Quelle carte che ti servono si chiamano outs.", n=5)
    s.b("Equity è quante volte su cento vinci. Pot odds è quante volte su cento ti serve vincere. Questi sono i due numeri di prima.", n=7)
    s.b("E all-in vuol dire puntare tutte le fiches che hai davanti.", n=8)
    S += s.fine()

    # 4 ---- primo numero: outs
    s = P("Numero 1 · Conta gli outs")
    s.b("Primo numero: gli outs. Sono le carte nel mazzo che ti completano il progetto. Devi saperli a memoria, sono pochi.", modo="tabella", titolo="Gli outs da imparare a memoria", testa=TAB_OUTS[0], righe=TAB_OUTS[1], n=1, sov="OUTS = le carte che ti servono")
    s.b("Quattro cuori e ti manca il quinto per il colore? Nove outs, perché nel mazzo restano nove cuori.", n=1)
    s.b("Scala aperta, cioè ti serve una carta da una parte o dall'altra? Otto outs.", n=2)
    s.b("Scala interna, una sola carta che ti serve? Quattro outs.", n=3)
    s.b("Due carte alte sopra il tavolo, che se pescano il loro valore ti fanno coppia? Sei outs.", n=4)
    s.b("Coppia in mano e vuoi un tris? Due outs. E se hai colore e scala insieme, quindici.", n=6, sov="9 · 8 · 4 · 6 · 2 · 15")
    S += s.fine()

    # 5 ---- outs -> equity
    s = P("Numero 1 · Da outs a percentuale", hero=B1, board=BD, pot=100, ev=["Kh", "7h", "9h", "8h"], lav=[("Flush draw: 9 outs", "w")])
    s.b("Ora trasformiamo gli outs in percentuale. Qui hai nove cuori e manca una carta da scoprire.")
    s.b("Il trucco è semplicissimo: moltiplica gli outs per due. Nove per due fa diciotto. Hai circa il diciotto per cento di fare colore alla prossima carta.", lav=("9 × 2 = 18%", "y"), sov="OUTS × 2 = la tua percentuale")
    s.b("Il numero esatto è diciannove e sei, quindi il trucco sbaglia di poco. Va benissimo.", lav=("esatto: 19,6%", "g"))
    s.b("Attenzione a una cosa sola. Il per quattro, al posto del per due, si usa solo se sei all-in e vedrai due carte. Se l'avversario può ancora puntare, usa sempre il per due.", sov="× 4 solo se all-in · altrimenti × 2", reset=True)
    S += s.fine()

    # 6 ---- secondo numero
    s = P("Numero 2 · Quanto mi serve vincere")
    s.b("Secondo numero: quanto ti serve vincere. Dipende solo da quanto è grande la puntata rispetto al piatto.", modo="tabella", titolo="Quanto ti serve vincere, in base alla bet", testa=TAB_ODDS[0], righe=TAB_ODDS[1], n=1, sov="POT ODDS = quanto ti serve vincere")
    s.b("Se ti puntano un terzo del piatto, ti serve vincere il venti per cento delle volte.", n=1)
    s.b("Mezzo piatto: venticinque per cento. Due terzi: circa ventinove. Tutto il piatto: trentatré. E se ti puntano il doppio del piatto: quaranta.", n=5)
    s.b("Questi cinque numeri bastano per quasi ogni mano. Se ti piace il conto preciso: la bet, diviso il piatto più la bet più i tuoi soldi per pagare. Ma a mente basta la tabella.", sov="20 · 25 · 29 · 33 · 40")
    S += s.fine()

    # 7 ---- schema mentale
    s = P("Lo schema da avere in testa", modo="scheda", passi=["Che progetto ho? → quanti outs", "Moltiplica: × 2 (× 4 solo se all-in)", "Che parte del piatto è la bet? → 20 · 25 · 29 · 33", "Il mio numero è più alto? Call · Altrimenti fold"], n=1, tabelle=False)
    s.b("Mettiamo tutto in ordine. Ogni volta che l'avversario punta, ti fai quattro domande, sempre le stesse.", n=1)
    s.b("Uno: che progetto ho? Conto gli outs. Due: moltiplico per due. Se sono all-in, per quattro.", n=2)
    s.b("Tre: quanto è grande la bet rispetto al piatto? Un terzo, metà, due terzi, tutto. E mi ricordo il numero della tabella.", n=3)
    s.b("Quattro: confronto. Se la mia percentuale è più alta, call. Se è più bassa, fold. Tutto qui.", n=4, sov="Più alto → call · più basso → fold")
    S += s.fine()

    # 8 ---- situazione 1
    s = P("Situazione 1 · Il colore a una carta", hero=B1, board=BD, pot=100, bet=50, vil="x", ev=["Kh", "7h", "9h", "8h"])
    s.b("Prima situazione. Hai nove di cuori e otto di cuori. Sul tavolo ci sono re, sette, due e quattro, e due carte sono cuori. Nel piatto ci sono cento fiches, l'avversario ne punta cinquanta.", lav=("Pot 100 · bet 50", "w"))
    s.b("Uno: nove outs. Due: nove per due, diciotto per cento.", lav=[("9 outs × 2 = 18%", "y")])
    s.b("Tre: cinquanta su cento è metà piatto. Ti serve il venticinque per cento.", lav=[("bet = metà piatto → 25%", "b")])
    s.b("Quattro: diciotto è meno di venticinque. Fold.", lav=[("18% < 25% → FOLD", "r")], sov="FOLD")
    s.b("Ora cambia una sola cosa: l'avversario punta venticinque invece di cinquanta. Un quarto del piatto: ti serve circa il diciassette per cento. Tu hai diciotto. Adesso è call.", bet=25, lav=[("bet 25 → serve ~17%", "b"), ("18% > 17% → CALL", "g")], sov="Stessa mano, bet diversa, decisione diversa")
    s.b("Ricordati questo: non esiste una percentuale buona in assoluto. La decide la bet dell'avversario.")
    S += s.fine()

    # 9 ---- situazione 2
    s = P("Situazione 2 · La scala interna", hero=["9s", "8d"], board=["6c", "5h", "2s"], pot=90, bet=30, vil="x", ev=[])
    s.b("Seconda situazione. Hai nove e otto, sul tavolo sei, cinque e due. Ti serve un sette per la scala: una sola carta. Il piatto è novanta, l'avversario punta trenta.", lav=("Pot 90 · bet 30", "w"))
    s.b("Quattro outs. Quattro per due: otto per cento. La bet è un terzo del piatto: ti serve il venti per cento.", lav=[("4 outs × 2 = 8%", "y"), ("bet = un terzo → 20%", "b")])
    s.b("Otto è molto meno di venti. Fold, senza pensarci troppo.", lav=[("8% < 20% → FOLD", "r")], sov="FOLD")
    s.b("Regola pratica: con una scala interna e basta, quasi sempre si lascia.")
    S += s.fine()

    # 10 ---- situazione 3
    s = P("Situazione 3 · Due carte alte", hero=["As", "Kd"], board=["9c", "6h", "2s"], pot=100, bet=50, vil="x", ev=[])
    s.b("Terza situazione. Hai asso e re, ma sul tavolo non c'è niente: nove, sei e due. Se esce un asso o un re, fai coppia. Il piatto è cento, la bet cinquanta.", lav=("Pot 100 · bet 50", "w"))
    s.b("Sei outs: tre assi e tre re. Sei per due: dodici per cento. Mezzo piatto: venticinque. Dodici meno di venticinque: fold.", lav=[("6 outs × 2 = 12%", "y"), ("serve 25%", "b"), ("12% < 25% → FOLD", "r")], sov="FOLD")
    s.b("Attenzione a una trappola. Anche se peschi un asso o un re, l'avversario potrebbe avere una coppia migliore della tua. Quando una tua carta può aiutare anche lui, conta quell'out per metà. Si chiamano dirty outs, outs sporchi.", sov="DIRTY OUTS = outs che aiutano anche lui: contali metà")
    S += s.fine()

    # 11 ---- situazione 4 all-in
    s = P("Situazione 4 · Colore e scala insieme, all-in", hero=["Js", "Ts"], board=["9s", "8s", "2d"], pot=100, bet=100, bet_t="ALL-IN", vil=["Ad", "Ac"], ev=[])
    s.b("Quarta situazione, la più bella. Hai fante e dieci di picche. Sul tavolo ci sono nove e otto di picche, e un due. Hai il progetto di colore e quello di scala insieme.", lav=("Pot 100 · all-in 100", "w"))
    s.b("Conta gli outs: nove picche per il colore, più sei carte per la scala. Quindici outs.", lav=[("9 + 6 = 15 outs", "y")])
    s.b("L'avversario va all-in, quindi vedrai due carte: qui si usa il per quattro. Quindici per quattro fa sessanta. Ma con tanti outs il trucco esagera: si toglie la differenza tra gli outs e otto. Quindici meno otto, sette. Sessanta meno sette: cinquantatré per cento.", lav=[("15 × 4 = 60 − 7 = 53%", "y")], sov="Con più di 8 outs: togli (outs − 8)")
    s.b("Quanto ti serve? Cento da pagare, il piatto sarebbe trecento: un terzo, trentatré per cento. Hai cinquantatré. Call, e anche forte.", lav=[("serve 33%", "b"), ("53% > 33% → CALL", "g")], sov="CALL")
    s.b("Il numero esatto è cinquantaquattro: il trucco è andato vicinissimo, anche contro due assi.")
    S += s.fine()

    # 12 ---- situazione 5 set mining
    s = P("Situazione 5 · La coppia piccola", hero=["5c", "5d"], board=[], pot=None, bet=30, bet_t="RILANCIO", stack="1000", vil="x")
    s.b("Quinta e ultima situazione, quella che ti sembra strana. Hai due cinque. L'avversario rilancia a trenta, e ha davanti mille fiches. Prima che esca qualsiasi carta.")
    s.b("Con la coppia piccola puoi solo sperare in un tris, cioè nel set. Succede una volta ogni otto e mezzo, circa il dodici per cento. Il conto di prima direbbe fold.", lav=[("set al flop: ~12%", "y")])
    s.b("Ma se lo fai, l'avversario non lo vede. E ha mille fiches davanti: puoi vincerle quasi tutte. Per questo si guarda quanto puoi vincere dopo, che si chiama implied odds.", sov="IMPLIED ODDS = quanto puoi vincere dopo")
    s.b("Regola pratica: se l'avversario ha davanti almeno quindici o venti volte quello che devi pagare, il call conviene. Qui sono più di trenta volte: call.", lav=[("1000 ÷ 30 = più di 30 volte", "b"), ("≥ 15-20 volte → CALL", "g")], sov="Stack ≥ 15-20 × il call → call")
    s.b("Se invece ha poche fiches davanti, non vale la pena: lascia.")
    S += s.fine()

    # 13 ---- leggere l'avversario
    s = P("Come pensare: leggere l'avversario", modo="cartelli", testi=["Bet piccola: vuole che paghi, oppure prova", "Bet grande: molto forte, oppure bluff", "Chiediti: che mani punterebbero così?"], n=1)
    s.b("Finora ho parlato di carte tue. Ma il conto cambia anche in base a chi hai davanti. Non puoi sapere cosa ha, ma puoi farti tre domande.", n=1)
    s.b("La prima: quanto ha puntato? Una bet piccola spesso è di chi vuole farsi pagare, o di chi prova a vedere se lasci. Una bet grande o è una mano molto forte, o un bluff per farti lasciare.", n=2)
    s.b("La seconda: che storia racconta la mano? Ha puntato tutte le carte, o è comparso solo adesso? Una puntata dopo tanta calma di solito pesa di più.", n=3)
    s.b("La terza: che giocatore è? Se è uno che bluffa spesso, puoi pagare anche con un conto un po' sotto. Se è uno prudente e ha puntato forte, fidati di lui e lascia con un conto dubbio.", sov="Bluffatore → paga di più · Prudente → fidati")
    s.b("Non sono regole fisse, sono correzioni. Il conto resta la base, la lettura lo sposta di qualche punto.")
    S += s.fine()

    # 14 ---- errori
    s = P("I quattro errori da evitare", modo="cartelli", testi=["× 4 solo se all-in", "Dirty outs: contali metà", "Guarda la bet, non solo le tue carte", "Lascia le scale interne"], n=1)
    s.b("Quattro errori fanno perdere quasi tutte le fiches ai principianti.", n=1)
    s.b("Uno: usare il per quattro quando non sei all-in. Il per quattro è solo per l'all-in.", n=1)
    s.b("Due: contare outs che aiutano anche l'avversario. Contali metà.", n=2)
    s.b("Tre: decidere guardando solo le tue carte. La stessa mano è un call con una bet piccola e un fold con una bet grande.", n=3)
    s.b("Quattro: chiamare con una scala interna, solo perché ti manca una carta. Sono quattro outs, di solito non bastano.", n=4)
    S += s.fine()

    # 15 ---- quiz
    s = P("Quiz", hero=[], board=[], pot=None, bet=None)
    s.b("Tocca a te. Tre mani: per ognuna metti in pausa, fai il conto con lo schema e decidi call o fold. Poi riparti e controlla.", sov="Tocca a te")
    Q = [(["7d", "6d"], ["Qd", "Jd", "3c", "2s"], 200, 50, "Hai sette e sei di quadri. Sul tavolo ci sono donna e fante di quadri, un tre e un due. Il piatto è duecento, l'avversario punta cinquanta.",
          "Hai un colore da completare: nove outs. Nove per due fa diciotto. La bet è un quarto del piatto: ti serve circa il diciassette per cento. Diciotto è più di diciassette: call.",
          [("OUTS: 9 quadri", "w"), ("9 × 2 = 18%", "y"), ("Pot odds: 50 ÷ 300 = 16,7%", "b"), ("18% > 16,7% → CALL", "g")]),
         (["9s", "8s"], ["Ks", "6s", "2d"], 60, 40, "Hai nove e otto di picche. Sul tavolo re, sei di picche e due. Il piatto è sessanta, l'avversario punta quaranta, e non è all-in.",
          "Nove outs, ma non sei all-in: per due, diciotto per cento. La bet è due terzi del piatto: ti serve circa ventinove. Diciotto è meno: fold.",
          [("OUTS: 9 picche", "w"), ("Non all-in → 9 × 2 = 18%", "y"), ("Pot odds: 40 ÷ 140 = 28,6%", "b"), ("18% < 28,6% → FOLD", "r")]),
         (["8h", "7h"], ["9h", "6d", "2h"], 120, 60, "Hai otto e sette di cuori. Sul tavolo nove di cuori, sei e due di cuori. Il piatto è centoventi, l'avversario va all-in per sessanta.",
          "Colore e scala insieme: quindici outs. All-in, quindi per quattro, con la correzione: circa cinquantatré per cento. Ti serve venticinque. Call, e forte.",
          [("OUTS: 9 + 6 = 15", "w"), ("15 × 4 − 7 = 53%", "y"), ("Pot odds: 60 ÷ 240 = 25%", "b"), ("53% > 25% → CALL", "g")])]
    for hh, bb, pot, bet, dom, sol, righe in Q:
        s.cur.update(dict(modo="tavolo", hero=hh, board=bb, pot=pot, bet=bet, vil="x", ev=[]))
        s.cur["lav"] = []
        s.b("Domanda. " + dom, sov="", dopo=0.4)
        s.b("", silenzio=6.0, dopo=0, pausa=True, sov="Metti in pausa e decidi: CALL o FOLD?")
        s.b("Soluzione. " + sol, lav=righe, sov="Soluzione", dopo=1.0, pausa=False)
    S += s.fine()

    # 16 ---- chiusura
    s = P("Riepilogo e gioco responsabile", modo="scheda", passi=["Conta gli outs", "× 2 · (× 4 solo all-in)", "Bet in frazione del piatto → 20 · 25 · 29 · 33", "Più alto → call · più basso → fold"], n=4, tabelle=False)
    s.b("Ricapitolando, quattro righe da salvare. Conta gli outs. Moltiplica per due, per quattro solo all-in. Guarda la bet: venti, venticinque, ventinove, trentatré. Se il tuo numero è più alto, call.", sov="Salva questa schermata")
    s.b("Questo conto ti fa decidere meglio, ma non elimina la fortuna. Puoi fare tutto giusto e perdere una mano, una sera, anche una settimana.")
    s.b("Gioca solo con soldi che puoi permetterti di perdere. Il poker è vietato ai minori di 18 anni. Se il gioco smette di essere un divertimento, chiedi aiuto: in Italia c'è il numero verde unico per le dipendenze dell'Istituto Superiore di Sanità, gratuito e anonimo: 800 940 789.", modo="chiusura")
    S += s.fine()
    return S


def beats_pratico():
    return scene()
