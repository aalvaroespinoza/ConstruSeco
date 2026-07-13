import re

with open('ui/modules/stock/ajustes_stock.py', 'r', encoding='utf-8') as f:
    text = f.read()

new = '''        from db.queries_stock import ejecutar_consulta_historial
        movimientos = ejecutar_consulta_historial(self.conn, sql, params)'''
text = re.sub(r'c = self\.conn\.cursor\(\)\s*c\.execute\(sql, params\)\s*movimientos = c\.fetchall\(\)', new, text)

with open('ui/modules/stock/ajustes_stock.py', 'w', encoding='utf-8') as f:
    f.write(text)


with open('ui/modules/stock/excel_stock.py', 'r', encoding='utf-8') as f:
    text2 = f.read()

new1 = '''        from db.queries_stock import obtener_productos_activos_exportacion
        productos_bd = obtener_productos_activos_exportacion(conn)'''
text2 = re.sub(r'c = conn\.cursor\(\)\s*c\.execute\(\"SELECT codigo, lower\(descripcion\) FROM productos WHERE activo = 1\"\)\s*productos_bd = c\.fetchall\(\)', new1, text2)

new2 = r'''            from db.queries_stock import ejecutar_importacion_excel
            ejecutar_importacion_excel(self.conn, self.modo_importacion, self.filas_validas)
            QMessageBox.information(self, "Éxito", f"Se procesaron {len(self.filas_validas)} productos exitosamente.")
            self.accept()
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "Error Fatal", f"La importación falló y se revirtió. Detalles:\n{e}")'''

text2 = re.sub(r'c = self\.conn\.cursor\(\)\s*try:\s*c\.execute\(\"BEGIN TRANSACTION;\"\).*?QMessageBox\.critical\(self, \"Error Fatal\", f\"La importacin fall y se revirti\. Detalles:\\n\{e\}\"\)', new2, text2, flags=re.DOTALL)
text2 = re.sub(r'c = self\.conn\.cursor\(\)\s*try:\s*c\.execute\(\"BEGIN TRANSACTION;\"\).*?QMessageBox\.critical\(self, \"Error Fatal\", f\"La importación falló y se revirtió\. Detalles:\\n\{e\}\"\)', new2, text2, flags=re.DOTALL)

with open('ui/modules/stock/excel_stock.py', 'w', encoding='utf-8') as f:
    f.write(text2)
