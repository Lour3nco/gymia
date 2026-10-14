import { useEffect, useState } from "react";
import api, { mensagemErro } from "../api";
import { cpfMascara, data } from "../formato";

// Situação resumida do aluno (vem de GET /alunos)
export function SituacaoAluno({ a }) {
  if (a.atrasados > 0) return <span className="chip atrasado">{a.atrasados} em atraso</span>;
  if (a.vigente) return <span className="chip ativa">Plano até {data(a.matricula_fim)}</span>;
  if (a.matricula_status) return <span className="chip pendente">Sem plano ativo</span>;
  return <span className="chip">Sem matrícula</span>;
}

// Campo de busca de aluno; acao(aluno) desenha o botão de cada resultado.
// Mudar "versao" refaz a busca (ex.: depois de um check-in).
export default function BuscaAluno({ acao, versao = 0, rotulo = "Buscar aluno" }) {
  const [busca, setBusca] = useState("");
  const [lista, setLista] = useState(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    if (busca.trim().length < 2) { setLista(null); return undefined; }
    const id = setTimeout(() => {
      api.get("/alunos", { params: { busca } })
        .then((r) => { setErro(""); setLista(r.data.slice(0, 8)); })
        .catch((e) => setErro(mensagemErro(e)));
    }, 300);
    return () => clearTimeout(id);
  }, [busca, versao]);

  return (
    <div className="busca">
      <label>{rotulo}
        <input type="search" value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Nome, e-mail, CPF ou nº de matrícula" />
      </label>
      <div className="err" role="alert">{erro}</div>
      {lista && (
        <ul className="resultados">
          {lista.map((a) => (
            <li key={a.id}>
              <div>
                <strong>{a.nome}</strong>
                <small>Matrícula {a.numero_matricula}{a.cpf ? ` · CPF ${cpfMascara(a.cpf)}` : ""} <SituacaoAluno a={a} /></small>
              </div>
              {acao(a)}
            </li>
          ))}
          {lista.length === 0 && <li className="vazio">Nenhum aluno encontrado.</li>}
        </ul>
      )}
    </div>
  );
}
