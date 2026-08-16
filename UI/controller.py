# Il Controller sta in mezzo tra View e Model: la View non parla mai
# direttamente con il Model, passa sempre da qui.


class Controller:
    def __init__(self, view, model):
        self._view = view
        self._model = model

    def get_prodotti(self):
        # i prodotti sono gia' stati caricati dal database in main.py,
        # con model.carica_dati(), quindi qui li restituisco solo
        return self._model.prodotti

    def get_preset(self):
        return self._model.preset

    def get_preset_by_nome(self, nome_preset):
        return self._model.get_preset_by_nome(nome_preset)

    def get_statistiche(self):
        return self._model.get_statistiche_magazzino()

    def get_budget_minimo(self):
        return self._model.get_budget_minimo()

    def genera_bundle_handler(self, nome_preset, budget_scelto):
        # margine minimo e pesi vengono dal preset, ma il budget e' quello
        # scelto dall'utente nel campo del Configuratore
        preset = self._model.get_preset_by_nome(nome_preset)
        return self._model.genera_bundle(
            budget_max=budget_scelto,
            margine_minimo_pct=preset["margine_minimo_pct"],
            peso_profitto_a=preset["peso_profitto_a"],
            peso_anzianita_b=preset["peso_anzianita_b"],
        )

    def salva_bundle_handler(self, nome_preset, bundle):
        preset = self._model.get_preset_by_nome(nome_preset)
        self._model.salva_bundle_scelto(preset["id_preset"], bundle)

    def get_bundle_salvati(self):
        return self._model.get_bundle_salvati()
