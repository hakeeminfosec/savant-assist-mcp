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

def calculate_similarity_score(document, search_term):
    """Calculate similarity score between document and search term"""
    if not search_term or not document:
        return 0
    
    doc_lower = str(document).lower()
    search_lower = search_term.lower()
    
    # Base score for exact phrase match
    score = 0
    if search_lower in doc_lower:
        score += 90
    
    # Check individual words
    search_words = search_lower.split()
    doc_words = doc_lower.split()
    
    matched_words = 0
    for word in search_words:
        if word in doc_words:
            matched_words += 1
    
    if search_words:
        word_match_score = (matched_words / len(search_words)) * 60
        score += word_match_score
    
    return min(score, 100)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "chromadb-viewer"}

@app.get("/", response_class=HTMLResponse)
async def home():
    """Improved home page with overview and navigation"""
    # Get quick stats
    documents, total_count = get_documents_from_backend()
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ChromaDB Document Viewer</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh; 
                color: #333;
            }}
            
            .header {{
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                padding: 1rem 2rem;
                box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            }}
            
            .header-content {{
                max-width: 1200px;
                margin: 0 auto;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .logo {{
                font-size: 1.5rem;
                font-weight: 600;
                color: #667eea;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .nav {{
                display: flex;
                gap: 1rem;
            }}
            
            .nav-btn {{
                background: #667eea;
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 6px;
                text-decoration: none;
                font-size: 0.9rem;
                transition: all 0.3s ease;
            }}
            
            .nav-btn:hover {{
                background: #5a6fd8;
                transform: translateY(-1px);
            }}
            
            .main-content {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 3rem 2rem;
            }}
            
            .hero-section {{
                text-align: center;
                margin-bottom: 4rem;
            }}
            
            .hero-title {{
                font-size: 3rem;
                font-weight: 300;
                color: white;
                margin-bottom: 1rem;
                text-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }}
            
            .hero-subtitle {{
                font-size: 1.2rem;
                color: rgba(255,255,255,0.9);
                margin-bottom: 2rem;
                max-width: 600px;
                margin-left: auto;
                margin-right: auto;
                line-height: 1.6;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1.5rem;
                margin: 3rem 0;
            }}
            
            .stat-card {{
                background: rgba(255, 255, 255, 0.95);
                padding: 2rem;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                backdrop-filter: blur(10px);
                transition: transform 0.3s ease;
            }}
            
            .stat-card:hover {{
                transform: translateY(-5px);
            }}
            
            .stat-number {{
                font-size: 2.5rem;
                font-weight: 700;
                color: #667eea;
                display: block;
                margin-bottom: 0.5rem;
            }}
            
            .stat-label {{
                color: #666;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-weight: 500;
            }}
            
            .features-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
                margin: 3rem 0;
            }}
            
            .feature-card {{
                background: rgba(255, 255, 255, 0.95);
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                backdrop-filter: blur(10px);
                transition: transform 0.3s ease;
            }}
            
            .feature-card:hover {{
                transform: translateY(-5px);
            }}
            
            .feature-icon {{
                font-size: 2.5rem;
                margin-bottom: 1rem;
                display: block;
            }}
            
            .feature-title {{
                font-size: 1.2rem;
                font-weight: 600;
                color: #333;
                margin-bottom: 0.5rem;
            }}
            
            .feature-desc {{
                color: #666;
                line-height: 1.6;
            }}
            
            .cta-section {{
                text-align: center;
                margin: 4rem 0;
            }}
            
            .cta-btn {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1rem 2rem;
                border-radius: 8px;
                text-decoration: none;
                font-size: 1.1rem;
                font-weight: 500;
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                transition: all 0.3s ease;
            }}
            
            .cta-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
            }}
            
            .footer {{
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.8);
                text-align: center;
                padding: 2rem;
                margin-top: 4rem;
                backdrop-filter: blur(10px);
            }}
            
            @media (max-width: 768px) {{
                .header-content {{
                    flex-direction: column;
                    gap: 1rem;
                }}
                .hero-title {{
                    font-size: 2rem;
                }}
                .main-content {{
                    padding: 2rem 1rem;
                }}
                .stats-grid {{
                    grid-template-columns: repeat(2, 1fr);
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo">
                    📚 ChromaDB Viewer
                </div>
                <nav class="nav">
                    <a href="/documents" class="nav-btn">📄 Browse Documents</a>
                    <a href="/search" class="nav-btn">🔍 Search</a>
                    <a href="/upload" class="nav-btn">⬆️ Upload</a>
                </nav>
            </div>
        </div>
        
        <div class="main-content">
            <div class="hero-section">
                <h1 class="hero-title">Document Knowledge Base</h1>
                <p class="hero-subtitle">
                    Explore, search, and manage your document collection with intelligent AI-powered features. 
                    Access your knowledge base with semantic search and smart document analysis.
                </p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-number">{total_count}</span>
                    <div class="stat-label">Total Documents</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{len([doc for doc in documents if doc.get('has_metadata', False)])}</span>
                    <div class="stat-label">With Metadata</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{sum(doc.get('word_count', 0) for doc in documents):,}</span>
                    <div class="stat-label">Total Words</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number">✓</span>
                    <div class="stat-label">System Status</div>
                </div>
            </div>
            
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">🔍</div>
                    <div class="feature-title">Smart Search</div>
                    <div class="feature-desc">
                        Use AI-powered semantic search to find relevant documents based on meaning, not just keywords.
                    </div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <div class="feature-title">Document Analytics</div>
                    <div class="feature-desc">
                        View detailed analytics and insights about your document collection and content patterns.
                    </div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">💬</div>
                    <div class="feature-title">AI Chat</div>
                    <div class="feature-desc">
                        Ask questions about your documents and get intelligent responses powered by your knowledge base.
                    </div>
                </div>
            </div>
            
            <div class="cta-section">
                <a href="/documents" class="cta-btn">
                    📚 Explore Documents
                    <span>→</span>
                </a>
            </div>
        </div>
        
        <div class="footer">
            <p>ChromaDB Document Viewer • Powered by AI • Built for Knowledge Management</p>
        </div>
    </body>
    </html>
    """)

@app.get("/documents", response_class=HTMLResponse)
async def documents_page(search: str = Query("", description="Search term"), page: int = Query(1, ge=1)):
    """Enhanced documents page with better UI"""
    try:
        # Get documents from backend
        documents, total_count = get_documents_from_backend()
        
        if not documents:
            return HTMLResponse("""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Documents - No Connection</title>
                <style>
                    body {{ 
                        font-family: system-ui; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        min-height: 100vh; 
                        display: flex; 
                        align-items: center; 
                        justify-content: center; 
                        margin: 0; 
                    }}
                    .error-container {{
                        background: rgba(255, 255, 255, 0.95);
                        padding: 3rem;
                        border-radius: 12px;
                        text-align: center;
                        max-width: 500px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    }}
                    .error-icon {{ font-size: 4rem; margin-bottom: 1rem; }}
                    .error-title {{ font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #333; }}
                    .error-desc {{ color: #666; margin-bottom: 2rem; line-height: 1.6; }}
                    .btn {{ 
                        background: #667eea; 
                        color: white; 
                        padding: 0.75rem 1.5rem; 
                        border-radius: 6px; 
                        text-decoration: none; 
                        margin: 0 0.5rem; 
                        display: inline-block;
                        transition: all 0.3s ease;
                    }}
                    .btn:hover {{ background: #5a6fd8; transform: translateY(-1px); }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <div class="error-icon">🔌</div>
                    <div class="error-title">Backend Connection Failed</div>
                    <div class="error-desc">
                        Unable to connect to the document service. Please ensure all services are running and try again.
                    </div>
                    <a href="/documents" class="btn">🔄 Retry</a>
                    <a href="/" class="btn">🏠 Home</a>
                </div>
            </body>
            </html>
            """)
        
        # Filter documents if search is provided
        filtered_documents = documents
        if search:
            scored_docs = []
            for doc in documents:
                doc_text = doc.get('preview', '') or doc.get('content', '')
                score = calculate_similarity_score(doc_text, search)
                if score > 15:
                    doc['similarity_score'] = score
                    scored_docs.append(doc)
            filtered_documents = sorted(scored_docs, key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        # Pagination
        per_page = 12
        total_pages = max(1, (len(filtered_documents) + per_page - 1) // per_page)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_docs = filtered_documents[start_idx:end_idx]
        
        # Create document cards
        cards_html = ""
        for i, doc in enumerate(paginated_docs):
            doc_number = start_idx + i + 1
            doc_id = doc.get('id', f'doc_{doc_number}')
            doc_content = doc.get('preview', '') or doc.get('content', '')
            word_count = doc.get('word_count', len(doc_content.split()) if doc_content else 0)
            title = doc.get('title', f'Document {doc_number}')
            category = doc.get('category', 'Unknown')
            has_metadata = doc.get('has_metadata', False)
            similarity_score = doc.get('similarity_score', 0) if search else 0
            
            # Match indicator
            match_indicator = ""
            if search and similarity_score > 0:
                if similarity_score >= 80:
                    color, label = "#22c55e", "Excellent match"
                elif similarity_score >= 60:
                    color, label = "#3b82f6", "Good match"
                elif similarity_score >= 40:
                    color, label = "#f59e0b", "Fair match"
                else:
                    color, label = "#ef4444", "Poor match"
                
                match_indicator = f"""
                <div class="match-indicator" style="background: {color};">
                    {similarity_score:.0f}% • {label}
                </div>
                """
            
            # Metadata badge
            metadata_badge = ""
            if has_metadata:
                metadata_badge = '<div class="metadata-badge">📋 Rich metadata</div>'
            
            cards_html += f"""
            <div class="document-card">
                <div class="card-header">
                    <div class="doc-number">#{doc_number}</div>
                    <div class="doc-category">{category}</div>
                </div>
                {match_indicator}
                <div class="card-body">
                    <h3 class="doc-title">{title}</h3>
                    <p class="doc-preview">{doc_content[:150]}{"..." if len(doc_content) > 150 else ""}</p>
                    <div class="doc-stats">
                        <span class="word-count">📄 {word_count:,} words</span>
                        {metadata_badge}
                    </div>
                </div>
                <div class="card-footer">
                    <a href="/document/{doc_id}" class="view-btn">View Document →</a>
                </div>
            </div>
            """
        
        # Pagination controls
        pagination_html = ""
        if total_pages > 1:
            prev_page = max(1, page - 1)
            next_page = min(total_pages, page + 1)
            
            pagination_html = f"""
            <div class="pagination">
                {"" if page <= 1 else f'<a href="/documents?search={search}&page={prev_page}" class="page-btn">← Previous</a>'}
                <div class="page-info">Page {page} of {total_pages}</div>
                {"" if page >= total_pages else f'<a href="/documents?search={search}&page={next_page}" class="page-btn">Next →</a>'}
            </div>
            """
        
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Documents - ChromaDB Viewer</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                
                .header {{
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    padding: 1rem 0;
                    box-shadow: 0 2px 20px rgba(0,0,0,0.1);
                }}
                
                .header-content {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 0 2rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                
                .breadcrumb {{
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    color: #666;
                }}
                
                .breadcrumb a {{
                    color: #667eea;
                    text-decoration: none;
                }}
                
                .breadcrumb a:hover {{ text-decoration: underline; }}
                
                .search-section {{
                    background: rgba(255, 255, 255, 0.95);
                    margin: 2rem auto;
                    max-width: 1200px;
                    padding: 2rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                    backdrop-filter: blur(10px);
                }}
                
                .search-form {{
                    display: flex;
                    gap: 1rem;
                    align-items: center;
                    max-width: 600px;
                    margin: 0 auto;
                }}
                
                .search-input {{
                    flex: 1;
                    padding: 1rem;
                    border: 2px solid #e5e7eb;
                    border-radius: 8px;
                    font-size: 1rem;
                    outline: none;
                    transition: border-color 0.3s ease;
                }}
                
                .search-input:focus {{ border-color: #667eea; }}
                
                .search-btn {{
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 1rem 2rem;
                    border-radius: 8px;
                    font-size: 1rem;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }}
                
                .search-btn:hover {{
                    background: #5a6fd8;
                    transform: translateY(-1px);
                }}
                
                .clear-btn {{
                    background: #ef4444;
                    color: white;
                    padding: 1rem 2rem;
                    border-radius: 8px;
                    text-decoration: none;
                    transition: all 0.3s ease;
                }}
                
                .clear-btn:hover {{
                    background: #dc2626;
                    transform: translateY(-1px);
                }}
                
                .results-info {{
                    text-align: center;
                    margin-top: 1rem;
                    color: #666;
                }}
                
                .main-content {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 2rem;
                }}
                
                .documents-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                    gap: 2rem;
                    margin: 2rem 0;
                }}
                
                .document-card {{
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                    backdrop-filter: blur(10px);
                    transition: all 0.3s ease;
                }}
                
                .document-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 8px 30px rgba(0,0,0,0.15);
                }}
                
                .card-header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 1rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                
                .doc-number {{
                    font-weight: 600;
                    font-size: 1.1rem;
                }}
                
                .doc-category {{
                    background: rgba(255, 255, 255, 0.2);
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.8rem;
                }}
                
                .match-indicator {{
                    color: white;
                    padding: 0.5rem 1rem;
                    font-size: 0.85rem;
                    font-weight: 500;
                }}
                
                .card-body {{
                    padding: 1.5rem;
                }}
                
                .doc-title {{
                    font-size: 1.1rem;
                    font-weight: 600;
                    margin-bottom: 0.75rem;
                    color: #333;
                }}
                
                .doc-preview {{
                    color: #666;
                    line-height: 1.6;
                    margin-bottom: 1rem;
                    font-size: 0.9rem;
                }}
                
                .doc-stats {{
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                }}
                
                .word-count {{
                    color: #666;
                    font-size: 0.85rem;
                }}
                
                .metadata-badge {{
                    color: #667eea;
                    font-size: 0.8rem;
                    font-weight: 500;
                }}
                
                .card-footer {{
                    padding: 1rem 1.5rem;
                    background: #f8fafc;
                    border-top: 1px solid #e5e7eb;
                }}
                
                .view-btn {{
                    color: #667eea;
                    text-decoration: none;
                    font-weight: 500;
                    transition: color 0.3s ease;
                }}
                
                .view-btn:hover {{
                    color: #5a6fd8;
                }}
                
                .pagination {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 2rem;
                    margin: 3rem 0;
                }}
                
                .page-btn {{
                    background: rgba(255, 255, 255, 0.95);
                    color: #667eea;
                    padding: 1rem 2rem;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                
                .page-btn:hover {{
                    background: white;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                }}
                
                .page-info {{
                    color: white;
                    font-weight: 500;
                    background: rgba(255, 255, 255, 0.2);
                    padding: 1rem 2rem;
                    border-radius: 8px;
                    backdrop-filter: blur(10px);
                }}
                
                @media (max-width: 768px) {{
                    .search-form {{
                        flex-direction: column;
                        align-items: stretch;
                    }}
                    .documents-grid {{
                        grid-template-columns: 1fr;
                    }}
                    .header-content {{
                        flex-direction: column;
                        gap: 1rem;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="header-content">
                    <div class="breadcrumb">
                        <a href="/">🏠 Home</a>
                        <span>→</span>
                        <span>📄 Documents</span>
                    </div>
                    <div style="color: #666;">
                        {len(filtered_documents)} of {total_count} documents
                    </div>
                </div>
            </div>
            
            <div class="search-section">
                <form class="search-form" method="get">
                    <input type="text" name="search" class="search-input" 
                           placeholder="Search documents by content, title, or keywords..." 
                           value="{search}">
                    <input type="hidden" name="page" value="1">
                    <button type="submit" class="search-btn">🔍 Search</button>
                    <a href="/documents" class="clear-btn">✕ Clear</a>
                </form>
                <div class="results-info">
                    {"🔍 Search results for '" + search + "'" if search else "📚 All documents in your knowledge base"}
                </div>
            </div>
            
            <div class="main-content">
                <div class="documents-grid">
                    {cards_html}
                </div>
                {pagination_html}
            </div>
        </body>
        </html>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error - Documents</title></head>
        <body style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; font-family: system-ui; min-height: 100vh; display: flex; align-items: center; justify-content: center;">
            <div style="background: rgba(255,255,255,0.95); color: #333; padding: 3rem; border-radius: 12px; max-width: 500px;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">⚠️</div>
                <h1>Error Loading Documents</h1>
                <p style="margin: 1rem 0; color: #666;">Error: {str(e)}</p>
                <a href="/" style="background: #667eea; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 6px; display: inline-block; margin-top: 1rem;">🏠 Back to Home</a>
            </div>
        </body>
        </html>
        """)

@app.get("/document/{doc_id}", response_class=HTMLResponse)
async def view_document(doc_id: str):
    """Enhanced document view page"""
    try:
        # Get document from backend
        response = requests.get(f"{BACKEND_URL}/document/{doc_id}", timeout=10)
        
        if response.status_code != 200:
            return HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head><title>Document Not Found</title></head>
            <body style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; font-family: system-ui; min-height: 100vh; display: flex; align-items: center; justify-content: center;">
                <div style="background: rgba(255,255,255,0.95); color: #333; padding: 3rem; border-radius: 12px; max-width: 500px;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
                    <h1>Document Not Found</h1>
                    <p style="margin: 1rem 0; color: #666;">The requested document could not be found.</p>
                    <a href="/documents" style="background: #667eea; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 6px; display: inline-block; margin: 0.5rem;">📄 Browse Documents</a>
                    <a href="/" style="background: #6b7280; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 6px; display: inline-block; margin: 0.5rem;">🏠 Home</a>
                </div>
            </body>
            </html>
            """)
        
        doc_data = response.json()
        content = doc_data.get('content', 'No content available')
        metadata = doc_data.get('metadata', {})
        word_count = doc_data.get('word_count', len(content.split()) if content else 0)
        
        # Create metadata display
        metadata_html = ""
        if metadata:
            for key, value in metadata.items():
                if value:
                    metadata_html += f"""
                    <div class="metadata-item">
                        <div class="metadata-key">{key.replace('_', ' ').title()}</div>
                        <div class="metadata-value">{value}</div>
                    </div>
                    """
        
        if not metadata_html:
            metadata_html = '<div class="no-metadata">No metadata available for this document.</div>'
        
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Document View - ChromaDB Viewer</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    color: #333;
                }}
                
                .header {{
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    padding: 1rem 0;
                    box-shadow: 0 2px 20px rgba(0,0,0,0.1);
                }}
                
                .header-content {{
                    max-width: 1000px;
                    margin: 0 auto;
                    padding: 0 2rem;
                }}
                
                .breadcrumb {{
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    color: #666;
                }}
                
                .breadcrumb a {{
                    color: #667eea;
                    text-decoration: none;
                }}
                
                .breadcrumb a:hover {{ text-decoration: underline; }}
                
                .main-content {{
                    max-width: 1000px;
                    margin: 2rem auto;
                    padding: 0 2rem;
                }}
                
                .document-container {{
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    backdrop-filter: blur(10px);
                }}
                
                .document-header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 2rem;
                }}
                
                .doc-title {{
                    font-size: 1.5rem;
                    font-weight: 600;
                    margin-bottom: 1rem;
                }}
                
                .doc-info {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 1rem;
                    opacity: 0.9;
                }}
                
                .info-item {{
                    text-align: center;
                }}
                
                .info-label {{
                    font-size: 0.8rem;
                    opacity: 0.8;
                    margin-bottom: 0.25rem;
                }}
                
                .info-value {{
                    font-weight: 600;
                }}
                
                .document-tabs {{
                    background: #f8fafc;
                    border-bottom: 1px solid #e5e7eb;
                    display: flex;
                }}
                
                .tab {{
                    padding: 1rem 2rem;
                    background: none;
                    border: none;
                    cursor: pointer;
                    font-size: 1rem;
                    color: #666;
                    border-bottom: 3px solid transparent;
                    transition: all 0.3s ease;
                }}
                
                .tab.active {{
                    color: #667eea;
                    border-bottom-color: #667eea;
                    background: white;
                }}
                
                .tab-content {{
                    padding: 2rem;
                }}
                
                .document-content {{
                    line-height: 1.8;
                    font-size: 1.1rem;
                    white-space: pre-wrap;
                    color: #333;
                }}
                
                .metadata-grid {{
                    display: grid;
                    gap: 1rem;
                }}
                
                .metadata-item {{
                    display: grid;
                    grid-template-columns: 150px 1fr;
                    gap: 1rem;
                    padding: 0.75rem;
                    background: #f8fafc;
                    border-radius: 6px;
                }}
                
                .metadata-key {{
                    font-weight: 600;
                    color: #374151;
                }}
                
                .metadata-value {{
                    color: #666;
                }}
                
                .no-metadata {{
                    text-align: center;
                    color: #666;
                    font-style: italic;
                    padding: 2rem;
                }}
                
                .actions {{
                    margin-top: 2rem;
                    text-align: center;
                }}
                
                .btn {{
                    background: #667eea;
                    color: white;
                    padding: 0.75rem 1.5rem;
                    border-radius: 6px;
                    text-decoration: none;
                    margin: 0 0.5rem;
                    display: inline-block;
                    transition: all 0.3s ease;
                }}
                
                .btn:hover {{
                    background: #5a6fd8;
                    transform: translateY(-1px);
                }}
                
                .btn-secondary {{
                    background: #6b7280;
                }}
                
                .btn-secondary:hover {{
                    background: #565e6b;
                }}
                
                @media (max-width: 768px) {{
                    .metadata-item {{
                        grid-template-columns: 1fr;
                        gap: 0.5rem;
                    }}
                    .document-tabs {{
                        overflow-x: auto;
                    }}
                    .doc-info {{
                        grid-template-columns: repeat(2, 1fr);
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="header-content">
                    <div class="breadcrumb">
                        <a href="/">🏠 Home</a>
                        <span>→</span>
                        <a href="/documents">📄 Documents</a>
                        <span>→</span>
                        <span>📖 Document View</span>
                    </div>
                </div>
            </div>
            
            <div class="main-content">
                <div class="document-container">
                    <div class="document-header">
                        <div class="doc-title">📖 Document: {doc_id}</div>
                        <div class="doc-info">
                            <div class="info-item">
                                <div class="info-label">Word Count</div>
                                <div class="info-value">{word_count:,}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">Characters</div>
                                <div class="info-value">{len(content):,}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">Metadata</div>
                                <div class="info-value">{"Yes" if metadata else "No"}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="document-tabs">
                        <button class="tab active" onclick="showTab('content')">📄 Content</button>
                        <button class="tab" onclick="showTab('metadata')">📋 Metadata</button>
                    </div>
                    
                    <div class="tab-content" id="content-tab">
                        <div class="document-content">{content}</div>
                    </div>
                    
                    <div class="tab-content" id="metadata-tab" style="display: none;">
                        <div class="metadata-grid">
                            {metadata_html}
                        </div>
                    </div>
                    
                    <div class="actions">
                        <a href="/documents" class="btn">📄 Browse More Documents</a>
                        <a href="/" class="btn btn-secondary">🏠 Home</a>
                    </div>
                </div>
            </div>
            
            <script>
                function showTab(tabName) {{
                    // Hide all tabs
                    document.getElementById('content-tab').style.display = 'none';
                    document.getElementById('metadata-tab').style.display = 'none';
                    
                    // Remove active class from all tabs
                    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
                    
                    // Show selected tab
                    document.getElementById(tabName + '-tab').style.display = 'block';
                    
                    // Add active class to clicked tab
                    event.target.classList.add('active');
                }}
            </script>
        </body>
        </html>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error - Document View</title></head>
        <body style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; font-family: system-ui; min-height: 100vh; display: flex; align-items: center; justify-content: center;">
            <div style="background: rgba(255,255,255,0.95); color: #333; padding: 3rem; border-radius: 12px; max-width: 500px;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">⚠️</div>
                <h1>Error Loading Document</h1>
                <p style="margin: 1rem 0; color: #666;">Error: {str(e)}</p>
                <a href="/documents" style="background: #667eea; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 6px; display: inline-block; margin: 0.5rem;">📄 Browse Documents</a>
                <a href="/" style="background: #6b7280; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 6px; display: inline-block; margin: 0.5rem;">🏠 Home</a>
            </div>
        </body>
        </html>
        """)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)