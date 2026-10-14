from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import exige_perfis
from ..models import Usuario
from ..perfis import normalizar_perfil, perfil_para_banco
from ..schemas import UsuarioAlterarIn, UsuarioCriarIn, UsuarioListaOut
from ..services.alunos import vincular_aluno
from ..services.usuarios import criar_usuario

so_admin = exige_perfis("administrador")
router = APIRouter(prefix="/usuarios", tags=["usuarios"], dependencies=[Depends(so_admin)])


def _out(u: Usuario) -> UsuarioListaOut:
    return UsuarioListaOut(id=u.id, nome=u.nome, email=u.email, perfil=normalizar_perfil(u.perfil), ativo=u.ativo)


@router.get("", response_model=list[UsuarioListaOut])
def listar(db: Session = Depends(get_db)):
    return [_out(u) for u in db.scalars(select(Usuario).order_by(Usuario.nome)).all()]


@router.post("", response_model=UsuarioListaOut, status_code=status.HTTP_201_CREATED)
def criar(dados: UsuarioCriarIn, db: Session = Depends(get_db)):
    # o administrador é confiável: conta de aluno pode ser ligada à ficha pelo e-mail
    return _out(criar_usuario(db, dados.nome, dados.email, dados.senha, dados.perfil, por_email=True))


@router.patch("/{usuario_id}", response_model=UsuarioListaOut)
def alterar(usuario_id: int, dados: UsuarioAlterarIn, db: Session = Depends(get_db),
            admin: Usuario = Depends(so_admin)):
    """Aprovar/desativar conta e trocar o perfil."""
    u = db.get(Usuario, usuario_id)
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado.")
    if u.id == admin.id and (dados.ativo is False or dados.perfil not in (None, "administrador")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Você não pode desativar nem rebaixar a própria conta.")
    virou_aluno = dados.perfil == "aluno" and normalizar_perfil(u.perfil) != "aluno"
    if dados.perfil is not None:
        u.perfil = perfil_para_banco(dados.perfil)
    if dados.ativo is not None:
        u.ativo = dados.ativo
    db.commit()
    db.refresh(u)
    if virou_aluno:
        vincular_aluno(db, u, por_email=True)
    return _out(u)
