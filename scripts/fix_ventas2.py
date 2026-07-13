import ast

with open('ui/modules/ventas/tab_ventas.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace migrar_esquema
import re
text = re.sub(
    r'    def migrar_esquema\(self\):.*?self\.conn\.commit\(\)',
    r'''    def migrar_esquema(self):
        from db.queries_ventas import migrar_esquema_ventas
        migrar_esquema_ventas(self.conn)''',
    text,
    flags=re.DOTALL
)

# Replace cargar_clientes
text = re.sub(
    r'    def cargar_clientes\(self\):.*?try:\s*cursor = self\.conn\.cursor\(\)\s*cursor\.execute\(\"SELECT id_cliente, nombre_completo, cuit_dni, telefono FROM clientes WHERE activo = 1\"\)\s*self\.clientes_db = cursor\.fetchall\(\)',
    r'''    def cargar_clientes(self):
        self.input_buscar_cliente.clear()
        try:
            from db.queries_ventas import obtener_clientes_activos_resumen
            self.clientes_db = obtener_clientes_activos_resumen(self.conn)''',
    text,
    flags=re.DOTALL
)

with open('ui/modules/ventas/tab_ventas.py', 'w', encoding='utf-8') as f:
    f.write(text)
