import re

with open('ui/modules/stock/ajustes_stock.py', 'r', encoding='utf-8') as f:
    text = f.read()

new = '''        from db.queries_stock import ejecutar_consulta_historial
        filas = ejecutar_consulta_historial(self.conn, sql, params)'''
text = text.replace('''        c = self.conn.cursor()
        c.execute(sql, params)
        filas = c.fetchall()''', new)

with open('ui/modules/stock/ajustes_stock.py', 'w', encoding='utf-8') as f:
    f.write(text)


with open('ui/modules/stock/excel_stock.py', 'r', encoding='utf-8') as f:
    text2 = f.read()

new2 = '''        from db.queries_stock import obtener_productos_activos_exportacion
        existentes = obtener_productos_activos_exportacion(self.conn)'''
text2 = text2.replace('''        c = self.conn.cursor()
        c.execute("SELECT codigo, lower(descripcion) FROM productos WHERE activo = 1")
        existentes = c.fetchall()''', new2)

with open('ui/modules/stock/excel_stock.py', 'w', encoding='utf-8') as f:
    f.write(text2)
