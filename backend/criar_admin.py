"""Cria um administrador:  python criar_admin.py  (pede nome, e-mail e senha)"""
import getpass

from app.database import SessionLocal
from app.services.usuarios import criar_usuario

nome = input("Nome: ").strip() or "Administrador"
email = input("E-mail: ").strip()
senha = getpass.getpass("Senha (mín. 6 caracteres): ")

with SessionLocal() as db:
    u = criar_usuario(db, nome, email, senha, "administrador")
    print(f"Administrador criado: {u.email} (id {u.id})")
