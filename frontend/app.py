import sys
import subprocess
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, render_template

try:
    import flask
    import openpyxl
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Flask", "pandas", "openpyxl"])

app = Flask(__name__)

BASE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "base"
)
FILE_CRONO = os.path.join(BASE_DIR, "Comparativo Cronograma Atualização.xlsx")
FILE_PLAN = os.path.join(BASE_DIR, "PLANEJAMENTO BQM-LS - BV.xlsx")

def obter_data_referencia():
    try:
        mtime = os.path.getmtime(FILE_CRONO)
        dt_modificacao = datetime.fromtimestamp(mtime)
        sugestao_str = (dt_modificacao - timedelta(days=1)).strftime('%Y-%m-%d')
    except:
        sugestao_str = datetime.now().strftime('%Y-%m-%d')

    print("\n" + "="*60)
    print("ENGINEERING DATA ENGINE - COLUNAS AMARELAS IDENTIFICADAS")
    print("="*60)
    confirmacao = input(f"Data de Referência sugerida (Corte - 1 dia): {sugestao_str}\n"
                        f"Pressione ENTER para aceitar ou digite (AAAA-MM-DD): ")
    return confirmacao.strip() if confirmacao.strip() != "" else str(sugestao_str)

DATA_CORTE = obter_data_referencia()

def carregar_dados_dashboard():
    # 1. LEITURA DA ABA RESUMO (CÉLULAS FIXAS + MUDANÇA PARA COLUNAS AMARELAS)
    df_resumo_raw = pd.read_excel(FILE_CRONO, sheet_name="Resumo", header=None)
    
    try: total_documentos = int(df_resumo_raw.iloc[0, 1])
    except: total_documentos = 0

    try:
        aderencia_val = df_resumo_raw.iloc[1, 1]
        aderencia_global = float(aderencia_val) * 100 if float(aderencia_val) <= 1.0 else float(aderencia_val)
    except:
        aderencia_global = 0.0

    # Carrega a Tabela 2 considerando os cabeçalhos reais corretos
    df_resumo_tabela = pd.read_excel(FILE_CRONO, sheet_name="Resumo", skiprows=3)
    df_resumo_tabela.columns = [str(c).strip() for c in df_resumo_tabela.columns]

    labels_disciplinas = []
    ei_previsto = []
    ei_real = []
    ap_previsto = []
    ap_real = []

    if 'Disciplina' in df_resumo_tabela.columns:
        df_clean = df_resumo_tabela.dropna(subset=['Disciplina'])
        labels_disciplinas = df_clean['Disciplina'].astype(str).tolist()
        
        # Mapeamento estrito das 4 colunas amarelas da imagem para o empilhamento
        def normalizar_lista(col_name):
            if col_name in df_clean.columns:
                return [float(x) * 100 if float(x) <= 1.0 else float(x) for x in df_clean[col_name].fillna(0).tolist()]
            return [0.0] * len(labels_disciplinas)

        ei_previsto = normalizar_lista('Avanço da EI previsto na LB')
        ei_real = normalizar_lista('Avanço real da EI na LB')
        ap_previsto = normalizar_lista('Avanço da AP previsto na LB')
        ap_real = normalizar_lista('Avanço da AP real na LB')

    # 2. OUTRAS ABAS E INTEGRAÇÃO CROSSTAB
    df_base = pd.read_excel(FILE_CRONO, sheet_name="Base")
    df_curva_s = pd.read_excel(FILE_CRONO, sheet_name="Curva S")
    df_ld = pd.read_excel(FILE_PLAN, sheet_name="LD PROJETO")

    df_base.columns = [str(c).strip() for c in df_base.columns]
    df_curva_s.columns = [str(c).strip() for c in df_curva_s.columns]
    df_ld.columns = [str(c).strip() for c in df_ld.columns]

    if '% concluída' in df_base.columns and 'Nome da Tarefa' in df_base.columns:
        docs_100 = df_base[df_base['% concluída'] == 1]['Nome da Tarefa'].astype(str).str.strip().tolist()
        c_ld_name = 'NAME' if 'NAME' in df_ld.columns else df_ld.columns[0]
        c_ld_pct = '%' if '%' in df_ld.columns else df_ld.columns[1]
        
        df_ld['Fin_Calc'] = df_ld.apply(
            lambda r: r[c_ld_pct] if str(r[c_ld_name]).strip() in docs_100 else 0, axis=1
        )
        avanco_financeiro = float(df_ld['Fin_Calc'].sum() * 100)
    else:
        avanco_financeiro = 0.0

    if 'Data' in df_curva_s.columns:
        df_curva_s['Data'] = pd.to_datetime(df_curva_s['Data']).dt.strftime('%Y-%m-%d')
        row_corte = df_curva_s[df_curva_s['Data'] == DATA_CORTE]
        if row_corte.empty: row_corte = df_curva_s.tail(1)
        
        val_ei_real = float(row_corte['Avanço real da EI na LB'].values[0] * 100) if 'Avanço real da EI na LB' in row_corte.columns else 0.0
    else:
        val_ei_real = 0.0

    try: pipeline_docs = df_base.head(5).fillna("-").to_dict(orient='records')
    except: pipeline_docs = []
    try: lookahead_sprint = df_base.tail(5).fillna("-").to_dict(orient='records')
    except: lookahead_sprint = []

    return {
        'data_ref': DATA_CORTE,
        'kpis': {
            'total_documentos': total_documentos,
            'aderencia': round(float(aderencia_global), 1),
            'avanco_ei_real': round(float(val_ei_real), 1),
            'avanco_financeiro': round(float(avanco_financeiro), 1)
        },
        'grafico_empilhado_resumo': {
            'labels': labels_disciplinas,
            'ei_previsto': [round(x, 1) for x in ei_previsto],
            'ei_real': [round(x, 1) for x in ei_real],
            'ap_previsto': [round(x, 1) for x in ap_previsto],
            'ap_real': [round(x, 1) for x in ap_real]
        },
        'curva_s': {
            'datas': df_curva_s['Data'].tolist() if 'Data' in df_curva_s.columns else ["Semana 1"],
            'previsto': [round(float(x)*100, 1) if float(x) <= 1 else round(float(x), 1) for x in df_curva_s['Avanço da EI previsto na LB'].fillna(0).tolist()] if 'Avanço da EI previsto na LB' in df_curva_s.columns else [0],
            'real': [round(float(x)*100, 1) if float(x) <= 1 else round(float(x), 1) for x in df_curva_s['Avanço real da EI na LB'].fillna(0).tolist()] if 'Avanço real da EI na LB' in df_curva_s.columns else [0]
        },
        'pipeline_docs': pipeline_docs,
        'lookahead_sprint': lookahead_sprint
    }

@app.route('/')
def index():
    try:
        data = carregar_dados_dashboard()
        return render_template('index.html', data=data)
    except Exception as e:
        return f"<div style='font-family:sans-serif; padding:40px; background:#fef2f2; color:#991b1b;'><h2>❌ Erro de Processamento:</h2><pre>{str(e)}</pre></div>"

if __name__ == '__main__':
    app.run(debug=False, port=5000)