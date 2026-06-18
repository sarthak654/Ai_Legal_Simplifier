# How to Start the AI Legal Simplifier

## Quick Setup (5 minutes)

### 1. Install Ollama
- Download from https://ollama.ai and install
- Open a terminal and pull the model based on your GPU VRAM:

  | VRAM | Recommended Model | Command |
  |------|-------------------|---------|
  | 4 GB | qwen2.5:3b (default) | `ollama pull qwen2.5:3b` |
  | 6 GB+ | gemma3:4b | `ollama pull gemma3:4b` |
  | 8 GB+ | gemma3:12b | `ollama pull gemma3:12b` |

  > The default config uses `qwen2.5:3b`. If you want a different model, update `OLLAMA_MODEL` in `backend/app/config.py`.

### 2. Set Up the Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> `requirements.txt` installs everything the backend needs:
> FastAPI, Uvicorn, pdfplumber (PDF reading), sentence-transformers (embeddings),
> faiss-cpu (vector search), ollama (local LLM), pydantic, numpy, and more.

### 3. Set Up the Frontend

```powershell
cd frontend
npm install
```

### 4. Start the App (3 terminals needed)

**Terminal 1 — Ollama:**
```bash
ollama serve
```

**Terminal 2 — Backend:**
```powershell
cd backend
venv\Scripts\activate
python -m app.main
```

**Terminal 3 — Frontend:**
```powershell
cd frontend
npm run dev
```

### 5. Open the App
Go to: **http://localhost:3000**

---

## How to Use
1. Upload a PDF legal document
2. Wait for analysis (30–60 seconds)
3. Review simplified clauses and risk levels
4. Ask questions about the document

---

## Troubleshooting

- **venv activation error (PowerShell)**: Run this once, then retry:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

- **pip install errors**: Make sure the venv is activated (you should see `(venv)` in your prompt), then run:
  ```powershell
  pip install -r requirements.txt
  ```

- **Ollama error**: Make sure `ollama serve` is running in its own terminal and the model pull completed. If you see a memory error in the backend logs, your GPU doesn't have enough VRAM — switch to a smaller model (see step 1 above)

- **Port conflict**: Kill processes on ports 8000 (backend) and 3000 (frontend)

- **PDF error**: Use text-based PDFs only (not scanned images)
