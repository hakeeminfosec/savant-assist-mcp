# Chat Backend (FastAPI)

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the FastAPI server:
   ```bash
   python main.py
   ```

The server will start on `http://localhost:8000`

## API Endpoints

- **POST** `/chat`
  - Request: `{"message": "your message"}`
  - Response: `{"response": "your message"}`