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
    COLOR_BORDER, COLOR_TEXT_MAIN, COLOR_DANGER
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
        
        from PyQt6.QtCore import QSettings
        settings = QSettings("ConstrusecoPereyra", "StockConfig")
        stk_min_def = settings.value("default_stock_min", 0.0, type=float)
        self.inp_stock_min = SelectAllLineEdit(f"{stk_min_def:g}")
        
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
        
        self.err_min = QLabel()
        self.err_min.setStyleSheet("color: red; font-size: 11px;")
        self.err_min.hide()
        
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
        add_validated_row("Stock Mínimo:", self.inp_stock_min, self.err_min)
        
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
            self.inp_stock_min.setText(f"{min_stock:g}")
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
            self.inp_stock_min.setReadOnly(True)
            self.cmb_unidad.setEnabled(False)
            
            self.inp_desc.setStyleSheet(disabled_style)
            self.inp_precio.setStyleSheet(disabled_style)
            self.inp_stock_min.setStyleSheet(disabled_style)
            
            self.img_selector.btn_select.setEnabled(False)
            self.img_selector.btn_clear.setEnabled(False)
            self.img_selector.setStyleSheet(f"border: 2px dashed #cbd5e1; border-radius: 6px; background-color: #f8fafc;")
        else:
            self.setWindowTitle("Nuevo Producto")
            self.btn_guardar.setText("Guardar Producto")
            self.lbl_lbl_stock.setText("Stock Inicial:")
            
            self.inp_desc.setReadOnly(False)
            self.inp_precio.setReadOnly(False)
            self.inp_stock_min.setReadOnly(False)
            self.cmb_unidad.setEnabled(True)
            
            self.inp_desc.setStyleSheet(normal_style)
            self.inp_precio.setStyleSheet(normal_style)
            self.inp_stock_min.setStyleSheet(normal_style)
            
            self.img_selector.btn_select.setEnabled(True)
            self.img_selector.btn_clear.setEnabled(True)
            self.img_selector.setStyleSheet(f"border: 2px dashed {COLOR_BORDER}; border-radius: 6px; background-color: {COLOR_BG};")
            
            # Limpiar labels de error si estaban visibles por algo viejo
            self.err_desc.hide()
            self.err_precio.hide()
            self.err_min.hide()

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
        if not self.es_existente:
            try:
                stk_min = float(self.inp_stock_min.text().replace(',', '.'))
                if stk_min < 0: raise ValueError
            except ValueError:
                self.inp_stock_min.setStyleSheet("border: 1px solid red;")
                self.err_min.setText("Debe ser un número >= 0.")
                self.err_min.show()
                hay_error = True
                
        stk_ini = 0.0
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
        self.btn_eliminar.setStyleSheet(f"background-color: {COLOR_DANGER}; color: white; padding: 10px; border-radius: 4px; font-weight: bold;")
        self.btn_eliminar.clicked.connect(self.eliminar_producto)
        
        self.btn_guardar = QPushButton("Guardar Cambios")
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
        self.setFixedSize(500, 400)
        self.datos = datos_catalogo
        self.callback = callback_seleccionar
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl_info = QLabel("Productos que requieren atención inmediata:")
        lbl_info.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl_info)
        
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QWidget
        self.lista = QListWidget()
        self.lista.setStyleSheet("""
            QListWidget { border: 1px solid #e2e8f0; border-radius: 6px; }
            QListWidget::item { border-bottom: 1px solid #f1f5f9; padding: 10px; }
            QListWidget::item:hover { background-color: #f8fafc; }
        """)
        self.lista.itemClicked.connect(self.on_item_clicked)
        
        count = 0
        for p in self.datos:
            atp = p['atp']
            stk_min = p['stock_minimo']
            
            estado = 0
            if atp <= 0: estado = 2
            elif stk_min > 0 and atp <= stk_min: estado = 1
            
            if estado == 0: continue
            count += 1
            
            item = QListWidgetItem()
            w = QWidget()
            l = QVBoxLayout(w)
            l.setContentsMargins(8, 6, 8, 6)
            l.setSpacing(2)
            
            lbl_desc = QLabel(f"{p['descripcion']}")
            lbl_desc.setStyleSheet("font-weight: bold; font-size: 13px; color: #1e293b;")
            lbl_desc.setWordWrap(True)
            
            color = "#ef4444" if estado == 2 else "#f59e0b"
            texto_estado = "SIN STOCK" if estado == 2 else f"BAJO (Mín: {stk_min:g})"
            
            lbl_det = QLabel(f"Cód: {p['codigo']} | Disp: <span style='color:{color}; font-weight:bold;'>{atp:g}</span> {p['unidad_base']} ({texto_estado})")
            lbl_det.setStyleSheet("font-size: 11px; color: #64748b;")
            lbl_det.setWordWrap(True)
            
            l.addWidget(lbl_desc)
            l.addWidget(lbl_det)
            
            w.adjustSize()
            item.setSizeHint(w.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, p['codigo'])
            
            self.lista.addItem(item)
            self.lista.setItemWidget(item, w)
            
        if count == 0:
            item = QListWidgetItem("No hay alertas activas de inventario.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.lista.addItem(item)
            
        layout.addWidget(self.lista)
        
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar)
        
    def on_item_clicked(self, item):
        codigo = item.data(Qt.ItemDataRole.UserRole)
        if codigo:
            self.accept()
            self.callback(codigo)

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
            
        add_row("Stock Físico:", f"{producto.get('stock', 0):g}")
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
