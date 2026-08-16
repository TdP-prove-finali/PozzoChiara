import flet as ft

from model.model import SOGLIA_DEADSTOCK_GIORNI

# nomi delle sezioni, nell'ordine in cui compaiono nel menu laterale
SEZIONE_HOME = "Home"
SEZIONE_MAGAZZINO = "Magazzino"
SEZIONE_CONFIGURATORE = "Configuratore"
SEZIONE_RISULTATI = "Risultati"
SEZIONE_STORICO = "Storico"
SEZIONI = [SEZIONE_HOME, SEZIONE_MAGAZZINO, SEZIONE_CONFIGURATORE, SEZIONE_RISULTATI, SEZIONE_STORICO]

# colore principale dell'app, usato per il tema e per i dettagli grafici
COLORE_PRINCIPALE = ft.colors.INDIGO

# breve spiegazione di cosa cambia tra un preset e l'altro, mostrata
# nel Configuratore quando l'utente ne sceglie uno
DESCRIZIONI_PRESET = {
    "Outfit Economico": "Budget contenuto e margine minimo leggero: pensato per outfit "
                         "accessibili, con profitto e smaltimento delle scorte vecchie pesati allo stesso modo.",
    "Outfit Bilanciato": "Via di mezzo tra profitto e smaltimento scorte, con budget e "
                          "margine minimo piu' alti dell'Economico.",
    "Outfit Premium": "Budget piu' alto e margine minimo piu' esigente: privilegia il "
                       "profitto rispetto allo smaltimento dei prodotti piu' vecchi.",
    "Smaltimento Scorte": "Margine minimo basso e forte peso sull'anzianita': pensato per "
                           "smaltire i prodotti fermi in magazzino da piu' tempo, anche a scapito del profitto.",
}


