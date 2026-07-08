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

conn.close()