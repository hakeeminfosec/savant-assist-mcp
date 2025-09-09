# Savant Assist MCP

A comprehensive AI-powered document management system built with FastAPI, ChromaDB, and OpenAI. Features semantic search, document analytics, and intelligent chat capabilities using advanced vector embeddings and retrieval-augmented generation (RAG).

## 🚀 Features

- **🧠 AI Semantic Search**: OpenAI text-embedding-ada-002 with 1536-dimensional vectors
- **📄 Document Management**: Upload, organize, and explore document collections
- **🔍 Dual Interface Architecture**: Admin panel for grouped documents, viewer for individual chunks
- **💬 Intelligent Chat**: RAG-powered conversational AI with context awareness
- **📊 Analytics Dashboard**: Document statistics, metadata insights, and search analytics
- **🐳 Containerized Deployment**: Full Docker orchestration with MinIO and ChromaDB
- **🎨 Modern UI**: Clean, responsive interface optimized for semantic search workflows

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Admin Panel    │    │  FastAPI Backend │    │   ChromaDB      │
│  (Port 3000)    │────│  (Port 8002)     │────│  (Port 8001)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        
┌─────────────────┐             │               
│ ChromaDB Viewer │─────────────┘               
│  (Port 8080)    │                             
└─────────────────┘                             
                                │
                       ┌──────────────────┐    ┌─────────────────┐
                       │   OpenAI API     │    │     MinIO       │
                       │  • Embeddings    │    │  File Storage   │
                       │  • GPT-4         │    │  (Port 9000)    │
                       └──────────────────┘    └─────────────────┘
```

## 📦 Installation

### Prerequisites

- Docker & Docker Compose
- OpenAI API Key

### Quick Start with Docker

1. Clone the repository:
```bash
git clone https://github.com/hakeeminfosec/savant-assist-mcp.git
cd savant-assist-mcp
```

2. Set your OpenAI API key:
```bash
# Create backend/.env file
echo "OPENAI_API_KEY=your-openai-api-key-here" > backend/.env
```

3. Start all services:
```bash
docker-compose up -d
```

4. Wait for services to initialize (about 2 minutes), then access:
   - **Admin Panel**: http://localhost:3000
   - **ChromaDB Viewer**: http://localhost:8080
   - **Backend API**: http://localhost:8002

### Manual Development Setup

If you prefer running without Docker:

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
echo "OPENAI_API_KEY=your-key-here" > .env
python main.py
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

#### ChromaDB Viewer Setup
```bash
cd chromadb-viewer
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8080
```

## 🖥️ Usage

### Admin Panel (Document Management)
- **URL**: `http://localhost:3000`
- Upload and manage documents
- View grouped documents with metadata
- Modern chat interface with RAG capabilities
- Document analytics and insights

### ChromaDB Viewer (Semantic Search)
- **URL**: `http://localhost:8080`
- AI-powered semantic search interface
- Explore individual document chunks
- View similarity scores and embeddings
- Clean, focused search experience

### API Documentation
- **URL**: `http://localhost:8002/docs`
- Interactive API documentation via FastAPI Swagger UI
- Test all endpoints including search, chat, and file operations

## 💬 Sample Questions

Try asking these questions in the chat:

- "What is wave picking?"
- "How does FIFO inventory work?"
- "Explain cycle counting"
- "What is cross-docking?"
- "How does ABC analysis work?"

## 📊 Knowledge Base

The system currently includes 8 documents covering:

1. **Wave Picking** - Warehouse management method
2. **FIFO** - First-In-First-Out inventory method
3. **Cycle Counting** - Inventory auditing process
4. **Cross-docking** - Logistics practice
5. **ABC Analysis** - Inventory categorization
6. **JIT Inventory** - Just-in-time strategy
7. **WMS** - Warehouse Management System
8. **Barcode Scanning** - Product information capture

## 🔧 Technical Details

### Core Technologies
- **FastAPI**: Modern Python web framework with automatic API documentation
- **ChromaDB**: Vector database for semantic embeddings storage
- **OpenAI API**: GPT-4 for chat and text-embedding-ada-002 for 1536D vectors
- **MinIO**: S3-compatible object storage for file management
- **Docker**: Containerized deployment with service orchestration

### Frontend Stack
- **React**: User interface library with modern hooks
- **CSS3**: Clean, responsive styling with modern design patterns
- **Fetch API**: HTTP client for seamless backend communication

### AI/ML Stack
- **Vector Embeddings**: 1536-dimensional OpenAI text-embedding-ada-002
- **Semantic Search**: Hybrid search with BM25 and vector similarity
- **RAG Pipeline**: Retrieval-augmented generation for contextual responses
- **Document Processing**: Intelligent chunking and metadata extraction

## 🚀 Extending the System

### Adding Documents

#### Via Web Interface (Recommended)
1. Access the Admin Panel at `http://localhost:3000`
2. Use the upload functionality to add new documents
3. Documents are automatically processed and embedded

#### Via API
```bash
curl -X POST "http://localhost:8002/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your-document.pdf"
```

### Configuration

#### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `MINIO_ENDPOINT`: MinIO server endpoint
- `CHROMADB_HOST`: ChromaDB server host
- `CHROMADB_PORT`: ChromaDB server port

#### Docker Services
- Modify `docker-compose.yml` to adjust ports or add services
- Scale services: `docker-compose up -d --scale backend=2`

## 📄 License

This project is open source and available under the MIT License.