class View:
    def __init__(self, page):
        page.title = "Fashion Bundle Optimizer"
        page.window_width = 1300
        page.window_height = 850
        page.window_resizable = True
        page.padding = 0
        page.bgcolor = ft.colors.GREY_50

        self._page = page
        self._page.theme_mode = ft.ThemeMode.LIGHT
        self._page.theme = ft.Theme(color_scheme_seed=COLORE_PRINCIPALE)

        # Controller (impostato dopo la costruzione, per evitare dipendenza circolare)
        self._controller = None

        # menu laterale a sinistra, sempre visibile, per spostarsi tra le sezioni
        self._nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=90,
            min_extended_width=180,
            bgcolor=ft.colors.WHITE,
            destinations=[
                ft.NavigationRailDestination(icon=ft.icons.HOME_OUTLINED, selected_icon=ft.icons.HOME, label="Home"),
                ft.NavigationRailDestination(icon=ft.icons.INVENTORY_2_OUTLINED, selected_icon=ft.icons.INVENTORY_2, label="Magazzino"),
                ft.NavigationRailDestination(icon=ft.icons.TUNE, selected_icon=ft.icons.TUNE, label="Configuratore"),
                ft.NavigationRailDestination(icon=ft.icons.CHECKLIST_OUTLINED, selected_icon=ft.icons.CHECKLIST, label="Risultati"),
                ft.NavigationRailDestination(icon=ft.icons.HISTORY_OUTLINED, selected_icon=ft.icons.HISTORY, label="Storico"),
            ],
            on_change=self._on_cambio_sezione,
        )

        # colonna dove viene disegnata la sezione attualmente selezionata
        self._colonna_contenuto = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

        # riferimenti ai controlli che dovremo aggiornare piu' avanti
        self._dropdown_preset = None

        # ultimo risultato della generazione, tenuto qui perche' la sezione
        # Risultati viene ricostruita da zero ogni volta che ci si passa
        self._ultimo_preset_usato = None
        self._ultimi_bundle_trovati = None

        # indici (posizione nella lista _ultimi_bundle_trovati) dei bundle
        # gia' salvati in questa generazione. Serve perche' la sezione
        # Risultati viene ricostruita da zero ogni volta che ci si torna:
        # senza questo insieme, il bottone "perderebbe memoria" di quali
        # bundle erano gia' stati salvati e si potrebbe salvare piu' volte
        # lo stesso bundle
        self._indici_bundle_salvati = set()

    def set_controller(self, controller):
        self._controller = controller

    def load_interface(self):
        layout = ft.Row(
            controls=[
                self._nav_rail,
                ft.VerticalDivider(width=1),
                ft.Container(content=self._colonna_contenuto, padding=40, expand=True),
            ],
            expand=True,
        )
        self._page.add(layout)
        self._mostra_sezione(SEZIONE_HOME)

    # ------------------------------------------------------------
    # Navigazione tramite il menu laterale
    # ------------------------------------------------------------
    def _on_cambio_sezione(self, e):
        self._mostra_sezione(SEZIONI[self._nav_rail.selected_index])

    def _mostra_sezione(self, nome_sezione):
        costruttori = {
            SEZIONE_HOME: self._costruisci_home,
            SEZIONE_MAGAZZINO: self._costruisci_magazzino,
            SEZIONE_CONFIGURATORE: self._costruisci_configuratore,
            SEZIONE_RISULTATI: self._costruisci_risultati,
            SEZIONE_STORICO: self._costruisci_storico,
        }

        self._nav_rail.selected_index = SEZIONI.index(nome_sezione)
        self._colonna_contenuto.controls = [costruttori[nome_sezione]()]
        self._page.update()

    # ------------------------------------------------------------
    # Home: banner di benvenuto + statistiche veloci sul magazzino
    # ------------------------------------------------------------
    def _costruisci_home(self):
        stat = self._controller.get_statistiche()

        banner = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Fashion Bundle Optimizer", size=32, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                    ft.Text(
                        "Genera bundle di outfit ottimizzati a partire dallo stock di magazzino, "
                        "bilanciando profitto e smaltimento dei prodotti fermi da piu' tempo.",
                        size=15,
                        color=ft.colors.WHITE,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=COLORE_PRINCIPALE,
            border_radius=16,
            padding=30,
        )

        riga_statistiche = ft.Row(
            controls=[
                self._card_statistica("Prodotti in stock", stat["totale_prodotti"], ft.icons.INVENTORY_2, ft.colors.INDIGO),
                self._card_statistica("Prodotti deadstock", stat["totale_deadstock"], ft.icons.WARNING_AMBER_ROUNDED, ft.colors.RED),
                self._card_statistica("Valore magazzino", f"{stat['valore_totale_magazzino']} $", ft.icons.ATTACH_MONEY, ft.colors.GREEN),
                self._card_statistica("Margine potenziale", f"{stat['margine_totale_magazzino']} $", ft.icons.TRENDING_UP, ft.colors.PURPLE),
            ],
            wrap=True,
            spacing=20,
        )

        return ft.Column(
            controls=[
                banner,
                ft.Container(height=25),
                riga_statistiche,
            ],
        )

    def _card_statistica(self, titolo, valore, icona, colore):
        # riquadro bianco con icona colorata, numero grande e etichetta sotto
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(icona, color=colore, size=26),
                        bgcolor=ft.colors.with_opacity(0.12, colore),
                        border_radius=50,
                        padding=12,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(str(valore), size=22, weight=ft.FontWeight.BOLD),
                            ft.Text(titolo, size=12, color=ft.colors.GREY_600),
                        ],
                        spacing=2,
                    ),
                ],
                spacing=15,
            ),
            bgcolor=ft.colors.WHITE,
            border_radius=12,
            padding=18,
            width=260,
            shadow=ft.BoxShadow(
                blur_radius=10,
                color=ft.colors.with_opacity(0.08, ft.colors.BLACK),
                offset=ft.Offset(0, 3),
            ),
        )

    # ------------------------------------------------------------
    # Sezione Magazzino: tabella con tutti i prodotti in stock
    # ------------------------------------------------------------
    def _costruisci_magazzino(self):
        prodotti = self._controller.get_prodotti()

        righe = []
        for p in prodotti:
            e_deadstock = p.giorni_in_magazzino > SOGLIA_DEADSTOCK_GIORNI

            riga = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(p.nome)),
                    ft.DataCell(ft.Text(p.categoria_outfit)),
                    ft.DataCell(ft.Text(p.colore)),
                    ft.DataCell(ft.Text(f"{p.prezzo_vendita} $")),
                    ft.DataCell(ft.Text(str(p.giorni_in_magazzino))),
                    ft.DataCell(ft.Text(str(p.quantita_stock))),
                ],
                # se e' deadstock, coloro la riga di rosso chiaro per farla notare
                color=ft.colors.RED_50 if e_deadstock else None,
            )
            righe.append(riga)

        tabella = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nome")),
                ft.DataColumn(ft.Text("Categoria")),
                ft.DataColumn(ft.Text("Colore")),
                ft.DataColumn(ft.Text("Prezzo")),
                ft.DataColumn(ft.Text("Giorni in magazzino")),
                ft.DataColumn(ft.Text("Quantita'")),
            ],
            rows=righe,
            heading_row_color=ft.colors.INDIGO_50,
            column_spacing=40,
        )

        intestazione = ft.Row(
            controls=[
                ft.Icon(ft.icons.INVENTORY_2_OUTLINED, color=COLORE_PRINCIPALE),
                ft.Text(f"Prodotti in stock: {len(prodotti)}", size=20, weight=ft.FontWeight.BOLD),
            ],
            spacing=10,
        )

        legenda = ft.Text(
            f"In rosso i prodotti fermi da piu' di {SOGLIA_DEADSTOCK_GIORNI} giorni (deadstock)",
            italic=True,
            size=12,
            color=ft.colors.GREY_600,
        )

        return ft.Container(
            content=ft.Column(
                controls=[intestazione, legenda, ft.Container(height=10), tabella],
                scroll=ft.ScrollMode.AUTO,
            ),
            bgcolor=ft.colors.WHITE,
            border_radius=12,
            padding=25,
            shadow=ft.BoxShadow(
                blur_radius=10,
                color=ft.colors.with_opacity(0.06, ft.colors.BLACK),
                offset=ft.Offset(0, 3),
            ),
        )

    # ------------------------------------------------------------
    # Sezione Configuratore: scelta preset e bottone per generare il bundle
    # ------------------------------------------------------------
    def _costruisci_configuratore(self):
        preset = self._controller.get_preset()

        self._dropdown_preset = ft.Dropdown(
            label="Scegli un preset",
            options=[ft.dropdown.Option(p["nome_preset"]) for p in preset],
            width=320,
            on_change=self._on_cambio_preset,
        )

        # testo che spiega cosa cambia nel preset scelto (aggiornato in
        # _on_cambio_preset quando l'utente seleziona un valore diverso)
        self._testo_descrizione_preset = ft.Text(
            "Scegli un preset per vedere una breve spiegazione.",
            italic=True,
            size=12,
            color=ft.colors.GREY_600,
            width=320,
        )

        # budget piu' basso che potrebbe teoricamente bastare (somma dei
        # prodotti piu' economici delle 5 categorie): lo tengo qui per
        # poterlo controllare quando si clicca "Genera Bundle"
        self._budget_minimo = self._controller.get_budget_minimo()

        # campo dove l'utente puo' scrivere il budget che vuole usare.
        # quando si sceglie un preset viene precompilato con il suo valore,
        # ma resta modificabile
        self._campo_budget = ft.TextField(
            label="Budget massimo ($)",
            width=320,
            keyboard_type=ft.KeyboardType.NUMBER,
            helper_text=f"Con meno di {self._budget_minimo} $ non e' possibile generare nessun bundle "
                        f"(e' la somma dei prodotti piu' economici delle 5 categorie obbligatorie).",
        )

        bottone_genera = ft.ElevatedButton(
            text="Genera Bundle",
            icon=ft.icons.AUTO_AWESOME,
            on_click=self._on_click_genera_bundle,
        )

        intestazione = ft.Row(
            controls=[
                ft.Icon(ft.icons.TUNE, color=COLORE_PRINCIPALE),
                ft.Text("Configuratore Strategico", size=20, weight=ft.FontWeight.BOLD),
            ],
            spacing=10,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    intestazione,
                    ft.Text(
                        "Scegli un preset (imposta margine minimo e pesi consigliati) e "
                        "poi personalizza il budget come preferisci.",
                        size=13,
                        color=ft.colors.GREY_600,
                    ),
                    ft.Container(height=15),
                    self._dropdown_preset,
                    ft.Container(height=8),
                    self._testo_descrizione_preset,
                    ft.Container(height=15),
                    self._campo_budget,
                    ft.Container(height=15),
                    bottone_genera,
                ],
            ),
            bgcolor=ft.colors.WHITE,
            border_radius=12,
            padding=30,
            width=420,
            shadow=ft.BoxShadow(
                blur_radius=10,
                color=ft.colors.with_opacity(0.06, ft.colors.BLACK),
                offset=ft.Offset(0, 3),
            ),
        )

    def _mostra_messaggio(self, testo):
        # modo "classico" di mostrare un messaggio in basso (snack bar),
        # per conferme leggere che non serve che l'utente clicchi via
        self._page.snack_bar = ft.SnackBar(ft.Text(testo))
        self._page.snack_bar.open = True
        self._page.update()

    def _mostra_alert(self, testo):
        # popup ben visibile, l'utente deve cliccare "OK" per chiuderlo:
        # usato per gli avvisi importanti che non deve perdere
        dialogo = ft.AlertDialog(
            title=ft.Text("Attenzione"),
            content=ft.Text(testo),
            actions=[ft.TextButton("OK", on_click=lambda e: self._chiudi_alert(dialogo))],
        )
        self._page.dialog = dialogo
        dialogo.open = True
        self._page.update()

    def _chiudi_alert(self, dialogo):
        dialogo.open = False
        self._page.update()

    def _on_cambio_preset(self, e):
        # quando si sceglie un preset, scrivo il suo budget nel campo,
        # cosi' l'utente parte da un valore sensato e puo' modificarlo
        preset = self._controller.get_preset_by_nome(self._dropdown_preset.value)
        self._campo_budget.value = str(preset["budget_max"])

        # aggiorno anche la spiegazione del preset scelto
        self._testo_descrizione_preset.value = DESCRIZIONI_PRESET.get(
            self._dropdown_preset.value, ""
        )
        self._page.update()

    def _on_click_genera_bundle(self, e):
        if self._dropdown_preset.value is None:
            self._mostra_alert("Scegli prima un preset")
            return

        # il budget scritto nel campo deve essere un numero valido e positivo
        try:
            budget_scelto = float(self._campo_budget.value)
        except (TypeError, ValueError):
            self._mostra_alert("Scrivi un budget valido (es. 120)")
            return

        if budget_scelto <= 0:
            self._mostra_alert("Il budget deve essere maggiore di zero")
            return

        # sotto il budget minimo teorico non serve nemmeno lanciare la
        # ricerca: sarebbe impossibile trovare un bundle, meglio dirlo subito
        if self._budget_minimo is not None and budget_scelto < self._budget_minimo:
            self._mostra_alert(f"Budget troppo basso: con questo preset servono almeno {self._budget_minimo} $ per poter generare un bundle.")
            return

        # ricordo con quale preset ho generato, mi serve dopo per salvare
        self._ultimo_preset_usato = self._dropdown_preset.value
        self._ultimi_bundle_trovati = self._controller.genera_bundle_handler(self._ultimo_preset_usato, budget_scelto)

        # e' una generazione nuova: nessuno di questi bundle e' stato ancora salvato
        self._indici_bundle_salvati = set()

        # porto subito l'utente sui risultati appena generati
        self._mostra_sezione(SEZIONE_RISULTATI)

    # ------------------------------------------------------------
    # Sezione Risultati: galleria dei bundle generati
    # ------------------------------------------------------------
    def _costruisci_risultati(self):
        # non e' ancora stata fatta nessuna ricerca
        if self._ultimi_bundle_trovati is None:
            return self._stato_vuoto_risultati("Genera un bundle dal Configuratore per vedere qui i risultati.")

        # ricerca fatta, ma nessun bundle rispetta i vincoli scelti
        if len(self._ultimi_bundle_trovati) == 0:
            return self._stato_vuoto_risultati(
                "Nessun bundle trovato con questi vincoli. Prova ad aumentare il budget o a scegliere un altro preset."
            )

        bundle_da_mostrare = self._ultimi_bundle_trovati[:50]

        # insieme degli sku (uno per prodotto) di ogni bundle gia' salvato nel
        # database, cosi' posso riconoscere un bundle identico a uno gia' salvato
        # anche se arriva da una generazione diversa (es. rigenerando con lo
        # stesso preset e budget, l'algoritmo e' deterministico e puo' ridare
        # esattamente lo stesso bundle in cima ai risultati)
        sku_bundle_gia_salvati = {
            frozenset(p.id_prodotto for p in b["prodotti"]) for b in self._controller.get_bundle_salvati()
        }

        intestazione = ft.Text(
            f"{len(self._ultimi_bundle_trovati)} bundle trovati con il preset \"{self._ultimo_preset_usato}\"",
            size=20,
            weight=ft.FontWeight.BOLD,
        )

        controlli = [intestazione]

        if len(self._ultimi_bundle_trovati) > len(bundle_da_mostrare):
            controlli.append(
                ft.Text(
                    f"Mostro i primi {len(bundle_da_mostrare)}, ordinati dal punteggio piu' alto.",
                    italic=True,
                    size=12,
                    color=ft.colors.GREY_600,
                )
            )

        controlli.append(ft.Container(height=15))
        for indice, bundle in enumerate(bundle_da_mostrare):
            controlli.append(self._card_bundle(indice, bundle, sku_bundle_gia_salvati))

        return ft.Column(controls=controlli, scroll=ft.ScrollMode.AUTO)

    def _stato_vuoto_risultati(self, testo):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.icons.CHECKLIST_RTL, size=60, color=ft.colors.GREY_400),
                    ft.Text(testo, italic=True, color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            padding=60,
        )

    def _riga_metriche_extra(self, bundle):
        # le 3 informazioni che nella proposta al prof avevamo promesso di
        # mostrare per ogni bundle: compatibilita', risparmio, spazio liberato
        compatibilita_pct = round(bundle["punteggio_compatibilita"] * 100)

        return ft.Row(
            controls=[
                self._chip_metrica(
                    ft.icons.PALETTE_OUTLINED,
                    f"Compatibilita' {compatibilita_pct}%",
                    ft.colors.INDIGO,
                ),
                self._chip_metrica(
                    ft.icons.SAVINGS_OUTLINED,
                    f"Risparmio {bundle['risparmio_totale']} $ ({bundle['risparmio_pct']}%)",
                    ft.colors.GREEN,
                ),
                self._chip_metrica(
                    ft.icons.INVENTORY_2_OUTLINED,
                    f"Spazio liberato ~{bundle['indice_spazio_liberato']}%",
                    ft.colors.ORANGE,
                ),
            ],
            spacing=10,
            wrap=True,
        )

    def _chip_metrica(self, icona, testo, colore):
        # piccola "etichetta" colorata per mostrare una metrica in modo compatto
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icona, size=14, color=colore),
                    ft.Text(testo, size=12, color=colore),
                ],
                spacing=4,
            ),
            bgcolor=ft.colors.with_opacity(0.1, colore),
            border_radius=20,
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
        )

    def _card_bundle(self, indice, bundle, sku_bundle_gia_salvati):
        # elenco dei prodotti scelti in questo bundle, una riga per prodotto
        righe_prodotti = ft.Column(
            controls=[
                ft.Text(f"• {p.categoria_outfit}: {p.nome} ({p.colore}) - {p.prezzo_vendita} $", size=13)
                for p in bundle["prodotti"]
            ],
            spacing=3,
        )

        # un bundle e' gia' salvato se: o l'ho appena salvato in questa stessa
        # generazione (stesso indice, controllo veloce senza rileggere il database),
        # oppure se i suoi prodotti (stessi sku) coincidono con un bundle gia'
        # presente nel database. Questo secondo controllo serve perche' l'algoritmo
        # e' deterministico: rigenerando con lo stesso preset e budget puo' ridare
        # esattamente lo stesso bundle, che pero' e' gia' stato salvato in passato
        sku_bundle_corrente = frozenset(p.id_prodotto for p in bundle["prodotti"])
        gia_salvato = indice in self._indici_bundle_salvati or sku_bundle_corrente in sku_bundle_gia_salvati

        bottone_salva = ft.ElevatedButton(
            text="Bundle salvato" if gia_salvato else "Salva questo bundle",
            icon=ft.icons.CHECK_CIRCLE if gia_salvato else ft.icons.SAVE_OUTLINED,
            disabled=gia_salvato,
            style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_50, color=ft.colors.GREEN_700) if gia_salvato else None,
        )
        # passo anche il bottone e l'indice, cosi' dopo il salvataggio posso
        # cambiare il bottone stesso e segnare l'indice come gia' salvato
        bottone_salva.on_click = lambda e, b=bundle, i=indice, pulsante=bottone_salva: self._on_click_salva_bundle(b, i, pulsante)

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(f"Bundle #{indice + 1} - punteggio: {bundle['punteggio_z']}", size=16, weight=ft.FontWeight.BOLD),
                    righe_prodotti,
                    ft.Container(height=8),
                    self._riga_metriche_extra(bundle),
                    ft.Container(height=8),
                    ft.Text(
                        f"Prezzo totale: {bundle['prezzo_totale']} $     Margine totale: {bundle['margine_totale']} $",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Container(height=8),
                    bottone_salva,
                ],
            ),
            bgcolor=ft.colors.WHITE,
            border_radius=12,
            padding=20,
            margin=ft.margin.only(bottom=15),
            shadow=ft.BoxShadow(
                blur_radius=8,
                color=ft.colors.with_opacity(0.06, ft.colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )

    def _on_click_salva_bundle(self, bundle, indice, pulsante):
        self._controller.salva_bundle_handler(self._ultimo_preset_usato, bundle)

        # segno questo indice come gia' salvato, cosi' se si esce e si
        # ritorna su Risultati il bottone nasce gia' disabilitato
        self._indici_bundle_salvati.add(indice)

        # invece di un messaggio a parte, cambio il bottone stesso: diventa
        # verde, cambia scritta e si disabilita (non si puo' salvare due volte)
        pulsante.text = "Bundle salvato"
        pulsante.icon = ft.icons.CHECK_CIRCLE
        pulsante.style = ft.ButtonStyle(
            bgcolor=ft.colors.GREEN_50,
            color=ft.colors.GREEN_700,
        )
        pulsante.disabled = True
        self._page.update()

    # ------------------------------------------------------------
    # Sezione Storico: tutti i bundle salvati in passato
    # ------------------------------------------------------------
    def _costruisci_storico(self):
        # rileggo sempre dal database quando si apre la sezione, cosi'
        # se nel frattempo hai salvato un nuovo bundle lo vedi subito
        bundle_salvati = self._controller.get_bundle_salvati()

        if len(bundle_salvati) == 0:
            return self._stato_vuoto_risultati(
                "Non hai ancora salvato nessun bundle. Generane uno dal Configuratore e salvalo dai Risultati."
            )

        intestazione = ft.Text(f"{len(bundle_salvati)} bundle salvati", size=20, weight=ft.FontWeight.BOLD)

        controlli = [intestazione, ft.Container(height=15)]
        for bundle in bundle_salvati:
            controlli.append(self._card_bundle_salvato(bundle))

        return ft.Column(controls=controlli, scroll=ft.ScrollMode.AUTO)

    def _card_bundle_salvato(self, bundle):
        righe_prodotti = ft.Column(
            controls=[
                ft.Text(f"• {p.categoria_outfit}: {p.nome} ({p.colore}) - {p.prezzo_vendita} $", size=13)
                for p in bundle["prodotti"]
            ],
            spacing=3,
        )

        # la data arriva dal database come oggetto datetime, la formatto
        # in un modo piu' leggibile (gg/mm/aaaa ore:minuti)
        data_testo = bundle["data_creazione"].strftime("%d/%m/%Y %H:%M") if bundle["data_creazione"] else ""

        intestazione = ft.Row(
            controls=[
                ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=18),
                ft.Text(
                    f"Salvato il {data_testo} - preset \"{bundle['nome_preset']}\"",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                ),
            ],
            spacing=8,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    intestazione,
                    righe_prodotti,
                    ft.Container(height=8),
                    self._riga_metriche_extra(bundle),
                    ft.Container(height=8),
                    ft.Text(
                        f"Prezzo totale: {bundle['prezzo_totale']} $     "
                        f"Margine totale: {bundle['margine_totale']} $     "
                        f"Punteggio: {bundle['punteggio_z']}",
                        size=13,
                    ),
                ],
            ),
            bgcolor=ft.colors.WHITE,
            border_radius=12,
            padding=20,
            margin=ft.margin.only(bottom=15),
            shadow=ft.BoxShadow(
                blur_radius=8,
                color=ft.colors.with_opacity(0.06, ft.colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )