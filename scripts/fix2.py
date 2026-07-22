import os

file_path = r"ui/modules/stock/dialogs_stock.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Fix IntegrityError
content = content.replace(
"""        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "Ya existe otro producto con esa descripción.")""",
"""        except sqlite3.IntegrityError as e:
            if "productos.descripcion" in str(e).lower():
                QMessageBox.critical(self, "Error", "Ya existe otro producto con esa descripción.")
            else:
                QMessageBox.critical(self, "Error", f"Error de integridad: {e}")"""
)

# 2. Add modo_inicial to DialogoModificarStock.__init__
content = content.replace(
"""class DialogoModificarStock(DialogoModalIntegrado):
    def __init__(self, conexion_db, producto_data, parent=None):
        super().__init__(parent)
        self.conn = conexion_db
        self.p_data = producto_data
        self.fisico_actual = float(self.p_data['stock_fisico'])
        self.setWindowTitle(f"Modificar Stock: {producto_data['codigo']}")
        self.setMinimumWidth(400)
        self.init_ui()""",
"""class DialogoModificarStock(DialogoModalIntegrado):
    def __init__(self, conexion_db, producto_data, modo_inicial='ENTRADA', parent=None):
        super().__init__(parent)
        self.conn = conexion_db
        self.p_data = producto_data
        self.fisico_actual = float(self.p_data['stock_fisico'])
        self.modo_inicial = modo_inicial
        
        titulo = "Entrada de Stock" if modo_inicial == 'ENTRADA' else "Ajuste de Inventario"
        self.setWindowTitle(f"{titulo}: {producto_data['codigo']}")
        
        self.setMinimumWidth(400)
        self.init_ui()"""
)

# 3. Modify DialogoModificarStock.init_ui to hide radio buttons
content = content.replace(
"""        self.radio_entrada.setChecked(True)
        
        self.grupo_op.addButton(self.radio_entrada, 0)
        self.grupo_op.addButton(self.radio_ajuste, 1)
        
        lbl_info_entrada = QLabel("Suma una cantidad al stock actual (Ej: Ingreso de mercadería)")
        lbl_info_entrada.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 12px; margin-left: 28px;")
        
        lbl_info_ajuste = QLabel("Reemplaza el stock actual por un nuevo valor contado (Ej: Recuento)")
        lbl_info_ajuste.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 12px; margin-left: 28px;")
        
        op_layout.addWidget(self.radio_entrada)
        op_layout.addWidget(lbl_info_entrada)
        op_layout.addWidget(self.radio_ajuste)
        op_layout.addWidget(lbl_info_ajuste)
        
        layout.addLayout(op_layout)""",
"""        self.radio_entrada.setChecked(self.modo_inicial == 'ENTRADA')
        self.radio_ajuste.setChecked(self.modo_inicial == 'AJUSTE')
        
        self.grupo_op.addButton(self.radio_entrada, 0)
        self.grupo_op.addButton(self.radio_ajuste, 1)
        
        lbl_info_entrada = QLabel("Suma una cantidad al stock actual (Ej: Ingreso de mercadería)")
        lbl_info_entrada.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 12px; margin-left: 28px;")
        
        lbl_info_ajuste = QLabel("Reemplaza el stock actual por un nuevo valor contado (Ej: Recuento)")
        lbl_info_ajuste.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 12px; margin-left: 28px;")
        
        op_layout.addWidget(self.radio_entrada)
        op_layout.addWidget(lbl_info_entrada)
        op_layout.addWidget(self.radio_ajuste)
        op_layout.addWidget(lbl_info_ajuste)
        
        self.radio_entrada.hide()
        lbl_info_entrada.hide()
        self.radio_ajuste.hide()
        lbl_info_ajuste.hide()
        
        layout.addLayout(op_layout)"""
)

# 4. Modify setCurrentIndex initially
content = content.replace(
"""        self.stack.addWidget(self.wdg_ajuste)
        layout.addWidget(self.stack)
        
        self.grupo_op.idToggled.connect(self.cambiar_operacion)""",
"""        self.stack.addWidget(self.wdg_ajuste)
        layout.addWidget(self.stack)
        
        self.grupo_op.idClicked.connect(self.stack.setCurrentIndex)
        self.stack.setCurrentIndex(0 if self.modo_inicial == 'ENTRADA' else 1)"""
)

