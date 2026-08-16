import mysql.connector
from mysql.connector import errorcode
import pathlib


class DBConnect:
    """Classe che crea e gestisce un pool di connessioni al database.
    Espone un metodo di classe che funge da factory per prestare le connessioni dal pool."""
    # il pool di connessioni e' un attributo di classe, non di istanza
    _cnxpool = None

    def __init__(self):
        raise RuntimeError('Non istanziare questa classe, usa il metodo di classe get_connection()!')

    @classmethod
    def get_connection(cls, pool_name="my_pool", pool_size=3) -> mysql.connector.pooling.PooledMySQLConnection:
        """Metodo factory per prestare connessioni dal pool. Inizializza il pool se non esiste ancora.
        :param pool_name: nome del pool
        :param pool_size: numero di connessioni nel pool
        :return: mysql.connector.connection"""
        if cls._cnxpool is None:
            try:
                cls._cnxpool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name=pool_name,
                    pool_size=pool_size,
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
