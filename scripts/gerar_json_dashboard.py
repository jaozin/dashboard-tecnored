import sqlite3
import pandas as pd
import os
import json

# ============================================================
# PASTAS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BANCO = os.path.join(
    BASE_DIR,
    "banco",
    "planejamento.db"
)

DADOS_DIR = os.path.join(BASE_DIR, "dados")
os.makedirs(DADOS_DIR, exist_ok=True)

ARQUIVO_JSON = os.path.join(
    DADOS_DIR,
    "dashboard.json"
)

# ============================================================
# CONECTAR BANCO
# ============================================================

conn = sqlite3.connect(BANCO)

# ============================================================
# CONSULTAR DADOS
# ============================================================

query = """
SELECT

    projeto,
    documento,
    sprint,
    tarefa,
    disciplina,
    responsavel,
    critica,
    emitido

FROM tarefas

ORDER BY
    projeto,
    documento,
    tarefa
"""

df = pd.read_sql_query(query, conn)

conn.close()

# ============================================================
# GERAR JSON
# ============================================================

dados = df.to_dict(
    orient="records"
)

with open(
    ARQUIVO_JSON,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        dados,
        f,
        ensure_ascii=False,
        indent=4
    )

# ============================================================
# FINALIZAÇÃO
# ============================================================

print("========================================")
print("JSON GERADO COM SUCESSO")
print("========================================")
print()
print(f"Arquivo: {ARQUIVO_JSON}")
print(f"Registros: {len(df)}")