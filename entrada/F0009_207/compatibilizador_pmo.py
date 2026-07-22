import pandas as pd
import numpy as np
import re
import os

print("Iniciando a extração trilateral...")

# 1. Caminhos absolutos dos arquivos
caminho_base = r"D:\TECNORED\DADOS\F0009\F0009 - Periféricos - TENAX\0207"

ld_file = rf"{caminho_base}\LD-F0009-0207-MB-G-00001 ATUALIZADO.xlsx"
master_file = rf"{caminho_base}\CD - F0009 - 0207 - STOCKHOUSE - 20260721.xlsx"
supplier_file = rf"{caminho_base}\Plano macro 0207 revisão 21072026.xlsx"

# 2. Carregar LD (Filtrando FASE = 1)
ld_xls = pd.ExcelFile(ld_file)
ld_raw = pd.read_excel(ld_xls, header=None)
header_idx = ld_raw.notnull().sum(axis=1).idxmax()
ld_df = pd.read_excel(ld_xls, header=header_idx)
ld_df.columns = ld_df.columns.str.strip()
ld_fase1 = ld_df[ld_df['FASE'] == 1.0].copy()
name_col = [c for c in ld_fase1.columns if 'NAME' in c][0]
ld_fase1.rename(columns={name_col: 'NAME'}, inplace=True)

# 3. Carregar Master e Supplier
master_df = pd.read_excel(master_file, sheet_name='Tabela_Tarefas')
supplier_df = pd.read_excel(supplier_file, sheet_name='Tabela_Tarefas')
supplier_attr = pd.read_excel(supplier_file, sheet_name='Tabela_Atribuição')

# Agrupar Recursos do Fornecedor por Tarefa
macro_l3 = supplier_df[supplier_df['Nível da estrutura de tópicos'] == 3].copy()
grouped_assignments = []
curr_task, curr_res = None, []
for idx, row in supplier_attr.iterrows():
    t_name = row['Nome da tarefa']
    res = row['Nome do recurso']
    if t_name != curr_task:
        if curr_task is not None:
            grouped_assignments.append({'Nome': curr_task, 'Recursos': curr_res})
        curr_task = t_name
        curr_res = [res]
    else:
        curr_res.append(res)
if curr_task is not None:
    grouped_assignments.append({'Nome': curr_task, 'Recursos': curr_res})

recursos_por_id_macro = {}
for i, (idx, row) in enumerate(macro_l3.iterrows()):
    if i < len(grouped_assignments) and grouped_assignments[i]['Nome'] == row['Nome']:
        recursos_por_id_macro[row['Id']] = grouped_assignments[i]['Recursos']
    else:
        recursos_por_id_macro[row['Id']] = []

# Adicionar Disciplina de Agrupamento ao Fornecedor (com tipagem explícita para evitar TypeError)
supplier_df['Discipline'] = pd.Series(dtype='object')
curr_disc = None
for idx, row in supplier_df.iterrows():
    if row['Nível da estrutura de tópicos'] == 2:
        curr_disc = row['Nome']
    supplier_df.at[idx, 'Discipline'] = curr_disc

# 4. Lógica Dicionário de Equivalência (LD -> Macro Task)
disc_map = {
    'P': 'Processo', 'M': 'Mecânica', 'U': 'Tubulação', 'S': 'Estrutura',
    'E': 'Elétrica', 'J': 'Automação', 'J00001': 'Automação', 'C': 'Civil', 'T': 'Tubulação'
}
ld_fase1['Disc_Code'] = ld_fase1['NAME'].str.split('-').str[4]
ld_fase1['Discipline'] = ld_fase1['Disc_Code'].map(disc_map)
ld_fase1['Doc_Prefix'] = ld_fase1['DOCUMENT TYPE'].str.split(' - ').str[0].str.strip()

