import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QMessageBox, QComboBox, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QCursor

from db.queries import UNIDADES_PERMITIDAS
from ui.core.modal import DialogoModalIntegrado

# Rutas

from ui.core.theme import (
    COLOR_PRIMARY, COLOR_BG, COLOR_CARD_BG,
    COLOR_BORDER, COLOR_TEXT_MAIN, COLOR_TEXT_SEC, COLOR_DANGER
)


from db.queries_stock import (
    obtener_detalles_producto, crear_producto_con_stock_inicial,
    sumar_stock_producto_existente, actualizar_producto_y_registrar,
    obtener_imagen_path, intentar_eliminar_producto,
    actualizar_stock_minimo, registrar_ingreso_manual,
    registrar_ajuste_inventario
)

from ui.components.image_selector import ImageSelectorWidget, resolver_ruta_imagen, ASSETS_PROD_DIR

class SelectAllLineEdit(QLineEdit):
    def mousePressEvent(self, event):
        was_focused = self.hasFocus()
        super().mousePressEvent(event)
        if not was_focused:
            self.selectAll()

# =====================================================================
# DIÁLOGOS DE PRODUCTOS
# =====================================================================


class DialogoAgregarProducto(DialogoModalIntegrado):
    def __init__(self, conexion_db, parent=None):
        super().__init__(parent)
        self.conn = conexion_db
        self.setWindowTitle("Nuevo Producto")
        self.setMinimumWidth(400)
        self.es_existente = False
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Imagen
        img_layout = QHBoxLayout()
        img_layout.addStretch()
        self.img_selector = ImageSelectorWidget()
        img_layout.addWidget(self.img_selector)
        img_layout.addStretch()
        main_layout.addLayout(img_layout)
        
        # Formulario
        self.form = QFormLayout()
        
        self.inp_codigo = SelectAllLineEdit()
        self.inp_desc = SelectAllLineEdit()
        
        self.cmb_unidad = QComboBox()
        for v, l in UNIDADES_PERMITIDAS:
            self.cmb_unidad.addItem(l, userData=v)
            
        self.inp_precio = SelectAllLineEdit("0.0")
        self.inp_stock_ini = SelectAllLineEdit("0.0")
        
        self.err_codigo = QLabel()
        self.err_codigo.setStyleSheet("color: red; font-size: 11px;")
        self.err_codigo.hide()
        
        self.err_desc = QLabel()
        self.err_desc.setStyleSheet("color: red; font-size: 11px;")
        self.err_desc.hide()
        
        self.err_precio = QLabel()
        self.err_precio.setStyleSheet("color: red; font-size: 11px;")
        self.err_precio.hide()
        
        self.err_stock = QLabel()
        self.err_stock.setStyleSheet("color: red; font-size: 11px;")
        self.err_stock.hide()
        
        def add_validated_row(titulo, widget, err_lbl):
            ly = QVBoxLayout()
            ly.setContentsMargins(0,0,0,0)
            ly.setSpacing(2)
            ly.addWidget(widget)
            ly.addWidget(err_lbl)
            self.form.addRow(titulo, ly)
            widget.textChanged.connect(lambda: (widget.setStyleSheet(""), err_lbl.hide()))
        
        add_validated_row("Código (*):", self.inp_codigo, self.err_codigo)
        add_validated_row("Nombre o Producto (*):", self.inp_desc, self.err_desc)
        self.form.addRow("Unidad:", self.cmb_unidad)
        add_validated_row("Precio Venta ($):", self.inp_precio, self.err_precio)
        
        self.lbl_lbl_stock = QLabel("Cantidad (Agregar Stock):")
        ly_stk = QVBoxLayout()
        ly_stk.setContentsMargins(0,0,0,0)
        ly_stk.setSpacing(2)
        ly_stk.addWidget(self.inp_stock_ini)
        ly_stk.addWidget(self.err_stock)
        self.form.addRow(self.lbl_lbl_stock, ly_stk)
        self.inp_stock_ini.textChanged.connect(lambda: (self.inp_stock_ini.setStyleSheet(""), self.err_stock.hide()))
        
        main_layout.addLayout(self.form)
        
        self.btn_guardar = QPushButton("Guardar Producto")
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setStyleSheet(f"background-color: {COLOR_PRIMARY}; color: white; padding: 10px; border-radius: 4px; font-weight: bold;")
        self.btn_guardar.clicked.connect(self.guardar)
        main_layout.addWidget(self.btn_guardar)
        
        self.inp_codigo.textChanged.connect(self._verificar_codigo)

    def _verificar_codigo(self, text):
        cod = text.strip()
        if not cod:
            self._set_modo_existente(False)
            return
            
        row = obtener_detalles_producto(self.conn, cod)
        
        if row:
            desc, unidad, precio, min_stock, img = row
            self.inp_desc.setText(desc)
            self.inp_precio.setText(f"{precio:g}")
            idx = self.cmb_unidad.findData(unidad)
            if idx >= 0:
                self.cmb_unidad.setCurrentIndex(idx)
                
            self.img_selector.image_path = img
            self.img_selector._update_preview()
            
            self._set_modo_existente(True)
        else:
            self._set_modo_existente(False)
            
    def _set_modo_existente(self, existe):
        self.es_existente = existe
        disabled_style = "background-color: #f1f5f9; color: #64748b; border: 1px solid #e2e8f0;"
        normal_style = ""
        
        if existe:
            self.setWindowTitle("Agregar Stock a Producto Existente")
            self.btn_guardar.setText("Sumar Stock")
            self.lbl_lbl_stock.setText("Cantidad a Sumar (*):")
            
            self.inp_desc.setReadOnly(True)
            self.inp_precio.setReadOnly(True)
            self.cmb_unidad.setEnabled(False)
            
            self.inp_desc.setStyleSheet(disabled_style)
            self.inp_precio.setStyleSheet(disabled_style)
            
            self.img_selector.btn_select.setEnabled(False)
            self.img_selector.btn_clear.setEnabled(False)
            self.img_selector.setStyleSheet(f"border: 2px dashed #cbd5e1; border-radius: 6px; background-color: #f8fafc;")
        else:
            self.setWindowTitle("Nuevo Producto")
            self.btn_guardar.setText("Guardar Producto")
            self.lbl_lbl_stock.setText("Stock Inicial:")
            
            self.inp_desc.setReadOnly(False)
            self.inp_precio.setReadOnly(False)
            self.cmb_unidad.setEnabled(True)
            
            self.inp_desc.setStyleSheet(normal_style)
            self.inp_precio.setStyleSheet(normal_style)
            
            self.img_selector.btn_select.setEnabled(True)
            self.img_selector.btn_clear.setEnabled(True)
            self.img_selector.setStyleSheet(f"border: 2px dashed {COLOR_BORDER}; border-radius: 6px; background-color: {COLOR_BG};")
            
            # Limpiar labels de error si estaban visibles por algo viejo
            self.err_desc.hide()
            self.err_precio.hide()

    def guardar(self):
        cod = self.inp_codigo.text().strip()
        desc = self.inp_desc.text().strip()
        uni = self.cmb_unidad.currentData()
        
        hay_error = False
        
        if not cod:
            self.inp_codigo.setStyleSheet("border: 1px solid red;")
            self.err_codigo.setText("El código es obligatorio.")
            self.err_codigo.show()
            hay_error = True
            
        if not self.es_existente and not desc:
            self.inp_desc.setStyleSheet("border: 1px solid red;")
            self.err_desc.setText("El nombre es obligatorio.")
            self.err_desc.show()
            hay_error = True
            
        precio = 0.0
        if not self.es_existente:
            try:
                precio = float(self.inp_precio.text().replace(',', '.'))
                if precio < 0: raise ValueError
            except ValueError:
                self.inp_precio.setStyleSheet("border: 1px solid red;")
                self.err_precio.setText("Debe ser un número >= 0.")
                self.err_precio.show()
                hay_error = True
                
        stk_min = 0.0
        try:
            stk_ini_str = self.inp_stock_ini.text().strip().replace(',', '.')
            if not stk_ini_str:
                raise ValueError("empty")
            stk_ini = float(stk_ini_str)
            if self.es_existente and stk_ini <= 0:
                self.inp_stock_ini.setStyleSheet("border: 1px solid red;")
                self.err_stock.setText("Debe ingresar una cantidad > 0.")
                self.err_stock.show()
                hay_error = True
            elif not self.es_existente and stk_ini < 0:
                self.inp_stock_ini.setStyleSheet("border: 1px solid red;")
                self.err_stock.setText("Debe ser un número >= 0.")
                self.err_stock.show()
                hay_error = True
        except ValueError:
            self.inp_stock_ini.setStyleSheet("border: 1px solid red;")
            self.err_stock.setText("Cantidad obligatoria y válida.")
            self.err_stock.show()
            hay_error = True
        
        if hay_error:
            return

        final_img = self.img_selector.get_final_path(cod)
        
        if self.es_existente:
            try:
                sumar_stock_producto_existente(self.conn, cod, stk_ini)
                QMessageBox.information(self, "Éxito", f"Se sumaron {stk_ini:g} unidades al producto existente.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al sumar stock: {e}")
        else:
            try:
                crear_producto_con_stock_inicial(self.conn, cod, desc, uni, precio, stk_min, final_img, stk_ini)
                QMessageBox.information(self, "Éxito", "Producto registrado correctamente.")
                self.accept()
            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Error", "Ya existe un producto con ese código o descripción.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


