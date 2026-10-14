"""Área do aluno. RN04: o aluno só enxerga os próprios dados (tudo parte do usuário logado).
Lê as tabelas por reflexão e aceita nomes de coluna alternativos; o que não puder ser lido vai em "avisos"."""
# pyright: reportMissingImports=false
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import exige_perfis
from ..models import Usuario
from ..reflexao import coluna, tabela
from ..schemas import AssinarPlanoIn, DadosAlunoIn, PagarIn
from ..services.academia import (FORMAS, checkin_aberto, criar_matricula, planos_ativos, quitar,
                                 registrar_entrada, registrar_saida, salvar_aluno, utc)
from ..services.alunos import aluno_do_usuario

log = logging.getLogger("gymai")
router = APIRouter(prefix="/meu", tags=["area do aluno"])
so_aluno = exige_perfis("aluno")


def _pk(t):
    return next(iter(t.primary_key.columns))


def _falta(*itens):
    if any(i is None for i in itens):
        raise LookupError("tabela ou coluna não encontrada")


def _get(m, *nomes):
    for n in nomes:
        if n in m and m[n] is not None:
            return m[n]
    return None


def _seguro(db: Session, avisos: list, rotulo_: str, fn, padrao):
    try:
        return fn()
    except Exception as erro:
        db.rollback()
        log.warning("area do aluno/%s: %s", rotulo_, erro)
        avisos.append(f"Não foi possível carregar “{rotulo_}”.")
        return padrao


CAMPOS_ALUNO = ("cpf", "data_nascimento", "sexo", "telefone", "altura_cm", "peso_kg")


def _perfil(aluno: dict | None) -> dict:
    """Dados que o aluno pode editar, como estão no banco."""
    return {k: (aluno or {}).get(k) for k in CAMPOS_ALUNO}


def _matricula(db: Session, aluno_id):
    mat = tabela("matriculas")
    al = coluna(mat, "aluno_id")
    _falta(mat, al)
    ini = coluna(mat, "data_inicio", "inicio")
    ordem = ini if ini is not None else _pk(mat)
    linha = db.execute(select(mat).where(al == aluno_id).order_by(ordem.desc()).limit(1)).first()
    if not linha:
        return None
    m = linha._mapping
    plano, valor = None, None
    planos, pf = tabela("planos"), coluna(mat, "plano_id")
    if planos is not None and pf is not None and m[pf.name] is not None:
        p = db.execute(select(planos).where(_pk(planos) == m[pf.name])).first()
        if p:
            plano, valor = p._mapping.get("nome"), p._mapping.get("valor")
    return {"plano": plano, "valor": valor,
            "inicio": _get(m, "data_inicio", "inicio"),
            "fim": _get(m, "data_fim", "fim", "data_vencimento", "vencimento"),
            "status": str(_get(m, "status", "situacao") or "").lower()}


def _ids_matriculas(db: Session, aluno_id) -> list:
    mat = tabela("matriculas")
    al = coluna(mat, "aluno_id")
    _falta(mat, al)
    return [l[0] for l in db.execute(select(_pk(mat)).where(al == aluno_id)).all()]


def _pagamentos(db: Session, aluno_id):
    pag = tabela("pagamentos")
    mf = coluna(pag, "matricula_id")
    venc = coluna(pag, "vencimento", "data_vencimento")
    _falta(pag, mf)
    ids = _ids_matriculas(db, aluno_id)
    if not ids:
        return []
    ordem = venc if venc is not None else _pk(pag)
    linhas = db.execute(select(pag).where(mf.in_(ids)).order_by(ordem.desc()).limit(12)).all()
    saida = []
    for l in linhas:
        m = l._mapping
        saida.append({"id": m[_pk(pag).name],
                      "valor": _get(m, "valor", "valor_pago"),
                      "forma": _get(m, "forma_pagamento"),
                      "vencimento": _get(m, "vencimento", "data_vencimento"),
                      "pago_em": _get(m, "data_pagamento", "pago_em"),
                      "status": str(_get(m, "status", "situacao") or "").lower()})
    return saida


