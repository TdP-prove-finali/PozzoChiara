import flet as ft

from model.model import Model
from UI.view import View
from UI.controller import Controller


def main(page):
    # se qualcosa va storto in fase di avvio (es. database non raggiungibile)
    # evito che la finestra resti vuota e mostro almeno un messaggio d'errore
    try:
        my_model = Model()
        my_model.carica_dati(mercato="USA")
        my_view = View(page)
        my_controller = Controller(my_view, my_model)
        my_view.set_controller(my_controller)
        my_view.load_interface()
    except Exception as errore:
        print("Errore in avvio:", errore)
        page.add(ft.Text("Errore, guarda la console di PyCharm", color="red", size=20))
        page.update()


ft.app(target=main)
