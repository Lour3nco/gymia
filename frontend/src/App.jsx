import { useState } from "react";
import { useAuth } from "./auth.jsx";
import Login from "./pages/Login.jsx";
import Cadastro from "./pages/Cadastro.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import MeusDados from "./pages/MeusDados.jsx";
import MeusTreinos from "./pages/MeusTreinos.jsx";
import MeuCheckin from "./pages/MeuCheckin.jsx";
import MeusPagamentos from "./pages/MeusPagamentos.jsx";
import Alunos from "./pages/Alunos.jsx";
import PlanosMatriculas from "./pages/PlanosMatriculas.jsx";
import Financeiro from "./pages/Financeiro.jsx";
import CheckinRecepcao from "./pages/CheckinRecepcao.jsx";
import Treinos from "./pages/Treinos.jsx";
import Postura from "./pages/Postura.jsx";
import Relatorios from "./pages/Relatorios.jsx";
import Usuarios from "./pages/Usuarios.jsx";
import Sidebar, { MENU } from "./components/Sidebar.jsx";

function abaSalva() {
  try {
    return localStorage.getItem("gymai_aba") === "equipe" ? "equipe" : "aluno";
  } catch {
    return "aluno";
  }
}

export default function App() {
  const { usuario, carregando, semConexao, verificar } = useAuth();
  const [tela, setTela] = useState("login");
  const [aba, setAba] = useState(abaSalva); // lembra a última aba usada neste navegador
  const [pagina, setPagina] = useState("Dashboard");
  const [menuAberto, setMenuAberto] = useState(false);

  if (carregando) return null;
  if (semConexao) {
    return (
      <div className="ph" style={{ margin: 40 }} role="alert">
        Não foi possível conectar à API. Verifique se o backend está rodando.{" "}
        <button type="button" className="linkbtn" onClick={verificar}>Tentar de novo</button>
      </div>
    );
  }
  if (!usuario) {
    const mudarAba = (nova) => {
      setAba(nova);
      try { localStorage.setItem("gymai_aba", nova); } catch { /* sem armazenamento: só não lembra */ }
    };
    return tela === "cadastro"
      ? <Cadastro aba={aba} onAba={mudarAba} onLogin={() => setTela("login")} />
      : <Login aba={aba} onAba={mudarAba} onCadastro={() => setTela("cadastro")} />;
  }

  const permitidas = MENU.filter((m) => m.perfis.includes(usuario.perfil)).map((m) => m.nome);
  const atual = permitidas.includes(pagina) ? pagina : permitidas[0];

  return (
    <div className="app">
      <Sidebar atual={atual} onSelecionar={(p) => { setPagina(p); setMenuAberto(false); }} aberto={menuAberto} />
      <main>
        <div className="top">
          <div>
            <button className="menu" onClick={() => setMenuAberto(!menuAberto)}>Menu</button>
            <h2>{atual}</h2>
            <span>{new Date().toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" })}</span>
          </div>
        </div>
        {atual === "Dashboard" ? <Dashboard />
          : atual === "Usuários" ? <Usuarios />
          : atual === "Meus dados" ? <MeusDados />
          : atual === "Pagamentos" ? <MeusPagamentos />
          : atual === "Check-in" ? (usuario.perfil === "aluno" ? <MeuCheckin /> : <CheckinRecepcao />)
          : atual === "Alunos" ? <Alunos />
          : atual === "Planos e matrículas" ? <PlanosMatriculas />
          : atual === "Financeiro" ? <Financeiro />
          : atual === "Treinos" ? (usuario.perfil === "aluno" ? <MeusTreinos /> : <Treinos />)
          : atual === "Análise de postura" ? <Postura />
          : atual === "Relatórios" ? <Relatorios />
          : null}
      </main>
    </div>
  );
}