class DialogoEditarProducto(DialogoModalIntegrado):
    def __init__(self, conexion_db, producto_data, parent=None):
        super().__init__(parent)
        self.conn = conexion_db
        self.p_data = producto_data
        self.setWindowTitle(f"Editar: {producto_data['codigo']}")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Recuperar imagen actual
        img_path = obtener_imagen_path(self.conn, self.p_data['codigo'])
        
        # Imagen
        img_layout = QHBoxLayout()
        img_layout.addStretch()
        self.img_selector = ImageSelectorWidget(current_image_path=img_path)
        img_layout.addWidget(self.img_selector)
        img_layout.addStretch()
        main_layout.addLayout(img_layout)
        
        # Formulario
        form = QFormLayout()
        
        self.inp_desc = QLineEdit(self.p_data['descripcion'])
        self.inp_precio = QLineEdit(str(self.p_data['precio_venta']))
        self.inp_stock_min = QLineEdit(str(self.p_data.get('stock_minimo', 0)))
        
        form.addRow("Descripción (*):", self.inp_desc)
        form.addRow("Precio Venta ($):", self.inp_precio)
        form.addRow("Stock Mínimo:", self.inp_stock_min)
        
        # Solo mostrar info (físico y ATP no se editan acá)
        lbl_info = QLabel(f"<b>Stock Físico:</b> {self.p_data.get('stock_fisico',0):g} {self.p_data['unidad_base']} <br>"
                          f"<b>ATP:</b> {self.p_data.get('atp',0):g} {self.p_data['unidad_base']}")
        lbl_info.setStyleSheet("color: #64748b; margin-top: 10px;")
        form.addRow(lbl_info)
        
        main_layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        self.btn_eliminar = QPushButton("Eliminar producto")
        self.btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eliminar.setStyleSheet(f"background-color: {COLOR_DANGER}; color: white; padding: 10px; border-radius: 4px; font-weight: bold;")
        self.btn_eliminar.clicked.connect(self.eliminar_producto)
        
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setStyleSheet(f"background-color: {COLOR_PRIMARY}; color: white; padding: 10px; border-radius: 4px; font-weight: bold;")
        self.btn_guardar.clicked.connect(self.guardar)
        
        btn_layout.addWidget(self.btn_eliminar)
        btn_layout.addWidget(self.btn_guardar)
        main_layout.addLayout(btn_layout)

    def eliminar_producto(self):
        cod = self.p_data['codigo']
        desc = self.p_data['descripcion']
        
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Está seguro que desea eliminar el producto?\n\nCódigo: {cod}\nDescripción: {desc}\n\nSi el producto tiene historial, será desactivado en lugar de eliminado.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return
            
        try:
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
            QMessageBox.critical(self, "Error", f"No se pudo eliminar: {e}")

    def guardar(self):
        desc = self.inp_desc.text().strip()
        cod = self.p_data['codigo']
        
        if not desc:
            QMessageBox.warning(self, "Error", "La descripción es obligatoria.")
            return
            
        try:
            precio = float(self.inp_precio.text().replace(',', '.'))
            stk_min = float(self.inp_stock_min.text().replace(',', '.'))
            if precio < 0 or stk_min < 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Precios y stocks deben ser números válidos y positivos.")
            return

        final_img = self.img_selector.get_final_path(cod)
        
        try:
            actualizar_producto_y_registrar(self.conn, cod, desc, self.p_data['unidad_base'], precio, stk_min, final_img)
            QMessageBox.information(self, "Éxito", "Producto actualizado.")
            self.accept()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "Ya existe otro producto con esa descripción.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class DialogoStockMinimo(DialogoModalIntegrado):
    def __init__(self, conexion_db, producto_data, parent=None):
        super().__init__(parent)
        self.conn = conexion_db
        self.p_data = producto_data
        self.setWindowTitle("Configurar Stock Mínimo")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel(f"Producto: <b>{producto_data['descripcion']}</b>")
        layout.addWidget(lbl)
        
        form = QFormLayout()
        self.inp_min = QLineEdit(str(producto_data.get('stock_minimo', 0)))
        form.addRow("Alerta en Stock <= a:", self.inp_min)
        layout.addLayout(form)
        
        btn = QPushButton("Guardar")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"background-color: {COLOR_PRIMARY}; color: white; padding: 10px; border-radius: 4px; font-weight: bold;")
        btn.clicked.connect(self.guardar)
        layout.addWidget(btn)
        
    def guardar(self):
        try:
            stk = float(self.inp_min.text().replace(',', '.'))
            if stk < 0: raise ValueError
        except:
            QMessageBox.warning(self, "Error", "Valor inválido.")
            return
            
        try:
            actualizar_stock_minimo(self.conn, self.p_data['codigo'], stk)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# =====================================================================