def _checkins(db: Session, aluno_id):
    chk = tabela("checkins")
    af = coluna(chk, "aluno_id")
    dt = coluna(chk, "data_hora", "data_checkin", "data", "criado_em", "created_at")
    _falta(chk, af, dt)
    desde = func.now() - timedelta(days=30)
    total = db.scalar(select(func.count()).select_from(chk).where(af == aluno_id, dt >= desde)) or 0
    recentes = [utc(l[0]) for l in db.execute(select(dt).where(af == aluno_id).order_by(dt.desc()).limit(10)).all()]
    return {"ultimos_30_dias": total, "recentes": recentes}


@router.get("/resumo")
def resumo(db: Session = Depends(get_db), usuario: Usuario = Depends(so_aluno)):
    avisos: list = []
    base = {"usuario": {"nome": usuario.nome, "email": usuario.email}, "avisos": avisos,
            "vinculado": False, "numero_matricula": None, "perfil": _perfil(None), "matricula": None, "pagamentos": [],
            "checkins": {"ultimos_30_dias": 0, "recentes": []}}
    aluno = _seguro(db, avisos, "dados cadastrais", lambda: aluno_do_usuario(db, usuario), None)
    if aluno is None:
        return jsonable_encoder(base)
    aluno_id = aluno[_pk(tabela("alunos")).name]
    base["vinculado"] = True
    base["perfil"] = _perfil(aluno)
    base["numero_matricula"] = aluno.get("numero_matricula")
    base["matricula"] = _seguro(db, avisos, "matrícula", lambda: _matricula(db, aluno_id), None)
    base["pagamentos"] = _seguro(db, avisos, "pagamentos", lambda: _pagamentos(db, aluno_id), [])
    base["checkins"] = _seguro(db, avisos, "check-ins", lambda: _checkins(db, aluno_id), base["checkins"])
    return jsonable_encoder(base)


def _treinos(db: Session, aluno_id):
    tr, itens, ex = tabela("treinos"), tabela("treino_itens"), tabela("exercicios")
    af = coluna(tr, "aluno_id")
    _falta(tr, af)
    q = select(tr).where(af == aluno_id)
    if coluna(tr, "ativo") is not None:  # treinos arquivados pelo instrutor não aparecem
        q = q.where(tr.c.ativo.is_(True))
    treinos = db.execute(q.order_by(_pk(tr).desc()).limit(10)).all()
    tf = coluna(itens, "treino_id")
    ef = coluna(itens, "exercicio_id")
    ordem = coluna(itens, "ordem")
    nomes_ex: dict = {}
    todos_itens: dict = {}
    if itens is not None and tf is not None and treinos:
        ids = [t._mapping[_pk(tr).name] for t in treinos]
        q = select(itens).where(tf.in_(ids)).order_by(ordem if ordem is not None else _pk(itens))
        for l in db.execute(q).all():
            todos_itens.setdefault(l._mapping[tf.name], []).append(l._mapping)
        if ex is not None and ef is not None:
            ex_ids = {m[ef.name] for lista in todos_itens.values() for m in lista if m[ef.name] is not None}
            nome_ex = coluna(ex, "nome", "titulo")
            if ex_ids and nome_ex is not None:
                nomes_ex = dict(db.execute(select(_pk(ex), nome_ex).where(_pk(ex).in_(ex_ids))).all())
    saida = []
    for t in treinos:
        m = t._mapping
        tid = m[_pk(tr).name]
        saida.append({
            "id": tid,
            "nome": _get(m, "nome", "titulo", "descricao") or f"Treino #{tid}",
            "objetivo": _get(m, "objetivo"),
            "itens": [{"exercicio": nomes_ex.get(i[ef.name]) if ef is not None else None,
                       "series": _get(i, "series", "qtd_series", "num_series"),
                       "repeticoes": _get(i, "repeticoes", "reps", "qtd_repeticoes"),
                       "carga": _get(i, "carga_kg", "carga", "peso"),
                       "descanso": _get(i, "descanso_seg"),
                       "obs": _get(i, "observacao", "observacoes")} for i in todos_itens.get(tid, [])],
        })
    return saida


