from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
import requests
import uvicorn
from typing import Optional
import os

app = FastAPI(title="ChromaDB Document Viewer", version="2.0.0")

# Backend API URL - use container network
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8002")

def get_documents_from_backend():
    """Get all documents from backend API"""
    try:
        response = requests.get(f"{BACKEND_URL}/documents", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('documents', []), data.get('total', 0)
        else:
            print(f"Backend API error: {response.status_code} - {response.text}")
            return [], 0
    except Exception as e:
        print(f"Error connecting to backend: {e}")
        return [], 0

def semantic_search_backend(query: str, limit: int = 10):
    """Perform semantic search using backend API"""
    try:
        response = requests.post(f"{BACKEND_URL}/search", 
                                json={"query": query, "n_results": limit}, 
                                timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Convert backend format to viewer format
            results = []
            for i, result in enumerate(data.get('results', [])):
                results.append({
                    "id": result.get('chunk_id', f'search_{i}'),
                    "content": result.get('content', ''),
                    "preview": result.get('preview', ''),
                    "similarity_score": int(min(result.get('relevance_score', 0) * 50, 95)) if result.get('similarity', 0) == 0 else int(result.get('similarity', 0) * 100),
                    "word_count": result.get('word_count', 0),
                    "title": result.get('title', f'Search Result {i+1}'),
                    "category": result.get('category', 'Search Result'),
                    "has_metadata": bool(result.get('metadata', {}))
                })
            return results, data.get('total_found', 0)
        else:
            print(f"Search API error: {response.status_code} - {response.text}")
            return [], 0
    except Exception as e:
        print(f"Error in semantic search: {e}")
        return [], 0

# Semantic search is now handled by the backend using OpenAI embeddings

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "chromadb-viewer"}

@app.get("/", response_class=HTMLResponse)
async def home():
    """Clean and focused ChromaDB viewer homepage"""
    # Get essential stats only
    documents, total_count = get_documents_from_backend()
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ChromaDB Viewer</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                background: #f8fafc;
                min-height: 100vh;
                color: #1e293b;
            }}
            
            .container {{
                max-width: 900px;
                margin: 0 auto;
                padding: 2rem 1rem;
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 3rem;
                padding: 2rem 0;
            }}
            
            .title {{
                font-size: 2.5rem;
                font-weight: 800;
                color: #1e40af;
                margin-bottom: 0.5rem;
            }}
            
            .subtitle {{
                font-size: 1.1rem;
                color: #64748b;
                max-width: 500px;
                margin: 0 auto;
                line-height: 1.6;
            }}
            
            .search-section {{
                background: white;
                border-radius: 16px;
                padding: 2rem;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                margin-bottom: 3rem;
                border: 1px solid #e2e8f0;
            }}
            
            .search-form {{
                display: flex;
                gap: 1rem;
                margin-bottom: 1rem;
            }}
            
            .search-input {{
                flex: 1;
                padding: 0.875rem 1rem;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                font-size: 1rem;
                transition: all 0.2s;
            }}
            
            .search-input:focus {{
                outline: none;
                border-color: #1e40af;
                box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1);
            }}
            
            .search-btn {{
                background: #1e40af;
                color: white;
                border: none;
                padding: 0.875rem 1.5rem;
                border-radius: 8px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
            }}
            
            .search-btn:hover {{
                background: #1d4ed8;
                transform: translateY(-1px);
            }}
            
            .search-hint {{
                color: #64748b;
                font-size: 0.875rem;
                text-align: center;
            }}
            
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 1rem;
                margin-bottom: 2rem;
            }}
            
            .stat {{
                background: white;
                border-radius: 12px;
                padding: 1.5rem 1rem;
                text-align: center;
                border: 1px solid #e2e8f0;
                transition: all 0.2s;
            }}
            
            .stat:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            
            .stat-number {{
                font-size: 1.75rem;
                font-weight: 700;
                color: #1e40af;
                display: block;
                margin-bottom: 0.25rem;
            }}
            
            .stat-label {{
                font-size: 0.75rem;
                color: #64748b;
                text-transform: uppercase;
                font-weight: 500;
                letter-spacing: 0.05em;
            }}
            
            .actions {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
            }}
            
            .action-btn {{
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 1.5rem;
                text-decoration: none;
                color: inherit;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 1rem;
            }}
            
            .action-btn:hover {{
                border-color: #1e40af;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            
            .action-icon {{
                font-size: 1.5rem;
                flex-shrink: 0;
            }}
            
            .action-text {{
                flex: 1;
            }}
            
            .action-title {{
                font-weight: 600;
                margin-bottom: 0.25rem;
                color: #1e293b;
            }}
            
            .action-desc {{
                font-size: 0.875rem;
                color: #64748b;
            }}
            
            @media (max-width: 640px) {{
                .search-form {{
                    flex-direction: column;
                }}
                .stats {{
                    grid-template-columns: repeat(2, 1fr);
                }}
                .actions {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="title">ChromaDB Viewer</h1>
                <p class="subtitle">AI-powered document search and exploration with semantic understanding</p>
            </div>
            
            <div class="search-section">
                <form class="search-form" action="/documents" method="get">
                    <input type="text" name="search" class="search-input" 
                           placeholder="Search documents with AI semantic understanding..." 
                           autofocus>
                    <button type="submit" class="search-btn">🔍 Search</button>
                </form>
                <p class="search-hint">Ask questions or describe what you're looking for - powered by OpenAI embeddings</p>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <span class="stat-number">{total_count}</span>
                    <div class="stat-label">Documents</div>
                </div>
                <div class="stat">
                    <span class="stat-number">{sum(doc.get('word_count', 0) for doc in documents):,}</span>
                    <div class="stat-label">Words</div>
                </div>
                <div class="stat">
                    <span class="stat-number">1536</span>
                    <div class="stat-label">Dimensions</div>
                </div>
                <div class="stat">
                    <span class="stat-number">AI</span>
                    <div class="stat-label">Powered</div>
                </div>
            </div>
            
            <div class="actions">
                <a href="/documents" class="action-btn">
                    <div class="action-icon">📄</div>
                    <div class="action-text">
                        <div class="action-title">Browse All Documents</div>
                        <div class="action-desc">View and explore your document collection</div>
                    </div>
                </a>
                <a href="#" class="action-btn" onclick="const query = prompt('What are you looking for?'); if(query) {{ window.location.href = '/documents?search=' + encodeURIComponent(query); }} return false;">
                    <div class="action-icon">🧠</div>
                    <div class="action-text">
                        <div class="action-title">Semantic Search</div>
                        <div class="action-desc">Find documents by meaning, not just keywords</div>
                    </div>
                </a>
            </div>
        </div>
    </body>
    </html>
    """)