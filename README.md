# Savant Assist MCP

A knowledge-based chatbot system built with FastAPI, ChromaDB, and OpenAI that provides intelligent responses using vector search and retrieval-augmented generation (RAG).

## 🚀 Features

- **Vector-Based Knowledge Base**: Uses ChromaDB for semantic search
- **OpenAI Integration**: Embeddings and GPT-3.5-turbo for intelligent responses
- **Real-time Chat**: React frontend with WhatsApp-style UI
- **Knowledge Base Viewer**: Web interface to explore and search the vector database
- **RESTful API**: FastAPI backend with comprehensive endpoints

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React UI      │────│  FastAPI Backend │────│   ChromaDB      │
│  (Port 3000)    │    │  (Port 8000)     │    │  Vector Store   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   OpenAI API     │    │  Knowledge Base │
                       │  • Embeddings    │    │  • 8 Documents  │
                       │  • GPT-3.5       │    │  • Embeddings   │
                       └──────────────────┘    └─────────────────┘
```

## 📦 Installation

### Prerequisites

- Python 3.9+
- Node.js 16+
- OpenAI API Key

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file:
```bash
OPENAI_API_KEY=your-openai-api-key-here
```

4. Start the backend server:
```bash
python main.py
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

## 🖥️ Usage

### Main Chat Interface
- **URL**: `http://localhost:3000`
- Features a WhatsApp-style chat interface
- Ask questions about warehouse management and inventory systems

### Knowledge Base Viewer
- **URL**: `http://localhost:8001`
- Explore the vector database
- Perform semantic searches
- View document statistics and embeddings

### API Documentation
- **URL**: `http://localhost:8000/docs`
- Interactive API documentation via Swagger UI

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

### Backend Stack
- **FastAPI**: Modern Python web framework
- **ChromaDB**: Vector database for embeddings
- **OpenAI API**: GPT-3.5-turbo and text-embedding-ada-002
- **Uvicorn**: ASGI server

### Frontend Stack
- **React**: User interface library
- **CSS3**: Styling with modern design
- **Fetch API**: HTTP client for backend communication

## 🚀 Extending the System

### Adding More Documents

1. Edit `kb_documents` in `main.py`:
```python
kb_documents = [
    {"id": "9", "text": "Your new document content..."},
    # Add more documents
]
```

2. Restart the backend to process new embeddings

## 📄 License

This project is open source and available under the MIT License.
