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
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)
        
        # Contenedor central dividido (Imagen | Formulario)
        center_layout = QHBoxLayout()
        center_layout.setSpacing(32)
        
        # --- PANEL IZQUIERDO: Imagen ---
        left_panel = QVBoxLayout()
        left_panel.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.img_selector = ImageSelectorWidget()
        left_panel.addWidget(self.img_selector, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # Panel informativo
        self.lbl_existente_info = QLabel("Ingrese un código para verificar si el producto ya existe. Si existe, podrá sumarle stock.")
        self.lbl_existente_info.setWordWrap(True)
        self.lbl_existente_info.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 11px; margin-top: 16px; background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 8px; padding: 12px;")
        left_panel.addWidget(self.lbl_existente_info)
        
        center_layout.addLayout(left_panel)
        
        # --- PANEL DERECHO: Formulario ---
        right_panel = QVBoxLayout()
        right_panel.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.form = QFormLayout()
        self.form.setVerticalSpacing(16)
        
        style_input = f"""
            QLineEdit, QComboBox {{
                padding: 10px;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                background-color: {COLOR_BG};
                font-size: 13px;
                color: {COLOR_TEXT_MAIN};
            }}
            QLineEdit:focus, QComboBox:focus {{ border: 1px solid {COLOR_PRIMARY}; }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox::down-arrow {{ image: none; }}
        """
        style_label = f"font-weight: bold; color: {COLOR_TEXT_SEC}; font-size: 12px;"
        
        self.inp_codigo = SelectAllLineEdit()
        self.inp_codigo.setStyleSheet(style_input)
        
        self.inp_desc = SelectAllLineEdit()
        self.inp_desc.setStyleSheet(style_input)
        
        self.cmb_unidad = QComboBox()
        self.cmb_unidad.setStyleSheet(style_input)
        for v, l in UNIDADES_PERMITIDAS:
            self.cmb_unidad.addItem(l, userData=v)
            
        self.inp_precio = SelectAllLineEdit("0.0")
        self.inp_precio.setStyleSheet(style_input)
        
        self.inp_stock_ini = SelectAllLineEdit("0.0")
        self.inp_stock_ini.setStyleSheet(style_input)
        
        self.err_codigo = QLabel(); self.err_codigo.setStyleSheet("color: #ef4444; font-size: 11px;"); self.err_codigo.hide()
        self.err_desc = QLabel(); self.err_desc.setStyleSheet("color: #ef4444; font-size: 11px;"); self.err_desc.hide()
        self.err_precio = QLabel(); self.err_precio.setStyleSheet("color: #ef4444; font-size: 11px;"); self.err_precio.hide()
        self.err_stock = QLabel(); self.err_stock.setStyleSheet("color: #ef4444; font-size: 11px;"); self.err_stock.hide()
        
        def add_validated_row(titulo, widget, err_lbl):
            ly = QVBoxLayout()
            ly.setContentsMargins(0,0,0,0)
            ly.setSpacing(4)
            ly.addWidget(widget)
            ly.addWidget(err_lbl)
            lbl = QLabel(titulo)
            lbl.setStyleSheet(style_label)
            self.form.addRow(lbl, ly)
            widget.textChanged.connect(lambda: (widget.setStyleSheet(style_input), err_lbl.hide()))
        
        add_validated_row("Código (*):", self.inp_codigo, self.err_codigo)
        add_validated_row("Nombre o Producto (*):", self.inp_desc, self.err_desc)
        
        lbl_uni = QLabel("Unidad:")
        lbl_uni.setStyleSheet(style_label)
        self.form.addRow(lbl_uni, self.cmb_unidad)
        
        add_validated_row("Precio Venta ($):", self.inp_precio, self.err_precio)
        
        self.lbl_lbl_stock = QLabel("Cantidad (Agregar Stock):")
        self.lbl_lbl_stock.setStyleSheet(style_label)
        ly_stk = QVBoxLayout()
        ly_stk.setContentsMargins(0,0,0,0)
        ly_stk.setSpacing(4)
        ly_stk.addWidget(self.inp_stock_ini)
        ly_stk.addWidget(self.err_stock)
        self.form.addRow(self.lbl_lbl_stock, ly_stk)
        self.inp_stock_ini.textChanged.connect(lambda: (self.inp_stock_ini.setStyleSheet(style_input), self.err_stock.hide()))
        
        right_panel.addLayout(self.form)
        center_layout.addLayout(right_panel)
        
        main_layout.addLayout(center_layout)
        
        # --- BOTONES ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_guardar = QPushButton("Guardar Producto")
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setStyleSheet(f"QPushButton {{ background-color: {COLOR_PRIMARY}; color: white; padding: 10px 24px; border-radius: 6px; font-weight: bold; border: none; }} QPushButton:hover {{ background-color: #1d4ed8; }}")
        self.btn_guardar.clicked.connect(self.guardar)
        btn_layout.addWidget(self.btn_guardar)
        
        main_layout.addLayout(btn_layout)
        
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
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)
        
        # Contenedor central dividido (Imagen | Formulario)
        center_layout = QHBoxLayout()
        center_layout.setSpacing(32)
        
        # --- PANEL IZQUIERDO: Imagen e Info ---
        left_panel = QVBoxLayout()
        left_panel.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        img_path = obtener_imagen_path(self.conn, self.p_data['codigo'])
        self.img_selector = ImageSelectorWidget(current_image_path=img_path)
        left_panel.addWidget(self.img_selector, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        lbl_info = QLabel(
            f"<div style='text-align: center;'>"
            f"<span style='color: {COLOR_TEXT_SEC}; font-size: 11px; text-transform: uppercase;'>Stock Físico</span><br>"
            f"<span style='font-size: 16px; font-weight: bold; color: {COLOR_TEXT_MAIN};'>{self.p_data.get('stock_fisico',0):g} {self.p_data['unidad_base']}</span><br><br>"
            f"<span style='color: {COLOR_TEXT_SEC}; font-size: 11px; text-transform: uppercase;'>ATP</span><br>"
            f"<span style='font-size: 16px; font-weight: bold; color: {COLOR_TEXT_MAIN};'>{self.p_data.get('atp',0):g} {self.p_data['unidad_base']}</span>"
            f"</div>"
        )
        lbl_info.setStyleSheet(f"background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 8px; padding: 16px; margin-top: 16px;")
        left_panel.addWidget(lbl_info)
        
        center_layout.addLayout(left_panel)
        
        # --- PANEL DERECHO: Formulario ---
        right_panel = QVBoxLayout()
        right_panel.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        form = QFormLayout()
        form.setVerticalSpacing(16)
        
        style_input = f"""
            QLineEdit {{
                padding: 10px;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                background-color: {COLOR_BG};
                font-size: 13px;
                color: {COLOR_TEXT_MAIN};
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_PRIMARY}; }}
        """
        style_label = f"font-weight: bold; color: {COLOR_TEXT_SEC}; font-size: 12px;"
        
        self.inp_desc = SelectAllLineEdit(self.p_data['descripcion'])
        self.inp_desc.setStyleSheet(style_input)
        
        self.inp_precio = SelectAllLineEdit(str(self.p_data['precio_venta']))
        self.inp_precio.setStyleSheet(style_input)
        
        self.inp_stock_min = SelectAllLineEdit(str(self.p_data.get('stock_minimo', 0)))
        self.inp_stock_min.setStyleSheet(style_input)
        
        lbl_desc = QLabel("Descripción (*):")
        lbl_desc.setStyleSheet(style_label)
        form.addRow(lbl_desc, self.inp_desc)
        
        lbl_precio = QLabel("Precio Venta ($):")
        lbl_precio.setStyleSheet(style_label)
        form.addRow(lbl_precio, self.inp_precio)
        
        lbl_smin = QLabel("Stock Mínimo:")
        lbl_smin.setStyleSheet(style_label)
        form.addRow(lbl_smin, self.inp_stock_min)
        
        right_panel.addLayout(form)
        center_layout.addLayout(right_panel)
        
        main_layout.addLayout(center_layout)
        
        # --- BOTONES ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        self.btn_eliminar = QPushButton("Eliminar producto")
        self.btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eliminar.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {COLOR_DANGER}; padding: 10px 20px; border-radius: 6px; font-weight: bold; border: 1px solid {COLOR_DANGER}; }} QPushButton:hover {{ background-color: #fef2f2; }}")
        self.btn_eliminar.clicked.connect(self.eliminar_producto)
        
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setStyleSheet(f"QPushButton {{ background-color: {COLOR_PRIMARY}; color: white; padding: 10px 20px; border-radius: 6px; font-weight: bold; border: none; }} QPushButton:hover {{ background-color: #1d4ed8; }}")
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
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        lbl = QLabel(f"Producto: <b>{producto_data['descripcion']}</b>")
        lbl.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_MAIN};")
        layout.addWidget(lbl)
        
        form = QFormLayout()
        form.setVerticalSpacing(16)
        
        self.inp_min = SelectAllLineEdit(str(producto_data.get('stock_minimo', 0)))
        self.inp_min.setStyleSheet(f"padding: 10px; border: 1px solid {COLOR_BORDER}; border-radius: 6px; background-color: {COLOR_BG}; font-size: 13px; color: {COLOR_TEXT_MAIN};")
        
        lbl_alerta = QLabel("Alerta en Stock <= a:")
        lbl_alerta.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXT_SEC}; font-size: 12px;")
        
        form.addRow(lbl_alerta, self.inp_min)
        layout.addLayout(form)
        
        btn_ly = QHBoxLayout()
        btn_ly.addStretch()
        btn = QPushButton("Guardar Configuración")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton {{ background-color: {COLOR_PRIMARY}; color: white; padding: 10px 24px; border-radius: 6px; font-weight: bold; border: none; }} QPushButton:hover {{ background-color: #1d4ed8; }}")
        btn.clicked.connect(self.guardar)
        btn_ly.addWidget(btn)
        layout.addLayout(btn_ly)
        
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

class DialogoModificarStock(DialogoModalIntegrado):
    def __init__(self, conexion_db, producto_data, parent=None):
        super().__init__(parent)
        self.conn = conexion_db
        self.p_data = producto_data
        self.fisico_actual = float(self.p_data['stock_fisico'])
        self.setWindowTitle(f"Modificar Stock: {producto_data['codigo']}")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        from PyQt6.QtWidgets import QRadioButton, QButtonGroup, QStackedWidget, QWidget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # Header Info
        header_ly = QHBoxLayout()
        header_ly.setSpacing(16)
        
        lbl_img = QLabel()
        lbl_img.setFixedSize(48, 48)
        lbl_img.setStyleSheet(f"background-color: {COLOR_CARD_BG}; border-radius: 24px; border: 1px solid {COLOR_BORDER}; font-size: 20px;")
        lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_img.setText("📦")
        header_ly.addWidget(lbl_img)
        
        info_ly = QVBoxLayout()
        info_ly.setSpacing(4)
        lbl_desc = QLabel(self.p_data['descripcion'])
        lbl_desc.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        self.lbl_actual = QLabel(f"Stock Físico Actual: <b>{self.fisico_actual:g} {self.p_data['unidad_base']}</b>")
        self.lbl_actual.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 13px;")
        info_ly.addWidget(lbl_desc)
        info_ly.addWidget(self.lbl_actual)
        
        header_ly.addLayout(info_ly)
        header_ly.addStretch()
        layout.addLayout(header_ly)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {COLOR_BORDER}; margin: 8px 0;")
        layout.addWidget(sep)
        
        # Radio buttons con estilo
        op_layout = QVBoxLayout()
        op_layout.setSpacing(12)
        
        self.grupo_op = QButtonGroup(self)
        
        style_radio = f"""
            QRadioButton {{ font-size: 13px; font-weight: bold; color: {COLOR_TEXT_MAIN}; }}
        """
        
        self.radio_entrada = QRadioButton(" Entrada de Stock")
        self.radio_entrada.setStyleSheet(style_radio)
        self.radio_ajuste = QRadioButton(" Ajuste de Inventario")
        self.radio_ajuste.setStyleSheet(style_radio)
        self.radio_entrada.setChecked(True)
        
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
        
        layout.addLayout(op_layout)
        
        # Contenedor de formulario
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")
        
        style_input = f"""
            QLineEdit {{ padding: 10px; border: 1px solid {COLOR_BORDER}; border-radius: 6px; background-color: {COLOR_BG}; font-size: 13px; color: {COLOR_TEXT_MAIN}; }}
            QLineEdit:focus {{ border: 1px solid {COLOR_PRIMARY}; }}
        """
        style_label = f"font-weight: bold; color: {COLOR_TEXT_SEC}; font-size: 12px;"
        
        # WIDGET ENTRADA
        self.wdg_entrada = QWidget()
        form_entrada = QFormLayout(self.wdg_entrada)
        form_entrada.setContentsMargins(20, 20, 20, 20)
        form_entrada.setVerticalSpacing(16)
        
        self.inp_cant_entrada = SelectAllLineEdit("0.0")
        self.inp_cant_entrada.setStyleSheet(style_input)
        self.inp_notas_entrada = SelectAllLineEdit()
        self.inp_notas_entrada.setPlaceholderText("Remito, proveedor, motivo...")
        self.inp_notas_entrada.setStyleSheet(style_input)
        
        lbl_cant_ent = QLabel(f"Cantidad a Ingresar ({self.p_data['unidad_base']}):")
        lbl_cant_ent.setStyleSheet(style_label)
        lbl_obs_ent = QLabel("Observaciones:")
        lbl_obs_ent.setStyleSheet(style_label)
        
        form_entrada.addRow(lbl_cant_ent, self.inp_cant_entrada)
        form_entrada.addRow(lbl_obs_ent, self.inp_notas_entrada)
        
        # WIDGET AJUSTE
        self.wdg_ajuste = QWidget()
        form_ajuste = QFormLayout(self.wdg_ajuste)
        form_ajuste.setContentsMargins(20, 20, 20, 20)
        form_ajuste.setVerticalSpacing(16)
        
        self.inp_real_ajuste = SelectAllLineEdit()
        self.inp_real_ajuste.setPlaceholderText("Ej: 15.5")
        self.inp_real_ajuste.setStyleSheet(style_input)
        self.inp_real_ajuste.textChanged.connect(self.calcular_diferencia_ajuste)
        
        self.lbl_diff_ajuste = QLabel("Diferencia: 0.0")
        self.lbl_diff_ajuste.setStyleSheet("font-weight: bold; font-size: 13px; padding: 8px;")
        
        self.inp_motivo_ajuste = SelectAllLineEdit()
        self.inp_motivo_ajuste.setPlaceholderText("Rotura, pérdida, recuento, etc.")
        self.inp_motivo_ajuste.setStyleSheet(style_input)
        
        lbl_real_aju = QLabel("Stock Físico Real (Contado):")
        lbl_real_aju.setStyleSheet(style_label)
        lbl_mot_aju = QLabel("Motivo del Ajuste (*):")
        lbl_mot_aju.setStyleSheet(style_label)
        
        form_ajuste.addRow(lbl_real_aju, self.inp_real_ajuste)
        form_ajuste.addRow("", self.lbl_diff_ajuste)
        form_ajuste.addRow(lbl_mot_aju, self.inp_motivo_ajuste)
        
        self.stack.addWidget(self.wdg_entrada)
        self.stack.addWidget(self.wdg_ajuste)
        layout.addWidget(self.stack)
        
        self.grupo_op.idToggled.connect(self.cambiar_operacion)
        
        btn_ly = QHBoxLayout()
        btn_ly.addStretch()
        self.btn_confirmar = QPushButton("Confirmar Operación")
        self.btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirmar.setStyleSheet(f"QPushButton {{ background-color: {COLOR_PRIMARY}; color: white; padding: 10px 24px; font-weight: bold; border-radius: 6px; border: none; }} QPushButton:hover {{ background-color: #1d4ed8; }}")
        self.btn_confirmar.clicked.connect(self.guardar)
        btn_ly.addWidget(self.btn_confirmar)
        
        layout.addLayout(btn_ly)
        
        self.diferencia = 0.0
        self.cambiar_operacion()

    def cambiar_operacion(self):
        op_id = self.grupo_op.checkedId()
        self.stack.setCurrentIndex(op_id)
        if op_id == 0:
            self.btn_confirmar.setText("Confirmar Entrada")
        else:
            self.btn_confirmar.setText("Aplicar Ajuste")

    def calcular_diferencia_ajuste(self):
        txt = self.inp_real_ajuste.text().replace(',', '.')
        try:
            real = float(txt)
            self.diferencia = real - self.fisico_actual
            if self.diferencia > 0:
                self.lbl_diff_ajuste.setText(f"Diferencia: +{self.diferencia:g} (Se creará ENTRADA)")
                self.lbl_diff_ajuste.setStyleSheet("color: #10b981; font-weight: bold;")
            elif self.diferencia < 0:
                self.lbl_diff_ajuste.setText(f"Diferencia: {self.diferencia:g} (Se creará SALIDA)")
                self.lbl_diff_ajuste.setStyleSheet("color: #ef4444; font-weight: bold;")
            else:
                self.lbl_diff_ajuste.setText("Diferencia: 0 (No hay ajuste)")
                self.lbl_diff_ajuste.setStyleSheet("color: #64748b; font-weight: bold;")
        except:
            self.diferencia = 0.0
            self.lbl_diff_ajuste.setText("Diferencia: --")
            self.lbl_diff_ajuste.setStyleSheet("color: #64748b;")

    def guardar(self):
        cod = self.p_data['codigo']
        op_id = self.grupo_op.checkedId()
        
        if op_id == 0:
            try:
                cant = float(self.inp_cant_entrada.text().replace(',', '.'))
                if cant <= 0: raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Error", "La cantidad debe ser un número mayor a 0.")
                return
                
            notas = self.inp_notas_entrada.text().strip()
            
            try:
                registrar_ingreso_manual(self.conn, cod, cant, notas)
                QMessageBox.information(self, "Éxito", "Entrada registrada correctamente.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                
        else:
            motivo = self.inp_motivo_ajuste.text().strip()
            if not motivo:
                QMessageBox.warning(self, "Error", "El motivo del ajuste es obligatorio para la trazabilidad.")
                return
                
            if abs(self.diferencia) < 0.001:
                QMessageBox.information(self, "Aviso", "No hay diferencia que ajustar.")
                self.accept()
                return
                
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
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        lbl_info = QLabel("Productos que requieren atención inmediata:")
        lbl_info.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl_info)
        
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["Cód.", "Producto", "Disp.", "Mín.", "Prioridad"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {COLOR_BORDER}; border-radius: 8px;
                gridline-color: {COLOR_BORDER};
                background-color: {COLOR_CARD_BG}; outline: none; font-size: 13px;
                color: {COLOR_TEXT_MAIN};
            }}
            QHeaderView::section {{
                background-color: {COLOR_BG}; color: {COLOR_TEXT_SEC};
                font-weight: 700; font-size: 12px;
                border: none; border-bottom: 1px solid {COLOR_BORDER}; padding: 10px 8px;
            }}
            QTableWidget::item {{
                border-bottom: 1px solid #f1f5f9;
                padding: 4px 8px;
            }}
            QTableWidget::item:selected {{
                background-color: #ebf5ff;
            }}
        """)
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
                border-radius: 16px;
                border: 1px solid {COLOR_BORDER};
            }}
        """)
        self.card.setFixedWidth(520)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(24)
        
        # Header (Close button)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_title = QLabel("Detalle del Producto")
        lbl_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        header_layout.addWidget(lbl_title)
        
        header_layout.addStretch()
        
        from ui.components.boton_x import BotonCerrarX
        btn_close = BotonCerrarX()
        btn_close.clicked.connect(self.cerrar)
        header_layout.addWidget(btn_close)
        
        card_layout.addLayout(header_layout)
        
        # --- PERFIL DEL PRODUCTO ---
        profile_layout = QHBoxLayout()
        profile_layout.setSpacing(24)
        
        # Imagen
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setFixedSize(140, 140)
        img_label.setStyleSheet(f"background-color: {COLOR_BG}; border-radius: 16px; border: 1px solid {COLOR_BORDER};")
        
        has_image = False
        img_path = producto.get('imagen_path')
        p_res = resolver_ruta_imagen(img_path)
        
        if p_res:
            pix = QPixmap(str(p_res))
            if not pix.isNull():
                img_label.setPixmap(pix.scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                img_label.setStyleSheet("background-color: transparent; border: none;")
                has_image = True
                
        if not has_image:
            img_label.setText("📦")
            img_label.setStyleSheet(f"background-color: {COLOR_BG}; border-radius: 16px; border: 1px dashed #CBD5E1; color: #94A3B8; font-size: 48px;")
            
        profile_layout.addWidget(img_label)
        
        # Info Principal
        from PyQt6.QtWidgets import QSizePolicy
        info_ly = QVBoxLayout()
        info_ly.setSpacing(4)
        
        atp = producto.get('atp', 0.0)
        min_stk = producto.get('stock_minimo', 0.0)
        
        estado_txt = "DISPONIBLE"
        bg_badge = "#dcfce7"
        color_badge = "#166534"
        
        if atp <= 0:
            estado_txt = "SIN STOCK"
            bg_badge = "#fee2e2"
            color_badge = "#991b1b"
        elif min_stk > 0 and atp <= min_stk:
            estado_txt = "STOCK BAJO"
            bg_badge = "#fef9c3"
            color_badge = "#854d0e"
            
        lbl_estado = QLabel(estado_txt)
        lbl_estado.setStyleSheet(f"background-color: {bg_badge}; color: {color_badge}; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 10px; letter-spacing: 0.5px;")
        lbl_estado.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        
        lbl_desc = QLabel(producto['descripcion'])
        lbl_desc.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {COLOR_TEXT_MAIN}; letter-spacing: -0.5px;")
        lbl_desc.setWordWrap(True)
        
        lbl_cod = QLabel(f"Código: {producto['codigo']}")
        lbl_cod.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_SEC}; font-weight: 500;")
        
        lbl_precio = QLabel(f"$ {producto['precio_venta']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        lbl_precio.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {COLOR_PRIMARY}; margin-top: 6px;")
        
        info_ly.addWidget(lbl_estado)
        info_ly.addWidget(lbl_desc)
        info_ly.addWidget(lbl_cod)
        info_ly.addWidget(lbl_precio)
        info_ly.addStretch()
        
        profile_layout.addLayout(info_ly)
        
        card_layout.addLayout(profile_layout)
        card_layout.addSpacing(20)
        
        # Divisor
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {COLOR_BORDER}; border: none; min-height: 1px; max-height: 1px;")
        card_layout.addWidget(sep)
        card_layout.addSpacing(20)
        
        # --- MÉTRICAS DE STOCK ---
        from PyQt6.QtWidgets import QGridLayout
        
        lbl_stk_tit = QLabel("Métricas de Inventario")
        lbl_stk_tit.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {COLOR_TEXT_MAIN};")
        card_layout.addWidget(lbl_stk_tit)
        card_layout.addSpacing(12)
        
        grid_ly = QGridLayout()
        grid_ly.setSpacing(12)
        
        def crear_tarjeta_metrica(titulo, valor, color_valor, es_destacado=False):
            f = QFrame()
            bg = COLOR_BG if not es_destacado else "#f0f9ff"
            border = COLOR_BORDER if not es_destacado else "#bae6fd"
            f.setStyleSheet(f"background-color: {bg}; border: 1px solid {border}; border-radius: 8px;")
            l = QVBoxLayout(f)
            l.setContentsMargins(14, 12, 14, 12)
            l.setSpacing(2)
            lt = QLabel(titulo)
            lt.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 11px; font-weight: bold; border: none; background: transparent; text-transform: uppercase;")
            lv = QLabel(valor)
            lv.setStyleSheet(f"color: {color_valor}; font-size: 17px; font-weight: 900; border: none; background: transparent;")
            l.addWidget(lt)
            l.addWidget(lv)
            return f
            
        uni = producto['unidad_base']
        fis = f"{producto.get('stock_fisico', 0):g} {uni}"
        comp = f"{producto.get('comprometido', 0):g} {uni}"
        disp = f"{atp:g} {uni}"
        min_v = f"{min_stk:g} {uni}"
        
        t_fis = crear_tarjeta_metrica("Físico", fis, COLOR_TEXT_MAIN)
        t_comp = crear_tarjeta_metrica("Comprometido", comp, COLOR_TEXT_MAIN)
        t_disp = crear_tarjeta_metrica("ATP (Disponible)", disp, COLOR_PRIMARY, True)
        t_min = crear_tarjeta_metrica("Mínimo", min_v, COLOR_TEXT_MAIN)
        
        grid_ly.addWidget(t_fis, 0, 0)
        grid_ly.addWidget(t_comp, 0, 1)
        grid_ly.addWidget(t_disp, 1, 0)
        grid_ly.addWidget(t_min, 1, 1)
        
        card_layout.addLayout(grid_ly)
        
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
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        lbl_info = QLabel("Análisis de rotación de productos:")
        lbl_info.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl_info)
        
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["Cód.", "Producto", "Vendidos", "Stock Actual", "Sugerencia"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {COLOR_BORDER}; border-radius: 8px;
                gridline-color: {COLOR_BORDER};
                background-color: {COLOR_CARD_BG}; outline: none; font-size: 13px;
                color: {COLOR_TEXT_MAIN};
            }}
            QHeaderView::section {{
                background-color: {COLOR_BG}; color: {COLOR_TEXT_SEC};
                font-weight: 700; font-size: 12px;
                border: none; border-bottom: 1px solid {COLOR_BORDER}; padding: 10px 8px;
            }}
            QTableWidget::item {{
                border-bottom: 1px solid #f1f5f9;
                padding: 4px 8px;
            }}
            QTableWidget::item:selected {{
                background-color: #ebf5ff;
            }}
        """)
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
