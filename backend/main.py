from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
import openai
import os
import uuid
import datetime
import json
from typing import List, Optional
from dotenv import load_dotenv
import PyPDF2
import docx
import io
from minio import Minio
from minio.error import S3Error
import aiofiles
import re
import time
import logging
from collections import Counter
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import hashlib

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

# ChromaDB connection variables
chroma_host = os.getenv("CHROMA_HOST", "chromadb")
chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
chroma_client = None
collection = None

def connect_to_chromadb():
    """Connect to ChromaDB with retry logic"""
    global chroma_client
    if chroma_client is not None:
        return True
        
    try:
        chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        print(f"Connected to ChromaDB at {chroma_host}:{chroma_port}")
        return True
    except Exception as e:
        print(f"Failed to connect to ChromaDB: {e}")
        chroma_client = None
        return False

# Initialize MinIO client
minio_client = Minio(
    os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ACCESS_KEY", "admin"),
    secret_key=os.getenv("MINIO_SECRET_KEY", "minio123456"),
    secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
)
bucket_name = os.getenv("MINIO_BUCKET_NAME", "documents")

def ensure_bucket_exists():
    """Ensure the MinIO bucket exists"""
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            print(f"Created bucket: {bucket_name}")
        else:
            print(f"Bucket {bucket_name} already exists")
    except S3Error as e:
        print(f"Error with MinIO bucket: {e}")

# Ensure bucket exists on startup
ensure_bucket_exists()

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
    
    if not connect_to_chromadb():
        print("Could not connect to ChromaDB, skipping initialization")
        return False
        
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

class SearchRequest(BaseModel):
    query: str
    n_results: Optional[int] = 5
    min_similarity: Optional[float] = 0.7
    category_filter: Optional[str] = None
    document_type_filter: Optional[str] = None
    strategy: Optional[str] = "hybrid"  # hybrid, semantic, lexical, auto

class SearchResponse(BaseModel):
    results: List[dict]
    total_found: int
    query: str
    search_time_ms: float
    search_strategy: str

# Professional Search Architecture
class SearchStrategy(Enum):
    SEMANTIC_ONLY = "semantic_only"
    LEXICAL_ONLY = "lexical_only" 
    HYBRID = "hybrid"
    AUTO = "auto"

@dataclass
class SearchResult:
    chunk_id: str
    content: str
    title: str
    metadata: dict
    semantic_score: float
    lexical_score: float
    final_score: float
    highlights: List[str]
    rank_factors: dict

@dataclass
class QueryContext:
    original_query: str
    preprocessed_query: str
    expanded_terms: List[str]
    query_type: str
    intent: str
    entities: List[str]

