import sqlite3

conn = sqlite3.connect('corralon_profesional.db')
c = conn.cursor()
for row in c.execute("SELECT name, sql FROM sqlite_master WHERE type='table'"):
    if row[0] in ('documentos', 'compromisos_stock'):
        print(row[1])
