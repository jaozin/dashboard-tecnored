import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BANCO = os.path.join(
    BASE_DIR,
    "banco",
    "planejamento.db"
)

conn = sqlite3.connect(BANCO)
cursor = conn.cursor()

tabelas = [
    "tarefas",
    "kpis",
    "curva_s",
    "resumo_disciplinas"
]


for tabela in tabelas:

    cursor.execute(
        f"SELECT COUNT(*) FROM {tabela}"
    )

    total = cursor.fetchone()[0]

    print(f"{tabela}: {total}")

    print("\nCOLUNAS CURVA_S")

    cursor.execute("PRAGMA table_info(curva_s)")

for coluna in cursor.fetchall():
    print(coluna)

cursor.execute("""
INSERT INTO acoes_usuario
(
    projeto,
    documento,
    etapa,
    status,
    data_acao
)
VALUES
(
    'F0009_306',
    'TESTE_DOCUMENTO',
    'Emissao',
    'Emitido',
    '08/07/2026 19:00'
)
""")

conn.commit()


print("\nACOES_USUARIO")

cursor.execute("""
SELECT *
FROM acoes_usuario
""")

for linha in cursor.fetchall():
    print(linha)

conn.close()