# Decisioni di progetto (appunti per la relazione)

Questi appunti sono scritti via via durante lo sviluppo, da riprendere ed espandere
quando si scrive la relazione tecnica finale. Non è la relazione stessa, solo il "perchè abbiamo fatto cosiì" mentre è ancora fresco.

L'applicazione (Python/Flet + MySQL, architettura MVC) genera bundle di outfit tramite backtracking, a partire dallo stock di magazzino, secondo
4 preset di strategia (Configuratore) selezionabili dall'utente. Copre tutti e 3 i Moduli della proposta iniziale ,
su un singolo mercato (USA)..

## Corrispondenza con i Moduli della proposta iniziale

- **Modulo 1** (monitoraggio magazzino): sezione Magazzino, con evidenza dei prodotti deadstock (fermi da più di 180 giorni) e
statistiche riassuntive in Home.
- **Modulo 2** (generazione bundle): Configuratore (scelta della strategia tramite preset o parametri personalizzati) + algoritmo
 di backtracking che genera i bundle validi.
- **Modulo 3** (metriche aggiuntive): punteggio di compatibilità, indice di risparmio e stima dello spazio di magazzino liberato,
 mostrati su ogni bundle generato e in Storico


## Dataset

Dopom varie ricerche ho scelto il dataset "Adidas US Retail Products" (Kaggle), dati reali di un
retailer noto, non generato a tavolino, rispondendo alla sua richiesta di rièartirer da dati reali e non completamente sintetici.
Alcuni campi (giorni in magazzino, quantità stock, costo di acquisto, margine) sono stati generati sinteticamente sopra ai dati reali, perchè
un dataset e-commerce pubblico non contiene informazioni di magazzino interne .

## Scelta del mercato

Ho scelto di utilizzare  un singolo mercato (USA) per avere una base solida e ben testata, con la
possibilità di estendere a più mercati in un secondo momento se il tempo lo permette (i dati derivano comunque da un dataset multi-mercato, quindi
l'estensione resta possibile senza ricostruire il database da zero).



## Interfaccia (Flet)

Struttura finale: menu di navigazione laterale (NavigationRail) sempre visibile, con 4 sezioni corrispondenti ai moduli della proposta iniziale
più una home:
  1. Home - benvenuto e statistiche rapide sul magazzino
  2. Magazzino - dashboard di monitoraggio stock e deadstock
  3. Configuratore - scelta preset, generazione bundle
  4. Risultati - galleria degli outfit generati, con possibilità di salvare
Come soglia "deadstock" 8prodotto considerato fermo/invenduto) ho scelto 180 giorni in magazzino, questo dopo essermi informata su internet
ho notato che era un valore ragionevole.

## Algoritmo di backtracking (generazione bundle)

- **Categorie obbligatorie**: ogni bundle deve contenere esattamente un prodotto per ciascuna delle 5 categorie della proposta (Capospalla,
 Maglieria, Pantaloni, Scarpe, Accessori). La categoria "Vestiti" (5 articoli, fuori dalle 5 categorie originarie) non viene usata dall'algoritmo.
- **Vincolo di budget**: la somma dei prezzi di vendita dei prodotti scelti deve restare entro il `budget_max` del preset.
Viene indicato anche un budget minimo sotto il quale non esiste alcun bundle da poter generare. E' obbligatorio inserire un budget
altrimenti il sistema mostrerà un pop-up di alert
- **Vincolo di margine**: il margine percentuale medio del bundle deve essere >= al `margine_minimo_pct` del preset, altrimenti il bundle viene
scartato.
- **Compatibilità colore/stile**: per ogni bundle viene calcolata la media dei punteggi di compatibilità (dalle matrici in database) su tutte le coppie
di prodotti; se la media è sotto una soglia minima (0.5) il bundle viene
scartato.
- **Funzione obiettivo** Z = a * Profitto + b * Anzianità , dove il profitto è la somma dei margini unitari dei prodotti scelti e Anzianità è la somma
dei giorni in magazzino dei prodotti scelti (premia i bundle che smaltiscono più pezzi vecchi insieme). I pesi a/b vengono dal preset scelto.
- **Numero di risultati**: l'algoritmo restituisce tutti i bundle validi trovati (che rispettano budget, margine e compatibilità). Ho dovuto adattare un limite
di sicurezza sul numero massimo per evitare tempi di calcolo  (500 max)
(lo spazio di ricerca completo, sarebbe di circa 35 milioni di combinazioni: 12 Capospalla x 55 Maglieria x 38 Pantaloni x 58 Scarpe x
24 Accessori).
- **Problema scoperto e risolto**: con le 5 categorie obbligatorie, la somma minima teorica dei prezzi (Capospalla 40$ + Maglieria 16$ + Pantaloni 18$ +
Scarpe 20$ + Accessori 10$) è 104$, superiore al budget originale del
preset "Outfit Economico" (60$), che quindi non avrebbe mai potuto generare nessun bundle. Risolto alzando i budget dei preset nel database:
Economico 60 -> 120, Bilanciato 120 -> 160 (Premium 250 e Smaltimento Scorte 150 lasciati invariati, già sopra la soglia minima).
- **Budget scelto dall'utente**: nel Configuratore, scegliendo un preset si precompila il campo budget con il suo valore suggerito, ma l'utente puo'
modificarlo liberamente prima di generare. Margine minimo e pesi a/b restano invece legati al preset (diventatva troppo complicato farli scegliere a mano).
Sotto il campo è mostrato il budget minimo teorico sotto cui nessun bundle  possibile, calcolato dinamicamente sui prezzi correnti.

