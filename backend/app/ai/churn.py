"""Previsão de evasão: rede neural em PyTorch, treinada e executada em GPU (CUDA).

Entradas (RN07 / seção 12.1): check-ins 30d, check-ins período anterior, dias sem treinar,
atrasos de pagamento, meses de matrícula, valor do plano.
Dados de treino: conjunto sintético (gerar_dataset), menos frequência e mais atrasos => mais risco.
"""
import os
import tempfile
import time
from functools import lru_cache

import numpy as np
import torch
from torch import nn

MODEL_PATH = os.getenv("CHURN_MODEL_PATH", os.path.join(tempfile.gettempdir(), "churn_model.pt"))
ESCALA = np.array([30, 30, 30, 5, 24, 300], dtype=np.float32)


def dispositivo() -> torch.device:  # RNF07: GPU quando disponível, senão CPU
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def gerar_dataset(n: int = 20000, seed: int = 42):
    rng = np.random.default_rng(seed)
    c30 = rng.integers(0, 31, n)
    cprev = rng.integers(0, 31, n)
    dias = np.clip(30 - c30 + rng.integers(-5, 6, n), 0, 30)
    atrasos = rng.integers(0, 5, n)
    meses = rng.integers(1, 25, n)
    valor = rng.uniform(80, 300, n)
    logit = (1.5 - 0.18 * c30 + 0.05 * (cprev - c30) + 0.07 * dias
             + 0.6 * atrasos - 0.04 * meses + 0.004 * (valor - 150))
    y = rng.random(n) < 1 / (1 + np.exp(-logit))
    X = np.stack([c30, cprev, dias, atrasos, meses, valor], axis=1).astype(np.float32) / ESCALA
    return X, y.astype(np.float32)


class RedeEvasao(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(6, 32), nn.ReLU(), nn.Linear(32, 16), nn.ReLU(), nn.Linear(16, 1))

    def forward(self, x):
        return self.net(x).squeeze(-1)  # logit


def treinar(epocas: int = 30) -> RedeEvasao:
    dev = dispositivo()
    X, y = gerar_dataset()
    corte = int(len(X) * 0.8)
    Xtr, ytr = torch.tensor(X[:corte]).to(dev), torch.tensor(y[:corte]).to(dev)
    Xte, yte = torch.tensor(X[corte:]).to(dev), torch.tensor(y[corte:]).to(dev)
    modelo = RedeEvasao().to(dev)
    opt = torch.optim.Adam(modelo.parameters(), lr=1e-2)
    perda = nn.BCEWithLogitsLoss()
    for _ in range(epocas):
        for i in range(0, len(Xtr), 512):
            opt.zero_grad()
            perda(modelo(Xtr[i:i + 512]), ytr[i:i + 512]).backward()
            opt.step()
    with torch.no_grad():
        acc = ((torch.sigmoid(modelo(Xte)) > 0.5).float() == yte).float().mean().item()
    print(f"[IA] evasão treinada em {dev} | acurácia: {acc:.1%}")
    torch.save(modelo.state_dict(), MODEL_PATH)
    return modelo


@lru_cache(maxsize=1)
def carregar_modelo() -> RedeEvasao:
    dev = dispositivo()
    if os.path.exists(MODEL_PATH):
        modelo = RedeEvasao()
        modelo.load_state_dict(torch.load(MODEL_PATH, map_location=dev))
        modelo.to(dev)
    else:
        modelo = treinar()
    return modelo.eval()


def prever(features: list[list[float]]) -> list[float]:
    """Recebe linhas [c30, cprev, dias, atrasos, meses, valor] e devolve probabilidades 0..1."""
    modelo = carregar_modelo()
    x = torch.tensor(np.array(features, dtype=np.float32) / ESCALA).to(dispositivo())
    with torch.no_grad():
        return torch.sigmoid(modelo(x)).cpu().tolist()


@lru_cache(maxsize=1)
def benchmark(lote: int = 100_000) -> dict:
    """Compara tempo de inferência CPU x GPU em lote grande (métrica da seção 12.1).
    Roda uma vez por processo; as chamadas seguintes devolvem o resultado guardado."""
    X, _ = gerar_dataset(lote)
    resultado = {}
    for nome in ["cpu"] + (["cuda"] if torch.cuda.is_available() else []):
        dev = torch.device(nome)
        modelo = RedeEvasao().to(dev).eval()
        x = torch.tensor(X).to(dev)
        with torch.no_grad():
            modelo(x)  # aquecimento
            if nome == "cuda":
                torch.cuda.synchronize()
            ini = time.perf_counter()
            for _ in range(20):
                modelo(x)
            if nome == "cuda":
                torch.cuda.synchronize()
        resultado[nome] = (time.perf_counter() - ini) / 20
    return resultado