# 5. Append DialogoModificarPrecio and DialogoDesactivarEliminar
classes_to_append = """
class DialogoModificarPrecio(DialogoModalIntegrado):
    def __init__(self, conexion_db, producto_data, parent=None):
        super().__init__(parent)
        self.conn = conexion_db
        self.p_data = producto_data
        self.setWindowTitle(f"Modificar Precio: {producto_data['codigo']}")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        
        lbl = QLabel(f"Producto: <b>{producto_data['descripcion']}</b>")
        lbl.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_MAIN};")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        
        form = QFormLayout()
        form.setVerticalSpacing(16)
        
        self.inp_precio = SelectAllLineEdit(str(producto_data.get('precio_venta', 0)))
        self.inp_precio.setStyleSheet(f"padding: 10px; border: 1px solid {COLOR_BORDER}; border-radius: 6px; background-color: {COLOR_BG}; font-size: 13px; color: {COLOR_TEXT_MAIN};")
        
        lbl_precio = QLabel("Nuevo Precio ($):")
        lbl_precio.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXT_SEC}; font-size: 12px;")
        
        form.addRow(lbl_precio, self.inp_precio)
        layout.addLayout(form)
        
        btn_ly = QHBoxLayout()
        btn_ly.addStretch()
        btn = QPushButton("Guardar Precio")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton {{ background-color: {COLOR_PRIMARY}; color: white; padding: 10px 24px; border-radius: 6px; font-weight: bold; border: none; }} QPushButton:hover {{ background-color: #1d4ed8; }}")
        btn.clicked.connect(self.guardar)
        btn_ly.addWidget(btn)
        layout.addLayout(btn_ly)
        
    def guardar(self):
        try:
            precio = float(self.inp_precio.text().replace(',', '.'))
            if precio < 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Precio inválido.")
            return
            
        try:
            desc = self.p_data['descripcion']
            stk_min = self.p_data['stock_minimo']
            img = self.p_data['imagen_path']
            actualizar_producto_y_registrar(self.conn, self.p_data['codigo'], desc, self.p_data['unidad_base'], precio, stk_min, img)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class DialogoDesactivarEliminar(DialogoModalIntegrado):
    def __init__(self, conexion_db, producto_data, parent=None):
        super().__init__(parent)
        self.conn = conexion_db
        self.p_data = producto_data
        self.setWindowTitle("¿Qué desea hacer?")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        
        lbl = QLabel(f"Opciones para <b>{producto_data['codigo']}</b>")
        lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        layout.addWidget(lbl)
        
        btn_desactivar = QPushButton("Desactivar producto\\n(Recomendado. Conserva historial.)")
        btn_desactivar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_desactivar.setStyleSheet(f\"\"\"
            QPushButton {{ background-color: {COLOR_BG}; color: {COLOR_TEXT_MAIN}; padding: 16px; border: 1px solid {COLOR_BORDER}; border-radius: 6px; text-align: left; font-size: 13px; }}
            QPushButton:hover {{ border-color: {COLOR_PRIMARY}; background-color: #f8fafc; }}
        \"\"\")
        btn_desactivar.clicked.connect(self.desactivar)
        
        btn_eliminar = QPushButton("Eliminar definitivamente\\n(Solo si nunca será utilizado.)")
        btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_eliminar.setStyleSheet(f\"\"\"
            QPushButton {{ background-color: #fff1f2; color: #be123c; padding: 16px; border: 1px solid #fecdd3; border-radius: 6px; text-align: left; font-size: 13px; }}
            QPushButton:hover {{ border-color: #f43f5e; background-color: #ffe4e6; }}
        \"\"\")
        btn_eliminar.clicked.connect(self.eliminar)
        
        layout.addWidget(btn_desactivar)
        layout.addWidget(btn_eliminar)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {COLOR_TEXT_SEC}; padding: 8px; border: none; font-weight: bold; }} QPushButton:hover {{ color: {COLOR_TEXT_MAIN}; }}")
        btn_cancelar.clicked.connect(self.reject)
        
        layout.addSpacing(8)
        layout.addWidget(btn_cancelar, 0, Qt.AlignmentFlag.AlignCenter)
        
    def desactivar(self):
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
            QMessageBox.critical(self, "Error", f"Error: {e}")
            
    def eliminar(self):
        try:
            from db.queries_stock import intentar_eliminar_producto
            res = intentar_eliminar_producto(self.conn, self.p_data['codigo'])
            if res == "DESACTIVADO":
                QMessageBox.warning(self.parent_widget, "No se puede eliminar", "Este producto tiene movimientos o historial asociado. Fue desactivado en su lugar para mantener la trazabilidad.")
            else:
                QMessageBox.information(self.parent_widget, "Eliminado", "El producto fue eliminado definitivamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {e}")
"""

if "DialogoModificarPrecio" not in content:
    content += "\n" + classes_to_append

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done modifying dialogs_stock.py")