class SearchEngine:
    """Enterprise-grade hybrid search engine"""
    
    def __init__(self, collection, openai_client):
        self.collection = collection
        self.openai_client = openai_client
        self.query_cache = {}
        self.search_analytics = []
        
    def preprocess_query(self, query: str) -> QueryContext:
        """Advanced query preprocessing and understanding"""
        # Clean and normalize
        preprocessed = re.sub(r'[^\w\s-]', ' ', query.lower().strip())
        preprocessed = ' '.join(preprocessed.split())
        
        # Extract entities and intent
        entities = self._extract_entities(query)
        query_type = self._classify_query_type(query)
        intent = self._detect_intent(query)
        
        # Query expansion
        expanded_terms = self._expand_query(preprocessed)
        
        return QueryContext(
            original_query=query,
            preprocessed_query=preprocessed,
            expanded_terms=expanded_terms,
            query_type=query_type,
            intent=intent,
            entities=entities
        )
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract domain-specific entities"""
        warehouse_entities = [
            'wms', 'warehouse management system', 'inventory', 'picking', 'packing',
            'shipping', 'receiving', 'fifo', 'lifo', 'abc analysis', 'cycle count',
            'cross-docking', 'wave picking', 'batch picking', 'zone picking'
        ]
        
        entities = []
        query_lower = query.lower()
        for entity in warehouse_entities:
            if entity in query_lower:
                entities.append(entity)
        return entities
    
    def _classify_query_type(self, query: str) -> str:
        """Classify query type for optimized search strategy"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['what is', 'define', 'definition', 'meaning']):
            return 'definition'
        elif any(word in query_lower for word in ['how to', 'how do', 'steps', 'process']):
            return 'procedural'
        elif any(word in query_lower for word in ['best', 'compare', 'vs', 'versus', 'difference']):
            return 'comparative'
        elif any(word in query_lower for word in ['list', 'examples', 'types of']):
            return 'enumeration'
        else:
            return 'general'
    
    def _detect_intent(self, query: str) -> str:
        """Detect user intent"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['learn', 'understand', 'explain']):
            return 'educational'
        elif any(word in query_lower for word in ['implement', 'setup', 'configure']):
            return 'implementation'
        elif any(word in query_lower for word in ['problem', 'issue', 'troubleshoot', 'fix']):
            return 'troubleshooting'
        else:
            return 'informational'
    
    def _expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms and related terms"""
        expansion_map = {
            'inventory': ['stock', 'goods', 'products', 'items', 'materials'],
            'picking': ['order picking', 'item selection', 'fulfillment'],
            'warehouse': ['distribution center', 'fulfillment center', 'storage facility'],
            'management': ['control', 'administration', 'oversight', 'organization'],
            'system': ['software', 'platform', 'solution', 'technology'],
        }
        
        expanded = []
        words = query.split()
        
        for word in words:
            if word in expansion_map:
                expanded.extend(expansion_map[word][:2])  # Add top 2 synonyms
        
        return expanded
    
    async def hybrid_search(self, query_context: QueryContext, 
                           n_results: int = 10,
                           strategy: SearchStrategy = SearchStrategy.HYBRID,
                           filters: dict = None) -> List[SearchResult]:
        """Advanced hybrid search combining semantic and lexical approaches"""
        
        start_time = time.time()
        
        # Get semantic results
        semantic_results = await self._semantic_search(query_context, n_results * 2)
        
        # Get lexical results
        lexical_results = await self._lexical_search(query_context, n_results * 2)
        
        # Merge and rerank results
        merged_results = self._merge_and_rerank(
            semantic_results, lexical_results, query_context, strategy
        )
        
        # Apply filters
        if filters:
            merged_results = self._apply_filters(merged_results, filters)
        
        # Final ranking and scoring
        final_results = self._final_ranking(merged_results, query_context)[:n_results]
        
        search_time = (time.time() - start_time) * 1000
        
        # Log analytics
        self._log_search_analytics(query_context, len(final_results), search_time, strategy)
        
        return final_results
    
    async def _semantic_search(self, query_context: QueryContext, n_results: int) -> List[dict]:
        """Enhanced semantic search with query expansion"""
        try:
            # Create enhanced query for embedding
            enhanced_query = f"{query_context.preprocessed_query} {' '.join(query_context.expanded_terms[:3])}"
            
            embedding_response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=enhanced_query
            )
            query_embedding = embedding_response.data[0].embedding
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["metadatas", "documents", "distances"]
            )
            
            return self._process_semantic_results(results, query_context)
            
        except Exception as e:
            logging.error(f"Semantic search error: {e}")
            return []
    
    async def _lexical_search(self, query_context: QueryContext, n_results: int) -> List[dict]:
        """Advanced lexical search with BM25-like scoring"""
        try:
            # Get all documents for lexical matching
            all_results = self.collection.get(include=["metadatas", "documents"])
            
            if not all_results["documents"]:
                return []
            
            lexical_scores = []
            query_terms = query_context.preprocessed_query.split() + query_context.expanded_terms
            
            for i, doc in enumerate(all_results["documents"]):
                score = self._calculate_bm25_score(doc, query_terms)
                
                if score > 0:
                    metadata = all_results["metadatas"][i] if all_results["metadatas"] else {}
                    lexical_scores.append({
                        'doc_index': i,
                        'content': doc,
                        'metadata': metadata or {},
                        'lexical_score': score,
                        'highlights': self._extract_highlights(doc, query_terms[:3])
                    })
            
            # Sort by lexical score
            lexical_scores.sort(key=lambda x: x['lexical_score'], reverse=True)
            return lexical_scores[:n_results]
            
        except Exception as e:
            logging.error(f"Lexical search error: {e}")
            return []
    
    def _calculate_bm25_score(self, document: str, query_terms: List[str], 
                             k1: float = 1.5, b: float = 0.75) -> float:
        """BM25 scoring algorithm for lexical relevance"""
        doc_terms = document.lower().split()
        doc_len = len(doc_terms)
        avg_doc_len = 200  # Approximate average document length
        
        score = 0
        for term in query_terms:
            term = term.lower()
            tf = doc_terms.count(term)
            
            if tf > 0:
                # BM25 formula
                idf = 1  # Simplified IDF for this implementation
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_len / avg_doc_len))
                score += idf * (numerator / denominator)
        
        return score
    
    def _extract_highlights(self, document: str, terms: List[str]) -> List[str]:
        """Extract highlighted snippets around matching terms"""
        highlights = []
        doc_lower = document.lower()
        
        for term in terms:
            term_lower = term.lower()
            if term_lower in doc_lower:
                start_idx = doc_lower.find(term_lower)
                # Extract context around the term
                context_start = max(0, start_idx - 50)
                context_end = min(len(document), start_idx + len(term) + 50)
                context = document[context_start:context_end]
                
                # Highlight the term
                highlighted = re.sub(
                    f'({re.escape(term)})', 
                    r'<mark>\1</mark>', 
                    context, 
                    flags=re.IGNORECASE
                )
                highlights.append(highlighted)
        
        return highlights[:3]  # Limit to top 3 highlights
    
    def _merge_and_rerank(self, semantic_results: List[dict], lexical_results: List[dict],
                         query_context: QueryContext, strategy: SearchStrategy) -> List[SearchResult]:
        """Intelligent merging and reranking of results"""
        
        combined_results = {}
        
        # Process semantic results
        for result in semantic_results:
            chunk_id = result.get('chunk_id', result.get('doc_id', ''))
            combined_results[chunk_id] = SearchResult(
                chunk_id=chunk_id,
                content=result.get('content', ''),
                title=result.get('title', 'Unknown'),
                metadata=result.get('metadata', {}),
                semantic_score=result.get('semantic_score', 0),
                lexical_score=0,
                final_score=0,
                highlights=[],
                rank_factors={}
            )
        
        # Merge lexical results
        for result in lexical_results:
            chunk_id = str(result.get('doc_index', ''))
            if chunk_id in combined_results:
                combined_results[chunk_id].lexical_score = result.get('lexical_score', 0)
                combined_results[chunk_id].highlights = result.get('highlights', [])
            else:
                metadata = result.get('metadata', {})
                combined_results[chunk_id] = SearchResult(
                    chunk_id=chunk_id,
                    content=result.get('content', ''),
                    title=metadata.get('title', 'Unknown'),
                    metadata=metadata,
                    semantic_score=0,
                    lexical_score=result.get('lexical_score', 0),
                    final_score=0,
                    highlights=result.get('highlights', []),
                    rank_factors={}
                )
        
        return list(combined_results.values())
    
    def _final_ranking(self, results: List[SearchResult], query_context: QueryContext) -> List[SearchResult]:
        """Advanced final ranking with multiple signals"""
        
        for result in results:
            # Calculate composite score based on query type
            if query_context.query_type == 'definition':
                # For definitions, prioritize semantic similarity
                semantic_weight = 0.8
                lexical_weight = 0.2
            elif query_context.query_type == 'procedural':
                # For procedures, balance both approaches
                semantic_weight = 0.6
                lexical_weight = 0.4
            else:
                # Default balanced approach
                semantic_weight = 0.7
                lexical_weight = 0.3
            
            # Base score combination
            base_score = (result.semantic_score * semantic_weight + 
                         result.lexical_score * lexical_weight)
            
            # Apply boosters
            title_boost = self._calculate_title_boost(result.title, query_context)
            entity_boost = self._calculate_entity_boost(result.content, query_context)
            freshness_boost = self._calculate_freshness_boost(result.metadata)
            length_penalty = self._calculate_length_penalty(result.content)
            
            result.final_score = (base_score + title_boost + entity_boost + 
                                freshness_boost - length_penalty)
            
            result.rank_factors = {
                'base_score': base_score,
                'title_boost': title_boost,
                'entity_boost': entity_boost,
                'freshness_boost': freshness_boost,
                'length_penalty': length_penalty
            }
        
        # Sort by final score
        results.sort(key=lambda x: x.final_score, reverse=True)
        return results
    
    def _calculate_title_boost(self, title: str, query_context: QueryContext) -> float:
        """Boost score for title matches"""
        title_lower = title.lower()
        query_terms = query_context.preprocessed_query.split()
        
        matches = sum(1 for term in query_terms if term in title_lower)
        return min(matches * 0.1, 0.3)  # Cap at 0.3
    
    def _calculate_entity_boost(self, content: str, query_context: QueryContext) -> float:
        """Boost score for entity matches"""
        content_lower = content.lower()
        entity_matches = sum(1 for entity in query_context.entities if entity in content_lower)
        return min(entity_matches * 0.05, 0.2)  # Cap at 0.2
    
    def _calculate_freshness_boost(self, metadata: dict) -> float:
        """Boost newer documents slightly"""
        upload_time = metadata.get('upload_time', '')
        if upload_time:
            try:
                # Simple freshness boost (newer = slightly better)
                return 0.05 if '2025' in upload_time else 0
            except:
                pass
        return 0
    
    def _calculate_length_penalty(self, content: str) -> float:
        """Slight penalty for very short or very long content"""
        length = len(content.split())
        if length < 10:
            return 0.1  # Too short
        elif length > 500:
            return 0.05  # Too long
        return 0
    
    def _process_semantic_results(self, results: dict, query_context: QueryContext) -> List[dict]:
        """Process raw semantic results"""
        processed = []
        
        if not results["documents"] or not results["documents"][0]:
            return processed
        
        for i, doc in enumerate(results["documents"][0]):
            distance = results["distances"][0][i] if results["distances"] else 1.0
            semantic_score = max(0, 1 - distance)  # Convert distance to similarity
            
            metadata = results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {}
            if metadata is None:
                metadata = {}
            
            processed.append({
                'chunk_id': metadata.get('document_id', f'doc_{i}') if metadata else f'doc_{i}',
                'content': doc,
                'title': metadata.get('title', 'Unknown Document') if metadata else 'Unknown Document',
                'metadata': metadata,
                'semantic_score': semantic_score,
                'doc_id': f'doc_{i}'
            })
        
        return processed
    
    def _apply_filters(self, results: List[SearchResult], filters: dict) -> List[SearchResult]:
        """Apply additional filters to results"""
        filtered = []
        
        for result in results:
            if filters.get('category_filter') and result.metadata.get('category') != filters['category_filter']:
                continue
            if filters.get('document_type_filter') and result.metadata.get('document_type') != filters['document_type_filter']:
                continue
            if filters.get('min_score') and result.final_score < filters['min_score']:
                continue
            
            filtered.append(result)
        
        return filtered
    
    def _log_search_analytics(self, query_context: QueryContext, results_count: int, 
                             search_time: float, strategy: SearchStrategy):
        """Log search analytics for monitoring"""
        analytics_entry = {
            'timestamp': time.time(),
            'query': query_context.original_query,
            'query_type': query_context.query_type,
            'intent': query_context.intent,
            'results_count': results_count,
            'search_time_ms': search_time,
            'strategy': strategy.value
        }
        
        self.search_analytics.append(analytics_entry)
        
        # Keep only last 1000 entries
        if len(self.search_analytics) > 1000:
            self.search_analytics = self.search_analytics[-1000:]

