from dataclasses import dataclass
from datetime import date


@dataclass
class Prodotto:
    id_prodotto: str
    nome: str
    categoria_outfit: str
    segmento: str
    stile: str
    colore: str
    prezzo_vendita: float
    prezzo_originale: float
    costo_acquisto: float
    margine_unitario: float
    margine_percentuale: float
    quantita_stock: int
    data_ingresso_magazzino: date
    giorni_in_magazzino: int
    mercato: str
    disponibilita: str
    url: str = ""

    def __str__(self):
        return f"{self.categoria_outfit}: {self.nome} ({self.colore}, {self.stile}) - {self.prezzo_vendita}$"

    def __hash__(self):
        return hash(self.id_prodotto)
