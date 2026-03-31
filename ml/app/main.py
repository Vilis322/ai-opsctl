"""FastAPI ML Service — inference, RAG, and training."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.models import router as models_router

app = FastAPI(
    title="OpsCtl AI — ML Service",
    description="Inference, RAG, and training endpoints. All data is 100% synthetic.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router)
app.include_router(models_router)


@app.get("/ml/health")
async def health():
    return {"ok": True, "service": "ml", "synthetic_data": True}