### I quattro preset e cosa cambia tra loro

Nella proposta iniziale il Configuratore doveva permettere di scegliere tra diverse strategie di revenue management, non far impostare a mano parametri tecnici come i pesi a/b.
Poichè un utente ragiona in termini di obiettivi di business ("voglio smaltire le scorte vecchie", "voglio il massimo profitto"). I preset servono quindi da traduzione
tra un obiettivo di business e i parametri tecnici dell'algoritmo (budget, margine minimo, pesi a/b).

 Farne quattro mi è sempbrato abbastanza logico perchè coprono ile strategie possibili, agli estremi e nel mezzo:
- Smaltimento Scorte e Outfit Premium sono i due casi opposti sull'asse profitto/anzianita' della funzione Z (rispettivamente a=0.2/b=0.8 e a=0.7/b=0.3):
 il primo privilegia liberare spazio in magazzino anche a costo di margini piu' bassi, il secondo privilegia il profitto.
- Outfit Economico e Outfit Bilanciato coprono la via di mezzo, con budget e margine minimo via via crescenti, per outfit rispettivamente più accessibili
o più orientati al profitto ma senza gli estremi dei due preset precedenti.

Quattro mi è sembrato un numero abbastanza equilibrato: abbastanza per mostrare strategie davvero diverse tra loro (e non ridondanti), ma non così tanti da rendere la scelta confusa
 per l'utente finale. Restano comunque solo un punto di partenza: il budget resta modificabile liberamente dall'utente in ogni caso, quindi i preset
 guidano ma non vincolano del tutto la scelta.

I preset differiscono per budget massimo, margine minimo richiesto e per i pesi a/b della funzione obiettivo Z (a = peso del profitto, b = peso
dell'anzianità in magazzino). Nel Configuratore, scegliendo un preset compare anche una breve descrizione con lo stesso significato riportato qui,
in modo che sia chiaro durante l'utilizzo dell'app.

| Preset              | Budget | Margine min. | a   | b   | Logica |
|---------------------|--------|--------------|-----|-----|--------|
| Outfit Economico     | 120 $  | 20%          | 0.5 | 0.5 | outfit accessibili, profitto e smaltimento pesati allo stesso modo
| Outfit Bilanciato    | 160 $  | 30%          | 0.6 | 0.4 | via di mezzo, con budget e margine più alti dell'Economico
| Outfit Premium       | 250 $  | 35%          | 0.7 | 0.3 | privilegia il profitto, margine minimo più esigente
| Smaltimento Scorte   | 150 $  | 15%          | 0.2 | 0.8 | margine minimo basso, forte peso sull'anzianità per smaltire i prodotti più vecchi

Dopo aver vcrato una base solida ho deciso che, oltre a prezzo, margine e punteggio Z, ogni bundle mostrato (sia appena
generato che nello storico) dovesse riportare anche:

- **Punteggio di compatibilità **: la stessa media (colore + stile su tutte le coppie di prodotti) usata dall'algoritmo per decidere se il bundle è
valido, mostrata in percentuale.
- **Indice di risparmio**: differenza tra il prezzo originale (pre-sconto) e il prezzo di vendita attuale dei prodotti scelti, in valore assoluto e
in percentuale. Se un prodotto non ha un prezzo originale registrato, si assume che non sia scontato (risparmio 0 su quel prodotto).
- **Stima dello spazio di magazzino liberato**: il dataset non contiene le dimensioni fisiche dei prodotti, quindi non è possibile calcolare uno
spazio "vero". Ho usato un'approssimazione dichiarata: quanto incide la vendita di 1 unità sulla giacenza residua di ciascun prodotto (1 /
quantita_stock), mediata sui 5 prodotti del bundle. Un punteggio più alto indica che il bundle include prodotti vicini a esaurirsi.


## Storico dei bundle salvati

- Sezione Storico: mostra tutti i bundle salvati finora, dal più recente al più vecchio, con le stesse metriche extra dei bundle appena generati.
- **Decisione: nessuna eliminazione.** Era stata considerata l'idea di poter cancellare un bundle dallo Storico, ma la tabella si chiama `bundle_venduti`:
cancellare una riga implicherebbe che una vendita non sia mai avvenuta o sia tata annullata, il che non è il significato voluto. Ho scelto quindi di
 tenere lo Storico permanente e di sola lettura, coerente con il nome della tabella (un registro di vendite, non un carrello modificabile).
- **Bug scoperto e risolto: salvataggi duplicati.**
Ho dovuto utilizzare un doppio controllo prima di abilitare il pulsante "Salva questo bundle" per evitare che si potesse salvare più
 volye lo stesso bundle: un controllo veloce sugli indici della generazione corrente, e un controllo sugli SKU dei prodotti già presenti nel database
(letti da `bundle_venduti`), così un bundle con gli stessi identici prodotti di uno già salvato non si puo' risalvare.

## Note tecniche
- Versione di Flet bloccata a 0.24.1 in `requirements.txt` (invece di`>=0.24.0`) per evitare rotture dovute a versioni troppo recenti con API
 cambiate.