# Global search engine instance
search_engine = None

# Initialize search engine after class definition
def initialize_search_engine():
    """Initialize the enterprise search engine"""
    global search_engine
    if collection is not None and openai_client is not None:
        search_engine = SearchEngine(collection, openai_client)
        print("Advanced search engine initialized")
    else:
        print("Warning: Search engine could not be initialized")

# Initialize on startup
initialize_search_engine()

async def search_knowledge_base_new(query: str, n_results: int = 5, 
                                   strategy: str = "hybrid",
                                   category_filter: Optional[str] = None, 
                                   document_type_filter: Optional[str] = None) -> List[dict]:
    """New enterprise-grade search function"""
    global search_engine
    
    if search_engine is None:
        return []
    
    try:
        # Preprocess query
        query_context = search_engine.preprocess_query(query)
        
        # Build filters
        filters = {}
        if category_filter:
            filters['category_filter'] = category_filter
        if document_type_filter:
            filters['document_type_filter'] = document_type_filter
        
        # Map strategy
        strategy_map = {
            "semantic": SearchStrategy.SEMANTIC_ONLY,
            "lexical": SearchStrategy.LEXICAL_ONLY,
            "hybrid": SearchStrategy.HYBRID,
            "auto": SearchStrategy.AUTO
        }
        search_strategy = strategy_map.get(strategy, SearchStrategy.HYBRID)
        
        # Perform hybrid search
        results = await search_engine.hybrid_search(
            query_context=query_context,
            n_results=n_results,
            strategy=search_strategy,
            filters=filters
        )
        
        # Convert to legacy format for compatibility
        legacy_results = []
        for result in results:
            legacy_results.append({
                "content": result.content,
                "metadata": result.metadata,
                "similarity": result.semantic_score,
                "relevance_score": result.final_score,
                "chunk_id": result.chunk_id,
                "title": result.title,
                "category": result.metadata.get('category', 'Document'),
                "document_type": result.metadata.get('document_type', 'Unknown'),
                "highlights": result.highlights,
                "rank_factors": result.rank_factors
            })
        
        return legacy_results
        
    except Exception as e:
        logging.error(f"Search error: {e}")
        return []

