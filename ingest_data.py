"""
Data Ingestion Script
Creates the ChromaDB vector database from the car CSV data.
Run this script to generate the vector database before running the app.
"""

import os
from data_processor import DataProcessor
from chatbot_engine import LocalEmbeddings
import chromadb

def ingest_data():
    """Ingest car data into ChromaDB"""
    print("🚗 Starting data ingestion...")
    
    # Initialize data processor
    processor = DataProcessor(data_path="Cars Datasets 2025.csv")
    
    # Load and process data
    print("📊 Loading car data...")
    processor.load_data()
    documents, metadatas = processor.process_data()
    
    # Initialize embeddings
    print("🔤 Loading embedding model...")
    embeddings = LocalEmbeddings(model_name='all-MiniLM-L6-v2')
    
    # Create ChromaDB
    print("💾 Creating vector database...")
    db_path = "data/chroma_db"
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=db_path)
    
    # Try to get existing collection or create new one
    try:
        collection = client.get_collection(name="cars")
        print("📝 Found existing collection, will add to it")
        # Clear existing data
        collection.delete(where={})
        print("🗑️ Cleared existing data from collection")
    except Exception as e:
        print(f"📝 No existing collection found or error: {e}")
        print("📝 Creating new collection")
        collection = client.create_collection(
            name="cars",
            metadata={"description": "Car specifications database"}
        )
    
    # Generate embeddings for all documents
    print("🔢 Generating embeddings...")
    embedding_vectors = embeddings.embed_documents(documents)
    
    # Add documents to collection
    print("📝 Adding documents to collection...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=[f"car_{i}" for i in range(len(documents))],
        embeddings=embedding_vectors
    )
    
    print(f"✅ Successfully ingested {len(documents)} cars into vector database")
    print(f"📂 Database saved to: {db_path}")
    
    # Verify
    count = collection.count()
    print(f"📊 Total cars in database: {count}")

if __name__ == "__main__":
    ingest_data()
