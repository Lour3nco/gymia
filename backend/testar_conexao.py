"""Testa a conexão e imprime as colunas de TODAS as tabelas do schema.
Cole a saída na conversa para ajustar o dashboard aos nomes reais."""
# pyright: reportMissingImports=false
from sqlalchemy import inspect, text

from app.database import DB_HOST, DB_SCHEMA, engine
from app.perfis import valores_enum

with engine.connect() as conn:
    print("Host:", DB_HOST)
    print("Postgres:", conn.execute(text("select version()")).scalar())

insp = inspect(engine)
tabelas = sorted(insp.get_table_names(schema=DB_SCHEMA))
print(f"\nSchema {DB_SCHEMA}: {len(tabelas)} tabelas")
for nome in tabelas:
    print(f"\n{nome}")
    for c in insp.get_columns(nome, schema=DB_SCHEMA):
        print(f"  - {c['name']}: {c['type']}")

print("\nValores do enum perfil_usuario:", valores_enum())
