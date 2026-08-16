Fashion Bundle Optimizer - Chiara Pozzo (s312166)
==================================================

Struttura del progetto (stessa impostazione MVC + DAO usata in altri
progetti di questo corso):

main.py                              punto di ingresso, assembla Model/View/Controller
requirements.txt
database/
    connector.cnf                    credenziali MySQL (metti qui la tua password)
    DB_connect.py                    pool di connessioni al database
    DAO.py                           tutte le query SQL (prodotti, matrici, bundle)
    fashion_bundle_optimizer_db_dump.sql   dump completo (schema + dati) del database
model/
    prodotto.py                      entity Prodotto
    model.py                         logica applicativa, incluso l'algoritmo di backtracking
UI/
    view.py                          interfaccia grafica Flet
    controller.py                    collega la UI al Model
documents/
    Relazione Tecnica/               qui va la relazione di tesi

Come partire in PyCharm
------------------------
1. Estrai lo zip e apri la cartella "fashion_bundle_optimizer" in PyCharm
   (File > Open, seleziona la cartella che contiene main.py).
2. Terminale integrato: pip install -r requirements.txt
3. Apri database/connector.cnf e metti la tua password MySQL al posto di
   INSERISCI_LA_TUA_PASSWORD.
4. Se preferisci ripartire da zero con il database (invece di usare quello
   gia' importato con DBeaver), puoi eseguire in una volta sola tutto
   database/fashion_bundle_optimizer_db_dump.sql: ricrea schema e dati
   completi (192 prodotti, matrici di compatibilita', preset).
5. Esegui main.py: si apre la finestra Flet (per ora un placeholder,
   la GUI vera si costruisce nel modulo UI/view.py).

Prossimo passo
---------------
Implementare l'algoritmo di backtracking dentro model/model.py
(metodo genera_bundle), poi costruire la GUI nei 3 moduli previsti
dalla proposta dentro UI/view.py.
