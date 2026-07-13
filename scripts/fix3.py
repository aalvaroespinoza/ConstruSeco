import re
filepath = 'ui/modules/stock/ajustes_stock.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = r'''        c = self\.conn\.cursor\(\)\s*
        c\.execute\(sql, params\)\s*
        movimientos = c\.fetchall\(\)'''

new_block = '''        from db.queries_stock import ejecutar_consulta_historial
        movimientos = ejecutar_consulta_historial(self.conn, sql, params)'''

content = re.sub(old_block, new_block, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated ajustes_stock.py')
