import re
filepath = 'ui/modules/stock/tab_stock.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = r'''            c = self\.conn\.cursor\(\)\s*
            c\.execute\(\"UPDATE productos SET activo = 1 WHERE codigo = \?\", \(prod\['codigo'\],\)\)\s*
            self\.conn\.commit\(\)'''

new = '''            from db.queries_stock import reactivar_producto
            reactivar_producto(self.conn, prod['codigo'])'''

content = re.sub(old, new, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated tab_stock.py')