# Legacy compatibility function
def search_knowledge_base(query: str, n_results: int = 5, min_similarity: float = 0.7, 
                         category_filter: Optional[str] = None, document_type_filter: Optional[str] = None) -> List[dict]:
    """Legacy search function for backward compatibility"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If in async context, create a new task
            import asyncio
            task = asyncio.create_task(search_knowledge_base_new(
                query=query, 
                n_results=n_results,
                category_filter=category_filter,
                document_type_filter=document_type_filter
            ))
            return []  # Return empty for now in async context
        else:
            return asyncio.run(search_knowledge_base_new(
                query=query, 
                n_results=n_results,
                category_filter=category_filter,
                document_type_filter=document_type_filter
            ))
    except Exception as e:
        logging.error(f"Legacy search error: {e}")
        return []

def generate_response_with_openai(query: str, context_docs: List[dict]) -> str:
    """Generate response using OpenAI with knowledge base context"""
    try:
        # Format context with enhanced information
        context_parts = []
        for i, doc_data in enumerate(context_docs):
            content = doc_data.get("content", "")
            title = doc_data.get("title", "Unknown Document")
            relevance = doc_data.get("relevance_score", 0)
            
            context_parts.append(f"""Document {i+1} (Relevance: {relevance:.2f}):
Title: {title}
Content: {content}""")
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""You are a helpful assistant with access to a knowledge base about warehouse management and inventory systems. 

Based on the following ranked context documents (ordered by relevance), please answer the user's question. Pay more attention to documents with higher relevance scores.

Context Documents:
{context}

User Question: {query}

Please provide a clear, helpful response based on the most relevant context provided. If the answer isn't clearly available in the context, say so politely and suggest related topics that might help."""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating OpenAI response: {e}")
        context_preview = " | ".join([doc.get("title", "Unknown") for doc in context_docs[:2]])
        return f"I found some relevant information but encountered an error generating the response. The relevant sources were: {context_preview}"

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    try:
        # Search knowledge base with new engine
        relevant_docs = await search_knowledge_base_new(message.message, n_results=3)
        
        if relevant_docs:
            # Generate response with OpenAI using context
            response = generate_response_with_openai(message.message, relevant_docs)
        else:
            response = "I couldn't find relevant information in my knowledge base. Could you please rephrase your question or ask about warehouse management, inventory systems, or logistics topics?"
        
        return ChatResponse(response=response)
    
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return ChatResponse(response="I apologize, but I encountered an error processing your request. Please try again.")

@app.post("/search", response_model=SearchResponse)
async def search_documents(search_request: SearchRequest):
    """Enterprise-grade hybrid search with advanced ranking"""
    start_time = time.time()
    
    try:
        results = await search_knowledge_base_new(
            query=search_request.query,
            n_results=search_request.n_results,
            strategy=search_request.strategy,
            category_filter=search_request.category_filter,
            document_type_filter=search_request.document_type_filter
        )
        
        # Clean results for JSON serialization
        clean_results = []
        for result in results:
            clean_result = {
                "chunk_id": result["chunk_id"],
                "title": result["title"],
                "content": result["content"],
                "category": result["category"],
                "document_type": result["document_type"],
                "similarity": round(result["similarity"], 3),
                "relevance_score": round(result["relevance_score"], 3),
                "preview": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"],
                "word_count": len(result["content"].split()),
                "metadata": {
                    "filename": result["metadata"].get("filename", ""),
                    "upload_time": result["metadata"].get("upload_time", ""),
                    "topics": result["metadata"].get("topics", "").split(",") if result["metadata"].get("topics") else []
                }
            }
            clean_results.append(clean_result)
        
        search_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            results=clean_results,
            total_found=len(clean_results),
            query=search_request.query,
            search_time_ms=round(search_time, 2),
            search_strategy=search_request.strategy
        )
        
    except Exception as e:
        print(f"Error in search endpoint: {e}")
        search_time = (time.time() - start_time) * 1000
        return SearchResponse(
            results=[], 
            total_found=0, 
            query=search_request.query,
            search_time_ms=round(search_time, 2),
            search_strategy=search_request.strategy
        )

@app.get("/search/analytics")
async def get_search_analytics():
    """Get search analytics and performance metrics"""
    global search_engine
    
    if search_engine is None or not search_engine.search_analytics:
        return {
            "total_searches": 0,
            "recent_searches": [],
            "performance_metrics": {},
            "query_types": {},
            "popular_queries": []
        }
    
    analytics = search_engine.search_analytics
    
    # Calculate metrics
    total_searches = len(analytics)
    avg_search_time = sum(a['search_time_ms'] for a in analytics) / total_searches if total_searches > 0 else 0
    avg_results = sum(a['results_count'] for a in analytics) / total_searches if total_searches > 0 else 0
    
    # Query type distribution
    query_types = {}
    for entry in analytics:
        qt = entry['query_type']
        query_types[qt] = query_types.get(qt, 0) + 1
    
    # Popular queries (last 100)
    recent_queries = [a['query'] for a in analytics[-100:]]
    query_freq = Counter(recent_queries)
    popular_queries = [{"query": q, "count": c} for q, c in query_freq.most_common(10)]
    
    return {
        "total_searches": total_searches,
        "recent_searches": analytics[-10:],  # Last 10 searches
        "performance_metrics": {
            "avg_search_time_ms": round(avg_search_time, 2),
            "avg_results_count": round(avg_results, 2),
            "total_search_time_ms": sum(a['search_time_ms'] for a in analytics)
        },
        "query_types": query_types,
        "popular_queries": popular_queries
    }

