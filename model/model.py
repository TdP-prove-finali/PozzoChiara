from database.DAO import DAO

# il numero di giorni dopo i quali un prodotto viene considerato "fermo troppo a lungo" in magazzino, cioè invenduto
# da tanto tempo
SOGLIA_DEADSTOCK_GIORNI = 180

# Le 5 categorie che devono comparire, una e una sola volta, in ogni bundle.
# Ordinate dalla categoria con meno prodotti disponibili   cosi' l'algoritmo scarta i rami che non hanno senso il prima possibile
CATEGORIE_OBBLIGATORIE = ["Capospalla", "Accessori", "Pantaloni", "Maglieria", "Scarpe"]

# con 5 prodotti nel bundle, le coppie possibili sono 5*4/2 = 10
TOTALE_COPPIE = len(CATEGORIE_OBBLIGATORIE) * (len(CATEGORIE_OBBLIGATORIE) - 1) // 2

# sotto questa media, il bundle non  è bbastanza abbinato e viene scartato
SOGLIA_COMPATIBILITA = 0.5

# ho ridotto un po altrimenti lo  spazio di ricerca sarebbe enorme
# (circa 35 milioni di combinazioni), quindi mettiamo un limite al numero  di nodi esplorati e al numero di bundle raccolti, così
# la ricerca finisce sempre in tempi ragionevoli
LIMITE_NODI_ESPLORATI = 2000000
LIMITE_RISULTATI = 500


