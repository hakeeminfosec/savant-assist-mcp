from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
import openai
import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize ChromaDB (persistent storage)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = None

# Sample knowledge base documents
kb_documents = [
    {"id": "1", "text": "Wave picking is a warehouse management method where multiple orders are grouped into batches and picked simultaneously by warehouse workers, improving efficiency and reducing travel time."},
    {"id": "2", "text": "FIFO (First-In-First-Out) is an inventory management method ensuring older stock is used before newer stock to prevent spoilage and maintain product quality."},
    {"id": "3", "text": "Cycle counting is a systematic inventory auditing process where small subsets of inventory are counted on a regular rotating schedule to maintain accurate stock levels."},
    {"id": "4", "text": "Cross-docking is a logistics practice where products are directly transferred from inbound to outbound transportation with minimal storage time, reducing handling costs."},
    {"id": "5", "text": "ABC analysis categorizes inventory into three groups: A (high-value, low-quantity), B (moderate value/quantity), and C (low-value, high-quantity) for optimized management."},
    {"id": "6", "text": "Just-in-time (JIT) inventory is a strategy to increase efficiency by receiving goods only when needed for production or sales, reducing inventory costs."},
    {"id": "7", "text": "Warehouse Management System (WMS) is software that manages and optimizes warehouse operations including receiving, storage, picking, packing, and shipping."},
    {"id": "8", "text": "Barcode scanning uses optical readers to capture product information, improving accuracy and speed in inventory tracking and order fulfillment."},
]

def initialize_knowledge_base():
    """Initialize ChromaDB collection with knowledge base documents"""
    global collection
    try:
        collection = chroma_client.get_collection("knowledge_base")
        print("Loaded existing knowledge base collection")
    except:
        collection = chroma_client.create_collection("knowledge_base")
        print("Created new knowledge base collection")
        
        # Add documents with OpenAI embeddings
        for doc in kb_documents:
            try:
                # Get embedding from OpenAI
                embedding_response = openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=doc["text"]
                )
                embedding = embedding_response.data[0].embedding
                
                # Add to ChromaDB
                collection.add(
                    ids=[doc["id"]],
                    documents=[doc["text"]],
                    embeddings=[embedding]
                )
            except Exception as e:
                print(f"Error adding document {doc['id']}: {e}")
        
        print(f"Added {len(kb_documents)} documents to knowledge base")

# Initialize knowledge base on startup
initialize_knowledge_base()

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

def search_knowledge_base(query: str, n_results: int = 3) -> List[str]:
    """Search knowledge base for relevant documents"""
    try:
        # Get query embedding
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=query
        )
        query_embedding = embedding_response.data[0].embedding
        
        # Search ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        return results["documents"][0] if results["documents"] else []
    except Exception as e:
        print(f"Error searching knowledge base: {e}")
        return []

def generate_response_with_openai(query: str, context_docs: List[str]) -> str:
    """Generate response using OpenAI with knowledge base context"""
    try:
        context = "\n\n".join([f"Document {i+1}: {doc}" for i, doc in enumerate(context_docs)])
        
        prompt = f"""You are a helpful assistant with access to a knowledge base about warehouse management and inventory systems. 

Based on the following context documents, please answer the user's question. If the answer isn't in the context, say so politely.

Context:
{context}

User Question: {query}

Please provide a clear, helpful response based on the context provided."""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating OpenAI response: {e}")
        return f"I found some relevant information but encountered an error generating the response. The relevant context was: {' '.join(context_docs[:2])}"

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    try:
        # Search knowledge base
        relevant_docs = search_knowledge_base(message.message)
        
        if relevant_docs:
            # Generate response with OpenAI using context
            response = generate_response_with_openai(message.message, relevant_docs)
        else:
            response = "I couldn't find relevant information in my knowledge base. Could you please rephrase your question or ask about warehouse management, inventory systems, or logistics topics?"
        
        return ChatResponse(response=response)
    
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return ChatResponse(response="I apologize, but I encountered an error processing your request. Please try again.")

@app.get("/")
async def root():
    return {"message": "Knowledge Base Chat API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "kb_docs": len(kb_documents)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)