@app.get("/")
async def root():
    return {"message": "Knowledge Base Chat API is running - Enterprise Search Enabled"}

@app.get("/health")
async def health():
    try:
        doc_count = collection.count() if collection else 0
        return {"status": "healthy", "kb_docs": doc_count}
    except:
        return {"status": "healthy", "kb_docs": 0}

@app.get("/documents")
async def list_documents():
    """List all documents/chunks individually for ChromaDB viewer"""
    try:
        if not collection:
            return {"documents": [], "total": 0}
        
        results = collection.get(include=["metadatas", "documents"])
        
        # Show each chunk as an individual document (for ChromaDB viewer)
        documents = []
        for i, chunk_id in enumerate(results["ids"]):
            # Handle cases where metadatas might be None or contain None values
            metadata = {}
            if results["metadatas"] and i < len(results["metadatas"]) and results["metadatas"][i]:
                metadata = results["metadatas"][i]
            
            content = results["documents"][i] if results["documents"] and i < len(results["documents"]) else ""
            word_count = len(content.split()) if content else 0
            
            # Get document info
            document_id = metadata.get("document_id", chunk_id)
            filename = metadata.get("filename", f"document_{chunk_id[:8]}")
            chunk_index = metadata.get("chunk_index")
            total_chunks = metadata.get("total_chunks", 1)
            
            # Create enhanced title for chunks
            if chunk_index is not None and total_chunks > 1:
                title = f"{metadata.get('title', filename)} - {chunk_id}"
                chunk_info = f"Chunk {chunk_index + 1}/{total_chunks}"
            else:
                title = metadata.get("title", filename)
                chunk_info = "Complete Document"
            
            # Enhanced preview with better formatting
            preview = content[:300] + "..." if len(content) > 300 else content
            preview = preview.replace('\n', ' ').strip()
            
            # Format upload time
            upload_time = metadata.get("upload_time", "")
            if upload_time:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_time = upload_time[:16] if len(upload_time) > 16 else upload_time
            else:
                formatted_time = "Unknown"
            
            # Enhanced document object
            doc_obj = {
                "id": chunk_id,
                "document_id": document_id,
                "title": title,
                "filename": filename,
                "chunk_info": chunk_info,
                "chunk_index": chunk_index if chunk_index is not None else 0,
                "total_chunks": total_chunks,
                "preview": preview,
                "word_count": word_count,
                "content_type": metadata.get("content_type", "text/plain"),
                "category": metadata.get("category", "Document"),
                "document_type": metadata.get("document_type", "Unknown"),
                "topics": metadata.get("topics", "").split(",") if metadata.get("topics") else [],
                "summary": metadata.get("summary", ""),
                "upload_time": formatted_time,
                "file_size": metadata.get("size", 0),
                "text_size": metadata.get("text_size", 0),
                "minio_filename": metadata.get("minio_filename", ""),
                "has_metadata": bool(metadata and any(metadata.values())),
                "has_minio_file": bool(metadata.get("minio_filename")),
                "is_chunk": chunk_index is not None and total_chunks > 1,
                "content_preview_length": len(content)
            }
            
            documents.append(doc_obj)
        
        # Sort documents: by document_id, then by chunk_index
        documents.sort(key=lambda x: (x.get("document_id", ""), x.get("chunk_index", 0)))
        
        return {"documents": documents, "total": len(documents)}
    
    except Exception as e:
        print(f"Error listing documents: {e}")
        return {"documents": [], "total": 0}

