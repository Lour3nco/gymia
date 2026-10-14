"""As demais tabelas (alunos, checkins, matriculas, pagamentos, previsoes_evasao...) são lidas
direto do banco, sem precisar declarar models. coluna() aceita nomes alternativos."""
from functools import lru_cache

from sqlalchemy import MetaData

from .database import DB_SCHEMA, engine


@lru_cache(maxsize=1)
def _meta() -> MetaData:
    meta = MetaData(schema=DB_SCHEMA)
    meta.reflect(bind=engine)
    return meta


def tabela(nome: str):
    return _meta().tables.get(f"{DB_SCHEMA}.{nome}")


def coluna(tab, *candidatos: str):
    """Primeira coluna existente entre os nomes candidatos (ou None)."""
    if tab is None:
        return None
    for nome in candidatos:
        if nome in tab.c:
            return tab.c[nome]
    return None
