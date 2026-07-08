import pandas as pd
import re
from datetime import datetime

import os
import glob
from datetime import datetime

# ============================================================
# 1. Seleção automática de projetos
# ============================================================

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

saida_base = os.path.join(base_dir, "Comparativo_Cronograma", "saida")

projetos = [
    nome for nome in os.listdir(saida_base)
    if os.path.isdir(os.path.join(saida_base, nome))
]

if not projetos:
    raise ValueError("Nenhum projeto encontrado na pasta saída.")

projetos.sort()

print("Escolha o projeto:")

for i, proj in enumerate(projetos, start=1):
    print(f"{i} - {proj}")

opcao = input("Digite o número do projeto: ").strip()

try:
    projeto_nome = projetos[int(opcao) - 1]
except:
    raise ValueError("Projeto inválido!")

# ============================================================
# 2. Pegar o comparativo mais recente
# ============================================================

pasta_projeto = os.path.join(saida_base, projeto_nome)

arquivos = glob.glob(os.path.join(pasta_projeto, "Comparativo Cronograma*.xlsx"))

if not arquivos:
    raise FileNotFoundError("Nenhum comparativo encontrado.")

def extrair_data(nome_arquivo):
    base = os.path.basename(nome_arquivo)
    
    # pega a data do nome: Comparativo Cronograma 10-06-2026.xlsx
    data_str = base.replace("Comparativo Cronograma ", "").replace(".xlsx", "")
    
    return datetime.strptime(data_str, "%d-%m-%Y")

arquivo = max(arquivos, key=extrair_data)

data_ref = extrair_data(arquivo)
data_str = data_ref.strftime("%d-%m-%Y")

print(f"\nArquivo selecionado: {arquivo}")
print(f"Data identificada: {data_str}")

# =========================
# LIMPAR NOMES DE ABA
# =========================
def limpar_nome(nome):
    nome = re.sub(r'[\\/*?:\[\]]', '_', nome)
    return nome[:30]

# =========================
# DATA
# =========================
data_hoje = datetime.now().strftime("%d/%m/%Y")
texto_data = f"Atualizado em: {data_hoje}"

# =========================
# 1. LER BASE
# =========================
df = pd.read_excel(arquivo, sheet_name="Base")

df["Nome do Resumo da Tarefa"] = df["Nome do Resumo da Tarefa"].astype(str).str.strip()
df["Disciplina"] = df["Disciplina"].astype(str).str.strip()

# =========================
# 2. COLUNAS
# =========================

cols_conc = [
    "Emissão inicial concluída",
    "Avaliação do cliente concluída",
    "Atendimento de comentário concluído",
    "Aprovação concluída"
]

cols_atr = [
    "Emissão Inicial Atrasada",
    "Avaliação Cliente Atrasada",
    "Atendimento Atrasado",
    "Aprovação Atrasada"
]

for c in cols_conc + cols_atr:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

# =========================
# 3. CONSOLIDAÇÃO CORRETA
# =========================

resumo = (
    df.groupby(["Disciplina", "Nome do Resumo da Tarefa"])
    .agg({
        "Emissão inicial concluída": "sum",
        "Avaliação do cliente concluída": "sum",
        "Atendimento de comentário concluído": "sum",
        "Aprovação concluída": "sum",
        "Emissão Inicial Atrasada": "max",
        "Avaliação Cliente Atrasada": "max",
        "Atendimento Atrasado": "max",
        "Aprovação Atrasada": "max"
    })
    .reset_index()
)

# transformar concluído em binário
for c in cols_conc:
    resumo[c] = (resumo[c] > 0).astype(int)

# remover linhas de projeto
resumo = resumo[~resumo["Nome do Resumo da Tarefa"].str.contains("project", case=False, na=False)]

# =========================
# 4. PIPELINE CONCLUÍDO
# =========================

resumo["Etapa_C"] = resumo[cols_conc].sum(axis=1)

resumo["Emissão_c"] = (resumo["Etapa_C"] >= 1).astype(int)
resumo["Avaliação_c"] = (resumo["Etapa_C"] >= 2).astype(int)
resumo["Comentário_c"] = (resumo["Etapa_C"] >= 3).astype(int)
resumo["Aprovação_c"] = (resumo["Etapa_C"] >= 4).astype(int)

# =========================
# 5. ATRASADO (SEM ALTERAÇÃO)
# =========================

resumo["Emissão_a"] = resumo["Emissão Inicial Atrasada"]
resumo["Avaliação_a"] = resumo["Avaliação Cliente Atrasada"]
resumo["Comentário_a"] = resumo["Atendimento Atrasado"]
resumo["Aprovação_a"] = resumo["Aprovação Atrasada"]

# =========================
# 6. EXPORTAÇÃO
# =========================

# NOVO CAMINHO DE SAÍDA
caminho_saida = os.path.join(
    base_dir,
    "Comparativo_Cronograma",
    "saida",
    projeto_nome,
    "Controle Status Documento"
)

os.makedirs(caminho_saida, exist_ok=True)

arquivo_saida = os.path.join(
    caminho_saida,
    f"Controle Status Documento {data_str}.xlsx"
)

