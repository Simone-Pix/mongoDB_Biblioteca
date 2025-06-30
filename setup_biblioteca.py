#!/usr/bin/env python3
"""
Sistema Gestione Biblioteca - MongoDB Setup Script
Esegue il setup completo del database biblioteca
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from bson import ObjectId
from datetime import datetime, timedelta
import json
import sys
import os
from typing import List, Dict, Any

class BibliotecaSetup:
    def __init__(self, connection_string: str = "mongodb://localhost:27017/"):
        """Inizializza la connessione MongoDB"""
        try:
            self.client = MongoClient(connection_string)
            # Test connessione
            self.client.admin.command('ping')
            self.db = self.client.biblioteca
            print("✅ Connessione MongoDB stabilita")
        except ConnectionFailure:
            print("❌ Errore: Impossibile connettersi a MongoDB")
            sys.exit(1)

    def drop_database(self):
        """Elimina il database esistente (per reset completo)"""
        try:
            self.client.drop_database('biblioteca')
            print("🗑️  Database esistente eliminato")
        except Exception as e:
            print(f"⚠️  Errore durante eliminazione database: {e}")

    def create_collections(self):
        """Crea le collezioni con validation schema"""
        print("\n📚 Creazione collezioni...")
        
        # Schema validazione Autori
        autori_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["nome", "cognome", "data_nascita"],
                "properties": {
                    "nome": {"bsonType": "string", "minLength": 1},
                    "cognome": {"bsonType": "string", "minLength": 1},
                    "data_nascita": {"bsonType": "date"},
                    "data_morte": {"bsonType": ["date", "null"]},
                    "nazionalita": {"bsonType": "string"},
                    "biografia": {"bsonType": "string"}
                }
            }
        }
        
        # Schema validazione Libri
        libri_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["titolo", "autore_id", "isbn", "anno_pubblicazione", "copie_disponibili"],
                "properties": {
                    "titolo": {"bsonType": "string", "minLength": 1},
                    "autore_id": {"bsonType": "objectId"},
                    "isbn": {"bsonType": "string", "pattern": "^[0-9-]{10,17}$"},
                    "anno_pubblicazione": {"bsonType": "int", "minimum": 1000, "maximum": 2030},
                    "genere": {"bsonType": "string"},
                    "editore": {"bsonType": "string"},
                    "pagine": {"bsonType": "int", "minimum": 1},
                    "copie_totali": {"bsonType": "int", "minimum": 1},
                    "copie_disponibili": {"bsonType": "int", "minimum": 0},
                    "descrizione": {"bsonType": "string"}
                }
            }
        }
        
        # Schema validazione Utenti
        utenti_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["nome", "cognome", "email", "codice_fiscale", "data_registrazione"],
                "properties": {
                    "nome": {"bsonType": "string", "minLength": 1},
                    "cognome": {"bsonType": "string", "minLength": 1},
                    "email": {"bsonType": "string", "pattern": "^[\\w\\.-]+@[\\w\\.-]+\\.[a-zA-Z]{2,}$"},
                    "codice_fiscale": {"bsonType": "string", "minLength": 16, "maxLength": 16},
                    "telefono": {"bsonType": "string"},
                    "data_registrazione": {"bsonType": "date"},
                    "attivo": {"bsonType": "bool"}
                }
            }
        }
        
        # Schema validazione Prestiti
        prestiti_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["libro_id", "utente_id", "data_prestito", "data_scadenza", "utente_nome", "utente_email"],
                "properties": {
                    "libro_id": {"bsonType": "objectId"},
                    "utente_id": {"bsonType": "objectId"},
                    "data_prestito": {"bsonType": "date"},
                    "data_scadenza": {"bsonType": "date"},
                    "data_restituzione": {"bsonType": ["date", "null"]},
                    "utente_nome": {"bsonType": "string"},
                    "utente_email": {"bsonType": "string"},
                    "note": {"bsonType": "string"},
                    "stato": {"enum": ["attivo", "restituito", "scaduto"]}
                }
            }
        }
        
        # Crea collezioni con validazione
        collections = [
            ("autori", autori_validator),
            ("libri", libri_validator),
            ("utenti", utenti_validator),
            ("prestiti", prestiti_validator)
        ]
        
        for collection_name, validator in collections:
            try:
                self.db.create_collection(
                    collection_name,
                    validator=validator
                )
                print(f"  ✅ Collezione '{collection_name}' creata")
            except Exception as e:
                print(f"  ⚠️  Collezione '{collection_name}' già esistente o errore: {e}")

    def create_indexes(self):
        """Crea indici per ottimizzare le performance"""
        print("\n🔍 Creazione indici...")
        
        try:
            # Indici Autori
            self.db.autori.create_index([("nome", ASCENDING), ("cognome", ASCENDING)])
            self.db.autori.create_index([("cognome", ASCENDING)])
            print("  ✅ Indici autori creati")
            
            # Indici Libri
            self.db.libri.create_index([("autore_id", ASCENDING)])
            self.db.libri.create_index([("isbn", ASCENDING)], unique=True)
            self.db.libri.create_index([("titolo", ASCENDING)])
            self.db.libri.create_index([("genere", ASCENDING)])
            print("  ✅ Indici libri creati")
            
            # Indici Utenti
            self.db.utenti.create_index([("email", ASCENDING)], unique=True)
            self.db.utenti.create_index([("codice_fiscale", ASCENDING)], unique=True)
            self.db.utenti.create_index([("cognome", ASCENDING)])
            print("  ✅ Indici utenti creati")
            
            # Indici Prestiti
            self.db.prestiti.create_index([("utente_id", ASCENDING)])
            self.db.prestiti.create_index([("libro_id", ASCENDING)])
            self.db.prestiti.create_index([("data_prestito", DESCENDING)])
            self.db.prestiti.create_index([("data_scadenza", ASCENDING)])
            self.db.prestiti.create_index([("stato", ASCENDING)])
            print("  ✅ Indici prestiti creati")
            
        except Exception as e:
            print(f"  ⚠️  Errore creazione indici: {e}")

    def load_sample_data(self):
        """Carica dati di esempio"""
        print("\n📝 Caricamento dati di esempio...")
        
        # Dati Autori
        autori_data = [
            {
                "nome": "Alessandro",
                "cognome": "Manzoni",
                "data_nascita": datetime(1785, 3, 7),
                "data_morte": datetime(1873, 5, 22),
                "nazionalita": "Italiana",
                "biografia": "Scrittore e poeta italiano del romanticismo"
            },
            {
                "nome": "Italo",
                "cognome": "Calvino",
                "data_nascita": datetime(1923, 10, 15),
                "data_morte": datetime(1985, 9, 19),
                "nazionalita": "Italiana",
                "biografia": "Scrittore e giornalista italiano"
            },
            {
                "nome": "Umberto",
                "cognome": "Eco",
                "data_nascita": datetime(1932, 1, 5),
                "data_morte": datetime(2016, 2, 19),
                "nazionalita": "Italiana",
                "biografia": "Scrittore, filosofo e semiologo italiano"
            }
        ]
        
        try:
            result = self.db.autori.insert_many(autori_data)
            autori_ids = result.inserted_ids
            print(f"  ✅ {len(autori_ids)} autori inseriti")
        except Exception as e:
            print(f"   Errore inserimento autori: {e}")
            return
        
        # Dati Libri
        libri_data = [
            {
                "titolo": "I Promessi Sposi",
                "autore_id": autori_ids[0],
                "isbn": "978-88-17-12345-1",
                "anno_pubblicazione": 1827,
                "genere": "Romanzo storico",
                "editore": "Feltrinelli",
                "pagine": 720,
                "copie_totali": 5,
                "copie_disponibili": 3,
                "descrizione": "Capolavoro della letteratura italiana"
            },
            {
                "titolo": "Il Barone Rampante",
                "autore_id": autori_ids[1],
                "isbn": "978-88-06-12345-2",
                "anno_pubblicazione": 1957,
                "genere": "Narrativa",
                "editore": "Einaudi",
                "pagine": 280,
                "copie_totali": 3,
                "copie_disponibili": 2,
                "descrizione": "Secondo romanzo della trilogia I nostri antenati"
            },
            {
                "titolo": "Il Nome della Rosa",
                "autore_id": autori_ids[2],
                "isbn": "978-88-45-12345-3",
                "anno_pubblicazione": 1980,
                "genere": "Giallo storico",
                "editore": "Bompiani",
                "pagine": 550,
                "copie_totali": 4,
                "copie_disponibili": 1,
                "descrizione": "Romanzo giallo ambientato in un monastero medievale"
            }
        ]
        
        try:
            result = self.db.libri.insert_many(libri_data)
            libri_ids = result.inserted_ids
            print(f"   {len(libri_ids)} libri inseriti")
        except Exception as e:
            print(f"   Errore inserimento libri: {e}")
            return
        
        # Dati Utenti
        utenti_data = [
            {
                "nome": "Mario",
                "cognome": "Rossi",
                "email": "mario.rossi@email.com",
                "codice_fiscale": "RSSMRA80A01H501Z",
                "telefono": "+39 320 1234567",
                "data_registrazione": datetime(2023, 1, 15),
                "attivo": True
            },
            {
                "nome": "Giulia",
                "cognome": "Bianchi",
                "email": "giulia.bianchi@email.com",
                "codice_fiscale": "BNCGLI85B42F205X",
                "telefono": "+39 345 7890123",
                "data_registrazione": datetime(2023, 3, 22),
                "attivo": True
            },
            {
                "nome": "Luca",
                "cognome": "Verdi",
                "email": "luca.verdi@email.com",
                "codice_fiscale": "VRDLCU90C15G224Y",
                "telefono": "+39 366 4567890",
                "data_registrazione": datetime(2023, 5, 10),
                "attivo": True
            }
        ]
        
        try:
            result = self.db.utenti.insert_many(utenti_data)
            utenti_ids = result.inserted_ids
            print(f"   {len(utenti_ids)} utenti inseriti")
        except Exception as e:
            print(f"   Errore inserimento utenti: {e}")
            return
        
        # Dati Prestiti
        base_date = datetime.now() - timedelta(days=30)
        prestiti_data = [
            {
                "libro_id": libri_ids[0],
                "utente_id": utenti_ids[0],
                "data_prestito": base_date,
                "data_scadenza": base_date + timedelta(days=30),
                "data_restituzione": base_date + timedelta(days=25),
                "utente_nome": "Mario Rossi",
                "utente_email": "mario.rossi@email.com",
                "stato": "restituito",
                "note": "Restituito in perfette condizioni"
            },
            {
                "libro_id": libri_ids[2],
                "utente_id": utenti_ids[1],
                "data_prestito": datetime.now() - timedelta(days=10),
                "data_scadenza": datetime.now() + timedelta(days=20),
                "data_restituzione": None,
                "utente_nome": "Giulia Bianchi",
                "utente_email": "giulia.bianchi@email.com",
                "stato": "attivo",
                "note": "Prestito in corso"
            }
        ]
        
        try:
            result = self.db.prestiti.insert_many(prestiti_data)
            print(f"   {len(result.inserted_ids)} prestiti inseriti")
        except Exception as e:
            print(f"   Errore inserimento prestiti: {e}")

    def validate_setup(self):
        """Valida il setup controllando i dati inseriti"""
        print("\n Validazione setup...")
        
        # Conta documenti per collezione
        counts = {
            "autori": self.db.autori.count_documents({}),
            "libri": self.db.libri.count_documents({}),
            "utenti": self.db.utenti.count_documents({}),
            "prestiti": self.db.prestiti.count_documents({})
        }
        
        print(" Documenti per collezione:")
        for collection, count in counts.items():
            print(f"  • {collection}: {count}")
        
        # Test query di esempio
        print("\n Test query:")
        
        # Query con join per libri e autori
        pipeline = [
            {
                "$lookup": {
                    "from": "autori",
                    "localField": "autore_id",
                    "foreignField": "_id",
                    "as": "autore"
                }
            },
            {"$unwind": "$autore"},
            {
                "$project": {
                    "titolo": 1,
                    "autore_nome": {"$concat": ["$autore.nome", " ", "$autore.cognome"]},
                    "copie_disponibili": 1
                }
            }
        ]
        
        try:
            libri_con_autori = list(self.db.libri.aggregate(pipeline))
            print(f"   Query libri con autori: {len(libri_con_autori)} risultati")
            
            # Mostra primo risultato
            if libri_con_autori:
                primo = libri_con_autori[0]
                print(f"    Esempio: '{primo['titolo']}' di {primo['autore_nome']}")
                
        except Exception as e:
            print(f"   Errore test query: {e}")

    def export_sample_json(self):
        """Esporta esempi in formato JSON"""
        print("\nEsportazione esempi JSON...")
        
        # Crea directory data se non esiste
        os.makedirs("data", exist_ok=True)
        
        collections = ["autori", "libri", "utenti", "prestiti"]
        
        for collection_name in collections:
            try:
                # Recupera documenti
                documents = list(self.db[collection_name].find())
                
                # Converte ObjectId in stringhe per JSON
                for doc in documents:
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])
                    # Converte altri ObjectId
                    for key, value in doc.items():
                        if isinstance(value, ObjectId):
                            doc[key] = str(value)
                        elif isinstance(value, datetime):
                            doc[key] = value.isoformat()
                
                # Salva in file JSON
                filename = f"data/{collection_name}_sample.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(documents, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"  ✅ {filename} creato ({len(documents)} documenti)")
                
            except Exception as e:
                print(f"  ❌ Errore esportazione {collection_name}: {e}")

    def run_complete_setup(self, reset: bool = False):
        """Esegue il setup completo"""
        print("🚀 Avvio setup Sistema Biblioteca MongoDB")
        print("=" * 50)
        
        if reset:
            self.drop_database()
        
        self.create_collections()
        self.create_indexes()
        self.load_sample_data()
        self.validate_setup()
        self.export_sample_json()
        
        print("\n" + "=" * 50)
        print("🎉 Setup completato con successo!")
        print("💡 Database 'biblioteca' pronto per l'uso")
        print("📁 File JSON di esempio salvati in /data/")

def main():
    """Funzione principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Database Biblioteca MongoDB")
    parser.add_argument("--reset", action="store_true", help="Elimina database esistente prima del setup")
    parser.add_argument("--connection", default="mongodb://localhost:27017/", help="Connection string MongoDB")
    
    args = parser.parse_args()
    
    try:
        setup = BibliotecaSetup(args.connection)
        setup.run_complete_setup(reset=args.reset)
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrotto dall'utente")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Errore durante setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()