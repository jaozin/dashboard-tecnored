import sqlite3

conn = sqlite3.connect("banco/planejamento.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM acoes_usuario")

conn.commit()
conn.close()

print("Tabela acoes_usuario limpa com sucesso.")