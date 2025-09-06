from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import chromadb
import json
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="ChromaDB Viewer")

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Connect to ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChromaDB Viewer</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .header {
                background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: #f8fafc;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                text-align: center;
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #6366f1;
            }
            .documents {
                margin-top: 20px;
            }
            .document {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            }
            .doc-id {
                font-weight: bold;
                color: #6366f1;
                margin-bottom: 10px;
            }
            .doc-content {
                line-height: 1.6;
                color: #334155;
            }
            .search-section {
                background: #f1f5f9;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .search-input {
                width: 70%;
                padding: 10px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 16px;
            }
            .search-btn {
                padding: 10px 20px;
                background: #6366f1;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                margin-left: 10px;
                font-size: 16px;
            }
            .search-btn:hover {
                background: #5855eb;
            }
            .search-results {
                margin-top: 20px;
            }
            .similarity-score {
                background: #10b981;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.8em;
                display: inline-block;
                margin-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🗃️ ChromaDB Knowledge Base Viewer</h1>
                <p>Explore your vector database and perform semantic search</p>
            </div>
            
            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="stat-number" id="doc-count">Loading...</div>
                    <div>Documents</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="collection-count">Loading...</div>
                    <div>Collections</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">1536</div>
                    <div>Vector Dimensions</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">OpenAI</div>
                    <div>Embedding Model</div>
                </div>
            </div>

            <div class="search-section">
                <h3>🔍 Semantic Search</h3>
                <input type="text" id="searchQuery" class="search-input" placeholder="Enter your search query..." value="inventory management">
                <button class="search-btn" onclick="performSearch()">Search</button>
                <div class="search-results" id="searchResults"></div>
            </div>

            <div class="documents">
                <h3>📄 All Documents</h3>
                <div id="documentList">Loading documents...</div>
            </div>
        </div>

        <script>
            let allDocuments = [];

            async function loadStats() {
                try {
                    const response = await fetch('/api/stats');
                    const stats = await response.json();
                    document.getElementById('doc-count').textContent = stats.document_count;
                    document.getElementById('collection-count').textContent = stats.collection_count;
                } catch (error) {
                    console.error('Error loading stats:', error);
                }
            }

            async function loadDocuments() {
                try {
                    const response = await fetch('/api/documents');
                    const documents = await response.json();
                    allDocuments = documents;
                    displayDocuments(documents);
                } catch (error) {
                    console.error('Error loading documents:', error);
                    document.getElementById('documentList').innerHTML = '<p>Error loading documents</p>';
                }
            }

            function displayDocuments(documents) {
                const container = document.getElementById('documentList');
                container.innerHTML = documents.map(doc => `
                    <div class="document">
                        <div class="doc-id">Document ID: ${doc.id}</div>
                        <div class="doc-content">${doc.content}</div>
                    </div>
                `).join('');
            }

            async function performSearch() {
                const query = document.getElementById('searchQuery').value;
                if (!query.trim()) return;

                try {
                    const response = await fetch('/api/search', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: query })
                    });
                    const results = await response.json();
                    
                    const container = document.getElementById('searchResults');
                    container.innerHTML = `
                        <h4>Search Results for: "${query}"</h4>
                        ${results.map((result, index) => `
                            <div class="document">
                                <div class="similarity-score">Similarity: ${(result.similarity * 100).toFixed(1)}%</div>
                                <div class="doc-id">Document ID: ${result.id}</div>
                                <div class="doc-content">${result.content}</div>
                            </div>
                        `).join('')}
                    `;
                } catch (error) {
                    console.error('Error searching:', error);
                    document.getElementById('searchResults').innerHTML = '<p>Error performing search</p>';
                }
            }

            // Load data on page load
            loadStats();
            loadDocuments();

            // Allow Enter key to search
            document.getElementById('searchQuery').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
        </script>
    </body>
    </html>
    """

@app.get("/api/stats")
async def get_stats():
    try:
        collections = chroma_client.list_collections()
        if collections:
            collection = chroma_client.get_collection("knowledge_base")
            doc_count = collection.count()
        else:
            doc_count = 0
        
        return {
            "collection_count": len(collections),
            "document_count": doc_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def get_documents():
    try:
        collection = chroma_client.get_collection("knowledge_base")
        results = collection.get()
        
        documents = []
        for i, (doc_id, content) in enumerate(zip(results['ids'], results['documents'])):
            documents.append({
                "id": doc_id,
                "content": content
            })
        
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_documents(request: dict):
    try:
        query = request.get("query", "")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        collection = chroma_client.get_collection("knowledge_base")
        
        # Get query embedding using OpenAI
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=query
        )
        query_embedding = embedding_response.data[0].embedding
        
        # Perform similarity search using embeddings
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )
        
        search_results = []
        if results['documents'] and results['documents'][0]:
            for doc_id, content, distance in zip(
                results['ids'][0], 
                results['documents'][0], 
                results['distances'][0]
            ):
                search_results.append({
                    "id": doc_id,
                    "content": content,
                    "similarity": max(0, 1 - distance)  # Convert distance to similarity, ensure non-negative
                })
        
        return search_results
    except Exception as e:
        print(f"Search error: {e}")  # Debug logging
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)