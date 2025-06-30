# Sistema Gestione Biblioteca - MongoDB

## Descrizione del Progetto
Sistema di gestione biblioteca implementato con MongoDB, progettato per gestire autori, libri, utenti e prestiti con relazioni ottimizzate.

## Struttura del Database

### Collezioni Principali
- **autori**: Informazioni degli autori
- **libri**: Catalogo dei libri con riferimenti agli autori
- **utenti**: Anagrafica degli utenti della biblioteca
- **prestiti**: Gestione dei prestiti attivi e storico

### Scelte Architetturali

#### 1. **Autori → Libri**: REFERENCE
- **Perché**: Gli autori sono entità indipendenti che possono scrivere più libri
- **Vantaggi**: Evita duplicazione dati, facilita aggiornamenti dell'autore
- **Implementazione**: Campo `autore_id` in `libri` che referenzia `_id` di `autori`

#### 2. **Libri → Prestiti**: REFERENCE  
- **Perché**: I libri sono entità master indipendenti
- **Vantaggi**: Prestiti multipli dello stesso libro, storico completo
- **Implementazione**: Campo `libro_id` in `prestiti`

#### 3. **Utenti → Prestiti**: REFERENCE
- **Perché**: Utenti indipendenti con più prestiti nel tempo
- **Vantaggi**: Storico completo per utente, privacy e gestione separata
- **Implementazione**: Campo `utente_id` in `prestiti`

#### 4. **Dati Utente nei Prestiti**: EMBEDDING (parziale)
- **Perché**: Snapshot dei dati al momento del prestito
- **Vantaggi**: Storico immutabile, performance nelle query sui prestiti
- **Implementazione**: Campi `utente_nome`, `utente_email` embedded in `prestiti`

## Setup dell'Ambiente

### Prerequisiti
- Python 3.8+
- MongoDB 4.4+
- pip (per installare dipendenze)

### Installazione

1. **Clona il repository**
```bash
git clone https://github.com/tuousername/biblioteca-mongodb.git
cd biblioteca-mongodb
```

2. **Installa le dipendenze**
```bash
pip install -r requirements.txt
```

3. **Configura MongoDB**
   - Assicurati che MongoDB sia in esecuzione
   - Modifica la connection string in `config.py` se necessario

4. **Esegui il setup**
```bash
python setup_biblioteca.py
```

## Utilizzo Rapido

### Setup Completo del Database
```bash
python setup_biblioteca.py
```

### Operazioni Disponibili
Il script principale offre le seguenti operazioni:
- Creazione database e collezioni
- Caricamento dati di esempio
- Creazione indici per performance
- Validazione dati inseriti

## Struttura File

```
biblioteca-mongodb/
├── README.md
├── Documentation.md
├── setup_biblioteca.py
├── struttura.json
```

## Performance e Indici

### Indici Creati Automaticamente
- `autori`: Indice composto su `(nome, cognome)`
- `libri`: Indici su `autore_id`, `isbn`, `titolo`
- `utenti`: Indici su `email` (unique), `codice_fiscale` (unique)
- `prestiti`: Indici su `utente_id`, `libro_id`, `data_prestito`

## Contribuire

1. Fork del repository
2. Crea un branch per la tua feature
3. Commit delle modifiche
4. Push al branch
5. Apri una Pull Request

## Licenza

MIT License - vedi file LICENSE per dettagli