
import pathlib
import mysql.connector

cnf_path = pathlib.Path(__file__).resolve().parent / "database" / "connector.cnf"
print("Percorso del file connector.cnf usato:", cnf_path)
print("Il file esiste?", cnf_path.exists())
print("Contenuto del file:")
print(cnf_path.read_text())
print("-" * 50)

try:
    pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="test_pool",
        pool_size=3,
        option_files=str(cnf_path),
    )
    cnx = pool.get_connection()
    print("CONNESSIONE TRAMITE POOL RIUSCITA!")
    cnx.close()
except Exception as err:
    print("ERRORE (tipo):", type(err).__name__)
    print("ERRORE (messaggio):", err)