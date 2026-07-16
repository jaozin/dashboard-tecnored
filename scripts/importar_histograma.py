import os
import sqlite3
import pandas as pd
from datetime import datetime

# ======================================================
# CAMINHOS
# ======================================================

PASTA_ENTRADA = r"C:\Users\jsantos250\OneDrive - Bureau Veritas\POP - Planejamento - Documentos\Automacoes\Comparativo_Cronograma\entrada"

BANCO = r"C:\Users\jsantos250\OneDrive - Bureau Veritas\POP - Planejamento - Documentos\Automacoes\Comparativo_Cronograma\banco\planejamento.db"

# ======================================================
# BANCO
# ======================================================

conn = sqlite3.connect(BANCO)
cursor = conn.cursor()

# ======================================================
# PROJETOS
# ======================================================

for projeto in os.listdir(PASTA_ENTRADA):

    pasta_projeto = os.path.join(
        PASTA_ENTRADA,
        projeto
    )

    if not os.path.isdir(pasta_projeto):
        continue

    pasta_histograma = os.path.join(
        pasta_projeto,
        "Histograma"
    )

    if not os.path.exists(pasta_histograma):
        continue

    arquivos = [
        arq
        for arq in os.listdir(pasta_histograma)
        if arq.lower().endswith(".xlsx")
    ]

    if not arquivos:
        continue

    arquivo_excel = os.path.join(
        pasta_histograma,
        arquivos[0]
    )

    print(f"\n📊 Importando {projeto}")

    df = pd.read_excel(
        arquivo_excel,
        header=None
    )

    # Remove carga anterior do projeto
    cursor.execute("""
        DELETE FROM histograma_recursos
        WHERE projeto = ?
    """, (projeto,))

    data_importacao = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    recurso_atual = None
    ordem = 0

    # ==================================================
    # RECURSOS
    # ==================================================

    for linha in range(6, 34):

        recurso = df.iloc[linha, 1]

        if pd.notna(recurso):
           recurso_atual = str(recurso)
           ordem += 1

        tipo = str(
            df.iloc[linha, 2]
        ).replace(".", "")

        if tipo not in ["Prev", "Real"]:
            continue

        # ==============================================
        # DIARIO
        # ==============================================

        for coluna in range(6, 114):

            data = df.iloc[5, coluna]

            valor = df.iloc[linha, coluna]

            if pd.isna(valor):
                continue

            cursor.execute("""
                INSERT INTO histograma_recursos
                (
                    projeto,
                    recurso,
                    tipo,
                    data,
                    valor,
                    data_importacao,
                    nivel,
                    ordem
                )
                VALUES
                (
                    ?,?,?,?,?,?,?,?
                )
            """,
            (
                projeto,
                recurso_atual,
                tipo,
                str(data),
                float(valor),
                data_importacao,
                "DIARIO",
                ordem
            ))

# ==========================================
# SEMANAL
# ==========================================

        for coluna in range(116, 147, 2):

            periodo = df.iloc[5, coluna]

            valor = df.iloc[linha, coluna]

            if pd.isna(valor):
                continue

            cursor.execute("""
                INSERT INTO histograma_recursos
                (
                    projeto,
                    recurso,
                    tipo,
                    data,
                    valor,
                    data_importacao,
                    nivel,
                    ordem
                )
                VALUES
                (
                    ?,?,?,?,?,?,?,?
                )
            """,
            (
                projeto,
                recurso_atual,
                tipo,
                str(periodo),
                float(valor),
                data_importacao,
                "SEMANAL",
                ordem
            ))
    print(f"✅ {projeto} importado")

conn.commit()
conn.close()

print("\n✅ IMPORTAÇÃO FINALIZADA")