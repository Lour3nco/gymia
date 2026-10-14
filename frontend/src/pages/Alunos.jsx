import { useEffect, useState } from "react";
import api, { mensagemErro } from "../api";
import { useAuth } from "../auth.jsx";
import { SituacaoAluno } from "../components/BuscaAluno.jsx";
import { cpfMascara, dataHora, hojeISO, moeda, numeroOuNulo } from "../formato";

const VAZIO = { nome: "", email: "", cpf: "", data_nascimento: "", sexo: "", telefone: "", altura_cm: "", peso_kg: "" };
const paraForm = (a) => ({
  nome: a.nome || "", email: a.email || "", cpf: cpfMascara(a.cpf),
  data_nascimento: a.data_nascimento ? String(a.data_nascimento).slice(0, 10) : "",
  sexo: (a.sexo || "").trim(), telefone: a.telefone || "", altura_cm: a.altura_cm ?? "", peso_kg: a.peso_kg ?? "",
});

export default function Alunos() {
  const { usuario } = useAuth();
  const podeEditar = ["administrador", "recepcao"].includes(usuario.perfil);
  const [busca, setBusca] = useState("");
  const [lista, setLista] = useState(null);
  const [erro, setErro] = useState("");
  const [editando, setEditando] = useState(null); // null = fechado, "novo" ou o id do aluno

  const carregar = (termo) =>
    api.get("/alunos", { params: { busca: termo } }).then((r) => setLista(r.data)).catch((e) => setErro(mensagemErro(e)));

  useEffect(() => {
    const id = setTimeout(() => carregar(busca), 300);
    return () => clearTimeout(id);
  }, [busca]);

  function salvo(aluno) {
    setLista((l) => (l.some((x) => x.id === aluno.id) ? l.map((x) => (x.id === aluno.id ? aluno : x)) : [aluno, ...l]));
    setEditando(null);
  }

  const alunoEditado = lista?.find((a) => a.id === editando);

  return (
    <>
      <div className="toolbar">
        <input type="search" value={busca} onChange={(e) => setBusca(e.target.value)}
          placeholder="Buscar por nome, e-mail, CPF ou nº de matrícula" aria-label="Buscar aluno" />
        {podeEditar && editando === null && (
          <button className="btn" type="button" onClick={() => setEditando("novo")}>Novo aluno</button>
        )}
      </div>

      {editando !== null && (
        <FormAluno key={editando} aluno={alunoEditado} onSalvo={salvo} onCancelar={() => setEditando(null)} />
      )}

      <section className="card">
        <h3>Alunos {lista && `(${lista.length}${lista.length === 200 ? "+" : ""})`}</h3>
        <div className="err" role="alert">{erro}</div>
        {!lista ? <p className="hint">Carregando...</p> : (
          <div className="tablewrap">
            <table className="t">
              <thead><tr><th>Matrícula</th><th>Nome</th><th>CPF</th><th>Telefone</th><th>Plano</th><th>Situação</th><th>Último check-in</th><th></th></tr></thead>
              <tbody>
                {lista.map((a) => (
                  <tr key={a.id}>
                    <td>{a.numero_matricula}</td>
                    <td>{a.nome}{a.na_academia && <span className="chip ativa" style={{ marginLeft: 6 }}>Na academia</span>}
                      {!a.tem_conta && <small className="hint" style={{ display: "block" }}>sem conta no app</small>}</td>
                    <td>{a.cpf ? cpfMascara(a.cpf) : "—"}</td>
                    <td>{a.telefone || "—"}</td>
                    <td>{a.plano || "—"}</td>
                    <td><SituacaoAluno a={a} /></td>
                    <td>{dataHora(a.ultimo_checkin)}</td>
                    <td>{podeEditar && <button type="button" className="btn-sec" onClick={() => setEditando(a.id)}>Editar</button>}</td>
                  </tr>
                ))}
                {lista.length === 0 && <tr><td colSpan="8" className="vazio">Nenhum aluno encontrado.</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}

function FormAluno({ aluno, onSalvo, onCancelar }) {
  const [f, setF] = useState(() => (aluno ? paraForm(aluno) : VAZIO));
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [planos, setPlanos] = useState([]);
  const [matricula, setMatricula] = useState({ plano_id: "", data_inicio: hojeISO() });
  const mudar = (campo, filtro = (v) => v) => (e) => setF({ ...f, [campo]: filtro(e.target.value) });

  useEffect(() => {
    if (!aluno) api.get("/planos").then((r) => setPlanos(r.data.filter((p) => p.ativo))).catch(() => {});
  }, [aluno]);

  async function salvar(e) {
    e.preventDefault();
    setErro("");
    setEnviando(true);
    const corpo = {
      nome: f.nome.trim(), email: f.email.trim() || null, cpf: f.cpf || null, data_nascimento: f.data_nascimento || null,
      sexo: f.sexo || null, telefone: f.telefone || null, altura_cm: numeroOuNulo(f.altura_cm), peso_kg: numeroOuNulo(f.peso_kg),
    };
    try {
      const { data } = aluno ? await api.put(`/alunos/${aluno.id}`, corpo)
        : await api.post("/alunos", { ...corpo, plano_id: Number(matricula.plano_id), data_inicio: matricula.data_inicio });
      onSalvo(data);
    } catch (err) {
      setErro(mensagemErro(err));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section className="card" style={{ marginBottom: 14 }}>
      <h3>{aluno ? `Editar ${aluno.nome} · matrícula ${aluno.numero_matricula}` : "Novo aluno"}</h3>
      <form className="form-row" onSubmit={salvar}>
        <label>Nome completo<input value={f.nome} onChange={mudar("nome")} maxLength={120} required /></label>
        <label>E-mail<input type="email" value={f.email} onChange={mudar("email")} maxLength={150} /></label>
        <label>CPF<input value={f.cpf} onChange={mudar("cpf", cpfMascara)} inputMode="numeric" placeholder="000.000.000-00" /></label>
        <label>Data de nascimento<input type="date" value={f.data_nascimento} onChange={mudar("data_nascimento")} max={hojeISO()} /></label>
        <label>Sexo
          <select value={f.sexo} onChange={mudar("sexo")}>
            <option value="">Não informado</option><option value="M">Masculino</option>
            <option value="F">Feminino</option><option value="O">Outro</option>
          </select>
        </label>
        <label>Telefone<input type="tel" value={f.telefone} onChange={mudar("telefone")} maxLength={20} /></label>
        <label>Altura (cm)<input type="number" value={f.altura_cm} onChange={mudar("altura_cm")} min="50" max="260" step="0.5" /></label>
        <label>Peso (kg)<input type="number" value={f.peso_kg} onChange={mudar("peso_kg")} min="20" max="400" step="0.1" /></label>
        {!aluno && (
          <>
            <label>Plano
              <select value={matricula.plano_id} onChange={(e) => setMatricula({ ...matricula, plano_id: e.target.value })} required>
                <option value="">Escolha...</option>
                {planos.map((p) => <option key={p.id} value={p.id}>{p.nome} · {moeda(p.valor)}</option>)}
              </select>
            </label>
            <label>Início do plano
              <input type="date" value={matricula.data_inicio} onChange={(e) => setMatricula({ ...matricula, data_inicio: e.target.value })} required />
            </label>
          </>
        )}
        <div className="acoes">
          <button className="btn" type="submit" disabled={enviando}>{enviando ? "Salvando..." : "Salvar"}</button>
          <button className="btn-sec" type="button" onClick={onCancelar}>Cancelar</button>
        </div>
      </form>
      <div className="err" role="alert">{erro}</div>
      {!aluno && <p className="hint">O número de matrícula é gerado ao salvar, junto com a primeira mensalidade do plano.
        Se o aluno criar uma conta no app com o mesmo e-mail, ela é ligada a este cadastro.</p>}
    </section>
  );
}
