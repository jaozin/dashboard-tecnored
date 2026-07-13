import sqlite3
import pandas as pd
from datetime import datetime

ARQUIVO = r"CAMINHO_DO_SEU_HISTOGRAMA.xlsx"

BANCO = r"C:\Users\jsantos250\OneDrive - Bureau Veritas\POP - Planejamento - Documentos\Automacoes\Comparativo_Cronograma\banco\planejamento.db"

PROJETO = "F0009_306"

df = pd.read_excel(
    ARQUIVO,
    header=None
)

conn = sqlite3.connect(BANCO)
cursor = conn.cursor()

cursor.execute("""
DELETE FROM histograma_recursos
WHERE projeto = ?
""", (PROJETO,))

data_importacao = datetime.now().strftime(
    "%Y-%m-%d %H:%M:%S"
)

# Linhas dos recursos
for linha in range(6, 34):

    recurso = df.iloc[linha, 1]

    tipo = str(df.iloc[linha, 2]).replace(".", "")

    if pd.isna(recurso):
        continue

    # Apenas Prev e Real
    if tipo not in ["Prev", "Real"]:
        continue

    # Colunas diárias
    for coluna in range(6, 114):

        cabecalho = df.iloc[5, coluna]

        valor = df.iloc[linha, coluna]

        if pd.isna(valor):
            continue

        cursor.execute("""
        INSERT INTO histograma_recursos (
            projeto,
            recurso,
            tipo,
            data,
            valor,
            data_importacao
        )
        VALUES (?,?,?,?,?,?)
        """, (
            PROJETO,
            str(recurso),
            tipo,
            str(cabecalho),
            float(valor),
            data_importacao
        ))

conn.commit()
conn.close()

print("✅ Histograma importado com sucesso")