# pyright: reportMissingImports=false

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import CORS_ORIGINS
from .database import DB_SCHEMA, get_db
from .routers import (aluno, auth, dashboard, financeiro, gestao_alunos, planos, postura, recepcao, relatorios,
                      treinos, usuarios)

app = FastAPI(title="GymAI API")

app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(aluno.router)
app.include_router(dashboard.router)
for r in (gestao_alunos, planos, financeiro, recepcao, treinos, postura, relatorios):
    app.include_router(r.router)


@app.get("/saude")
def saude(db: Session = Depends(get_db)):
    db.execute(text("select 1"))  # falha com 500 se o banco estiver inacessível
    return {"status": "ok", "schema": DB_SCHEMA}