def get_macro_task_id(row):
    disc, prefix = row['Discipline'], row['Doc_Prefix']
    title = str(row['TITLE']).lower()
    if pd.isna(disc): return None
    
    possible = supplier_df[(supplier_df['Nível da estrutura de tópicos'] == 3) & (supplier_df['Discipline'] == disc)]
    target_nome = None
    
    if disc == 'Mecânica':
        if prefix in ['ML', 'AG']: target_nome = f"{prefix} - silo" if 'silo' in title else (f"{prefix} - Despoeiramento" if any(x in title for x in ['dust', 'despoeiramento', 'baghouse']) else f"{prefix} - Equipamentos")
        elif prefix in ['MC', 'LE']: target_nome = 'MC/LE'
    elif disc == 'Estrutura':
        if prefix in ['ML', 'MC']: target_nome = 'ML e MC - silos' if 'silo' in title else ('ML e MC - Despoeiramento' if any(x in title for x in ['dust', 'despoeiramento', 'baghouse']) else 'ML e MC Equipamentos')
        elif prefix in ['AG', 'PL']: target_nome = 'AG e PL - silos' if 'silo' in title else ('AG e PL - Despoeiramento' if any(x in title for x in ['dust', 'despoeiramento', 'baghouse']) else 'AG e PL Equipamentos')
    elif disc == 'Elétrica': target_nome = 'MC/DU/FD/LC' if prefix in ['MC', 'DU', 'FD', 'LC'] else ('LM/PQ' if prefix in ['LM', 'PQ'] else None)
    elif disc == 'Automação': target_nome = 'LI/LE/DI/RE' if prefix in ['LI', 'LE', 'DI', 'RE'] else None

    if target_nome is None:
        direct = possible[possible['Nome'] == prefix]
        if len(direct) == 1: target_nome = prefix
        else:
            fallback = possible[possible['Nome'].str.contains(prefix, na=False, regex=False)]
            if len(fallback) == 1: target_nome = fallback.iloc[0]['Nome']

    if target_nome:
        matches = possible[possible['Nome'] == target_nome]
        if not matches.empty: return matches.iloc[0]['Id']
    return None

ld_fase1['Macro_Task_Id'] = ld_fase1.apply(get_macro_task_id, axis=1)
docs_sem_macro = ld_fase1[ld_fase1['Macro_Task_Id'].isnull()]

# 5. Cruzamento de Datas, Durações e Vínculos
master_updated = master_df.copy()
master_updated['Nova_Duração'] = pd.Series(dtype='object')
master_updated['Novo_Início'] = pd.Series(dtype='object')
master_updated['Novo_Término'] = pd.Series(dtype='object')
de_para_report = []

for idx, ld_row in ld_fase1.dropna(subset=['Macro_Task_Id']).iterrows():
    doc_name, macro_id = ld_row['NAME'], ld_row['Macro_Task_Id']
    master_doc_idx = master_updated[master_updated['Nome'] == doc_name].index
    if len(master_doc_idx) == 0: continue
    master_doc_idx = master_doc_idx[0]
    
    emissao_inicial_idx = None
    for i in range(master_doc_idx + 1, len(master_updated)):
        if master_updated.at[i, 'Nível da estrutura de tópicos'] <= master_updated.at[master_doc_idx, 'Nível da estrutura de tópicos']: break
        if 'Emissão' in str(master_updated.at[i, 'Nome']):
            emissao_inicial_idx = i
            break
            
    if emissao_inicial_idx is not None:
        macro_task = supplier_df[supplier_df['Id'] == macro_id].iloc[0]
        master_updated.at[emissao_inicial_idx, 'Nova_Duração'] = macro_task['Duração']
        master_updated.at[emissao_inicial_idx, 'Novo_Início'] = macro_task['Início']
        master_updated.at[emissao_inicial_idx, 'Novo_Término'] = macro_task['Término']
        
        de_para_report.append({
            'Doc_Mestre': doc_name,
            'Tarefa_Mestre_Id': master_updated.at[emissao_inicial_idx, 'Id'],
            'Tarefa_Mestre_Nome': master_updated.at[emissao_inicial_idx, 'Nome'],
            'Macro_Id': macro_id,
            'Macro_Nome': macro_task['Nome'],
            'Início_Antigo': master_updated.at[emissao_inicial_idx, 'Início'],
            'Início_Novo': macro_task['Início'],
            'Término_Antigo': master_updated.at[emissao_inicial_idx, 'Término'],
            'Término_Novo': macro_task['Término'],
            'Recursos_Atribuidos': ", ".join(recursos_por_id_macro.get(macro_id, []))
        })

