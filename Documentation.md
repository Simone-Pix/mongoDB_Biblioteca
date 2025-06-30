# Database Design - Sistema Biblioteca MongoDB

## Panoramica

Il database biblioteca è progettato per gestire un sistema completo di biblioteca con quattro collezioni principali interconnesse attraverso relazioni ottimizzate per performance e consistenza dei dati.

## Architettura delle Collezioni

### 1. Collezione `autori`

**Scopo**: Memorizza informazioni sugli autori dei libri

**Schema**:
```json
{
  "_id": ObjectId,
  "nome": String (required),
  "cognome": String (required),
  "data_nascita": Date (required),
  "data_morte": Date | null,
  "nazionalita": String,
  "biografia": String
}
```

**Caratteristiche**:
- Entità master indipendente
- Supporta autori viventi (data_morte = null)
- Indici su nome/cognome per ricerche rapide

### 2. Collezione `libri`

**Scopo**: Catalogo completo dei libri disponibili

**Schema**:
```json
{
  "_id": ObjectId,
  "titolo": String (required),
  "autore_id": ObjectId (required, ref: autori._id),
  "isbn": String (required, unique),
  "anno_pubblicazione": Integer (required),
  "genere": String,
  "editore": String,
  "pagine": Integer,
  "copie_totali": Integer (required),
  "copie_disponibili": Integer (required),
  "descrizione": String
}
```

**Caratteristiche**:
- Reference verso autori (relazione 1:N)
- ISBN unico per identificazione internazionale
- Gestione inventario con copie totali/disponibili
- Validazione anno pubblicazione (1000-2030)

### 3. Collezione `utenti`

**Scopo**: Anagrafica degli utenti della biblioteca

**Schema**:
```json
{
  "_id": ObjectId,
  "nome": String (required),
  "cognome": String (required),
  "email": String (required, unique),
  "codice_fiscale": String (required, unique, 16 chars),
  "telefono": String,
  "data_registrazione": Date (required),
  "attivo": Boolean
}
```

**Caratteristiche**:
- Email e codice fiscale univoci
- Flag attivo per gestione account sospesi
- Validazione email con pattern regex
- Indici per ricerche rapide

### 4. Collezione `prestiti`

**Scopo**: Gestione prestiti attivi e storico

**Schema**:
```json
{
  "_id": ObjectId,
  "libro_id": ObjectId (required, ref: libri._id),
  "utente_id": ObjectId (required, ref: utenti._id),
  "data_prestito": Date (required),
  "data_scadenza": Date (required),
  "data_restituzione": Date | null,
  "utente_nome": String (required, embedded),
  "utente_email": String (required, embedded),
  "stato": String (enum: ["attivo", "restituito", "scaduto"]),
  "note": String
}
```

**Caratteristiche**:
- Reference verso libri e utenti
- Dati utente embedded per snapshot storico
- Stato calcolato per query rapide
- Supporto prestiti multipli dello stesso libro

## Decisioni Architetturali

### 1. Reference vs Embedding

#### ✅ REFERENCE: Autori ↔ Libri
**Motivazione**: 
- Autori sono entità indipendenti riutilizzabili
- Un autore può scrivere molti libri
- Aggiornamenti autore si propagano automaticamente
- Evita duplicazione dati

**Implementazione**:
```javascript
// Query libri di un autore
db.libri.find({"autore_id": ObjectId("...")})

// Aggregation per join
db.libri.aggregate([
  {$lookup: {
    from: "autori",
    localField: "autore_id", 
    foreignField: "_id",
    as: "autore"
  }}
])
```

#### ✅ REFERENCE: Utenti ↔ Prestiti
**Motivazione**:
- Utenti esistono indipendentemente dai prestiti
- Storico completo per utente
- Privacy: separazione dati anagrafici
- Performance nelle query per utente

#### ✅ EMBEDDING PARZIALE: Dati Utente nei Prestiti
**Motivazione**:
- Snapshot immutabile al momento del prestito
- Performance: no join per report prestiti
- Storico: se utente cambia email, prestiti mantengono dati originali
- Compliance: tracciabilità completa

### 2. Indici e Performance

#### Strategia di Indicizzazione
- **Compound Index**: `(nome, cognome)` su autori per ricerche complete
- **Unique Index**: `isbn` su libri per integrità dati
- **Unique Index**: `email` e `codice_fiscale` su utenti per univocità
- **Reference Index**: `autore_id`, `libro_id`, `utente_id` per join veloci
- **Query Index**: `genere`, `stato`, `data_scadenza` per filtri comuni

#### Performance Considerations
```javascript
// Query ottimizzate con indici
db.libri.find({"genere": "Narrativa"})  // Usa indice genere
db.prestiti.find({"stato": "attivo"})   // Usa indice stato
db.utenti.find({"email": "user@email.com"}) // Usa indice unique
```

### 3. Validazione Dati

#### JSON Schema Validation
Ogni collezione ha validazione automatica per:
- **Campi obbligatori**: Prevenzione dati incompleti
- **Tipi di dato**: Consistenza tipizzazione
- **Pattern**: Email, ISBN, codice fiscale
- **Range**: Anno pubblicazione, pagine positive

#### Business Rules
```javascript
// Regole di business validate a livello applicazione
copie_disponibili <= copie_totali
data_scadenza > data_prestito
utente.attivo == true per nuovi prestiti
```

## Esempi di Query Comuni

### Query Base

