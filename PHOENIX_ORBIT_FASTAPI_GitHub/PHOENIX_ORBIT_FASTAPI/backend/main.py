import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from core import answer_question, index_pdf_bytes, list_documents

app = FastAPI(title="PHOENIX AI API", version="1.0.0")
origins = os.getenv("FRONTEND_ORIGINS", "*").split(",")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in origins if x.strip()], allow_credentials=False, allow_methods=["GET","POST"], allow_headers=["*"])

class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=10)

@app.get("/")
def home():
    return {"service":"PHOENIX AI API","status":"online","docs":"/docs"}
@app.get("/health")
def health():
    return {"status":"ok"}
@app.get("/documents")
def documents():
    return {"documents":list_documents()}
@app.post("/chat")
def chat(req: ChatRequest):
    try: return answer_question(req.question, req.top_k)
    except RuntimeError as e: raise HTTPException(status_code=503, detail=str(e))
    except Exception: raise HTTPException(status_code=500, detail="No se pudo procesar la consulta.")
@app.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten PDF.")
    data = await file.read()
    if len(data) > 25*1024*1024: raise HTTPException(status_code=413, detail="Máximo 25 MB.")
    try:
        count, message = index_pdf_bytes(file.filename, data)
        return {"filename":file.filename,"chunks_indexed":count,"message":message}
    except RuntimeError as e: raise HTTPException(status_code=503, detail=str(e))
    except Exception: raise HTTPException(status_code=500, detail="No se pudo indexar el documento.")
