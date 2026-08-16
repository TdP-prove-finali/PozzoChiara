from database.DB_connect import DBConnect
from model.prodotto import Prodotto



class DAO():

    @staticmethod
    def getAllProdotti(mercato):
        # prendo una connessione dal pool
        conn = DBConnect.get_connection()

        # qui accumulo gli oggetti Prodotto che leggo dal database
        results = []

        cursor = conn.cursor(dictionary=True)

        # prendo solo i prodotti del mercato che mi interessa
        query = """select *
                    from prodotti_stock
                    where mercato = %s"""


        cursor.execute(query, (mercato,))



        for row in cursor:
            results.append(Prodotto(**row))


        cursor.close()
        conn.close()
        return results

    @staticmethod
    def getMatriceColori():
        conn = DBConnect.get_connection()

        # qui uso un dizionario e non una lista, perche' mi serve poter chiedere "che punteggio hanno questi due colori insieme?" in modo veloce,
        # tipo matrice_colori[("Black", "White")]
        results = {}

        cursor = conn.cursor(dictionary=True)
        query = """select *
                    from matrice_compatibilita_colori"""

        cursor.execute(query)

        # per ogni riga della tabella creo la chiave (colore_1, colore_2) -> punteggio
        for row in cursor:
            results[(row["colore_1"], row["colore_2"])] = float(row["punteggio_compatibilita"])

        cursor.close()
        conn.close()
        return results

    @staticmethod
    def getMatriceStili():

        conn = DBConnect.get_connection()

        results = {}

        cursor = conn.cursor(dictionary=True)
        query = """select *
                    from matrice_compatibilita_stili"""

        cursor.execute(query)

        for row in cursor:
            results[(row["stile_1"], row["stile_2"])] = float(row["punteggio_compatibilita"])

        cursor.close()
        conn.close()
        return results

    @staticmethod
    def getPreset():
        # i preset sono le configurazioni pronte (Economico, Bilanciato, Premium, Smaltimento Scorte)
        # con budget massimo, margine minimo e pesi a/b della funzione obiettivo Z
        conn = DBConnect.get_connection()

        results = []

        cursor = conn.cursor(dictionary=True)
        query = """select *
                    from parametri_configurazione"""

        cursor.execute(query)

        # qui non serve costruire un oggetto apposito, mi tengo direttament il dizionario cosi' come arriva dal database
        for row in cursor:
            results.append(row)

        cursor.close()
        conn.close()
        return results

    @staticmethod
    def getBundleVenduti():
        # tutti i bundle salvati finora, con anche il nome del preset usato, dal piu' recente al piu' vecchio
        conn = DBConnect.get_connection()

        results = []

        cursor = conn.cursor(dictionary=True)
        query = """select *
                        from bundle_venduti
                        order by data_creazione desc"""

        cursor.execute(query)

        for row in cursor:
            results.append(row)

        cursor.close()
        conn.close()
        return results

    @staticmethod
    def salvaBundle(id_preset, prezzo_totale, margine_totale, punteggio_z, prodotti_sku):
        # questo metodo non legge, scrive: salva il bundle scelto dall'utente  nella tabella bundle_venduti, cosi' rimane traccia
        # di cosa e' stato generato.
        #A differenza delle select viste finora, qui uso una insert: la select serve solo per leggere righe gia' esistenti,
        # mentre la insert aggiunge una riga nuova alla tabella (qui una nuova riga in bundle_venduti)
        conn = DBConnect.get_connection()

        cursor = conn.cursor()

        #le colonne indicate tra parentesi sono quelle che vado a riempire
        #i valori vanno messi nello stesso ordine delle colonne

        query = """
            INSERT INTO bundle_venduti (id_preset, prezzo_totale, margine_totale, punteggio_z, prodotti_sku)
            VALUES (%s, %s, %s, %s, %s)
            """

        # prodotti_sku e' una lista di sku (es. ["ABC123", "DEF456"]), la trasformo in una stringa unica separata da virgole perche' la colonna
        # sul database è di tipo testo (non posso salvare una lista Python direttamente)
        sku_come_testo = ",".join(prodotti_sku)
        valori = (id_preset, prezzo_totale, margine_totale, punteggio_z, sku_come_testo)

        cursor.execute(query, valori)

        # con la insert devo anche fare il commit, altrimenti la modifica  non viene salvata davvero
        conn.commit()

        cursor.close()
        conn.close()
