from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
import openai
import os
import uuid
import datetime
from typing import List, Optional
from dotenv import load_dotenv
import PyPDF2
import docx
import io
from minio import Minio
from minio.error import S3Error
import aiofiles

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

# Initialize ChromaDB (connect to containerized service)
chromadb_host = os.getenv("CHROMADB_HOST", "localhost")
chromadb_port = int(os.getenv("CHROMADB_PORT", "8001"))
chroma_client = chromadb.HttpClient(host=chromadb_host, port=chromadb_port)
collection = None

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
    try:
        doc_count = collection.count() if collection else 0
        return {"status": "healthy", "kb_docs": doc_count}
    except:
        return {"status": "healthy", "kb_docs": 0}

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
        
        import json
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

@app.get("/documents")
async def list_documents():
    """List all documents in the knowledge base"""
    try:
        results = collection.get(include=["metadatas", "documents"])
        
        # Group chunks by document_id to show as single documents
        document_groups = {}
        for i, doc_id in enumerate(results["ids"]):
            # Handle cases where metadatas might be None or contain None values
            metadata = {}
            if results["metadatas"] and i < len(results["metadatas"]) and results["metadatas"][i]:
                metadata = results["metadatas"][i]
            
            content = results["documents"][i] if results["documents"] and i < len(results["documents"]) else ""
            
            # Use document_id for grouping, fallback to filename or doc_id
            document_id = metadata.get("document_id")
            if not document_id:
                document_id = doc_id.split('_chunk_')[0] if '_chunk_' in doc_id else doc_id
            
            filename = metadata.get("filename", f"document_{document_id[:8]}")
            
            if document_id not in document_groups:
                document_groups[document_id] = {
                    "id": document_id,
                    "filename": filename,
                    "minio_filename": metadata.get("minio_filename", ""),
                    "content_type": metadata.get("content_type", "text/plain"),
                    "upload_time": metadata.get("upload_time", ""),
                    "size": metadata.get("size", 0),
                    "text_size": metadata.get("text_size", 0),
                    "title": metadata.get("title", filename),
                    "category": metadata.get("category", "Document"),
                    "document_type": metadata.get("document_type", "Unknown"),
                    "topics": metadata.get("topics", "").split(",") if metadata.get("topics") else [],
                    "summary": metadata.get("summary", ""),
                    "chunks": 0,
                    "preview": "",
                    "has_minio_file": bool(metadata.get("minio_filename"))
                }
            
            # Update chunk count and preview
            document_groups[document_id]["chunks"] += 1
            if not document_groups[document_id]["preview"]:
                document_groups[document_id]["preview"] = content[:200] + "..." if len(content) > 200 else content
        
        documents = list(document_groups.values())
        return {"documents": documents, "total": len(documents)}
    
    except Exception as e:
        print(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving documents")

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