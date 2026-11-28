from lezione_testi_cg import S

TITOLO = "La nave: tipi, vita e misure"
INTRO = """Da qui entriamo nella parte navale del corso, quella più specifica delle imprese di trasporto marittimo. Prima di parlare di noli e di margini di viaggio, dobbiamo conoscere lo strumento con cui l'armatore lavora: la nave. In questa lezione vediamo che cosa viaggia per mare e su quali navi, perché al controller interessano le tonnellate-miglia più della domanda, come nasce e come vive una nave, chi la costruisce e quanto dura, come cambia il suo valore, e soprattutto le sue misure: stazza, dislocamento e portata. Le misure all'esame si confondono facilmente, quindi le vediamo con calma."""

SCHERMATE = [
    S("lista", "Cosa viaggia per mare", [
        ("**Petrolio**|la risorsa più trasportata via mare",
         """Partiamo dal mercato. Oggi la risorsa più trasportata via mare è il petrolio. Ma attenzione a una distinzione degli appunti: se si guarda il valore, e non la quantità, i container superano il 50 per cento del valore delle merci trasportate nel mondo."""),
        ("**Petroliere**|gru (tubazioni) ai lati della nave per far fluire il petrolio verso il distributore a terra e viceversa",
         """Le navi cambiano con il carico. Le petroliere si riconoscono dalle gru ai lati della nave, che in realtà sono tubazioni: permettono al petrolio di fluire dalla nave al distributore a terra, e viceversa. Gli appunti citano anche le categorie di tanker: le VLCC portano greggio dal Golfo Persico alla Cina, le Aframax portano greggio e raffinati, le MR solo prodotti raffinati."""),
        ("**Chemical tanker**|cisterne di materiali speciali per contenere i prodotti chimici",
         """Le chemical tanker sono navi cisterna con una differenza: le cisterne sono fatte di materiali speciali, adatti a contenere i prodotti chimici."""),
        ("**Bulk carrier**|le gru a bordo indicano navi medio-piccole: le grandi usano le gru del porto, più efficienti",
         """Le bulk carrier portano merci alla rinfusa. Un dettaglio utile: se una bulk carrier ha le gru a bordo, vuol dire che è una nave di dimensioni medio-piccole. Le navi grandi non le usano, perché le gru del porto sono più efficienti."""),
    ]),
    S("lista", "Tonnellate-miglia: la domanda che conta", [
        ("Al controller serve **la domanda**|e ancora di più le **tonnellate-miglia**",
         """Al controller serve conoscere la domanda di trasporto, cioè quante tonnellate devono essere spostate. Ma ancora di più gli servono le tonnellate-miglia: le tonnellate moltiplicate per la distanza da percorrere. Una tonnellata portata per mille miglia impegna la nave molto meno di una tonnellata portata per diecimila."""),
        ("Esempio: il **petrolio** importato in Italia|prima da Russia e Golfo Persico, oggi più dall'America",
         """L'esempio degli appunti è il petrolio importato in Italia. In passato arrivava dalla Russia, via oleodotto o via nave dal Mar Nero e dal Mare del Nord, e dal Golfo Persico. Oggi la quota russa è stata sostituita con petrolio americano, che viene da molto più lontano."""),
        ("Distanze maggiori|il costo del trasporto è cresciuto **più della domanda**",
         """Il risultato: il costo del trasporto del petrolio è aumentato molto di più della domanda di petrolio, perché le distanze si sono allungate. Se il controller guardasse solo le tonnellate, non capirebbe perché i noli sono saliti."""),
        ("**Specializzazione** delle navi|più merce trasportata per nave, meno equipaggio dedicato alla sicurezza",
         """Un'altra tendenza: la specializzazione delle navi ha aumentato molto il volume di merce trasportata per nave. In passato le capacità erano limitate e a bordo c'era più personale addetto alla sicurezza."""),
    ]),
    S("flusso", "La vita della nave", [
        ("**1. Nascita**|nasce dalla consapevolezza che c'è una domanda da soddisfare e si sa come soddisfarla",
         """La vita di una nave ha quattro fasi. La prima è la nascita: una nave nasce dalla consapevolezza che c'è una domanda da soddisfare, e dal sapere come soddisfarla. Gli appunti raccontano anche come è cambiato il modo di costruirle: prima degli anni Settanta era l'armatore a chiedere la costruzione; dopo, a partire dai cantieri coreani e giapponesi, i cantieri hanno cominciato a costruire lo scafo e l'armatore a decidere alcune caratteristiche, con un contratto di costruzione: una collaborazione tra armatore e cantiere."""),
        ("**2. Scelta della bandiera**|ne parliamo nel capitolo 12",
         """La seconda fase è la scelta della bandiera, cioè lo Stato in cui la nave viene registrata. È un tema così importante che ha un capitolo tutto suo, il dodicesimo."""),
        ("**3. Impiego commerciale**|operation: genera utili; può cambiare bandiera, contratti e proprietario",
         """La terza è l'impiego commerciale, in inglese operation: la nave lavora e genera utili. I ricavi dipendono da come viene impiegata. Durante la sua vita può cambiare bandiera, contratti di impiego e anche proprietario."""),
        ("**4. Demolizione**|scrapping: alla fine della vita la nave viene demolita",
         """La quarta è la demolizione, in inglese scrapping: a fine vita la nave viene smontata."""),
    ]),
    S("lista", "Chi costruisce e quanto dura", [
        ("**Chi costruisce navi**|mercantili: Cina, Giappone, Corea; crociere: prima Fincantieri, poi Germania e Francia",
         """Chi costruisce le navi? Per le navi mercantili i tre paesi principali sono Cina, Giappone e Corea. Nelle navi da crociera la prima al mondo è l'italiana Fincantieri, seguita da Germania e Francia. Gli appunti notano un fenomeno curioso: anche quando il mercato cala, i cantieri possono essere saturi di ordini, perché in passato la crescita è stata così forte da far esplodere le richieste."""),
        ("**Vita utile media**|circa 25 anni",
         """La vita utile media di una nave è di circa 25 anni."""),
        ("Chi dura meno, chi di più|bulk carrier meno; traghetti di più: dipende dalle sollecitazioni",
         """Non tutte durano uguale. Le bulk carrier per rinfuse durano meno, i traghetti di più. Dipende dalle sollecitazioni: più sono costanti, meno la nave si degrada."""),
        ("**Il valore della nave**|può salire nel tempo se il mercato cresce e le consegne sono in ritardo; la Grecia ha una forte abilità nell'**asset play**",
         """E il valore? Per camion e aerei il valore scende con il tempo; per le navi non è sempre così. Se il mercato cresce e le consegne delle navi nuove sono in ritardo, il valore delle navi può salire, e i cantieri possono chiedere prezzi alti quanto quelli delle navi usate. La compravendita di navi si chiama asset play, e gli appunti indicano la Grecia come particolarmente abile. Al contrario, un calo improvviso della domanda fa crollare i prezzi: l'aneddoto degli appunti sono le Olimpiadi del 2008, quando le industrie furono fermate per ridurre i fumi e la domanda di materie prime crollò, trascinando giù il prezzo delle navi."""),
    ]),
    S("tabella", "Le misure della nave", [
        ("**Stazza**|Lorda e netta|La tonnellata di stazza vale 100 piedi cubi, cioè 2,832 metri cubi. Lorda: volume di tutti gli spazi chiusi sopra e sotto il ponte principale. Netta: volume degli spazi per il carico.",
         """Ora le misure, che sono tre famiglie: una misura il volume, due misurano pesi. La prima è la stazza, che è un volume, anche se si chiama tonnellata. La tonnellata di stazza vale 100 piedi cubi, cioè 2,832 metri cubi. La stazza lorda, gross tonnage, è il volume di tutti gli spazi chiusi o chiudibili sopra e sotto il ponte principale. La stazza netta, net tonnage, è il volume degli spazi disponibili per il carico."""),
        ("**Dislocamento**|Leggero e a pieno carico|Leggero: peso della nave armata ma scarica. A pieno carico: peso della nave carica fino al massimo consentito.",
         """La seconda è il dislocamento, che è il peso della nave in tonnellate. Il dislocamento leggero è il peso della nave armata ma scarica. Il dislocamento a pieno carico è il peso della nave carica fino al massimo consentito dalle regole del bordo libero estivo. Attenzione: negli appunti questo secondo dislocamento è chiamato per errore «netto»; il nome corretto è a pieno carico."""),
        ("**Portata**|Lorda e netta|Lorda: differenza tra dislocamento a pieno carico e dislocamento leggero. Netta: misura il carico effettivo che può essere imbarcato.",
         """La terza è la portata, in inglese deadweight, che indica la capacità di carico. La portata lorda è la differenza tra il dislocamento a pieno carico e quello della nave vuota: in pratica, la somma dei pesi di tutto ciò che si può caricare a bordo. La portata netta misura il carico effettivo che può essere imbarcato."""),
    ], colonne=["Misura", "Tipi", "Definizione"]),
    S("tabella", "Esempio svolto: dalle misure ai numeri", [
        ("**Portata lorda**|dislocamento a pieno carico 120.000 t − leggero 20.000 t|**100.000 t**",
         """Un esercizio con numeri di esempio, inventati per allenarsi. Una nave a pieno carico pesa 120.000 tonnellate, armata ma scarica 20.000. La portata lorda è la differenza: 100.000 tonnellate. È tutto il peso che la nave può prendere a bordo."""),
        ("**Stazza lorda**|volume chiuso 283.200 m³ / 2,832|**100.000 tonnellate di stazza**",
         """La stazza invece è un volume. Se gli spazi chiusi misurano 283.200 metri cubi, si divide per 2,832 e si ottengono 100.000 tonnellate di stazza."""),
        ("**Attenzione**|stesso numero, grandezze diverse|portata = peso · stazza = volume",
         """Stesso numero per caso: la portata è un peso, la stazza è un volume, e non vanno mai confuse. È uno degli errori più frequenti all'esame."""),
    ], colonne=["Misura", "Calcolo", "Risultato"]),
    S("lista", "Perché queste misure contano", [
        ("**Tasse**|alcuni Stati calcolano le tasse e l'accesso al porto in base alla **stazza**, non al reddito",
         """Perché queste misure contano per il controller? Primo: alcuni Stati calcolano le tasse in base alla stazza, non al reddito, e lo stesso vale per l'accesso ai porti di alcuni Stati. Lo ritroveremo parlando di bandiera e fisco."""),
        ("**Prezzo di vendita**|il **dislocamento leggero** si usa per determinare il prezzo di una nave",
         """Secondo: quando si vende una nave, si usa il dislocamento leggero per determinarne il prezzo."""),
        ("**Portata netta**|varia in base al viaggio; la lorda resta invariata, quindi nel corso conta la **netta**",
         """Terzo: la portata netta varia in base al viaggio, mentre la lorda resta sempre uguale. Per questo nel corso conta la portata netta: è quella che dice quanto carico si può vendere in quel viaggio, e la ritroviamo subito nel calcolo del nolo."""),
        ("**Economie di scala**|oggi la nave più efficiente stimata è da **18.000 TEU**; le crociere crescono; le tanker arrivano a circa 441.585 tonnellate di portata",
         """Quarto: le dimensioni e le economie di scala. Secondo le stime citate negli appunti, confermate dagli ordini di nuove navi, oggi la portacontainer più efficiente è da 18.000 TEU. Le navi da crociera tendono a crescere, mentre per le petroliere le più grandi arrivano a circa 441.585 tonnellate di portata, costruite nel 2002 e 2003."""),
    ]),
]
