"""Dashboard (RF09). Lê as tabelas do banco por reflexão e aceita nomes de coluna alternativos.
Se algum indicador não puder ser calculado, o valor fica zerado e o motivo vai em "avisos"."""
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import Date, String, cast, func, literal, or_, select
from sqlalchemy.orm import Session

from ..ai import churn
from ..database import get_db
from ..deps import exige_perfis
from ..reflexao import coluna, tabela
from ..schemas import AlunoRisco, CheckinDia, DashboardOut
from ..services.academia import atualizar_atrasados, dia_local, hoje as hoje_local

log = logging.getLogger("gymai")
router = APIRouter(prefix="/dashboard", tags=["dashboard"])
DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
acesso = exige_perfis("administrador", "recepcao", "instrutor")

ATIVO, PAGO, ATRASADO = ("ativa", "ativo"), ("pago", "paga"), ("atrasado", "atrasada")


def _txt(col):
    return func.lower(cast(col, String))


def _falta(*itens):
    if any(i is None for i in itens):
        raise LookupError("tabela ou coluna não encontrada")


def _seguro(db, avisos, rotulo, fn, padrao):
    try:
        return fn()
    except Exception as erro:
        db.rollback()
        log.warning("dashboard/%s: %s", rotulo, erro)
        avisos.append(f"Não foi possível calcular “{rotulo}”: confira os nomes das colunas no banco.")
        return padrao


@router.get("", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), _=Depends(acesso)):
    hoje = hoje_local()
    avisos: list[str] = []
    _seguro(db, avisos, "mensalidades atrasadas", lambda: atualizar_atrasados(db), None)

    def alunos_ativos():
        mat = tabela("matriculas")
        st, al = coluna(mat, "status", "situacao"), coluna(mat, "aluno_id")
        if st is not None and al is not None:
            q = select(func.count(func.distinct(al))).where(_txt(st).in_(ATIVO))
            fim = coluna(mat, "data_fim", "fim")
            if fim is not None:  # matrícula "ativa" com data de fim passada já venceu: não conta
                q = q.where(or_(fim.is_(None), cast(fim, Date) >= hoje))
            return db.scalar(q) or 0
        alu = tabela("alunos")
        _falta(alu)
        q = select(func.count()).select_from(alu)
        ativo = coluna(alu, "ativo")
        if ativo is not None:
            q = q.where(ativo.is_(True))
        return db.scalar(q) or 0

    def receita():
        pag = tabela("pagamentos")
        val, st = coluna(pag, "valor", "valor_pago"), coluna(pag, "status", "situacao")
        dt = coluna(pag, "data_pagamento", "pago_em")
        _falta(val, st, dt)
        return float(db.scalar(select(func.coalesce(func.sum(val), 0)).where(
            _txt(st).in_(PAGO), cast(dt, Date) >= hoje.replace(day=1))) or 0)

    def inadimplencia():
        pag = tabela("pagamentos")
        st, venc = coluna(pag, "status", "situacao"), coluna(pag, "vencimento", "data_vencimento")
        _falta(pag, st)
        atrasados = db.scalar(select(func.count()).select_from(pag).where(_txt(st).in_(ATRASADO))) or 0
        q = select(func.count()).select_from(pag).where(_txt(st) != "cancelado")  # cancelada não é cobrança
        if venc is not None:
            q = q.where(cast(venc, Date) <= hoje)
        total = db.scalar(q) or 0
        return (round(atrasados / total * 100, 1) if total else 0.0), atrasados

    def checkins():
        chk = tabela("checkins")
        dt = coluna(chk, "data_hora", "data_checkin", "data", "criado_em", "created_at")
        _falta(chk, dt)
        dia = dia_local(dt)
        linhas = db.execute(select(dia, func.count()).where(dia >= hoje - timedelta(days=6)).group_by(dia)).all()
        mapa = {d: n for d, n in linhas}
        dias = [hoje - timedelta(days=i) for i in range(6, -1, -1)]
        return [CheckinDia(dia=DIAS[d.weekday()], total=mapa.get(d, 0)) for d in dias], mapa.get(hoje, 0)

    def em_risco():
        prev, alu = tabela("previsoes_evasao"), tabela("alunos")
        pc = coluna(prev, "probabilidade", "probabilidade_evasao", "prob")
        ai = coluna(prev, "aluno_id")
        dc = coluna(prev, "data", "data_previsao", "calculado_em", "criado_em")
        mt = coluna(prev, "motivo", "detalhes", "observacao")
        _falta(prev, pc, ai)
        q = select(ai, pc, mt if mt is not None else literal("").label("motivo"))
        if dc is not None:
            q = q.where(dc == select(func.max(dc)).scalar_subquery())
        linhas = db.execute(q.order_by(pc.desc()).limit(5)).all()
        nomes = {}
        id_col, nome_col = coluna(alu, "id"), coluna(alu, "nome")
        if linhas and id_col is not None and nome_col is not None:
            nomes = dict(db.execute(select(id_col, nome_col).where(id_col.in_([l[0] for l in linhas]))).all())
        saida = []
        for aluno_id, prob, motivo in linhas:
            p = float(prob)
            p = p * 100 if p <= 1 else p
            saida.append(AlunoRisco(id=aluno_id, nome=nomes.get(aluno_id, f"Aluno #{aluno_id}"),
                                    probabilidade=round(p), motivo=motivo or ""))
        return saida

    ativos = _seguro(db, avisos, "alunos ativos", alunos_ativos, 0)
    receita_mes = _seguro(db, avisos, "receita do mês", receita, 0.0)
    inad_pct, atrasados = _seguro(db, avisos, "inadimplência", inadimplencia, (0.0, 0))
    por_dia, hoje_n = _seguro(db, avisos, "check-ins", checkins,
                              ([CheckinDia(dia=DIAS[(hoje - timedelta(days=i)).weekday()], total=0)
                                for i in range(6, -1, -1)], 0))
    risco = _seguro(db, avisos, "alunos em risco", em_risco, [])

    return DashboardOut(
        alunos_ativos=ativos, receita_mes=receita_mes, inadimplencia_pct=inad_pct,
        pagamentos_atrasados=atrasados, checkins_hoje=hoje_n, checkins_por_dia=por_dia,
        alunos_em_risco=risco, dispositivo_ia=str(churn.dispositivo()), avisos=avisos,
    )


@router.get("/benchmark")  # RF12 (versão inicial)
def benchmark(_=Depends(exige_perfis("administrador", "instrutor"))):
    return churn.benchmark()
