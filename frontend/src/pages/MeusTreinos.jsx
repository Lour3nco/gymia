import { useEffect, useState } from "react";
import api, { mensagemErro } from "../api";

const vazio = (v) => (v === null || v === undefined || v === "" ? "—" : v);

export default function MeusTreinos() {
  const [r, setR] = useState(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    api.get("/meu/treinos").then((x) => setR(x.data)).catch((e) => setErro(mensagemErro(e)));
  }, []);

  if (erro) return <div className="ph">{erro}</div>;
  if (!r) return <div className="ph">Carregando seus treinos...</div>;

  return (
    <>
      {!r.vinculado && (
        <div className="aviso" role="status">
          Salve seus dados em “Meus dados” para liberar seus treinos.
        </div>
      )}
      {r.avisos.length > 0 && <div className="aviso" role="status">{r.avisos.map((a) => <div key={a}>{a}</div>)}</div>}

      {r.vinculado && r.treinos.length === 0 && (
        <div className="ph">Você ainda não tem treino montado. Peça ao seu instrutor.</div>
      )}

      {r.treinos.map((t) => (
        <section className="card" key={t.id} style={{ marginBottom: 14 }}>
          <h3>{t.nome}</h3>
          {t.objetivo && <p className="hint" style={{ margin: "-8px 0 12px" }}>Objetivo: {t.objetivo}</p>}
          <div className="tablewrap">
            <table className="t">
              <thead><tr><th>Exercício</th><th>Séries</th><th>Repetições</th><th>Carga</th><th>Descanso</th></tr></thead>
              <tbody>
                {t.itens.map((i, k) => (
                  <tr key={k}><td>{vazio(i.exercicio)}</td><td>{vazio(i.series)}</td><td>{vazio(i.repeticoes)}</td>
                    <td>{i.carga != null ? `${Number(i.carga)} kg` : "—"}</td>
                    <td>{i.descanso != null ? `${i.descanso}s` : vazio(i.obs)}</td></tr>
                ))}
                {t.itens.length === 0 && <tr><td colSpan="5" className="vazio">Este treino ainda não tem exercícios.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </>
  );
}