with pd.ExcelWriter(arquivo_saida, engine="xlsxwriter") as writer:

    workbook = writer.book

    painel_conc = workbook.add_worksheet("Painel_Concluido")
    painel_atr = workbook.add_worksheet("Painel_Atrasado")

    # formato da data
    formato_data = workbook.add_format({
        'bold': True,
        'font_color': '#006664',
        'font_size': 12
    })

    # escrever data nos painéis
    painel_conc.write("F1", texto_data, formato_data)
    painel_atr.write("F1", texto_data, formato_data)

    disciplinas = resumo["Disciplina"].dropna().unique()

    linha_conc = 3
    linha_atr = 3

    for disc in disciplinas:

        disc_limpo = limpar_nome(disc)
        base_disc = resumo[resumo["Disciplina"] == disc]

        # KPI
        total_emissao = int(base_disc["Emissão_c"].sum())
        total_avaliacao = int(base_disc["Avaliação_c"].sum())
        total_comentario = int(base_disc["Comentário_c"].sum())
        total_aprovacao = int(base_disc["Aprovação_c"].sum())

        total_emissao_a = int(base_disc["Emissão_a"].sum())
        total_avaliacao_a = int(base_disc["Avaliação_a"].sum())
        total_comentario_a = int(base_disc["Comentário_a"].sum())
        total_aprovacao_a = int(base_disc["Aprovação_a"].sum())

        # =========================
        # CONCLUÍDO
        # =========================

        base_c = base_disc[base_disc["Emissão inicial concluída"] == 1]

        if len(base_c) > 0:

            sheet = f"{disc_limpo}_C"
            base_c.to_excel(writer, sheet_name=sheet, index=False)

            n = len(base_c)
            chart = workbook.add_chart({'type': 'bar', 'subtype': 'stacked'})

            chart.add_series({
                'name': f'Emissão ({total_emissao})',
                'values': [sheet, 1, base_c.columns.get_loc("Emissão_c"), n, base_c.columns.get_loc("Emissão_c")],
                'categories': [sheet, 1, 1, n, 1],
                'fill': {'color': '#006664'}
            })

            chart.add_series({
                'name': f'Avaliação ({total_avaliacao})',
                'values': [sheet, 1, base_c.columns.get_loc("Avaliação_c"), n, base_c.columns.get_loc("Avaliação_c")],
                'categories': [sheet, 1, 1, n, 1],
                'fill': {'color': '#00B4B0'}
            })

            chart.add_series({
                'name': f'Comentário ({total_comentario})',
                'values': [sheet, 1, base_c.columns.get_loc("Comentário_c"), n, base_c.columns.get_loc("Comentário_c")],
                'categories': [sheet, 1, 1, n, 1],
                'fill': {'color': '#0BFDFF'}
            })

            # ✅ CORRIGIDO AQUI
            chart.add_series({
                'name': f'Aprovação ({total_aprovacao})',
                'values': [sheet, 1, base_c.columns.get_loc("Aprovação_c"), n, base_c.columns.get_loc("Aprovação_c")],
                'categories': [sheet, 1, 1, n, 1],
                'fill': {'color': '#00E676'}  # ✅ VERDE FORTE
            })

            chart.set_title({'name': f'{disc} - CONCLUÍDO'})
            chart.set_x_axis({'max': 4})
            chart.set_y_axis({'reverse': True})
            chart.set_legend({'position': 'bottom'})

            painel_conc.insert_chart(f"A{linha_conc}", chart, {'x_scale': 1.2, 'y_scale': 1.2})
            linha_conc += 20

        # =========================
        # ATRASADO
        # =========================

        base_a = base_disc[
            (base_disc["Emissão_a"] == 1) |
            (base_disc["Avaliação_a"] == 1) |
            (base_disc["Comentário_a"] == 1) |
            (base_disc["Aprovação_a"] == 1)
        ]

        if len(base_a) > 0:

            sheet = f"{disc_limpo}_A"
            base_a.to_excel(writer, sheet_name=sheet, index=False)

            n2 = len(base_a)
            chart = workbook.add_chart({'type': 'bar', 'subtype': 'stacked'})

            chart.add_series({
                'name': f'Emissão ({total_emissao_a})',
                'values': [sheet, 1, base_a.columns.get_loc("Emissão_a"), n2, base_a.columns.get_loc("Emissão_a")],
                'categories': [sheet, 1, 1, n2, 1],
                'fill': {'color': '#575757'}
            })

            chart.add_series({
                'name': f'Avaliação ({total_avaliacao_a})',
                'values': [sheet, 1, base_a.columns.get_loc("Avaliação_a"), n2, base_a.columns.get_loc("Avaliação_a")],
                'categories': [sheet, 1, 1, n2, 1],
                'fill': {'color': '#f6b26b'}
            })

            chart.add_series({
                'name': f'Comentário ({total_comentario_a})',
                'values': [sheet, 1, base_a.columns.get_loc("Comentário_a"), n2, base_a.columns.get_loc("Comentário_a")],
                'categories': [sheet, 1, 1, n2, 1],
                'fill': {'color': '#ffd966'}
            })

            chart.add_series({
                'name': f'Aprovação ({total_aprovacao_a})',
                'values': [sheet, 1, base_a.columns.get_loc("Aprovação_a"), n2, base_a.columns.get_loc("Aprovação_a")],
                'categories': [sheet, 1, 1, n2, 1],
                'fill': {'color': '#cc0000'}
            })

            chart.set_title({'name': f'{disc} - ATRASADO'})
            chart.set_x_axis({'max': 4})
            chart.set_y_axis({'reverse': True})
            chart.set_legend({'position': 'bottom'})

            painel_atr.insert_chart(f"A{linha_atr}", chart, {'x_scale': 1.2, 'y_scale': 1.2})
            linha_atr += 20

print("✅ Dashboard final com layout ajustado e data inserida")