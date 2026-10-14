# pyright: reportMissingImports=false
from fastapi import HTTPException, status  # type: ignore[import-not-found]
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Usuario
from ..perfis import perfil_para_banco
from ..security import hash_senha
from .alunos import vincular_aluno


def criar_usuario(db: Session, nome: str, email: str, senha: str, perfil: str, ativo: bool = True,
                  ficha_id=None, cpf: str | None = None, por_email: bool = False) -> Usuario:
    """ficha_id/cpf/por_email: como ligar a conta de aluno à ficha (ver services/alunos.vincular_aluno)."""
    email = email.strip().lower()
    if len(email) > 150:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "E-mail muito longo (máximo 150 caracteres).")
    if db.scalar(select(Usuario.id).where(func.lower(Usuario.email) == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma conta com este e-mail.")
    try:
        perfil_db = perfil_para_banco(perfil)
    except ValueError as erro:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(erro))
    usuario = Usuario(nome=nome.strip(), email=email, senha_hash=hash_senha(senha), perfil=perfil_db, ativo=ativo)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    if perfil == "aluno":
        vincular_aluno(db, usuario, ficha_id=ficha_id, cpf=cpf, por_email=por_email)
    return usuario
