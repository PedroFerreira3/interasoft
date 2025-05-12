import sqlite3
conn = sqlite3.connect('db.sqlite3')
print("Tabelas existentes:")
print(conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
print("\nEstrutura de cursos_capitulo:")
print(conn.execute("PRAGMA table_info('cursos_capitulo')").fetchall())
conn.close()