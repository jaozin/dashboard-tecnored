import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "frontend", "templates"),
    static_folder=os.path.join(BASE_DIR, "frontend", "static")
)

# ============================================================
# CAMINHOS
# ============================================================


BANCO = os.path.join(
    BASE_DIR,
    "banco",
    "planejamento.db"
)

print(BANCO)

# ============================================================
# CARREGAR DADOS
# ============================================================

def carregar_dados_dashboard(projeto):

    conn = sqlite3.connect(BANCO)

    try:

        df_projetos = pd.read_sql_query(
            
            """
                SELECT DISTINCT projeto
                FROM kpis
                ORDER BY projeto
                """,
                conn
            )
        projetos = ["INTEGRADO"] + sorted(
        df_projetos["projeto"].tolist()
        )

        df_kpi = pd.read_sql_query(
            """
            SELECT *
            FROM kpis
            WHERE projeto = ?
            """,
            conn,
            params=[projeto]
        )
        df_resumo = pd.read_sql_query(
            """
            SELECT *
            FROM resumo_disciplinas
            WHERE projeto = ?
            """,
            conn,
            params=[projeto]
        )          
        df_documentos_emitir = pd.read_sql_query(
            """
            SELECT DISTINCT
            documento,
            disciplina,
            tarefa
            FROM tarefas
            WHERE projeto = ?
            AND sprint = 'Sprint Atual'
            AND LOWER(tarefa) = 'emissão inicial'
            ORDER BY documento
            """,
            conn,
            params=[projeto]
            )
        
        df_avaliacao_cliente = pd.read_sql_query(
            """
            SELECT DISTINCT
            documento,
            disciplina,
            tarefa
            FROM tarefas
            WHERE projeto = ?
            AND sprint = 'Sprint Atual'
            AND (
            LOWER(tarefa) LIKE '%análise tecnored%'
            OR LOWER(tarefa) LIKE '%analise tecnored%'
            OR LOWER(tarefa) LIKE '%avaliação do cliente%'
            OR LOWER(tarefa) LIKE '%avaliacao do cliente%'
             )
             
             ORDER BY documento
            """,
            conn,
            params=[projeto]
            )

        df_atendimento_comentario = pd.read_sql_query(
            """
            SELECT DISTINCT
                documento,
                disciplina,
                tarefa
            FROM tarefas
            WHERE projeto = ?
            AND sprint = 'Sprint Atual'
            AND (
                LOWER(tarefa) LIKE '%atendimento de comentário%'
                OR LOWER(tarefa) LIKE '%atendimento de comentarios%'
                OR LOWER(tarefa) LIKE '%atendimento de comentario%'
            )
            ORDER BY documento
            """,
            conn,
            params=[projeto]
        )

        df_aprovacao = pd.read_sql_query(
            """
            SELECT DISTINCT
            documento,
            disciplina,
            tarefa
            FROM tarefas
            WHERE projeto = ?
            AND sprint = 'Sprint Atual'
            AND (
            LOWER(tarefa) LIKE '%aprovação%'
            OR LOWER(tarefa) LIKE '%aprovacao%'
            )
            ORDER BY documento
            """,
            conn,
            params=[projeto]
        )

        df_prox_emitir = pd.read_sql_query(
            """
            SELECT DISTINCT
            documento,
            disciplina,
            tarefa
            FROM tarefas
            WHERE projeto = ?
            AND sprint = 'Próximo Sprint'
            AND (
            LOWER(tarefa) LIKE '%emissão inicial%'
            OR LOWER(tarefa) LIKE '%emissao inicial%'
            )
            ORDER BY documento
            """,
            conn,
            params=[projeto]
        )
        df_prox_avaliacao = pd.read_sql_query(
            """
            SELECT DISTINCT
            documento,
            disciplina,
            tarefa
            FROM tarefas
            WHERE projeto = ?
            AND sprint = 'Próximo Sprint'
            AND (
            LOWER(tarefa) LIKE '%análise tecnored%'
            OR LOWER(tarefa) LIKE '%analise tecnored%'
            OR LOWER(tarefa) LIKE '%avaliação do cliente%'
            OR LOWER(tarefa) LIKE '%avaliacao do cliente%'
            )
            ORDER BY documento
            """,
            conn,
            params=[projeto]
        )

        df_prox_comentario = pd.read_sql_query(
            """
            SELECT DISTINCT
            documento,
            disciplina,
            tarefa
            FROM tarefas
            WHERE projeto = ?
            AND sprint = 'Próximo Sprint'
            AND (
            LOWER(tarefa) LIKE '%atendimento de comentário%'
            OR LOWER(tarefa) LIKE '%atendimento de comentarios%'
            OR LOWER(tarefa) LIKE '%atendimento de comentario%'
            )
            ORDER BY documento
            """,
            conn,
            params=[projeto]
        )
        df_prox_aprovacao = pd.read_sql_query(
            """
            SELECT DISTINCT
                documento,
                disciplina,
                tarefa
            FROM tarefas
            WHERE projeto = ?
            AND sprint = 'Próximo Sprint'
            AND (
                LOWER(tarefa) LIKE '%aprovação%'
                OR LOWER(tarefa) LIKE '%aprovacao%'
            )
            ORDER BY documento
            """,
            conn,
            params=[projeto]
        )

        df_curva = pd.read_sql_query(
            """
            SELECT *
            FROM curva_s
            WHERE projeto = ?
            """,
            conn,
            params=[projeto]
        )
        data_comp = df_kpi["data_comparativo"].iloc[0]

        data_comp = pd.to_datetime(
            data_comp,
            format="%d-%m-%Y"
        )

        df_curva["data"] = pd.to_datetime(
            df_curva["data"]
        )

        df_curva_filtrada = df_curva[
            df_curva["data"] <= data_comp
        ]

        if len(df_curva_filtrada) > 0:

            linha_curva = df_curva_filtrada.iloc[-1]

        else:

            linha_curva = df_curva.iloc[-1]

        ei_previsto_pct = float(
        linha_curva["ei_previsto"]
        )

        ap_previsto_pct = float(
        linha_curva["ap_previsto"]
        )

        ei_real_pct = float(
            linha_curva["ei_real"]
        )
        df_resumo["emissao_prevista"] = (
        df_resumo["ei_total"]
        *ei_previsto_pct
        ).round().astype(int)

        df_resumo["aprovacao_prevista"] = (
            df_resumo["ei_total"]
            * ap_previsto_pct
        ).round().astype(int)

        if len(df_kpi) > 0:

                total_documentos = int(
                    df_kpi["numero_documentos"].iloc[0]
                )

                aderencia = round(
                    float(df_kpi["aderencia"].iloc[0]) * 100,
                    1
                )

        else:

                total_documentos = 0
                aderencia = 0
        dados = {

            "projetos": projetos,


            "documentos_emitir": (
                df_documentos_emitir
                .fillna("")
                .to_dict(orient="records")
            ),

            "avaliacao_cliente": (
                df_avaliacao_cliente
                .fillna("")
                .to_dict(orient="records")
            ),

            "atendimento_comentario": (
                df_atendimento_comentario
                .fillna("")
                .to_dict(orient="records")
            ),  
            
            "aprovacao": (
                df_aprovacao
                .fillna("")
                .to_dict(orient="records")
            ),

            "prox_emitir": (
                df_prox_emitir
                .fillna("")
                .to_dict(orient="records")
            ),
            "prox_avaliacao": (
                df_prox_avaliacao
                .fillna("")
                .to_dict(orient="records")
            ),

            "prox_comentario": (
                df_prox_comentario
                .fillna("")
                .to_dict(orient="records")
            ),
            "prox_aprovacao": (
                df_prox_aprovacao
                .fillna("")
                .to_dict(orient="records")
            ),

            "resumo_disciplinas": (
                df_resumo
                .fillna(0)
                .to_dict(orient="records")
            ),
            "kpis": {

                "total_documentos": total_documentos,
                "aderencia": round(aderencia, 1),

                "avanco_ei_real": round(
                    ei_real_pct * 100,
                    1
                ),
                "avanco_financeiro": 0
            },
            
            "grafico_empilhado_resumo": {

                "labels": df_resumo["disciplina"].tolist(),

                "emissao_prevista": (
                    df_resumo["emissao_prevista"]
                    .round(1)
                    .tolist()
                ),              
          
                "emissao_real": (
                    df_resumo["ei_concluida"]
                    .round(1)
                    .tolist()
                ),      

                "aprovacao_prevista": (
                    df_resumo["aprovacao_prevista"]
                    .round(1)
                    .tolist()
                ),              
                
                "aprovacao_real": (
                    df_resumo["aprovacao_concluida"]
                    .round(1)
                    .tolist()
                ),
            },
                "curva_s": {

                    "datas": df_curva["data"].dt.strftime("%d/%m").tolist(),

                    "previsto": (
                        df_curva["ei_previsto_acumulado"]
                        .fillna(0)
                        .round(0)
                        .astype(int)
                        .tolist()
                    ),

                    "real": (
                        df_curva["ei_real_acumulado"]
                        .fillna(0)
                        .round(0)
                        .astype(int)
                        .tolist()
                    )
            },  
                "funil": {

                    "emitidos": int(
                        df_resumo["ei_concluida"].sum()
                    ),

                    "avaliacao": int(
                        df_resumo["avaliacao_cliente"].sum()
                    ),

                    "comentarios": int(
                        df_resumo["atendimento_comentario"].sum()
                    ),

                    "aprovados": int(
                        df_resumo["aprovacao_concluida"].sum()
                    )

                },

        }
        return dados

    finally:

        conn.close()

# ============================================================
# ROTA PRINCIPAL
# ============================================================

@app.route("/")
def index():

    try:

        projeto = request.args.get(
            "projeto",
            "F0009_000"
        )

        data = carregar_dados_dashboard(
            projeto
        )

        return render_template(
            "index.html",
            data=data,
            projeto_selecionado=projeto
        )

    except Exception as e:

        return f"""
        <h2>Erro</h2>
        <pre>{str(e)}</pre>
        """

# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
