

import mysql.connector

try:
    cnx = mysql.connector.connect(
        user="root",
        password="root",
        host="127.0.0.1",
        database="fashion_bundle_optimizer",
    )
    print("CONNESSIONE RIUSCITA!")
    cursor = cnx.cursor()
    cursor.execute("SELECT COUNT(*) FROM prodotti_stock")
    print("Prodotti nel database:", cursor.fetchone()[0])
    cursor.close()
    cnx.close()
except mysql.connector.Error as err:
    print("ERRORE DI CONNESSIONE:")
    print(type(err).__name__, "-", err)