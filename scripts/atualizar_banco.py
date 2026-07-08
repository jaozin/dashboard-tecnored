import pandas as pd
import sqlite3
import os
import re
from datetime import datetime

# ============================================================
# PASTAS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SAIDA_DIR = os.path.join(BASE_DIR, "saida")

BANCO = os.path.join(
    BASE_DIR,
    "banco",
    "planejamento.db"
)

# ============================================================
# FUNÇÃO PARA EXTRAIR DATA DO NOME
# ============================================================

def obter_data_arquivo(nome_arquivo):

    match = re.search(
        r'(\d{2}-\d{2}-\d{4})',
        nome_arquivo
    )

    if match:

        return datetime.strptime(
            match.group(1),
            "%d-%m-%Y"
        )

    return datetime.min

# ============================================================
# CONECTAR BANCO
# ============================================================

conn = sqlite3.connect(BANCO)
cursor = conn.cursor()

# ============================================================
# LIMPAR TABELA
# ============================================================

cursor.execute("DELETE FROM tarefas")
cursor.execute("DELETE FROM kpis")
cursor.execute("DELETE FROM curva_s")
cursor.execute("DELETE FROM resumo_disciplinas")
# ============================================================
# LISTAR PROJETOS
# ============================================================

projetos = sorted([
    p for p in os.listdir(SAIDA_DIR)
    if os.path.isdir(os.path.join(SAIDA_DIR, p))
    and p != "Consolidado_Sprint"
])

print("================================================")
print("IMPORTAÇÃO DOS SPRINTS")
print("================================================")

total_registros = 0

# ============================================================
# PROCESSAR PROJETOS
# ============================================================