de_para_df = pd.DataFrame(de_para_report)

# 6. Tradução Lógica de Predecessoras (Preservando LAG)
macro_to_master_ids = {}
for dp in de_para_report:
    mac_id, mast_id = dp['Macro_Id'], dp['Tarefa_Mestre_Id']
    if mac_id not in macro_to_master_ids: macro_to_master_ids[mac_id] = []
    macro_to_master_ids[mac_id].append(str(mast_id))

vinculos_orfaos = []
master_updated['Novas_Predecessoras'] = master_updated['Predecessoras']

for dp in de_para_report:
    mac_id, mast_id = dp['Macro_Id'], dp['Tarefa_Mestre_Id']
    mast_idx = master_updated[master_updated['Id'] == mast_id].index[0]
    macro_task = supplier_df[supplier_df['Id'] == mac_id].iloc[0]
    macro_preds = str(macro_task['Predecessoras'])
    
    if pd.isna(macro_task['Predecessoras']) or macro_preds == 'nan': continue
        
    translated_preds = []
    for p in macro_preds.split(';'):
        match = re.match(r'(\d+)(.*)', p.strip())
        if match:
            pred_id, suffix = int(match.group(1)), match.group(2)
            if pred_id in macro_to_master_ids:
                for t_id in macro_to_master_ids[pred_id]:
                    translated_preds.append(f"{t_id}{suffix}")
            else:
                vinculos_orfaos.append({'Origem_Macro': mac_id, 'Dependencia_Faltante': pred_id})
                
    if translated_preds:
        master_updated.at[mast_idx, 'Novas_Predecessoras'] = ";".join(translated_preds)

# Consolidação Inconsistências
inconsistencias = []
for idx, row in docs_sem_macro.iterrows():
    inconsistencias.append({'Tipo': 'Documento Órfão (LD)', 'Descrição': f"O documento {row['NAME']} não encontrou pacote técnico no Fornecedor."})
for vo in vinculos_orfaos:
    inconsistencias.append({'Tipo': 'Vínculo Quebrado', 'Descrição': f"O ID Macro {vo['Origem_Macro']} depende do ID Macro {vo['Dependencia_Faltante']}, que não foi mapeado no Mestre."})
inconsistencias_df = pd.DataFrame(inconsistencias)

# Atualizar Mestre Final Substituindo Valores
master_updated['Duração'] = master_updated['Nova_Duração'].fillna(master_updated['Duração'])
master_updated['Início'] = master_updated['Novo_Início'].fillna(master_updated['Início'])
master_updated['Término'] = master_updated['Novo_Término'].fillna(master_updated['Término'])
master_updated['Predecessoras'] = master_updated['Novas_Predecessoras'].fillna(master_updated['Predecessoras'])
master_final = master_updated.drop(columns=['Nova_Duração', 'Novo_Início', 'Novo_Término', 'Novas_Predecessoras'])

# 7. Exportação dos Entregáveis (Salvos na mesma pasta de origem)
print("Gerando arquivos físicos de entrega...")

caminho_mestre_atualizado = rf"{caminho_base}\CR-F0009_REV_COMPATIBILIZADA.xlsx"
caminho_relatorio = rf"{caminho_base}\Relatorio_De_Para.xlsx"
caminho_inconsistencias = rf"{caminho_base}\Relatorio_Inconsistencias.xlsx"

with pd.ExcelWriter(caminho_mestre_atualizado) as writer:
    master_final.to_excel(writer, index=False, sheet_name='Tabela_Tarefas')
with pd.ExcelWriter(caminho_relatorio) as writer:
    de_para_df.to_excel(writer, index=False, sheet_name='De-Para')
with pd.ExcelWriter(caminho_inconsistencias) as writer:
    inconsistencias_df.to_excel(writer, index=False, sheet_name='Inconsistencias')

print(f"Processo PMO Finalizado com Sucesso. Arquivos salvos em:\n{caminho_base}")