@app.get("/admin/documents")
async def list_admin_documents():
    """List documents grouped by document_id with enhanced metadata and action buttons for admin panel"""
    try:
        if not collection:
            return {"documents": [], "total": 0}
        
        results = collection.get(include=["metadatas", "documents"])
        
        # Group chunks by document_id to show as single documents (for admin panel)
        document_groups = {}
        for i, chunk_id in enumerate(results["ids"]):
            # Handle cases where metadatas might be None or contain None values
            metadata = {}
            if results["metadatas"] and i < len(results["metadatas"]) and results["metadatas"][i]:
                metadata = results["metadatas"][i]
            
            content = results["documents"][i] if results["documents"] and i < len(results["documents"]) else ""
            
            # Use document_id for grouping, fallback to filename or chunk_id
            document_id = metadata.get("document_id")
            if not document_id:
                document_id = chunk_id.split('_chunk_')[0] if '_chunk_' in chunk_id else chunk_id
            
            filename = metadata.get("filename", f"document_{document_id[:8]}")
            
            if document_id not in document_groups:
                # Format upload time
                upload_time = metadata.get("upload_time", "")
                formatted_time = "Unknown"
                if upload_time:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        formatted_time = upload_time[:16] if len(upload_time) > 16 else upload_time
                
                document_groups[document_id] = {
                    "id": document_id,
                    "filename": filename,
                    "minio_filename": metadata.get("minio_filename", ""),
                    "content_type": metadata.get("content_type", "text/plain"),
                    "upload_time": formatted_time,
                    "file_size": metadata.get("size", 0),
                    "text_size": metadata.get("text_size", 0),
                    "title": metadata.get("title", filename),
                    "category": metadata.get("category", "Document"),
                    "document_type": metadata.get("document_type", "Unknown"),
                    "topics": metadata.get("topics", "").split(",") if metadata.get("topics") else [],
                    "summary": metadata.get("summary", ""),
                    "chunks": 0,
                    "preview": "",
                    "word_count": 0,
                    "has_metadata": bool(metadata and any(metadata.values())),
                    "has_minio_file": bool(metadata.get("minio_filename")),
                    # Action button support for admin panel
                    "actions": {
                        "can_download": bool(metadata.get("minio_filename")),
                        "can_view_chunks": False,  # Will be updated below
                        "download_url": f"/download/{document_id}" if metadata.get("minio_filename") else None,
                        "chunks_url": f"/documents/{document_id}/chunks"
                    }
                }
            
            # Update chunk count and preview
            document_groups[document_id]["chunks"] += 1
            document_groups[document_id]["word_count"] += len(content.split()) if content else 0
            if not document_groups[document_id]["preview"]:
                document_groups[document_id]["preview"] = content[:250] + "..." if len(content) > 250 else content
        
        # Update actions based on chunk count
        for doc_data in document_groups.values():
            doc_data["actions"]["can_view_chunks"] = doc_data["chunks"] > 1
        
        documents = list(document_groups.values())
        
        # Sort by upload time (newest first), then by filename
        documents.sort(key=lambda x: (x.get("upload_time", ""), x.get("filename", "")), reverse=True)
        
        return {"documents": documents, "total": len(documents)}
    
    except Exception as e:
        print(f"Error listing admin documents: {e}")
        return {"documents": [], "total": 0}
        results = collection.get(include=["metadatas", "documents"])
        
        # Group chunks by document_id to show as single documents
        document_groups = {}
        for i, chunk_id in enumerate(results["ids"]):
            # Handle cases where metadatas might be None or contain None values
            metadata = {}
            if results["metadatas"] and i < len(results["metadatas"]) and results["metadatas"][i]:
                metadata = results["metadatas"][i]
            
            content = results["documents"][i] if results["documents"] and i < len(results["documents"]) else ""
            
            # Use document_id for grouping, fallback to filename or chunk_id
            document_id = metadata.get("document_id")
            if not document_id:
                document_id = chunk_id.split('_chunk_')[0] if '_chunk_' in chunk_id else chunk_id
            
            filename = metadata.get("filename", f"document_{document_id[:8]}")
            
            if document_id not in document_groups:
                # Format upload time
                upload_time = metadata.get("upload_time", "")
                formatted_time = "Unknown"
                if upload_time:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        formatted_time = upload_time[:16] if len(upload_time) > 16 else upload_time
                
                document_groups[document_id] = {
                    "id": document_id,
                    "filename": filename,
                    "minio_filename": metadata.get("minio_filename", ""),
                    "content_type": metadata.get("content_type", "text/plain"),
                    "upload_time": formatted_time,
                    "file_size": metadata.get("size", 0),
                    "text_size": metadata.get("text_size", 0),
                    "title": metadata.get("title", filename),
                    "category": metadata.get("category", "Document"),
                    "document_type": metadata.get("document_type", "Unknown"),
                    "topics": metadata.get("topics", "").split(",") if metadata.get("topics") else [],
                    "summary": metadata.get("summary", ""),
                    "chunks": 0,
                    "preview": "",
                    "word_count": 0,
                    "has_metadata": bool(metadata and any(metadata.values())),
                    "has_minio_file": bool(metadata.get("minio_filename")),
                    # New action button support
                    "actions": {
                        "can_download": bool(metadata.get("minio_filename")),
                        "can_view_chunks": False,  # Will be updated below
                        "download_url": f"/download/{document_id}" if metadata.get("minio_filename") else None,
                        "chunks_url": f"/documents/{document_id}/chunks"
                    }
                }
            
            # Update chunk count and preview
            document_groups[document_id]["chunks"] += 1
            document_groups[document_id]["word_count"] += len(content.split()) if content else 0
            if not document_groups[document_id]["preview"]:
                document_groups[document_id]["preview"] = content[:250] + "..." if len(content) > 250 else content
        
        # Update actions based on chunk count
        for doc_data in document_groups.values():
            doc_data["actions"]["can_view_chunks"] = doc_data["chunks"] > 1
        
        documents = list(document_groups.values())
        
        # Sort by upload time (newest first), then by filename
        documents.sort(key=lambda x: (x.get("upload_time", ""), x.get("filename", "")), reverse=True)
        
        return {"documents": documents, "total": len(documents)}
    
    except Exception as e:
        print(f"Error listing documents: {e}")
        return {"documents": [], "total": 0}

