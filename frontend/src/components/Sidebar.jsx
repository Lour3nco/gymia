import { useAuth } from "../auth.jsx";

const PERFIS = { administrador: "Administrador", recepcao: "Recepção", instrutor: "Instrutor", aluno: "Aluno" };

// RF02: itens do menu conforme o perfil
export const MENU = [
  { nome: "Meus dados", perfis: ["aluno"] },
  { nome: "Pagamentos", perfis: ["aluno"] },
  { nome: "Dashboard", perfis: ["administrador", "recepcao", "instrutor"] },
  { nome: "Alunos", perfis: ["administrador", "recepcao", "instrutor"] },
  { nome: "Planos e matrículas", perfis: ["administrador", "recepcao"] },
  { nome: "Financeiro", perfis: ["administrador", "recepcao"] },
  { nome: "Check-in", perfis: ["administrador", "recepcao", "aluno"] },
  { nome: "Treinos", perfis: ["administrador", "instrutor", "aluno"] },
  { nome: "Análise de postura", perfis: ["administrador", "instrutor"] },
  { nome: "Relatórios", perfis: ["administrador"] },
  { nome: "Usuários", perfis: ["administrador"] },
];

export default function Sidebar({ atual, onSelecionar, aberto }) {
  const { usuario, sair } = useAuth();
  return (
    <aside className={aberto ? "open" : ""}>
      <div className="brand">Gym<b>AI</b></div>
      <nav aria-label="Principal">
        {MENU.filter((m) => m.perfis.includes(usuario.perfil)).map((m) => (
          <button key={m.nome} aria-current={m.nome === atual ? "page" : undefined} onClick={() => onSelecionar(m.nome)}>
            {m.nome}
          </button>
        ))}
      </nav>
      <div className="who">
        <strong>{usuario.nome}</strong>
        <small>{PERFIS[usuario.perfil] || usuario.perfil}</small>
        <button onClick={sair}>Sair</button>
      </div>
    </aside>
  );
}