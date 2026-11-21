from lezione_testi_cg import S

TITOLO = "La nave: tipi, vita e misure"
INTRO = """Con questo capitolo cambiamo parte del corso: dal controllo di gestione in generale passiamo alle implicazioni economiche e finanziarie delle scelte armatoriali, cioè le scelte di chi possiede e gestisce le navi. Negli appunti è la parte del professor Ducci. Qui vedi che tipi di nave esistono, come nasce e muore una nave, e le misure che si usano per descriverla: stazza, dislocamento e portata. Sono definizioni, ma ricorrono spesso nelle domande."""

SCHERMATE = [
    S("lista", "Cosa viaggia per mare", [
        ("**Petrolio**|la risorsa più trasportata via mare",
         """Oggi la risorsa più trasportata via mare è il petrolio. Ma il tipo di merce che supera il cinquanta per cento del valore mondiale trasportato sono i container."""),
        ("**Petroliere**|gru (tubazioni) ai lati della nave per far fluire il petrolio verso il distributore a terra e viceversa",
         """Una caratteristica delle petroliere sono le gru ai lati della nave, che negli appunti servono a far fluire il petrolio verso il distributore a terra e viceversa."""),
        ("**Chemical tanker**|cisterne di materiali speciali per contenere i prodotti chimici",
         """Le chemical tanker si distinguono perché le cisterne sono fatte di materiali speciali, adatti a contenere prodotti chimici."""),
        ("**Bulk carrier**|le gru a bordo indicano navi medio-piccole: le grandi usano le gru del porto, più efficienti",
         """Le bulk carrier trasportano merci alla rinfusa. Se vedi le gru sulla nave, vuol dire che la nave ha dimensioni medio-piccole. Le grandi navi non le usano, perché le gru del porto sono più efficienti."""),
    ]),
    S("lista", "Tonnellate-miglia: la domanda che conta", [
        ("Al controller serve **la domanda**|e ancora di più le **tonnellate-miglia**",
         """Per il controller non basta conoscere l'entità della domanda: serve sapere le tonnellate-miglia, cioè quante tonnellate sono trasportate e per quante miglia."""),
        ("Esempio: il **petrolio** importato in Italia|prima da Russia e Golfo Persico, oggi più dall'America",
         """Esempio dagli appunti. In passato il petrolio importato in Italia arrivava dalla Russia, in parte con oleodotto e in parte via nave nel Mar Nero e nel Mare del Nord, e dal Golfo Persico. Oggi la richiesta alla Russia è stata sostituita da quella all'America."""),
        ("Distanze maggiori|il costo del trasporto è cresciuto **più della domanda**",
         """Questo ha portato costi maggiori per la distanza. Il costo del trasporto del petrolio è aumentato molto più dell'aumento della domanda, proprio perché le distanze si sono dilatate."""),
        ("**Specializzazione** delle navi|più merce trasportata per nave, meno equipaggio dedicato alla sicurezza",
         """La specializzazione della nave ha aumentato il volume di merce trasportato rispetto al passato, quando la capacità era limitata e a bordo c'erano molte persone addette alla sicurezza della nave."""),
    ]),
    S("flusso", "La vita della nave", [
        ("**1. Nascita**|nasce dalla consapevolezza che c'è una domanda da soddisfare e si sa come soddisfarla", """La nave attraversa quattro fasi. Prima: la nascita. La nave nasce dalla consapevolezza che c'è una domanda da soddisfare e che si sa come soddisfarla. Prima degli anni settanta era l'armatore a chiedere la costruzione. Dopo, i cantieri coreani e giapponesi hanno iniziato a costruire lo scafo nudo e poi l'armatore decideva alcune caratteristiche."""),
        ("**2. Scelta della bandiera**|ne parliamo nel capitolo 12", """Seconda fase: la scelta della bandiera, che vedremo nell'ultimo capitolo."""),
        ("**3. Impiego commerciale**|operation: genera utili; può cambiare bandiera, contratti e proprietario", """Terza fase: l'impiego commerciale, in inglese operation. Durante la vita la nave genera utili e può cambiare bandiera e contratti di impiego, e anche proprietario."""),
        ("**4. Demolizione**|scrapping: alla fine della vita la nave viene demolita", """Quarta fase: la demolizione, chiamata scrapping."""),
    ]),
    S("lista", "Chi costruisce e quanto dura", [
        ("**Chi costruisce navi**|mercantili: Cina, Giappone, Corea; crociere: prima Fincantieri, poi Germania e Francia",
         """Oggi i tre paesi che costruiscono più navi mercantili sono Cina, Giappone e Corea. Nel settore crocieristico Fincantieri è prima al mondo, seguita da Germania e Francia. Può succedere, come adesso, che anche con un mercato in calo ci sia saturazione dei cantieri, perché in passato la crescita è stata esponenziale e la richiesta eccessiva."""),
        ("**Vita utile media**|circa 25 anni",
         """La vita utile media di una nave è di circa venticinque anni."""),
        ("Chi dura meno, chi di più|bulk carrier meno; traghetti di più: dipende dalle sollecitazioni",
         """Quelle che durano meno sono le bulk carrier, mentre le più longeve sono i traghetti. Dipende dalle oscillazioni delle sollecitazioni: più sono costanti, più la nave si degrada lentamente."""),
        ("**Il valore della nave**|può salire nel tempo se il mercato cresce e le consegne sono in ritardo; la Grecia ha una forte abilità nell'**asset play**",
         """I ricavi nascono dall'impiego della nave. A differenza dei mezzi terrestri e aerei, il cui valore diminuisce col tempo, per le navi il discorso cambia: il valore può aumentare, se il mercato è in crescita e i tempi di consegna dei cantieri si allungano. La Grecia ha una forte abilità nell'asset play, cioè nella compravendita delle navi."""),
    ]),
    S("tabella", "Le misure della nave", [
        ("**Stazza**|Lorda e netta|La tonnellata di stazza vale 100 piedi cubi, cioè 2,832 metri cubi. Lorda: volume di tutti gli spazi chiusi sopra e sotto il ponte principale. Netta: volume degli spazi disponibili per il carico",
         """Prima misura: la stazza. È un volume, non un peso, e si esprime in tonnellate di stazza, dove una tonnellata di stazza vale cento piedi cubi, cioè due virgola ottocentotrentadue metri cubi. La stazza lorda è il volume di tutti gli spazi chiusi o chiudibili sopra e sotto il ponte principale. La stazza netta è il volume degli spazi disponibili per il carico."""),
        ("**Dislocamento**|Leggero e a pieno carico|Leggero: peso della nave armata ma scarica. A pieno carico: peso della nave carica fino al massimo consentito",
         """Seconda misura: il dislocamento, cioè il peso della nave in tonnellate. Il dislocamento leggero è il peso della nave armata ma scarica. Quello a pieno carico è il peso della nave carica fino al massimo consentito dalle regole di bordo libero estivo."""),
        ("**Portata**|Lorda e netta|Lorda: differenza tra dislocamento a pieno carico e dislocamento leggero. Netta: misura il carico effettivo che può essere imbarcato",
         """Terza misura: la portata, in inglese deadweight, cioè la capacità di carico. La portata lorda è la differenza tra il dislocamento a pieno carico e il dislocamento della nave vuota: la somma dei pesi di tutto ciò che si può caricare a bordo. La portata netta misura il carico effettivo che si può imbarcare."""),
    ], colonne=["Misura", "Tipi", "Definizione"]),
    S("lista", "Perché queste misure contano", [
        ("**Tasse**|alcuni Stati calcolano le tasse e l'accesso al porto in base alla **stazza**, non al reddito",
         """Perché servono? Alcuni Stati applicano le tasse in base alla stazza e non al reddito, e lo stesso vale per l'accesso al porto di alcuni Stati."""),
        ("**Prezzo di vendita**|il **dislocamento leggero** si usa per determinare il prezzo di una nave",
         """Il dislocamento leggero si usa nella vendita di una nave per determinare il prezzo."""),
        ("**Portata netta**|varia in base al viaggio; la lorda resta invariata, quindi nel corso conta la **netta**",
         """La portata netta varia in base al viaggio, mentre quella lorda resta invariata. Per questo, nel nostro corso, la portata rilevante è quella netta."""),
        ("**Economie di scala**|oggi la nave più efficiente stimata è da **18.000 TEU**; le crociere crescono; le tanker arrivano a circa 441.585 tonnellate di portata",
         """Un'ultima nota sulle dimensioni. Le stime, confermate dagli ordini di navi, indicano che la nave più efficiente nelle economie di scala è quella da diciottomila TEU, cioè contenitori da venti piedi. Le navi da crociera tendono a crescere. Le tanker si aggirano sulle quattrocentoquarantunomila tonnellate di portata, costruite nel duemiladue e duemilatre."""),
    ]),
]
