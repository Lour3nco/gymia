// Abas "Aluno" / "Equipe" usadas no login e no cadastro
const ROTULOS = { aluno: "Aluno", equipe: "Equipe" };

export default function Abas({ aba, onAba }) {
  return (
    <div className="abas" role="tablist" aria-label="Tipo de acesso">
      {Object.entries(ROTULOS).map(([chave, rotulo]) => (
        <button key={chave} type="button" role="tab" aria-selected={aba === chave} onClick={() => onAba(chave)}>
          {rotulo}
        </button>
      ))}
    </div>
  );
}
