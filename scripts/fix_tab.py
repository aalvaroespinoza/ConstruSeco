import os

file_path = r"ui/modules/stock/tab_stock.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace menu actions
old_menu_code = """                act_ver = QAction("👁 Ver detalle", self)
                act_ver.triggered.connect(lambda checked, prod=p: self.abrir_vista_detalle(prod))
                act_edit = QAction("✏️ Editar", self)
                act_edit.triggered.connect(lambda checked, prod=p: self.abrir_editar(prod))
                act_modificar = QAction("📦 Modificar stock", self)
                act_modificar.triggered.connect(lambda checked, prod=p: self.abrir_modificar_stock(prod))
                act_eliminar = QAction("🗑️ Eliminar/Desactivar", self)
                act_eliminar.triggered.connect(lambda checked, prod=p: self.eliminar_desactivar_producto(prod))
                
                menu.addAction(act_ver)
                menu.addAction(act_edit)
                menu.addAction(act_modificar)
                menu.addSeparator()
                menu.addAction(act_eliminar)
                btn_more.setMenu(menu)"""

new_menu_code = """                act_ver = QAction("👁 Ver detalle", self)
                act_ver.triggered.connect(lambda checked, prod=p: self.abrir_vista_detalle(prod))
                
                act_edit = QAction("✏️ Editar producto", self)
                act_edit.triggered.connect(lambda checked, prod=p: self.abrir_editar(prod))
                
                act_mod_precio = QAction("💲 Modificar precio", self)
                act_mod_precio.triggered.connect(lambda checked, prod=p: self.abrir_modificar_precio(prod))
                
                act_entrada = QAction("📥 Entrada de stock", self)
                act_entrada.triggered.connect(lambda checked, prod=p: self.abrir_modificar_stock(prod, modo='ENTRADA'))
                
                act_ajuste = QAction("📦 Ajuste de stock", self)
                act_ajuste.triggered.connect(lambda checked, prod=p: self.abrir_modificar_stock(prod, modo='AJUSTE'))
                
                act_eliminar = QAction("🗑️ Desactivar / Eliminar", self)
                act_eliminar.triggered.connect(lambda checked, prod=p: self.eliminar_desactivar_producto(prod))
                
                menu.addAction(act_ver)
                menu.addAction(act_edit)
                menu.addAction(act_mod_precio)
                menu.addSeparator()
                menu.addAction(act_entrada)
                menu.addAction(act_ajuste)
                menu.addSeparator()
                menu.addAction(act_eliminar)
                btn_more.setMenu(menu)"""
if old_menu_code in content:
    content = content.replace(old_menu_code, new_menu_code)
else:
    print("Menu code not found!")

# Replace abrir_modificar_stock and add abrir_modificar_precio
old_methods = """    def abrir_editar(self, producto_data):
        dialogo = DialogoEditarProducto(self.conn, producto_data, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()

    def abrir_modificar_stock(self, producto_data):
        dialogo = DialogoModificarStock(self.conn, producto_data, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()"""

new_methods = """    def abrir_editar(self, producto_data):
        dialogo = DialogoEditarProducto(self.conn, producto_data, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()
            
    def abrir_modificar_precio(self, producto_data):
        from ui.modules.stock.dialogs_stock import DialogoModificarPrecio
        dialogo = DialogoModificarPrecio(self.conn, producto_data, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()

    def abrir_modificar_stock(self, producto_data, modo='ENTRADA'):
        dialogo = DialogoModificarStock(self.conn, producto_data, modo, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()"""
if old_methods in content:
    content = content.replace(old_methods, new_methods)
else:
    print("Methods not found!")

# Replace eliminar_desactivar_producto
old_elim = """    def eliminar_desactivar_producto(self, prod):
        codigo = prod['codigo']
        reply = QMessageBox.question(self, 'Confirmar', f'¿Desea eliminar o desactivar el producto {codigo}?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from db.queries_stock import intentar_eliminar_producto
                res = intentar_eliminar_producto(self.conn, codigo)
                if res == "DESACTIVADO":
                    QMessageBox.information(self, "Desactivado", f"El producto {codigo} tiene dependencias y ha sido desactivado.")
                else:
                    QMessageBox.information(self, "Eliminado", f"El producto {codigo} fue eliminado.")
                self.cargar_datos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar/desactivar: {str(e)}")"""

new_elim = """    def eliminar_desactivar_producto(self, prod):
        from ui.modules.stock.dialogs_stock import DialogoDesactivarEliminar
        dialogo = DialogoDesactivarEliminar(self.conn, prod, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()"""
if old_elim in content:
    content = content.replace(old_elim, new_elim)
else:
    print("Elim method not found!")


with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done modifying tab_stock.py")