for projeto in projetos:

    print(f"\nProcessando projeto: {projeto}")

    caminho_projeto = os.path.join(SAIDA_DIR, projeto)

    arquivos = [
        f for f in os.listdir(caminho_projeto)
        if f.endswith(".xlsx")
        and "Sprint_" not in f
    ]

    if not arquivos:
        print("⚠ Nenhum arquivo encontrado.")
        continue

    arquivos_completos = [
        os.path.join(caminho_projeto, f)
        for f in arquivos
    ]

    # ========================================================
    # PEGAR ARQUIVO MAIS NOVO PELO NOME
    # ========================================================

    arquivo_recente = max(
        arquivos_completos,
        key=lambda x: obter_data_arquivo(
            os.path.basename(x)
        )
    )

    print(f"Arquivo selecionado: {os.path.basename(arquivo_recente)}")

    try:

        # ====================================================
        # SPRINT ATUAL
        # ====================================================

        df_atual = pd.read_excel(
            arquivo_recente,
            sheet_name="Sprint Atual",
            engine="openpyxl"
        )

        df_atual["Sprint_Origem"] = "Sprint Atual"

        # ====================================================
        # PRÓXIMO SPRINT
        # ====================================================

        df_proximo = pd.read_excel(
            arquivo_recente,
            sheet_name="Próximo Sprint",
            engine="openpyxl"
        )

        df_proximo["Sprint_Origem"] = "Próximo Sprint"

        # ====================================================
        # DATA DO COMPARATIVO
        # ====================================================

        data_comparativo = obter_data_arquivo(
          os.path.basename(arquivo_recente)
        ).strftime("%d-%m-%Y")

        # ====================================================
        # RESUMO
        # ====================================================

        df_resumo = pd.read_excel(
            arquivo_recente,
            sheet_name="Resumo",
            header=None,
            engine="openpyxl"
        )
        numero_documentos = None
        aderencia = None

        for i in range(len(df_resumo)):

            valor = str(df_resumo.iloc[i, 0]).strip()

            if valor == "Número de documentos listados":

                try:
                    numero_documentos = int(df_resumo.iloc[i, 1])
                except:
                    numero_documentos = 0

            if valor == "Aderência do modelo (%)":

                try:
                    aderencia = float(df_resumo.iloc[i, 1])
                except:
                    aderencia = 0
                    print("numero_documentos =", numero_documentos)
                    print("aderencia =", aderencia)

                    percentual_ei = None
                    percentual_ap = None

        for i in range(len(df_resumo)):

            linha = df_resumo.iloc[i].tolist()

            if len(linha) > 0:

                if str(linha[0]).strip().upper() == "TOTAL":
                    try:
                        percentual_ei = float(linha[3])
                    except:
                        percentual_ei = 0

                    try:
                        percentual_ap = float(linha[6])
                    except:
                        percentual_ap = 0
                    cursor.execute("""
                        INSERT INTO kpis (
                            projeto,
                            data_comparativo,
                            numero_documentos,
                            aderencia,
                            percentual_ei,
                            percentual_ap,
                            data_importacao
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        projeto,
                        data_comparativo,
                        numero_documentos,
                        aderencia,
                        percentual_ei,
                        percentual_ap,
                        datetime.now().strftime("%d/%m/%Y %H:%M")
                    ))

                    break


         # ====================================================
         # RESUMO DISCIPLINAS
         # ====================================================

        for i in range(3, len(df_resumo)):

            linha = df_resumo.iloc[i].tolist()

            disciplina = str(linha[0]).strip()

            if disciplina.upper() == "TOTAL":
                break

            if disciplina == "" or disciplina.lower() == "nan":
                continue

            cursor.execute("""

                INSERT INTO resumo_disciplinas (

                    projeto,
                    data_comparativo,
                    disciplina,

                    ei_total,
                    ei_concluida,
                    percentual_ei,

                    avaliacao_cliente,

                    atendimento_comentario,

                    aprovacao_concluida,
                    percentual_ap,

                    data_importacao

                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            """, (

                projeto,
                data_comparativo,
                disciplina,

                linha[1] if pd.notna(linha[1]) else 0,
                linha[2] if pd.notna(linha[2]) else 0,
                linha[3] if pd.notna(linha[3]) else 0,

                linha[4] if pd.notna(linha[4]) else 0,

                linha[5] if pd.notna(linha[5]) else 0,

                linha[6] if pd.notna(linha[6]) else 0,
                linha[7] if pd.notna(linha[7]) else 0,

                datetime.now().strftime("%d/%m/%Y %H:%M")

            ))




        # ====================================================
        # CURVA S
        # ====================================================

        df_curva = pd.read_excel(
          arquivo_recente,
          sheet_name="Curva S",
          engine="openpyxl"
        )
        
        for _, linha in df_curva.iterrows():
          
             if pd.isna(linha["Data"]):
                 continue
             cursor.execute("""

                INSERT INTO curva_s (

                    projeto,
                    data_comparativo,
                    data,

                    ei_previsto,
                    ei_real,

                    ei_previsto_acumulado,
                    ei_real_acumulado,

                    ap_previsto,
                    ap_real,

                    ap_previsto_acumulado,
                    ap_real_acumulado,

                    data_importacao

                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                 """, 
        (

          (
                projeto,

                data_comparativo,

                str(linha["Data"]),

                float(
                    linha["Avanço da EI previsto na LB"]
                ),

                float(
                    linha["Avanço real da EI na LB"]
                ),

                float(
                    linha["Emissão prevista na LB acumulada"]
                ),

                float(
                    linha["Emissão realizada acumulada"]
                ),

                float(
                    linha["Avanço da AP previsto na LB"]
                ),

                float(
                    linha["Avanço da AP real na LB"]
                ),

                float(
                    linha["Aprovação prevista na LB acumulada"]
                ),

                float(
                    linha["Aprovação realizada acumulada"]
                ),

                datetime.now().strftime(
                    "%d/%m/%Y %H:%M"
                )

            )

         ))

        # ====================================================
        # JUNTAR
        # ====================================================

        df = pd.concat(
            [df_atual, df_proximo],
            ignore_index=True
        )

        registros_projeto = 0

        # ====================================================
        # PERCORRER LINHAS
        # ====================================================

        for _, row in df.iterrows():

            documento = str(
                row.get("Nome do Resumo da Tarefa", "")
            ).strip()

            # Ignorar agrupadores
            if documento.count("-") < 5:
                continue

            cursor.execute("""

                INSERT OR IGNORE INTO tarefas (

                    projeto,
                    documento,
                    sprint,
                    id_tarefa,
                    edt,
                    tarefa,
                    responsavel,
                    disciplina,
                    critica,
                    emitido,
                    data_importacao

                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            """, (

                projeto,

                documento,

                str(row.get("Sprint_Origem", "")),

                row.get("Id"),

                str(row.get("EDT", "")),

                str(row.get("Nome da Tarefa", "")),

                str(row.get("Nomes dos recursos", "")),

                str(row.get("Disciplina", "")),

                str(row.get("Crítica", "")),

                "Não",

                datetime.now().strftime(
                    "%d/%m/%Y %H:%M"
                )

            ))

            registros_projeto += 1
            total_registros += 1

        print(
            f"✅ {registros_projeto} registros importados"
        )

    except Exception as e:

        print(f"❌ Erro: {e}")

# ============================================================
# FINALIZAR
# ============================================================

conn.commit()
conn.close()

print("\n================================================")
print("IMPORTAÇÃO FINALIZADA")
print("================================================")

print(
    f"\n✅ Total de registros importados: {total_registros}"
)