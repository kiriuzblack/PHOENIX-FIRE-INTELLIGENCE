
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from backend.ai_bridge import consultar_ia
from backend.data_routes import router as data_router



app = FastAPI(title="PHOENIX FIRE INTELLIGENCE API")

app.include_router(data_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    experiment_ids: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict] = Field(default_factory=list)
    grounded: bool = False


@app.get("/health")
def health():
    return {"status": "ok", "project": "PHOENIX"}


@app.post("/api/ai/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        return consultar_ia(
            request.question,
            request.experiment_ids
        )
    except Exception as error:
        print(f"Error de IA: {type(error).__name__}")
        raise HTTPException(
            status_code=502,
            detail="No fue posible obtener la respuesta de la IA."
        )

