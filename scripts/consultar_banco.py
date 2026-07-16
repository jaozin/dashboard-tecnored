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



print("\nCOLUNAS_ACOES_USUARIO")

cursor.execute("PRAGMA table_info(acoes_usuario)")

for coluna in cursor.fetchall():
    print(coluna)

print("\nACOES_USUARIO")

print("\nACOES_USUARIO")

cursor.execute("""
SELECT *
FROM acoes_usuario
""")

for linha in cursor.fetchall():
    print(linha)

print("\nCOLUNAS_HISTOGRAMA_RECURSOS")

for c in conn.execute(
    "PRAGMA table_info(histograma_recursos)"
):
    print(c)

cursor.execute("""
SELECT COUNT(*)
FROM histograma_recursos
""")

print(
    "histograma_recursos:",
    cursor.fetchone()[0]
)
print("\nCRONOGRAMA_INTEGRADO")

cursor.execute("""
SELECT
    projeto,
    atividade,
    responsavel,
    inicio_lb,
    termino_lb,
    conclusao
FROM cronograma_integrado
""")

for linha in cursor.fetchall():
    print(linha)

conn.close()
