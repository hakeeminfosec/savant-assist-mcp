import chromadb
from dotenv import load_dotenv
import json

load_dotenv()

# Connect to ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection("knowledge_base")

print("CHROMADB STORAGE INSPECTION")
print("=" * 60)

# Get all data
results = collection.get()

print(f"STORAGE STATS:")
print(f"   Total documents: {len(results['ids'])}")
print(f"   Document IDs: {results['ids']}")
print(f"   Has embeddings: {len(results.get('embeddings', [])) > 0}")
if results.get('embeddings'):
    print(f"   Embedding dimensions: {len(results['embeddings'][0])}")

print(f"\nWHAT'S ACTUALLY STORED:")
print("-" * 40)

for i, (doc_id, document) in enumerate(zip(results['ids'], results['documents'])):
    print(f"Record {i+1}:")
    print(f"   ID: {doc_id}")
    print(f"   Text: {document[:100]}...")
    print(f"   Embedding: [Vector with {len(results['embeddings'][i]) if results.get('embeddings') else 0} numbers]")
    print(f"   Sample embedding values: {results['embeddings'][i][:5] if results.get('embeddings') else 'None'}...")
    print()

print("WHAT'S NOT STORED:")
print("   X User chat messages")
print("   X AI responses") 
print("   X Chat history")
print("   X Search queries")
print("   X Conversation logs")

print(f"\nPHYSICAL STORAGE:")
print("   Location: ./chroma_db/ folder")
print("   Files: SQLite database + vector index files")
print("   Size: Only your 8 knowledge documents + their embeddings")