class Model:

    def __init__(self):

        self.prodotti = None
        self.matrice_colori = None
        self.matrice_stili = None
        self.preset = None

        # contatore usato dall'algoritmo di backtracking per non esplorare  troppi rami
        self._nodi_esplorati = 0

    def carica_dati(self, mercato):
        # va chiamato una volta all'avvio del programma, prima di generare i bundle
        self.prodotti = DAO.getAllProdotti(mercato)
        self.matrice_colori = DAO.getMatriceColori()
        self.matrice_stili = DAO.getMatriceStili()
        self.preset = DAO.getPreset()
        return self.prodotti

    def get_preset_by_nome(self, nome_preset):
        # cerco tra i preset caricati quello con il nome richiesto
        # (es. "Economico", "Bilanciato", "Premium", "Smaltimento Scorte")
        for p in self.preset:
            if p["nome_preset"] == nome_preset:
                return p
        return None

    def get_budget_minimo(self):
        # il budget piu' basso che potrebbe bastare: la somma del prodotto più economico disponibile in ciascuna delle 5
        # categorie obbligatorie. Sotto questa cifra, generare un bundle
        # è matematicamente impossibile, qualsiasi cosa si scelga
        totale = 0
        for categoria in CATEGORIE_OBBLIGATORIE:
            prezzi_categoria = [p.prezzo_vendita for p in self.prodotti if p.categoria_outfit == categoria]
            if len(prezzi_categoria) == 0:
                return None
            totale += min(prezzi_categoria)
        return round(totale, 2)

    def get_statistiche_magazzino(self):
        # piccolo riepilogo usato dalla home dell'app: quanti prodotti ci sono,
        # quanti sono deadstock, quanto vale il magazzino in totale
        deadstock = [p for p in self.prodotti if p.giorni_in_magazzino > SOGLIA_DEADSTOCK_GIORNI]
        valore_totale = sum(p.prezzo_vendita * p.quantita_stock for p in self.prodotti)
        margine_totale = sum(p.margine_unitario * p.quantita_stock for p in self.prodotti)

        return {
            "totale_prodotti": len(self.prodotti),
            "totale_deadstock": len(deadstock),
            "valore_totale_magazzino": round(valore_totale, 2),
            "margine_totale_magazzino": round(margine_totale, 2),
        }

    def _calcola_compatibilita_bundle(self, prodotti):
        # media dei punteggi di compatibilità' (colore+stile) su tutte le
        # coppie del bundle completo. Usata per i bundle già salvati, dove
        # non ho più il calcolo incrementale fatto durante la ricerca
        punteggi_coppie = []
        for i in range(len(prodotti)):
            for j in range(i + 1, len(prodotti)):
                p1 = prodotti[i]
                p2 = prodotti[j]
                punteggio_colore = self.matrice_colori.get((p1.colore, p2.colore), 0.5)
                punteggio_stile = self.matrice_stili.get((p1.stile, p2.stile), 0.5)
                punteggi_coppie.append((punteggio_colore + punteggio_stile) / 2)

        if len(punteggi_coppie) == 0:
            return 1.0
        return sum(punteggi_coppie) / len(punteggi_coppie)

    def _calcola_risparmio_e_spazio(self, prodotti):
        # indice di risparmio: quanto costa meno il bundle rispetto al
        # prezzo originale (pre-sconto) dei singoli prodotti. Se un prodotto
        # non ha un prezzo originale salvato, considero che non sia scontato
        prezzo_originale_totale = sum(
            p.prezzo_originale if p.prezzo_originale else p.prezzo_vendita for p in prodotti
        )
        prezzo_vendita_totale = sum(p.prezzo_vendita for p in prodotti)
        risparmio_totale = prezzo_originale_totale - prezzo_vendita_totale
        risparmio_pct = (risparmio_totale / prezzo_originale_totale * 100) if prezzo_originale_totale > 0 else 0

        # stima dello spazio di magazzino liberato: non abbiamo le dimensioni
        # fisiche dei prodotti, quindi la approssimiamo con quanto incide la
        # vendita di 1 pezzo sulla giacenza residua di ciascun prodotto
        # (più è vicino a esaurirsi, più alto è il punteggio)
        percentuali_liberate = [(1 / p.quantita_stock) * 100 for p in prodotti if p.quantita_stock > 0]
        indice_spazio_liberato = sum(percentuali_liberate) / len(prodotti) if percentuali_liberate else 0

        return {
            "risparmio_totale": round(risparmio_totale, 2),
            "risparmio_pct": round(risparmio_pct, 1),
            "indice_spazio_liberato": round(indice_spazio_liberato, 2),
        }

    def genera_bundle(self, budget_max, margine_minimo_pct, peso_profitto_a, peso_anzianita_b):
        # divido i prodotti per categoria una volta sola, così non rifaccio il filtro ad ogni chiamata ricorsiva
        prodotti_per_categoria = {}
        for categoria in CATEGORIE_OBBLIGATORIE:
            prodotti_per_categoria[categoria] = [p for p in self.prodotti if p.categoria_outfit == categoria]
            if len(prodotti_per_categoria[categoria]) == 0:
                # manca completamente una categoria: nessun bundle e' possibile
                return []

        risultati = []
        self._nodi_esplorati = 0

        self.ricorsione(
            prodotti_per_categoria,
            0,          # indice della categoria che sto per scegliere
            [],         # prodotti scelti finora
            0,          # prezzo totale parziale
            0,          # somma dei punteggi di compatibilità delle coppie gia' formate
            0,          # quante coppie ho già formato
            budget_max,
            margine_minimo_pct,
            peso_profitto_a,
            peso_anzianita_b,
            risultati,
        )

        #bundle con il punteggio più alto per primi
        risultati.sort(key=lambda b: b["punteggio_z"], reverse=True)
        return risultati

    def ricorsione(self, prodotti_per_categoria, indice_categoria, scelti, prezzo_parziale,
                   somma_compatibilita, coppie_contate, budget_max, margine_minimo_pct,
                   peso_profitto_a, peso_anzianita_b, risultati):

        #  mi fermo se ho già esplorato troppi rami o trovato già abbastanza bundle
        if self._nodi_esplorati >= LIMITE_NODI_ESPLORATI or len(risultati) >= LIMITE_RISULTATI:
            return
        self._nodi_esplorati += 1

        # caso base: ho scelto un prodotto per ognuna delle 5 categorie,
        # il bundle e' completo
        if indice_categoria == len(CATEGORIE_OBBLIGATORIE):
            margine_totale = sum(p.margine_unitario for p in scelti)

            # margine percentuale complessivo del bundle (  margine totale sul prezzo totale)
            margine_pct_bundle = (margine_totale / prezzo_parziale) * 100
            if margine_pct_bundle < margine_minimo_pct:
                return

            compatibilita_media = somma_compatibilita / TOTALE_COPPIE
            if compatibilita_media < SOGLIA_COMPATIBILITA:
                return

            anzianita_totale = sum(p.giorni_in_magazzino for p in scelti)
            punteggio_z = peso_profitto_a * margine_totale + peso_anzianita_b * anzianita_totale

            metriche_extra = self._calcola_risparmio_e_spazio(scelti)

            risultati.append({
                "prodotti": list(scelti),
                "prezzo_totale": round(prezzo_parziale, 2),
                "margine_totale": round(margine_totale, 2),
                "punteggio_z": round(punteggio_z, 2),
                "punteggio_compatibilita": round(compatibilita_media, 2),
                "risparmio_totale": metriche_extra["risparmio_totale"],
                "risparmio_pct": metriche_extra["risparmio_pct"],
                "indice_spazio_liberato": metriche_extra["indice_spazio_liberato"],
            })
            return

        # ricorsione: provo ogni prodotto della categoria corrente
        categoria = CATEGORIE_OBBLIGATORIE[indice_categoria]
        for prodotto in prodotti_per_categoria[categoria]:
            nuovo_prezzo = prezzo_parziale + prodotto.prezzo_vendita

            # POTATURA 1 - budget: se il parziale sfora gia' il budget,
            # non ha senso continuare su questo ramo
            if nuovo_prezzo > budget_max:
                continue

            # calcolo quanto aggiungerebbe alla compatibilita' totale
            # scegliere questo prodotto insieme a quelli gia' scelti
            nuova_somma_compatibilita = somma_compatibilita
            for gia_scelto in scelti:
                punteggio_colore = self.matrice_colori.get((prodotto.colore, gia_scelto.colore), 0.5)
                punteggio_stile = self.matrice_stili.get((prodotto.stile, gia_scelto.stile), 0.5)
                nuova_somma_compatibilita += (punteggio_colore + punteggio_stile) / 2

            nuove_coppie_contate = coppie_contate + len(scelti)

            # POTATURA 2 - compatibilita': calcolo la media che otterrei
            # nel MIGLIOR caso possibile, cioe' se tutte le coppie ancora
            # da formare avessero il punteggio massimo (1.0). Se nemmeno
            # cosi' si raggiunge la soglia, questo ramo non puo' produrre
            # un bundle valido: lo scarto subito, senza esplorarlo
            coppie_rimanenti = TOTALE_COPPIE - nuove_coppie_contate
            media_migliore_possibile = (nuova_somma_compatibilita + coppie_rimanenti) / TOTALE_COPPIE
            if media_migliore_possibile < SOGLIA_COMPATIBILITA:
                continue

            scelti.append(prodotto)
            self.ricorsione(
                prodotti_per_categoria, indice_categoria + 1, scelti, nuovo_prezzo,
                nuova_somma_compatibilita, nuove_coppie_contate, budget_max, margine_minimo_pct,
                peso_profitto_a, peso_anzianita_b, risultati,
            )
            scelti.pop()

            if self._nodi_esplorati >= LIMITE_NODI_ESPLORATI or len(risultati) >= LIMITE_RISULTATI:
                return

    def salva_bundle_scelto(self, id_preset, bundle):
        # bundle e' un dict con dentro prodotti, prezzo_totale, margine_totale, punteggio_z
        DAO.salvaBundle(
            id_preset=id_preset,
            prezzo_totale=bundle["prezzo_totale"],
            margine_totale=bundle["margine_totale"],
            punteggio_z=bundle["punteggio_z"],
            prodotti_sku=[p.id_prodotto for p in bundle["prodotti"]],
        )

    def get_bundle_salvati(self):
        # nel database ogni bundle salvato ha solo la lista di SKU (testo), quindi per ognuno ricostruisco i veri oggetti Prodotto usando
        # quelli gia' caricati in memoria
        prodotti_per_sku = {p.id_prodotto: p for p in self.prodotti}

        # per risalire dal nome del preset non uso una join in SQL: uso direttamente i preset che ho gia' caricato in memoria (self.preset),
        # costruendo un dizionario id_preset -> nome_preset
        nome_preset_per_id = {p["id_preset"]: p["nome_preset"] for p in self.preset}

        bundle_salvati = []
        for riga in DAO.getBundleVenduti():
            sku_scelti = riga["prodotti_sku"].split(",")
            prodotti_bundle = [prodotti_per_sku[sku] for sku in sku_scelti if sku in prodotti_per_sku]

            compatibilita = self._calcola_compatibilita_bundle(prodotti_bundle)
            metriche_extra = self._calcola_risparmio_e_spazio(prodotti_bundle)

            bundle_salvati.append({
                "id_bundle": riga["id_bundle"],
                "data_creazione": riga["data_creazione"],
                "nome_preset": nome_preset_per_id.get(riga["id_preset"], "Preset sconosciuto"),
                "prezzo_totale": riga["prezzo_totale"],
                "margine_totale": riga["margine_totale"],
                "punteggio_z": riga["punteggio_z"],
                "prodotti": prodotti_bundle,
                "punteggio_compatibilita": round(compatibilita, 2),
                "risparmio_totale": metriche_extra["risparmio_totale"],
                "risparmio_pct": metriche_extra["risparmio_pct"],
                "indice_spazio_liberato": metriche_extra["indice_spazio_liberato"],
            })
        return bundle_salvati