# DIÁLOGOS DE MOVIMIENTOS E INVENTARIO
# =====================================================================

class DialogoEntradaStock(DialogoModalIntegrado):
    def __init__(self, conexion_db, producto_data, parent=None):
        super().__init__(parent)
        self.conn = conexion_db
        self.p_data = producto_data
        self.setWindowTitle(f"Entrada de Stock: {producto_data['codigo']}")
        self.setMinimumWidth(350)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl = QLabel(f"<b>{self.p_data['descripcion']}</b>")
        lbl.setStyleSheet("font-size: 14px;")
        layout.addWidget(lbl)
        
        layout.addWidget(QLabel(f"Stock Físico Actual: {self.p_data['stock_fisico']:g} {self.p_data['unidad_base']}"))
        
        form = QFormLayout()
        self.inp_cant = QLineEdit("0.0")
        self.inp_notas = QLineEdit()
        self.inp_notas.setPlaceholderText("Remito, proveedor, motivo...")
        
        form.addRow(f"Cantidad a Ingresar ({self.p_data['unidad_base']}):", self.inp_cant)
        form.addRow("Observaciones:", self.inp_notas)
        
        layout.addLayout(form)
        
        self.btn_confirmar = QPushButton("Confirmar Entrada")
        self.btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirmar.setStyleSheet(f"background-color: {COLOR_PRIMARY}; color: white; padding: 10px;")
        self.btn_confirmar.clicked.connect(self.guardar)
        layout.addWidget(self.btn_confirmar)

    def guardar(self):
        try:
            cant = float(self.inp_cant.text().replace(',', '.'))
            if cant <= 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "La cantidad debe ser un número mayor a 0.")
            return
            
        notas = self.inp_notas.text().strip()
        cod = self.p_data['codigo']
        
        try:
            registrar_ingreso_manual(self.conn, cod, cant, notas)
            QMessageBox.information(self, "Éxito", "Entrada registrada correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class DialogoAjusteInventario(DialogoModalIntegrado):
    """
    Ajuste ciego o inventariado. El usuario ingresa cuánto HAY realmente,
    el sistema calcula la diferencia y genera el movimiento para igualar.
    """
    def __init__(self, conexion_db, producto_data, parent=None):
        super().__init__(parent)
        self.conn = conexion_db
        self.p_data = producto_data
        self.fisico_actual = float(self.p_data['stock_fisico'])
        self.setWindowTitle(f"Ajuste de Inventario: {producto_data['codigo']}")
        self.setMinimumWidth(380)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl = QLabel(f"<b>{self.p_data['descripcion']}</b>")
        layout.addWidget(lbl)
        
        self.lbl_actual = QLabel(f"Físico en sistema: {self.fisico_actual:g} {self.p_data['unidad_base']}")
        self.lbl_actual.setStyleSheet("color: #64748b; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(self.lbl_actual)
        
        form = QFormLayout()
        
        self.inp_real = QLineEdit()
        self.inp_real.setPlaceholderText("Ej: 15.5")
        self.inp_real.textChanged.connect(self.calcular_diferencia)
        
        self.lbl_diff = QLabel("Diferencia: 0.0")
        self.lbl_diff.setStyleSheet("font-weight: bold;")
        
        self.inp_motivo = QLineEdit()
        self.inp_motivo.setPlaceholderText("Rotura, pérdida, recuento, etc.")
        
        form.addRow("Stock Físico Real (Contado):", self.inp_real)
        form.addRow("", self.lbl_diff)
        form.addRow("Motivo del Ajuste (*):", self.inp_motivo)
        
        layout.addLayout(form)
        
        self.btn_confirmar = QPushButton("Aplicar Ajuste")
        self.btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirmar.setStyleSheet(f"background-color: {COLOR_PRIMARY}; color: white; padding: 10px;")
        self.btn_confirmar.clicked.connect(self.guardar)
        layout.addWidget(self.btn_confirmar)
        
        self.diferencia = 0.0

    def calcular_diferencia(self):
        txt = self.inp_real.text().replace(',', '.')
        try:
            real = float(txt)
            self.diferencia = real - self.fisico_actual
            if self.diferencia > 0:
                self.lbl_diff.setText(f"Diferencia: +{self.diferencia:g} (Se creará ENTRADA)")
                self.lbl_diff.setStyleSheet("color: #10b981; font-weight: bold;")
            elif self.diferencia < 0:
                self.lbl_diff.setText(f"Diferencia: {self.diferencia:g} (Se creará SALIDA)")
                self.lbl_diff.setStyleSheet("color: #ef4444; font-weight: bold;")
            else:
                self.lbl_diff.setText("Diferencia: 0 (No hay ajuste)")
                self.lbl_diff.setStyleSheet("color: #64748b; font-weight: bold;")
        except:
            self.diferencia = 0.0
            self.lbl_diff.setText("Diferencia: --")
            self.lbl_diff.setStyleSheet("color: #64748b;")

    def guardar(self):
        motivo = self.inp_motivo.text().strip()
        if not motivo:
            QMessageBox.warning(self, "Error", "El motivo del ajuste es obligatorio para la trazabilidad.")
            return
            
        if abs(self.diferencia) < 0.001:
            QMessageBox.information(self, "Aviso", "No hay diferencia que ajustar.")
            self.accept()
            return
            
        cod = self.p_data['codigo']
        tipo_mov = 'ENTRADA' if self.diferencia > 0 else 'SALIDA'
        cant_absoluta = abs(self.diferencia)
        
        try:
            registrar_ajuste_inventario(self.conn, cod, self.diferencia, motivo)
            QMessageBox.information(self, "Éxito", f"Inventario ajustado. {tipo_mov} de {cant_absoluta:g} aplicada.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

class DialogoAlertasInventario(DialogoModalIntegrado):
    def __init__(self, datos_catalogo, callback_seleccionar, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alertas de Inventario")
        self.setFixedSize(650, 450)
        self.datos = datos_catalogo
        self.callback = callback_seleccionar
        
        self.init_ui()
        
    def init_ui(self):
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
        from PyQt6.QtGui import QColor, QFont
        
        layout = QVBoxLayout(self)
        
        lbl_info = QLabel("Productos que requieren atención inmediata:")
        lbl_info.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl_info)
        
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["Cód.", "Producto", "Disp.", "Mín.", "Prioridad"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setStyleSheet(f"QTableWidget {{ border: 1px solid {COLOR_BORDER}; border-radius: 6px; font-size: 13px; }}")
        self.tabla.itemDoubleClicked.connect(self.on_item_clicked)
        
        layout.addWidget(self.tabla)
        
        alertas = []
        for p in self.datos:
            atp = p['atp']
            stk_min = p['stock_minimo']
            
            estado = 0
            if atp <= 0: estado = 2
            elif stk_min > 0 and atp <= stk_min: estado = 1
            
            if estado == 0: continue
            
            alertas.append({
                'prod': p,
                'estado': estado,
                'atp': atp,
                'stk_min': stk_min
            })
            
        # Sort by critical first, then by ATP
        alertas.sort(key=lambda x: (-x['estado'], x['atp']))
        
        self.tabla.setRowCount(len(alertas))
        for i, al in enumerate(alertas):
            p = al['prod']
            
            it_cod = QTableWidgetItem(p['codigo'])
            it_cod.setData(Qt.ItemDataRole.UserRole, p['codigo'])
            
            it_desc = QTableWidgetItem(p['descripcion'])
            
            it_disp = QTableWidgetItem(f"{al['atp']:g} {p['unidad_base']}")
            it_disp.setFont(QFont("Segoe UI", -1, QFont.Weight.Bold))
            
            it_min = QTableWidgetItem(f"{al['stk_min']:g}")
            
            color = QColor("#ef4444") if al['estado'] == 2 else QColor("#f59e0b")
            texto_estado = "CRÍTICO (Sin Stock)" if al['estado'] == 2 else "MEDIA (Stock Bajo)"
            
            it_est = QTableWidgetItem(texto_estado)
            it_est.setForeground(color)
            it_est.setFont(QFont("Segoe UI", -1, QFont.Weight.Bold))
            
            self.tabla.setItem(i, 0, it_cod)
            self.tabla.setItem(i, 1, it_desc)
            self.tabla.setItem(i, 2, it_disp)
            self.tabla.setItem(i, 3, it_min)
            self.tabla.setItem(i, 4, it_est)
            
        lbl_hint = QLabel("Doble clic en un producto para gestionarlo.")
        lbl_hint.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
        layout.addWidget(lbl_hint)

    def on_item_clicked(self, item):
        row = item.row()
        cod = self.tabla.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.callback(cod)
        self.accept()

class VistaDetalleProducto(QFrame):
    def __init__(self, producto, parent):
        super().__init__(parent)
        self.producto = producto
        self.parent_widget = parent
        
        self.setObjectName("vista_detalle_overlay")
        self.setStyleSheet("""
            QFrame#vista_detalle_overlay {
                background-color: rgba(15, 23, 42, 0.7); 
            }
        """)
        self.setGeometry(parent.rect())
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        # Interceptar redimensionamiento del padre para ajustar el overlay
        self.parent_widget.installEventFilter(self)
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.card = QFrame()
        self.card.setObjectName("vista_detalle_card")
        self.card.setStyleSheet(f"""
            QFrame#vista_detalle_card {{
                background-color: white;
                border-radius: 12px;
                border: 1px solid {COLOR_BORDER};
            }}
        """)
        self.card.setFixedWidth(420)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(24, 20, 24, 24)
        card_layout.setSpacing(12)
        
        # Header (Close button)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        lbl_titulo = QLabel("Detalles del Producto")
        lbl_titulo.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {COLOR_TEXT_MAIN};")
        header_layout.addWidget(lbl_titulo)
        header_layout.addStretch()
        
        from ui.components.boton_x import BotonCerrarX
        btn_close = BotonCerrarX()
        btn_close.clicked.connect(self.cerrar)
        header_layout.addWidget(btn_close)
        
        # Image
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setFixedSize(160, 160)
        img_label.setStyleSheet("background-color: #F8FAFC; border-radius: 8px; border: 1px dashed #CBD5E1;")
        
        has_image = False
        img_path = producto.get('imagen_path')
        p_res = resolver_ruta_imagen(img_path)
        
        if p_res:
            pix = QPixmap(str(p_res))
            if not pix.isNull():
                img_label.setPixmap(pix.scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                img_label.setStyleSheet("background-color: transparent; border: none;")
                has_image = True
                
        if not has_image:
            img_label.setText("📦\nSin imagen")
            img_label.setStyleSheet("background-color: #F8FAFC; border-radius: 8px; border: 1px dashed #CBD5E1; color: #94A3B8; font-size: 18px;")
        
        img_layout = QHBoxLayout()
        img_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_layout.addWidget(img_label)
        
        # Details
        det_layout = QFormLayout()
        det_layout.setSpacing(10)
        det_layout.setContentsMargins(10, 10, 10, 10)
        
        def add_row(label, value, bold=False, color="#1e293b"):
            lbl_key = QLabel(label)
            lbl_key.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 500;")
            lbl_val = QLabel(str(value))
            weight = "800" if bold else "normal"
            lbl_val.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: {weight};")
            lbl_val.setWordWrap(True)
            det_layout.addRow(lbl_key, lbl_val)
            
        add_row("Código:", producto['codigo'], True)
        add_row("Descripción:", producto['descripcion'], True)
        add_row("Unidad:", producto['unidad_base'])
        add_row("Precio Venta:", f"$ {producto['precio_venta']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), True, COLOR_PRIMARY)
        
        atp = producto.get('atp', 0.0)
        min_stk = producto.get('stock_minimo', 0.0)
        stk_color = COLOR_TEXT_MAIN
        estado = "Óptimo"
        if atp <= 0:
            stk_color = COLOR_DANGER
            estado = "Sin Stock"
        elif min_stk > 0 and atp <= min_stk:
            stk_color = "#D97706" # Warning/Orange
            estado = "Stock Bajo"
            
        add_row("Stock Físico:", f"{producto.get('stock_fisico', 0):g}")
        add_row("Comprometido:", f"{producto.get('comprometido', 0):g}")
        add_row("Disponible (ATP):", f"{atp:g}", True, stk_color)
        add_row("Stock Mínimo:", f"{min_stk:g}")
        add_row("Estado:", estado, True, stk_color)
        
        cat = producto.get('categoria')
        if cat:
            add_row("Categoría:", cat)
            
        card_layout.addLayout(header_layout)
        card_layout.addSpacing(10)
        card_layout.addLayout(img_layout)
        card_layout.addSpacing(16)
        
        # Marco de detalles
        frame_det = QFrame()
        frame_det.setStyleSheet(f"background-color: {COLOR_BG}; border-radius: 8px;")
        frame_det.setLayout(det_layout)
        
        card_layout.addWidget(frame_det)
        
        main_layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def eventFilter(self, obj, event):
        if obj == self.parent_widget and event.type() == event.Type.Resize:
            self.setGeometry(obj.rect())
        return super().eventFilter(obj, event)
        
    def mousePressEvent(self, event):
        if not self.card.geometry().contains(event.pos()):
            self.cerrar()
            
    def cerrar(self):
        self.parent_widget.removeEventFilter(self)
        self.deleteLater()


class DialogoProductosFrecuentes(DialogoModalIntegrado):
    def __init__(self, conexion_db, callback_seleccionar, parent=None):
        super().__init__(parent)
        self.conn = conexion_db
        self.callback = callback_seleccionar
        self.setWindowTitle("Productos Más Frecuentes (Últimos 30 días)")
        self.setFixedSize(700, 500)
        
        self.init_ui()
        
    def init_ui(self):
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
        from PyQt6.QtGui import QColor, QFont
        from db.queries import obtener_productos_frecuentes
        
        layout = QVBoxLayout(self)
        
        lbl_info = QLabel("Análisis de rotación de productos:")
        lbl_info.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl_info)
        
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["Cód.", "Producto", "Vendidos", "Stock Actual", "Sugerencia"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setStyleSheet(f"QTableWidget {{ border: 1px solid {COLOR_BORDER}; border-radius: 6px; font-size: 13px; }}")
        self.tabla.itemDoubleClicked.connect(self.on_item_clicked)
        
        layout.addWidget(self.tabla)
        
        # Load up to 50 frequent products
        frecuentes = obtener_productos_frecuentes(self.conn, limite=50, dias=30)
        
        self.tabla.setRowCount(len(frecuentes))
        for i, p in enumerate(frecuentes):
            it_cod = QTableWidgetItem(str(p['codigo']))
            it_cod.setData(Qt.ItemDataRole.UserRole, p['codigo'])
            it_desc = QTableWidgetItem(str(p['descripcion']))
            
            vendidos = p.get('vendido', 0)
            it_ven = QTableWidgetItem(f"{vendidos:g}")
            it_ven.setFont(QFont("Segoe UI", -1, QFont.Weight.Bold))
            
            atp = p.get('atp', 0)
            it_disp = QTableWidgetItem(f"{atp:g}")
            
            # Suggestion logic
            sug = "Stock OK"
            col = QColor("#64748b")
            
            if atp <= 0:
                sug = "URGENTE Reponer"
                col = QColor("#ef4444")
            elif atp < vendidos * 0.5:
                # Stock is less than half of what we sold last month
                sug = "Considerar Reposición"
                col = QColor("#f59e0b")
                
            it_sug = QTableWidgetItem(sug)
            it_sug.setForeground(col)
            it_sug.setFont(QFont("Segoe UI", -1, QFont.Weight.Bold))
            
            self.tabla.setItem(i, 0, it_cod)
            self.tabla.setItem(i, 1, it_desc)
            self.tabla.setItem(i, 2, it_ven)
            self.tabla.setItem(i, 3, it_disp)
            self.tabla.setItem(i, 4, it_sug)
            
        lbl_hint = QLabel("Doble clic en un producto para gestionarlo en el Control de Stock.")
        lbl_hint.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
        layout.addWidget(lbl_hint)

    def on_item_clicked(self, item):
        row = item.row()
        cod = self.tabla.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.callback(cod)
        self.accept()

class DialogoAyudaStock(DialogoModalIntegrado):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayuda: Control de Stock")
        self.setMinimumSize(800, 750)
        self.resize(800, 750)
        self.init_ui()
        
    def init_ui(self):
        from PyQt6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
        from PyQt6.QtCore import Qt
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background-color: {COLOR_BG}; }}")
        
        content = QWidget()
        content.setStyleSheet(f"background-color: {COLOR_BG};")
        ly_content = QVBoxLayout(content)
        ly_content.setContentsMargins(24, 24, 24, 24)
        ly_content.setSpacing(16)
        
        lbl_tit = QLabel("📖 Guía de Uso: Control de Stock")
        lbl_tit.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {COLOR_TEXT_MAIN};")
        ly_content.addWidget(lbl_tit)
        
        def add_section(icon, title, text):
            card = QFrame()
            card.setStyleSheet(f"background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")
            ly_card = QVBoxLayout(card)
            ly_card.setContentsMargins(16, 16, 16, 16)
            ly_card.setSpacing(8)
            
            lbl_title = QLabel(f"{icon} {title}")
            lbl_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_PRIMARY}; border: none;")
            
            lbl_text = QLabel(text)
            lbl_text.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_SEC}; border: none;")
            lbl_text.setWordWrap(True)
            
            ly_card.addWidget(lbl_title)
            ly_card.addWidget(lbl_text)
            ly_content.addWidget(card)
            
        add_section("📦", "¿Qué muestra esta pantalla?",
                    "Esta pantalla centraliza el inventario.\n"
                    "• <b>Stock Físico:</b> Mercadería real en depósito.\n"
                    "• <b>Stock Comprometido:</b> Mercadería reservada para ventas o presupuestos.\n"
                    "• <b>ATP (Disponible):</b> Stock Físico menos el Stock Comprometido (lo que realmente puedes vender).\n"
                    "• <b>Stock Mínimo:</b> Nivel para generar alertas de reposición.\n"
                    "• <b>Estado:</b> Indica si está Disponible, con Stock Bajo o Sin Stock.")

        add_section("🛠", "Barra superior",
                    "• <b>Nuevo Producto:</b> Alta de un artículo al catálogo.\n"
                    "• <b>Importar / Exportar:</b> Carga o descarga productos mediante Excel.\n"
                    "• <b>Historial de movimientos:</b> Consulta el registro de todas las operaciones de inventario.\n"
                    "• <b>Ayuda:</b> Muestra esta guía.")
                    
        add_section("⭐", "Productos frecuentes",
                    "Muestra los artículos con más movimiento reciente. Se generan automáticamente y permiten acceso rápido. Haz clic en 'Ver todos' para el análisis completo de rotación.")
                    
        add_section("⚠️", "Alertas de inventario",
                    "Aparecen cuando un artículo necesita atención:\n"
                    "• <b>CRÍTICO (Sin Stock):</b> El ATP llegó a cero o es negativo.\n"
                    "• <b>MEDIA (Stock Bajo):</b> El ATP es menor o igual al Stock Mínimo.\n"
                    "Úsalas para planificar la reposición de mercadería.")
                    
        add_section("📋", "Tabla principal",
                    "Muestra todos los artículos, cantidades, precios y estados. Puedes filtrar, buscar y ordenar. Desde la columna 'Acciones' o el panel lateral administras el stock.")
                    
        add_section("➡️", "Panel derecho",
                    "Al seleccionar un producto, muestra toda su información:\n"
                    "• <b>Datos generales:</b> Imagen, código, descripción, unidad, precio y estado.\n"
                    "• <b>Cantidades:</b> Físico, Comprometido, ATP y Mínimo.\n"
                    "• <b>Acciones disponibles:</b> Registrar Entradas, Ajustes, Editar datos o Configurar Stock Mínimo.")
                    
        add_section("🕒", "Historial de movimientos",
                    "Muestra la trazabilidad detallada:\n"
                    "• <b>Entradas / Compras:</b> Incrementan el stock.\n"
                    "• <b>Salidas / Ventas:</b> Reducen el stock.\n"
                    "• <b>Ajustes:</b> Correcciones manuales por sobrantes o faltantes (recuentos, mermas).")
                    
        add_section("💡", "Consejos",
                    "• Configura el <b>Stock Mínimo</b> en artículos clave para evitar quiebres de stock.\n"
                    "• Usa <b>Ajuste</b> solo para correcciones de inventario; para ingresos normales usa <b>Entrada</b>.\n"
                    "• Mantén las imágenes actualizadas para evitar errores de selección.")
                    
        ly_content.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet(f"background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN}; padding: 10px 20px; border-radius: 6px; border: 1px solid {COLOR_BORDER}; font-weight: bold;")
        btn_cerrar.clicked.connect(self.accept)
        
        ly_btn = QHBoxLayout()
        ly_btn.addStretch()
        ly_btn.addWidget(btn_cerrar)
        ly_btn.setContentsMargins(16, 8, 16, 16)
        main_layout.addLayout(ly_btn)
