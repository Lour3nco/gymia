import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Usuario
from .perfis import normalizar_perfil
from .security import ler_token

bearer = HTTPBearer(auto_error=False)


def usuario_atual(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Faça login para continuar.")
    try:
        dados = ler_token(cred.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão expirada. Entre novamente.")
    usuario = db.get(Usuario, int(dados["sub"]))
    if not usuario or not usuario.ativo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário inválido.")
    return usuario


def exige_perfis(*perfis: str):  # RF02
    def checar(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
        if normalizar_perfil(usuario.perfil) not in perfis:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Seu perfil não tem acesso a esta função.")
        return usuario

    return checar
