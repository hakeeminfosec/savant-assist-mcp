import chromadb
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Connect to ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")

try:
    # Get the collection
    collection = chroma_client.get_collection("knowledge_base")
    
    print("ChromaDB Knowledge Base Contents")
    print("=" * 50)
    
    # Get all documents
    results = collection.get()
    
    print(f"Total documents: {len(results['ids'])}")
    print()
    
    # Display each document
    for i, (doc_id, document, metadata) in enumerate(zip(results['ids'], results['documents'], results.get('metadatas', [None] * len(results['ids'])))):
        print(f"Document {i+1}")
        print(f"   ID: {doc_id}")
        print(f"   Content: {document}")
        if metadata:
            print(f"   Metadata: {json.dumps(metadata, indent=2)}")
        print("-" * 40)
    
    # Get collection info
    print(f"Collection Statistics:")
    print(f"   Name: {collection.name}")
    print(f"   Count: {collection.count()}")
    
    # Test a query to see similarity search in action
    print(f"\nTesting similarity search for 'inventory management':")
    query_results = collection.query(
        query_texts=["inventory management"],
        n_results=3
    )
    
    print(f"Top 3 similar documents:")
    for i, (doc_id, document, distance) in enumerate(zip(
        query_results['ids'][0], 
        query_results['documents'][0],
        query_results['distances'][0]
    )):
        print(f"  {i+1}. ID: {doc_id}")
        print(f"     Similarity: {1 - distance:.4f}")
        print(f"     Text: {document[:100]}...")
        print()

except Exception as e:
    print(f"Error accessing ChromaDB: {e}")
    print("Make sure the backend has been started at least once to create the database.")