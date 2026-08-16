-- Aggiorna i budget dei preset dopo aver reso obbligatorie tutte e 5 le
-- categorie in ogni bundle. Con 5 categorie obbligatorie il costo minimo
-- teorico e' 104$ (40 Capospalla + 16 Maglieria + 18 Pantaloni + 20 Scarpe
-- + 10 Accessori), quindi il vecchio budget di 60$ per "Outfit Economico"
-- non sarebbe mai stato raggiungibile.

UPDATE parametri_configurazione SET budget_max = 120 WHERE nome_preset = 'Outfit Economico';
UPDATE parametri_configurazione SET budget_max = 160 WHERE nome_preset = 'Outfit Bilanciato';
UPDATE parametri_configurazione SET budget_max = 250 WHERE nome_preset = 'Outfit Premium';
UPDATE parametri_configurazione SET budget_max = 150 WHERE nome_preset = 'Smaltimento Scorte';

-- verifica
SELECT * FROM parametri_configurazione;
