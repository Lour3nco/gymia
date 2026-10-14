import { createContext, useCallback, useContext, useEffect, useState } from "react";
import api from "./api";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [semConexao, setSemConexao] = useState(false); // backend fora do ar ao abrir: não desloga
  const [aviso, setAviso] = useState(""); // mostrado na tela de login (ex.: sessão expirada)

  const verificar = useCallback(() => {
    if (!localStorage.getItem("gymai_token")) return setCarregando(false);
    setCarregando(true);
    setSemConexao(false);
    api.get("/auth/me")
      .then((r) => setUsuario(r.data))
      .catch((e) => {
        if (e.response?.status === 401) localStorage.removeItem("gymai_token"); // token vencido/inválido
        else setSemConexao(true); // sem resposta da API: mantém o token e oferece tentar de novo
      })
      .finally(() => setCarregando(false));
  }, []);

  useEffect(() => { verificar(); }, [verificar]);

  // qualquer 401 com sessão aberta (token expirado, conta desativada) volta para o login
  useEffect(() => {
    const id = api.interceptors.response.use(undefined, (erro) => {
      const rota = erro.config?.url || "";
      if (erro.response?.status === 401 && !rota.startsWith("/auth/") && localStorage.getItem("gymai_token")) {
        localStorage.removeItem("gymai_token");
        setUsuario(null);
        setAviso(erro.response.data?.detail || "Sua sessão expirou. Entre novamente.");
      }
      return Promise.reject(erro);
    });
    return () => api.interceptors.response.eject(id);
  }, []);

  function guardar(data) {
    localStorage.setItem("gymai_token", data.access_token);
    setAviso("");
    setUsuario(data.usuario);
  }

  async function entrar(email, senha, acesso) {
    const { data } = await api.post("/auth/login", { email, senha, acesso });
    guardar(data);
  }

  async function cadastrar(dados) {
    const { data } = await api.post("/auth/cadastro", dados);
    guardar(data); // já entra logado, com perfil aluno
  }

  function sair() {
    localStorage.removeItem("gymai_token");
    setAviso("");
    setUsuario(null);
  }

  return (
    <AuthContext.Provider value={{ usuario, carregando, semConexao, aviso, verificar, entrar, cadastrar, sair }}>
      {children}
    </AuthContext.Provider>
  );
}
