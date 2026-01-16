# How to Start the AI Legal Simplifier

## Quick Setup (5 minutes)

### 1. Install Ollama
- Download from https://ollama.ai and install
- Open terminal and run: `ollama pull gemma3:12b` (or use your existing model)

### 2. Install Dependencies
```bash
# Backend - Install one by one to avoid conflicts
cd backend
pip install --upgrade pip setuptools wheel
pip install fastapi uvicorn python-multipart
pip install pdfplumber sentence-transformers
pip install faiss-cpu numpy ollama
pip install pydantic python-dotenv

# Frontend  
cd ../frontend
npm install
```

### 3. Start the App (3 terminals needed)

**Terminal 1 - Start Ollama:**
```bash
ollama serve
```

**Terminal 2 - Start Backend:**
```bash
cd backend
python -m app.main
```

**Terminal 3 - Start Frontend:**
```bash
cd frontend
npm run dev
```

### 4. Open App
Go to: **http://localhost:3000**

## How to Use
1. Upload a PDF legal document
2. Wait for analysis (30-60 seconds)
3. Review simplified clauses and risk levels
4. Ask questions about the document

## Troubleshooting
- **Python/pip errors**: Try installing packages individually (see step 2 above)
- **Ollama error**: Make sure `ollama serve` is running and `ollama pull gemma2:12b` completed
- **Port error**: Kill processes on ports 8000 and 3000
- **PDF error**: Use text-based PDFs only (not scanned images)
- **Still having issues**: Try creating a virtual environment:
  ```bash
  python -m venv venv
  # Windows: venv\Scripts\activate
  # Mac/Linux: source venv/bin/activate
  ```

That's it! 🎉