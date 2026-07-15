import sqlite3

conn = sqlite3.connect('corralon_profesional.db')
c = conn.cursor()
c.execute("SELECT id_documento, fecha_vencimiento FROM documentos WHERE tipo='PRESUPUESTO' AND estado='ACTIVO'")
print(c.fetchall())
