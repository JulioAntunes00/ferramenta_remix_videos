"""
Aplicação Principal FastAPI.
Configuração de CORS, montagem de rotas e ciclo de vida.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router

app = FastAPI(
    title="Remix Vídeos API",
    description="Motor modular de combinação de criativos em vídeo com sanitização Anti-Ban",
    version="1.0.0"
)

# Permitir requisições do frontend local e futuras origens
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
def health_check():
    return {"status": "ok", "service": "Remix Vídeos Core Engine"}
