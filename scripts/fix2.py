import re
filepath = 'ui/modules/stock/dialogs_stock.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_block1 = r'''        c = self\.conn\.cursor\(\)\s*
        try:
            c\.execute\(\"BEGIN TRANSACTION;\"\)\s*
            
            # Chequear dependencias
            c\.execute\(\"SELECT COUNT\(\*\) FROM detalle_documentos WHERE codigo_producto=\?\", \(cod,\)\)\s*
            c_doc = c\.fetchone\(\)\[0\]\s*
            c\.execute\(\"SELECT COUNT\(\*\) FROM movimientos_stock WHERE codigo_producto=\?\", \(cod,\)\)\s*
            c_mov = c\.fetchone\(\)\[0\]\s*
            c\.execute\(\"SELECT COUNT\(\*\) FROM compromisos_stock WHERE codigo_producto=\?\", \(cod,\)\)\s*
            c_comp = c\.fetchone\(\)\[0\]\s*
            
            if c_doc > 0 or c_mov > 0 or c_comp > 0:
                # Tiene historial, desactivar
                c\.execute\(\"UPDATE productos SET activo = 0 WHERE codigo = \?\", \(cod,\)\)\s*
                self\.conn\.commit\(\)\s*
                QMessageBox\.information\(
                    self, \"Producto Desactivado\",
                    \"Este producto tiene historial asociado y no puede eliminarse definitivamente sin perder trazabilidad\. Ha sido desactivado\.\"
                \)\s*
            else:
                # Sin historial, eliminar fisicamente
                c\.execute\(\"DELETE FROM productos WHERE codigo = \?\", \(cod,\)\)\s*
                self\.conn\.commit\(\)\s*
                QMessageBox\.information\(self, \"Eliminado\", \"El producto fue eliminado definitivamente\.\"\)\s*
                
            self\.accept\(\)\s*
        except Exception as e:
            self\.conn\.rollback\(\)\s*
            QMessageBox\.critical\(self, \"Error\", f\"No se pudo eliminar: \{e\}\"\)'''

new_block1 = '''        try:
            resultado = intentar_eliminar_producto(self.conn, cod)
            if resultado == "DESACTIVADO":
                QMessageBox.information(
                    self, "Producto Desactivado",
                    "Este producto tiene historial asociado y no puede eliminarse definitivamente sin perder trazabilidad. Ha sido desactivado."
                )
            else:
                QMessageBox.information(self, "Eliminado", "El producto fue eliminado definitivamente.")
                
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar: {e}")'''

content = re.sub(old_block1, new_block1, content)

old_block2 = r'''        c = self\.conn\.cursor\(\)\s*
        try:
            c\.execute\(\"BEGIN TRANSACTION;\"\)\s*
            c\.execute\(\"\"\"\s*
                UPDATE productos 
                SET descripcion = \?, precio_venta = \?, stock_minimo = \?, imagen_path = \?
                WHERE codigo = \?
            \"\"\", \(desc, precio, stk_min, final_img, cod\)\)\s*
            self\.conn\.commit\(\)\s*
            QMessageBox\.information\(self, \"Éxito\", \"Producto actualizado\.\"\)\s*
            self\.accept\(\)\s*
        except sqlite3\.IntegrityError:
            self\.conn\.rollback\(\)\s*
            QMessageBox\.critical\(self, \"Error\", \"Ya existe otro producto con esa descripción\.\"\)\s*
        except Exception as e:
            self\.conn\.rollback\(\)\s*
            QMessageBox\.critical\(self, \"Error\", str\(e\)\)'''

new_block2 = '''        try:
            actualizar_producto_y_registrar(self.conn, cod, desc, self.p_data['unidad_base'], precio, stk_min, final_img)
            QMessageBox.information(self, "Éxito", "Producto actualizado.")
            self.accept()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "Ya existe otro producto con esa descripción.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))'''

content = re.sub(old_block2, new_block2, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated dialogs_stock.py')
