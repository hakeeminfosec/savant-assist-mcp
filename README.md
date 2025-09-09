# Savant Assist MCP v1.0

A comprehensive AI-powered document management and chat system with modern UI and advanced ChromaDB viewer, built on MCP (Message Communication Protocol) architecture.

## 🚀 Features

### 💬 **Intelligent Chat Interface**
- Modern, responsive chat UI with streaming responses
- Real-time context awareness for natural conversations
- Advanced message formatting with syntax highlighting
- Smart document retrieval with semantic search

### 📚 **Advanced Document Management**
- **Multi-format support**: PDF, DOCX, TXT files
- **Intelligent processing**: Automatic text extraction and chunking
- **Vector embeddings**: Semantic search capabilities
- **AI-powered analysis**: Automatic categorization and topic extraction
- **MinIO integration**: Scalable cloud-native file storage

### 🔍 **Professional ChromaDB Viewer**
- **Beautiful web interface**: Modern gradient design with glass morphism
- **Smart pagination**: 10/25/50/100 documents per page with navigation
- **Semantic search**: AI-powered similarity matching with percentage scores
- **Document cards**: Clean, compact cards with essential information
- **Detail view**: Full document content with metadata on separate pages
- **Mobile responsive**: Works perfectly on all devices

### ⚡ **High-Performance Architecture**
- **FastAPI backend**: High-performance async API
- **React frontend**: Modern, responsive SPA
- **ChromaDB**: Efficient vector database (containerized)
- **Docker containerization**: Complete containerized deployment
- **MinIO**: S3-compatible object storage with web console

## 🏗 **Architecture**

```
Frontend (React) ←→ Backend (FastAPI) ←→ ChromaDB (Container)
                            ↓                    ↑
                      MinIO (Container)    ChromaDB Viewer
                            ↓                (Port 8080)
                    OpenAI API (Embeddings)
```

## 🚀 **Quick Start**

### Prerequisites
- Docker and Docker Compose
- OpenAI API key

### 1. **Environment Setup**
```bash
cd backend
echo "OPENAI_API_KEY=your-openai-api-key-here" > .env
```

### 2. **Start All Services**
```bash
# Start containers (MinIO, ChromaDB, ChromaDB Viewer)
docker-compose up -d

# Start backend
cd backend
pip install -r requirements.txt
python main.py

# Start frontend (new terminal)
cd frontend
npm install
npm start
```

### 3. **Access Applications**
- **Chat Interface**: http://localhost:3000
- **Admin Panel**: http://localhost:3000/admin
- **ChromaDB Viewer**: http://localhost:8080 ⭐
- **Backend API**: http://localhost:8002/docs
- **MinIO Console**: http://localhost:9001 (admin/minio123456)

## 🎨 **ChromaDB Viewer Features**

### **Beautiful Interface**
- 🎨 Gradient backgrounds with glass morphism effects
- 📱 Fully responsive design (mobile-optimized)
- 🃏 Clean, compact document cards
- 🔍 Professional search interface

### **Smart Search & Pagination**
- 🎯 **Semantic search** with AI similarity matching
- 📊 **Match percentages** (90%+ high, 60-79% medium, <60% low)
- 📄 **Smart pagination** with customizable page sizes
- 🔀 **Sort by relevance** with visual indicators

### **Document Management**
- 📋 **Card view**: Shows document number, ID, word count
- 🔍 **"View More"**: Full document content on detail page
- 📊 **Metadata display**: Complete document metadata
- 🏠 **Breadcrumb navigation**: Easy navigation between views

## 📖 **Usage Guide**

### **Document Upload (Admin Panel)**
1. Go to http://localhost:3000/admin
2. Upload documents (PDF, DOCX, TXT)
3. Files are processed and vectorized automatically

### **ChromaDB Viewer**
1. Visit http://localhost:8080
2. Browse document cards with pagination
3. **Search**: Type queries like "inventory management"
4. **View details**: Click "View More" for full content
5. **Navigate**: Use page numbers or Previous/Next

### **Chat Interface**
1. Go to http://localhost:3000
2. Ask natural language questions
3. Get AI responses with document context

## 🐳 **Docker Services**

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | React UI |
| Backend | 8002 | FastAPI server |
| ChromaDB | 8001 | Vector database |
| **ChromaDB Viewer** | **8080** | **Web interface** ⭐ |
| MinIO API | 9000 | Object storage |
| MinIO Console | 9001 | Storage web UI |

## 🎯 **Search Examples**

Try these in the ChromaDB Viewer:
- `warehouse management` - Find management-related docs
- `inventory` - Discover inventory concepts  
- `FIFO` - Exact term matching
- `optimization strategies` - Multi-word semantic search

## 📊 **Project Structure**

```
├── backend/              # FastAPI application
├── frontend/             # React application  
├── chromadb-viewer/      # ChromaDB web viewer ⭐
├── docker-compose.yml    # Container orchestration
└── README.md            # This file
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Backend (.env)
OPENAI_API_KEY=your-key-here
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=minio123456
```

## 🔐 **Security & Performance**

- **CORS protection**: Configured origins
- **File validation**: Size and type checking
- **Error handling**: Comprehensive exception management
- **Docker optimization**: Multi-stage builds and layer caching
- **Responsive design**: Mobile-first approach

## 🆘 **Troubleshooting**

### **Common Issues**
1. **Port conflicts**: Check ports 3000, 8001, 8002, 8080, 9000, 9001
2. **OpenAI API**: Verify API key and credits
3. **Docker issues**: `docker-compose down && docker-compose up -d`
4. **ChromaDB connection**: Ensure container is running

### **Service Status**
```bash
docker-compose ps                    # Check all services
docker-compose logs chromadb-viewer  # View ChromaDB viewer logs  
docker-compose logs backend         # View backend logs
```

---

**Built with**: FastAPI, React, ChromaDB, MinIO, OpenAI, Docker
**Special Feature**: Professional ChromaDB Viewer with semantic search 🎯