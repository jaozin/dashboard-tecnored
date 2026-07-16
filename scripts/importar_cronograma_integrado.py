import pandas as pd
import sqlite3
import os
from datetime import datetime

ARQUIVO = r"C:\Users\jsantos250\OneDrive - Bureau Veritas\POP - Planejamento - Documentos\Automacoes\Cronograma Integrado\Int_15-07-2026.xlsx"

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
BANCO = os.path.join(
    BASE_DIR,
    "banco",
    "planejamento.db"
)
conn = sqlite3.connect(BANCO)
cursor = conn.cursor()

df = pd.read_excel(ARQUIVO)

df["PROJETO"] = df["PROJETO"].fillna("[A DEFINIR]")

cursor.execute(
    "DELETE FROM cronograma_integrado"
)

for _, row in df.iterrows():

    cursor.execute("""
        INSERT INTO cronograma_integrado
        (
            projeto,
            atividade,
            responsavel,
            inicio_lb,
            termino_lb,
            inicio_real,
            termino_real,
            conclusao,
            data_importacao
        )
        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        row["PROJETO"],
        row["ATIVIDADE"],
        row["RESPONSÁVEL"],

        str(row["INÍCIO LB"].date()),
        str(row["TÉRMINO LB"].date()),

        str(row["INÍCIO REAL"].date()),
        str(row["TÉRMINO REAL"].date()),

        float(row["CONCL. %"]),

        datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ))

conn.commit()

print(
    "Registros importados:",
    len(df)
)
  
print(
    df[
        [
            "PROJETO",
            "ATIVIDADE",
            "RESPONSÁVEL",
            "INÍCIO LB",
            "TÉRMINO LB",
            "CONCL. %"
        ]
    ]
)