# Androide EPG

Questo repository contiene uno script che scarica automaticamente la guida TV (EPG) da Open-EPG e la converte in un formato JSON.

## Cosa fa

Lo script si collega a Open-EPG ogni 3 ore, scarica i dati aggiornati dei programmi televisivi e genera un file JSON con le informazioni su cosa sta andando in onda in questo momento su ogni canale.

Il file generato può essere utilizzato direttamente in Kodi tramite addon che supportano liste JSON esterne.

## Come funziona

Il sistema è completamente automatico grazie a GitHub Actions. Non c'è bisogno di fare nulla manualmente, tutto viene aggiornato da solo.

Ogni 3 ore il sistema:
1. Scarica l'EPG aggiornato da Open-EPG
2. Controlla se ci sono cambiamenti rispetto all'ultima versione
3. Se ci sono modifiche, genera un nuovo file JSON
4. Salva il file aggiornato nel repository 

## File generato

Il file JSON si trova in `json/androide_epg.json` e contiene:
- Nome del canale
- Programma attualmente in onda con orario di inizio e fine
- Descrizione del programma
- Programma successivo

Il file si aggiorna automaticamente in base ai dati ricevuti da Open-EPG.

## URL per Kodi

Per utilizzare questo EPG in Kodi, usa questo indirizzo:

```
https://raw.githubusercontent.com/aandroide/Epg/main/json/androide_epg.json
```

Inseriscilo nel campo per le liste JSON esterne del tuo addon.

## Configurazione

I canali configurati sono quelli impostati su Open-EPG. Se vuoi modificare quali canali vengono inclusi, devi cambiare la configurazione direttamente sul sito di Open-EPG.

L'URL dell'EPG è configurato in `scripts/fetch_openepg.py` alla riga che inizia con `OPENEPG_URL`.

## Aggiornamenti

Il sistema si aggiorna automaticamente. Non serve fare nulla. Puoi comunque forzare un aggiornamento manuale andando nella sezione Actions e cliccando su "Run workflow".

## Note tecniche

Lo script è scritto in Python e usa le librerie requests e lxml per scaricare e processare i dati XML dell'EPG.

Il fuso orario è impostato su Europa/Roma per avere gli orari corretti dei programmi.

Il file JSON viene rigenerato solo se ci sono effettivamente modifiche nei dati EPG, per evitare commit inutili.