@app.get("/document/{doc_id}")
async def get_document(doc_id: str):
    """Get a specific document by ID"""
    try:
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Get all documents and find chunks for this document ID
        results = collection.get(include=["metadatas", "documents"])
        
        document_chunks = []
        document_metadata = None
        
        for i, chunk_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i] if results["metadatas"] and i < len(results["metadatas"]) else {}
            content = results["documents"][i] if results["documents"] and i < len(results["documents"]) else ""
            
            # Check if this chunk belongs to the requested document
            chunk_doc_id = metadata.get("document_id") if metadata else None
            if chunk_doc_id == doc_id or chunk_id == doc_id or chunk_id.startswith(doc_id + "_chunk_"):
                document_chunks.append({
                    "chunk_id": chunk_id,
                    "content": content,
                    "chunk_index": metadata.get("chunk_index", 0) if metadata else 0
                })
                if not document_metadata and metadata:
                    document_metadata = metadata
        
        if not document_chunks:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Sort chunks by index
        document_chunks.sort(key=lambda x: x["chunk_index"])
        
        # Combine all chunks into full content
        full_content = "\n\n".join([chunk["content"] for chunk in document_chunks])
        
        doc_data = {
            "id": doc_id,
            "content": full_content,
            "metadata": document_metadata or {},
            "word_count": len(full_content.split()) if full_content else 0,
            "chunks": len(document_chunks)
        }
        
        return doc_data
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/documents/{doc_id}/chunks")
async def get_document_chunks(doc_id: str):
    """Get all chunks for a specific document with detailed metadata"""
    try:
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Get all documents and find chunks for this document ID
        results = collection.get(include=["metadatas", "documents"])
        
        document_chunks = []
        document_metadata = None
        
        for i, chunk_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i] if results["metadatas"] and i < len(results["metadatas"]) else {}
            content = results["documents"][i] if results["documents"] and i < len(results["documents"]) else ""
            
            # Check if this chunk belongs to the requested document
            chunk_doc_id = metadata.get("document_id") if metadata else None
            if chunk_doc_id == doc_id or chunk_id == doc_id or chunk_id.startswith(doc_id + "_chunk_"):
                
                # Format upload time
                upload_time = metadata.get("upload_time", "") if metadata else ""
                formatted_time = "Unknown"
                if upload_time:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        formatted_time = upload_time[:16] if len(upload_time) > 16 else upload_time
                
                chunk_index = metadata.get("chunk_index", 0) if metadata else 0
                total_chunks = metadata.get("total_chunks", 1) if metadata else 1
                
                # Enhanced preview with better formatting
                preview = content[:300] + "..." if len(content) > 300 else content
                preview = preview.replace('\n', ' ').strip()
                
                chunk_data = {
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "title": f"{metadata.get('title', 'Unknown Document') if metadata else 'Unknown Document'} - {chunk_id}",
                    "filename": metadata.get("filename", f"document_{chunk_id[:8]}") if metadata else f"document_{chunk_id[:8]}",
                    "chunk_info": f"Chunk {chunk_index + 1}/{total_chunks}" if total_chunks > 1 else "Complete Document",
                    "chunk_index": chunk_index,
                    "total_chunks": total_chunks,
                    "content": content,
                    "preview": preview,
                    "word_count": len(content.split()) if content else 0,
                    "content_type": metadata.get("content_type", "text/plain") if metadata else "text/plain",
                    "category": metadata.get("category", "Document") if metadata else "Document",
                    "document_type": metadata.get("document_type", "Unknown") if metadata else "Unknown",
                    "topics": metadata.get("topics", "").split(",") if metadata and metadata.get("topics") else [],
                    "summary": metadata.get("summary", "") if metadata else "",
                    "upload_time": formatted_time,
                    "file_size": metadata.get("size", 0) if metadata else 0,
                    "text_size": metadata.get("text_size", 0) if metadata else 0,
                    "minio_filename": metadata.get("minio_filename", "") if metadata else "",
                    "has_metadata": bool(metadata and any(metadata.values())),
                    "has_minio_file": bool(metadata.get("minio_filename") if metadata else False),
                    "is_chunk": total_chunks > 1,
                    "content_preview_length": len(content)
                }
                
                document_chunks.append(chunk_data)
                if not document_metadata and metadata:
                    document_metadata = metadata
        
        if not document_chunks:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Sort chunks by index
        document_chunks.sort(key=lambda x: x["chunk_index"])
        
        # Document summary
        total_word_count = sum(chunk["word_count"] for chunk in document_chunks)
        
        return {
            "document_id": doc_id,
            "document_title": document_metadata.get("title", "Unknown Document") if document_metadata else "Unknown Document",
            "total_chunks": len(document_chunks),
            "total_word_count": total_word_count,
            "document_metadata": document_metadata or {},
            "chunks": document_chunks
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting document chunks {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def extract_text_from_file(file: UploadFile) -> str:
    """Extract text from various file types"""
    try:
        content = file.file.read()
        
        if file.content_type == "text/plain":
            return content.decode('utf-8')
        
        elif file.content_type == "application/pdf":
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        
        elif file.content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            doc_file = io.BytesIO(content)
            doc = docx.Document(doc_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        
        else:
            # Try to decode as text for other formats
            return content.decode('utf-8', errors='ignore')
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting text from file: {str(e)}")
    finally:
        file.file.seek(0)  # Reset file pointer

def analyze_document_content(text: str, filename: str) -> dict:
    """Analyze document content to extract metadata and categorize"""
    try:
        # Use OpenAI to analyze the document content
        analysis_prompt = f"""Analyze this document and provide structured information about it.
        
Document filename: {filename}
Document content: {text[:2000]}...

Please provide a JSON response with:
- "title": A descriptive title for this document
- "category": The main category (e.g., "Policy", "Manual", "Guide", "Report", "Technical Documentation")
- "topics": List of 3-5 main topics/keywords covered
- "summary": A 2-3 sentence summary of the content
- "document_type": Type of document (e.g., "User Manual", "Business Process", "Technical Specification")

Respond only with valid JSON."""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=400,
            temperature=0.1
        )
        
        try:
            analysis = json.loads(response.choices[0].message.content)
            return analysis
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "title": filename.replace('.pdf', '').replace('.docx', '').replace('.txt', '').replace('_', ' ').title(),
                "category": "Document",
                "topics": ["general"],
                "summary": "Document content analysis unavailable",
                "document_type": "Unknown"
            }
    
    except Exception as e:
        print(f"Error analyzing document: {e}")
        return {
            "title": filename.replace('.pdf', '').replace('.docx', '').replace('.txt', '').replace('_', ' ').title(),
            "category": "Document", 
            "topics": ["general"],
            "summary": "Document uploaded successfully",
            "document_type": "Unknown"
        }

def chunk_document(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split document into overlapping chunks for better retrieval"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to end at a sentence boundary
        if end < len(text):
            # Look for sentence endings within the last 100 characters
            last_period = text.rfind('.', start + chunk_size - 100, end)
            last_newline = text.rfind('\n', start + chunk_size - 100, end)
            
            # Use the latest sentence/paragraph boundary
            boundary = max(last_period, last_newline)
            if boundary > start:
                end = boundary + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document into the knowledge base"""
    try:
        # Validate file type
        allowed_types = [
            "text/plain", 
            "application/pdf", 
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/markdown"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file.content_type} not supported. Supported: {', '.join(allowed_types)}"
            )
        
        # Generate unique document ID
        doc_id = str(uuid.uuid4())
        upload_time = datetime.datetime.now().isoformat()
        
        # Store original file in MinIO
        file_extension = os.path.splitext(file.filename)[1]
        minio_filename = f"{doc_id}_{file.filename}"
        
        # Read file content for both MinIO storage and text extraction
        file_content = await file.read()
        file_size = len(file_content)
        
        # Upload to MinIO
        try:
            minio_client.put_object(
                bucket_name,
                minio_filename,
                io.BytesIO(file_content),
                file_size,
                content_type=file.content_type
            )
            print(f"Uploaded {minio_filename} to MinIO")
        except S3Error as e:
            raise HTTPException(status_code=500, detail=f"Failed to store file in MinIO: {str(e)}")
        
        # Reset file for text extraction
        file.file = io.BytesIO(file_content)
        text_content = extract_text_from_file(file)
        
        if len(text_content.strip()) < 10:
            raise HTTPException(status_code=400, detail="File content is too short or empty")
        
        # Analyze document content using AI
        doc_analysis = analyze_document_content(text_content, file.filename)
        
        # Split document into chunks for better retrieval
        chunks = chunk_document(text_content)
        
        # Process each chunk separately
        chunk_ids = []
        for i, chunk in enumerate(chunks):
            # Generate unique ID for each chunk
            chunk_id = f"{doc_id}_chunk_{i}"
            chunk_ids.append(chunk_id)
            
            # Create embedding for this chunk
            embedding_response = openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=chunk
            )
            embedding = embedding_response.data[0].embedding
            
            # Enhanced metadata with AI analysis and MinIO reference
            metadata = {
                "document_id": doc_id,
                "filename": file.filename,
                "minio_filename": minio_filename,
                "content_type": file.content_type,
                "upload_time": upload_time,
                "size": file_size,
                "text_size": len(text_content),
                "chunk_index": i,
                "total_chunks": len(chunks),
                "title": doc_analysis.get("title", file.filename),
                "category": doc_analysis.get("category", "Document"),
                "document_type": doc_analysis.get("document_type", "Unknown"),
                "topics": ",".join(doc_analysis.get("topics", [])),
                "summary": doc_analysis.get("summary", "")
            }
            
            # Store chunk in ChromaDB
            collection.add(
                ids=[chunk_id],
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[metadata]
            )
        
        return {
            "message": "Document uploaded and analyzed successfully",
            "document_id": doc_id,
            "document_analysis": doc_analysis,
            "chunks_created": len(chunks),
            "chunk_ids": chunk_ids,
            "filename": file.filename,
            "minio_filename": minio_filename,
            "size": file_size,
            "upload_time": upload_time
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@app.get("/download/{doc_id}")
async def download_document(doc_id: str):
    """Download original document file from MinIO"""
    try:
        # Find document chunks to get MinIO filename
        results = collection.get(include=["metadatas"])
        minio_filename = None
        
        for i, chunk_id in enumerate(results["ids"]):
            if results["metadatas"] and i < len(results["metadatas"]) and results["metadatas"][i]:
                metadata = results["metadatas"][i]
                if metadata.get("document_id") == doc_id or chunk_id.startswith(doc_id):
                    minio_filename = metadata.get("minio_filename")
                    break
        
        if not minio_filename:
            raise HTTPException(status_code=404, detail="Document not found or no original file available")
        
        # Get file from MinIO
        try:
            response = minio_client.get_object(bucket_name, minio_filename)
            file_data = response.read()
            response.close()
            
            # Extract original filename from minio_filename (remove UUID prefix)
            original_filename = minio_filename.split('_', 1)[1] if '_' in minio_filename else minio_filename
            
            from fastapi.responses import Response
            return Response(
                content=file_data,
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={original_filename}"}
            )
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise HTTPException(status_code=404, detail="Original file not found in storage")
            else:
                raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error downloading document: {e}")
        raise HTTPException(status_code=500, detail="Error downloading document")

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from the knowledge base"""
    try:
        # Find all chunks for this document and get MinIO filename
        results = collection.get(include=["metadatas"])
        chunks_to_delete = []
        minio_filename = None
        
        for i, chunk_id in enumerate(results["ids"]):
            if results["metadatas"] and i < len(results["metadatas"]) and results["metadatas"][i]:
                metadata = results["metadatas"][i]
                if metadata.get("document_id") == doc_id or chunk_id.startswith(doc_id):
                    chunks_to_delete.append(chunk_id)
                    if not minio_filename:
                        minio_filename = metadata.get("minio_filename")
        
        if not chunks_to_delete:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from ChromaDB
        collection.delete(ids=chunks_to_delete)
        
        # Delete from MinIO if file exists
        if minio_filename:
            try:
                minio_client.remove_object(bucket_name, minio_filename)
                print(f"Deleted {minio_filename} from MinIO")
            except S3Error as e:
                print(f"Warning: Could not delete file from MinIO: {e}")
        
        return {
            "message": "Document deleted successfully", 
            "document_id": doc_id,
            "chunks_deleted": len(chunks_to_delete),
            "minio_file_deleted": bool(minio_filename)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Error deleting document")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)