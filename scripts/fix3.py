import os

file_path = r"ui/modules/stock/dialogs_stock.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_desactivar = """    def desactivar(self):
        try:
            from db.queries_stock import intentar_eliminar_producto
            # Si intentamos desactivarlo, asumiendo que intentar_eliminar_producto intenta eliminar, y si no puede lo desactiva.
            # En realidad, si queremos solo desactivarlo directamente...
            # The codebase uses `intentar_eliminar_producto` which already does this logic.
            res = intentar_eliminar_producto(self.conn, self.p_data['codigo'])
            if res == "DESACTIVADO":
                QMessageBox.information(self.parent_widget, "Desactivado", "Este producto tiene historial asociado y no puede eliminarse definitivamente. Ha sido desactivado.")
            else:
                QMessageBox.information(self.parent_widget, "Desactivado", "El producto fue desactivado.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {e}")"""

new_desactivar = """    def desactivar(self):
        try:
            c = self.conn.cursor()
            c.execute("UPDATE productos SET activo=0 WHERE codigo=?", (self.p_data['codigo'],))
            self.conn.commit()
            QMessageBox.information(self.parent_widget, "Desactivado", "El producto fue desactivado correctamente y ya no aparecerá en el catálogo activo.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {e}")"""

if old_desactivar in content:
    content = content.replace(old_desactivar, new_desactivar)
else:
    print("Old desactivar not found!")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done modifying desactivar in dialogs_stock.py")