@router.get("/treinos")
def meus_treinos(db: Session = Depends(get_db), usuario: Usuario = Depends(so_aluno)):
    avisos: list = []
    aluno = _seguro(db, avisos, "cadastro do aluno", lambda: aluno_do_usuario(db, usuario), None)
    if aluno is None:
        return {"vinculado": False, "treinos": [], "avisos": avisos}
    aluno_id = aluno[_pk(tabela("alunos")).name]
    treinos = _seguro(db, avisos, "treinos", lambda: _treinos(db, aluno_id), [])
    return jsonable_encoder({"vinculado": True, "treinos": treinos, "avisos": avisos})

# ---- Ações do aluno: editar dados, check-in/check-out e pagamentos de exemplo ----

def _aluno(db: Session, usuario: Usuario) -> dict:
    aluno = aluno_do_usuario(db, usuario)
    if aluno is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Salve seus dados em “Meus dados” para liberar esta função.")
    return aluno


@router.put("/dados")
def salvar_dados(dados: DadosAlunoIn, db: Session = Depends(get_db), usuario: Usuario = Depends(so_aluno)):
    aluno = aluno_do_usuario(db, usuario)
    if aluno is None:  # conta sem cadastro de aluno: cria agora
        salvar_aluno(db, {"nome": usuario.nome, "email": usuario.email, "usuario_id": usuario.id, **dados.model_dump()})
    else:
        salvar_aluno(db, dados.model_dump(), aluno["id"])
    return jsonable_encoder(_perfil(aluno_do_usuario(db, usuario)))


def _registro(m) -> dict:
    return {"id": m["id"], "entrada": utc(m["data_hora"]), "saida": utc(m["data_saida"])}


@router.get("/checkins")
def meus_checkins(db: Session = Depends(get_db), usuario: Usuario = Depends(so_aluno)):
    aluno = _aluno(db, usuario)
    chk = tabela("checkins")
    aberto = checkin_aberto(db, aluno["id"])
    linhas = db.execute(select(chk).where(chk.c.aluno_id == aluno["id"])
                        .order_by(chk.c.data_hora.desc()).limit(15)).all()
    return jsonable_encoder({"aberto": _registro(aberto._mapping) if aberto else None,
                             "recentes": [_registro(l._mapping) for l in linhas]})


@router.post("/checkin", status_code=status.HTTP_201_CREATED)
def fazer_checkin(db: Session = Depends(get_db), usuario: Usuario = Depends(so_aluno)):
    registrar_entrada(db, _aluno(db, usuario)["id"])
    return meus_checkins(db, usuario)


@router.post("/checkout")
def fazer_checkout(db: Session = Depends(get_db), usuario: Usuario = Depends(so_aluno)):
    registrar_saida(db, _aluno(db, usuario)["id"])
    return meus_checkins(db, usuario)


@router.get("/planos")
def planos_disponiveis(db: Session = Depends(get_db), _=Depends(so_aluno)):
    return jsonable_encoder(planos_ativos(db))


@router.post("/matricula", status_code=status.HTTP_201_CREATED)
def assinar_plano(dados: AssinarPlanoIn, db: Session = Depends(get_db), usuario: Usuario = Depends(so_aluno)):
    nome = criar_matricula(db, _aluno(db, usuario)["id"], dados.plano_id)
    return {"mensagem": f"Plano {nome} contratado. Pague a primeira mensalidade para concluir."}


@router.post("/pagamentos/{pagamento_id}/pagar")
def pagar(pagamento_id: int, dados: PagarIn, db: Session = Depends(get_db), usuario: Usuario = Depends(so_aluno)):
    """Pagamento de EXEMPLO: nenhuma cobrança real é feita, só marca como pago."""
    quitar(db, pagamento_id, dados.forma, aluno_id=_aluno(db, usuario)["id"])
    return {"mensagem": f"Pagamento confirmado via {FORMAS[dados.forma]} (exemplo, sem cobrança real)."}
