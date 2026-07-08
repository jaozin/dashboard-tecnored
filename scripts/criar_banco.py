import sqlite3
import os

# ============================================================
# PASTA DO PROJETO
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# PASTA DO BANCO
# ============================================================

BANCO_DIR = os.path.join(BASE_DIR, "banco")
os.makedirs(BANCO_DIR, exist_ok=True)

# ============================================================
# ARQUIVO DO BANCO
# ============================================================

caminho_banco = os.path.join(BANCO_DIR, "planejamento.db")

print("Banco localizado em:")
print(caminho_banco)

# ============================================================
# CONEXÃO
# ============================================================

conn = sqlite3.connect(caminho_banco)
cursor = conn.cursor()

# ============================================================
# TABELA TAREFAS
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS tarefas (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    projeto TEXT NOT NULL,

    documento TEXT NOT NULL,

    sprint TEXT,

    id_tarefa INTEGER,

    edt TEXT,

    tarefa TEXT,

    responsavel TEXT,

    disciplina TEXT,

    critica TEXT,

    emitido TEXT DEFAULT 'Não',

    data_comparativo TEXT,

    data_importacao TEXT,

    UNIQUE (
        projeto,
        documento,
        sprint,
        tarefa
    )
)
""")

# ============================================================
# TABELA HISTORICO
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS historico (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    projeto TEXT,

    documento TEXT,

    tarefa TEXT,

    acao TEXT,

    usuario TEXT,

    data_hora TEXT
)
""")

# ============================================================
# TABELA KPIS
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS kpis (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    projeto TEXT NOT NULL,

    data_comparativo TEXT,

    numero_documentos INTEGER,

    aderencia REAL,

    percentual_ei REAL,

    percentual_ap REAL,

    data_importacao TEXT
)
""")

# ============================================================
# TABELA CURVA S
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS curva_s (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    projeto TEXT NOT NULL,

    data_comparativo TEXT,

    data TEXT,

    ei_previsto REAL,

    ei_real REAL,

    ap_previsto REAL,

    ap_real REAL,
    ei_previsto_acumulado REAL,
    ei_real_acumulado REAL,

    ap_previsto_acumulado REAL,
    ap_real_acumulado REAL,           

    data_importacao TEXT
)
""")

# ============================================================
# TABELA RESUMO DISCIPLINAS
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS resumo_disciplinas (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    projeto TEXT NOT NULL,

    data_comparativo TEXT,

    disciplina TEXT,

    ei_total REAL,
    ei_concluida REAL,
    percentual_ei REAL,

    avaliacao_cliente REAL,

    atendimento_comentario REAL,

    aprovacao_concluida REAL,
    percentual_ap REAL,

    data_importacao TEXT

)
""")


# ============================================================
# FINALIZAR
# ============================================================

conn.commit()
conn.close()

print("\n✅ Tabela tarefas OK")
print("✅ Tabela historico OK")
print("✅ Tabela kpis OK")
print("✅ Tabela curva_s OK")
print("✅ Tabela resumo_disciplinas OK")
print("✅ Banco pronto")