#### 1. Ricerca Libri per Autore
```javascript
// Metodo 1: Reference lookup
const autore = db.autori.findOne({"nome": "Alessandro", "cognome": "Manzoni"});
const libri = db.libri.find({"autore_id": autore._id});

// Metodo 2: Aggregation pipeline
db.libri.aggregate([
  {$lookup: {
    from: "autori",
    localField: "autore_id",
    foreignField: "_id",
    as: "autore"
  }},
  {$match: {"autore.nome": "Alessandro", "autore.cognome": "Manzoni"}}
]);
```

#### 2. Prestiti Attivi per Utente
```javascript
db.prestiti.find({
  "utente_id": ObjectId("..."),
  "stato": "attivo"
});
```

#### 3. Libri Disponibili per Genere
```javascript
db.libri.find({
  "genere": "Narrativa",
  "copie_disponibili": {$gt: 0}
});
```

### Query Avanzate

#### 1. Report Prestiti in Scadenza
```javascript
const domani = new Date();
domani.setDate(domani.getDate() + 1);

db.prestiti.find({
  "stato": "attivo",
  "data_scadenza": {$lte: domani}
}).sort({"data_scadenza": 1});
```

#### 2. Statistiche per Autore
```javascript
db.prestiti.aggregate([
  {$lookup: {
    from: "libri",
    localField: "libro_id",
    foreignField: "_id",
    as: "libro"
  }},
  {$unwind: "$libro"},
  {$lookup: {
    from: "autori",
    localField: "libro.autore_id",
    foreignField: "_id",
    as: "autore"
  }},
  {$unwind: "$autore"},
  {$group: {
    _id: "$autore._id",
    nome_autore: {$first: {$concat: ["$autore.nome", " ", "$autore.cognome"]}},
    totale_prestiti: {$sum: 1},
    prestiti_attivi: {$sum: {$cond: [{$eq: ["$stato", "attivo"]}, 1, 0]}}
  }},
  {$sort: {"totale_prestiti": -1}}
]);
```

#### 3. Utenti Più Attivi
```javascript
db.prestiti.aggregate([
  {$group: {
    _id: "$utente_id",
    nome_utente: {$first: "$utente_nome"},
    email_utente: {$first: "$utente_email"},
    totale_prestiti: {$sum: 1},
    prestiti_attivi: {$sum: {$cond: [{$eq: ["$stato", "attivo"]}, 1, 0]}}
  }},
  {$sort: {"totale_prestiti": -1}},
  {$limit: 10}
]);
```

## Operazioni di Business Logic

### 1. Nuovo Prestito
```javascript
function nuovoPrestito(libro_id, utente_id) {
  // 1. Verifica disponibilità libro
  const libro = db.libri.findOne({_id: libro_id});
  if (libro.copie_disponibili <= 0) {
    throw new Error("Libro non disponibile");
  }
  
  // 2. Verifica utente attivo
  const utente = db.utenti.findOne({_id: utente_id});
  if (!utente.attivo) {
    throw new Error("Utente non attivo");
  }
  
  // 3. Crea prestito
  const dataScadenza = new Date();
  dataScadenza.setDate(dataScadenza.getDate() + 30);
  
  db.prestiti.insertOne({
    libro_id: libro_id,
    utente_id: utente_id,
    data_prestito: new Date(),
    data_scadenza: dataScadenza,
    data_restituzione: null,
    utente_nome: utente.nome + " " + utente.cognome,
    utente_email: utente.email,
    stato: "attivo"
  });
  
  // 4. Aggiorna disponibilità
  db.libri.updateOne(
    {_id: libro_id},
    {$inc: {copie_disponibili: -1}}
  );
}
```

### 2. Restituzione Libro
```javascript
function restituzioneLibro(prestito_id) {
  // 1. Aggiorna prestito
  const result = db.prestiti.updateOne(
    {_id: prestito_id, stato: "attivo"},
    {
      $set: {
        data_restituzione: new Date(),
        stato: "restituito"
      }
    }
  );
  
  if (result.matchedCount === 0) {
    throw new Error("Prestito non trovato o già restituito");
  }
  
  // 2. Recupera info libro
  const prestito = db.prestiti.findOne({_id: prestito_id});
  
  // 3. Aggiorna disponibilità
  db.libri.updateOne(
    {_id: prestito.libro_id},
    {$inc: {copie_disponibili: 1}}
  );
}
```

## Backup e Manutenzione

### Script di Backup
```bash
# Backup completo
mongodump --db biblioteca --out /backup/$(date +%Y%m%d)

# Backup collezione specifica
mongodump --db biblioteca --collection prestiti --out /backup/prestiti_$(date +%Y%m%d)
```

### Manutenzione Periodica
```javascript
// Aggiorna stato prestiti scaduti
db.prestiti.updateMany(
  {
    "stato": "attivo",
    "data_scadenza": {$lt: new Date()}
  },
  {
    $set: {"stato": "scaduto"}
  }
);

// Statistiche utilizzo indici
db.libri.getIndexes();
db.prestiti.explain("executionStats").find({"stato": "attivo"});
```

## Scalabilità e Ottimizzazioni Future

### Horizontal Scaling
- **Sharding Key**: `utente_id` per prestiti (distribuzione geografica)
- **Read Replicas**: Per query di sola lettura (catalogo, ricerche)

### Ottimizzazioni
- **Aggregation Pipeline**: Pre-calcolo statistiche frequenti
- **TTL Index**: Auto-eliminazione prestiti vecchi
- **Partial Index**: Solo su documenti attivi per performance

### Monitoring
- **Slow Query Log**: Identificazione query lente
- **Index Usage**: Monitoraggio utilizzo indici
- **Connection Pooling**: Gestione connessioni ottimale