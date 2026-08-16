import mysql.connector
from mysql.connector import errorcode
import pathlib


class DBConnect:
    # questa classe non va mai istanziata: serve solo a creare e gestire
    # il pool di connessioni al database, tramite il metodo get_connection()


    _cnxpool = None

    def __init__(self):
        raise RuntimeError('Non istanziare questa classe, usa il metodo di classe get_connection()!')

    @classmethod
    def get_connection(cls):
        # se il pool non è ancora stato creato lo creo adesso (la prima
        # volta che qualcuno chiede una connessione), altrimenti riuso
        # quello già esistente
        if cls._cnxpool is None:
            try:
                cls._cnxpool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="my_pool",
                    pool_size=3,
                    option_files=f"{pathlib.Path(__file__).resolve().parent}/connector.cnf"
                )
                return cls._cnxpool.get_connection()
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    print("Utente o password errati nel file connector.cnf")
                    return None
                elif err.errno == errorcode.ER_BAD_DB_ERROR:
                    print("Il database non esiste")
                    return None
                else:
                    print(err)
                    return None
        else:
            return cls._cnxpool.get_connection()