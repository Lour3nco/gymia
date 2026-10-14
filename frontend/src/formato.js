// Formatação compartilhada pelas telas (datas, dinheiro, CPF)

export const data = (v) => (v ? new Date(`${String(v).slice(0, 10)}T00:00:00`).toLocaleDateString("pt-BR") : "—");
export const hora = (v) => (v ? new Date(v).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "—");
export const dataHora = (v) => (v ? new Date(v).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }) : "—");
export const moeda = (v) => (v === null || v === undefined ? "—"
  : Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }));
export const hojeISO = () => new Date().toLocaleDateString("sv-SE"); // AAAA-MM-DD no fuso local

export const cpfMascara = (v) => {
  const d = String(v || "").replace(/\D/g, "").slice(0, 11);
  return d.replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d{1,2})$/, "$1-$2");
};

// "" -> null e vírgula decimal -> ponto, para enviar números opcionais à API
export const numeroOuNulo = (v) => (v === "" || v === null || v === undefined ? null : Number(String(v).replace(",", ".")));
