import { useEffect, useState } from "react";
import api, { mensagemErro } from "../api";
import { data, moeda } from "../formato";

const FILTROS = [["", "Todas"], ["pendente", "Pendentes"], ["atrasado", "Em atraso"], ["pago", "Pagas"], ["cancelado", "Canceladas"]];
const ROTULO = { pendente: "Pendente", atrasado: "Em atraso", pago: "Pago", cancelado: "Cancelado" };
const FORMAS = [["dinheiro", "Dinheiro"], ["pix", "Pix"], ["cartao", "Cartão de crédito"], ["boleto", "Boleto"]];

export default function Financeiro() {
  const [situacao, setSituacao] = useState("");
  const [mes, setMes] = useState("");
  const [busca, setBusca] = useState("");
  const [r, setR] = useState(null);
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");
  const [recebendo, setRecebendo] = useState(null); // id da mensalidade com a forma de pagamento aberta
  const [forma, setForma] = useState("dinheiro");

  const carregar = () =>
    api.get("/pagamentos", { params: { situacao, mes, busca } }).then((x) => setR(x.data)).catch((e) => setErro(mensagemErro(e)));

  useEffect(() => {
    const id = setTimeout(carregar, 300);
    return () => clearTimeout(id);
  }, [situacao, mes, busca]);

  async function acao(fn) {
    setErro(""); setMsg("");
    try {
      const { data: x } = await fn();
      setMsg(x.mensagem);
      setRecebendo(null);
      carregar();
    } catch (e) {
      setErro(mensagemErro(e));
    }
  }

  const s = r?.resumo;

  return (
    <>
      <div className="kpis">
        <div className="kpi"><small>Recebido no mês</small><strong>{s ? moeda(s.recebido_mes) : "—"}</strong></div>
        <div className="kpi"><small>A receber</small><strong>{s ? moeda(s.a_receber) : "—"}</strong></div>
        <div className="kpi"><small>Em atraso</small><strong>{s ? moeda(s.em_atraso) : "—"}</strong>
          {s?.qtd_atraso > 0 && <em className="down">{s.qtd_atraso} mensalidade(s)</em>}</div>
      </div>

      <section className="card" style={{ marginTop: 14 }}>
        <h3>Mensalidades</h3>
        <div className="toolbar">
          <select value={situacao} onChange={(e) => setSituacao(e.target.value)} aria-label="Filtrar por situação">
            {FILTROS.map(([v, n]) => <option key={v} value={v}>{n}</option>)}
          </select>
          <input type="month" value={mes} onChange={(e) => setMes(e.target.value)} aria-label="Mês de vencimento" />
          <input type="search" value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Nome do aluno" aria-label="Buscar aluno" />
        </div>
        <div className="err" role="alert">{erro}</div>
        {msg && <div className="okmsg" role="status" style={{ marginBottom: 8 }}>{msg}</div>}
        <div className="tablewrap">
          <table className="t">
            <thead><tr><th>Aluno</th><th>Plano</th><th>Vencimento</th><th>Valor</th><th>Situação</th><th>Pago em</th><th></th></tr></thead>
            <tbody>
              {(r?.pagamentos || []).map((p) => {
                const aberto = p.status === "pendente" || p.status === "atrasado";
                return (
                  <tr key={p.id}>
                    <td>{p.aluno}</td><td>{p.plano}</td><td>{data(p.data_vencimento)}</td><td>{moeda(p.valor)}</td>
                    <td><span className={`chip ${p.status}`}>{ROTULO[p.status] || p.status}</span></td>
                    <td>{p.data_pagamento ? `${data(p.data_pagamento)} · ${p.forma_pagamento || ""}` : "—"}</td>
                    <td>
                      {aberto && recebendo !== p.id && (
                        <div className="acoes">
                          <button className="btn compacto" type="button" onClick={() => { setRecebendo(p.id); setForma("dinheiro"); }}>Receber</button>
                          <button className="btn-sec perigo" type="button"
                            onClick={() => window.confirm(`Cancelar a mensalidade de ${p.aluno}?`) && acao(() => api.post(`/pagamentos/${p.id}/cancelar`))}>
                            Cancelar
                          </button>
                        </div>
                      )}
                      {recebendo === p.id && (
                        <div className="acoes">
                          <select className="compacto" value={forma} onChange={(e) => setForma(e.target.value)} aria-label="Forma de pagamento">
                            {FORMAS.map(([v, n]) => <option key={v} value={v}>{n}</option>)}
                          </select>
                          <button className="btn compacto" type="button" onClick={() => acao(() => api.post(`/pagamentos/${p.id}/baixa`, { forma }))}>Confirmar</button>
                          <button className="btn-sec" type="button" onClick={() => setRecebendo(null)}>Voltar</button>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
              {r && r.pagamentos.length === 0 && <tr><td colSpan="7" className="vazio">Nenhuma mensalidade neste filtro.</td></tr>}
            </tbody>
          </table>
        </div>
        <p className="hint">Recebimento de exemplo: não há integração com banco ou maquininha.</p>
      </section>
    </>
  );
}
