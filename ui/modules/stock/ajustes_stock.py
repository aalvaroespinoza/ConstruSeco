from ui.core.modal import DialogoModalIntegrado
import sqlite3
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QColor, QFont


from ui.core.theme import (
    COLOR_PRIMARY, COLOR_BG, COLOR_TEXT_MAIN, COLOR_BORDER
)


class DialogoConfiguracionGeneral(DialogoModalIntegrado):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración General de Stock")
        self.setMinimumWidth(350)
        self.settings = QSettings("ConstrusecoPereyra", "StockConfig")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # 1. Stock mínimo predeterminado para nuevos
        self.inp_min = QLineEdit(str(self.settings.value("default_stock_min", 0.0, type=float)))
        
        # 2. Cantidad mostrada en Frecuentes
        self.cmb_freq_limit = QComboBox()
        for v in [3, 4, 5, 8, 10]:
            self.cmb_freq_limit.addItem(str(v), v)
        idx_lim = self.cmb_freq_limit.findData(self.settings.value("freq_limit", 4, type=int))
        if idx_lim >= 0: self.cmb_freq_limit.setCurrentIndex(idx_lim)
        
        # 3. Período Frecuentes
        self.cmb_freq_days = QComboBox()
        self.cmb_freq_days.addItem("Últimos 30 días", 30)
        self.cmb_freq_days.addItem("Últimos 60 días", 60)
        self.cmb_freq_days.addItem("Últimos 90 días", 90)
        idx_days = self.cmb_freq_days.findData(self.settings.value("freq_days", 30, type=int))
        if idx_days >= 0: self.cmb_freq_days.setCurrentIndex(idx_days)
        
        form.addRow("Stock mínimo predeterminado:", self.inp_min)
        form.addRow("Productos en 'Frecuentes':", self.cmb_freq_limit)
        form.addRow("Período de análisis:", self.cmb_freq_days)
        
        layout.addLayout(form)
        
        self.btn_guardar = QPushButton("Guardar Configuración")
        self.btn_guardar.setObjectName("btn_guardar_config")
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setStyleSheet(f"""
            QPushButton#btn_guardar_config {{
                background-color: {COLOR_PRIMARY}; 
                color: white; 
                padding: 10px; 
                border-radius: 6px;
                font-weight: bold;
                border: none;
            }}
            QPushButton#btn_guardar_config:hover {{
                background-color: #1d4ed8;
                color: white;
            }}
            QPushButton#btn_guardar_config:pressed {{
                background-color: #1e3a8a;
                color: white;
            }}
        """)
        self.btn_guardar.clicked.connect(self.guardar)
        layout.addWidget(self.btn_guardar)

    def guardar(self):
        try:
            val_min = float(self.inp_min.text().replace(',', '.'))
            if val_min < 0: raise ValueError
        except:
            QMessageBox.warning(self, "Error", "Stock mínimo debe ser un número válido >= 0.")
            return
            
        self.settings.setValue("default_stock_min", val_min)
        self.settings.setValue("freq_limit", self.cmb_freq_limit.currentData())
        self.settings.setValue("freq_days", self.cmb_freq_days.currentData())
        
        QMessageBox.information(self, "Éxito", "Configuración guardada correctamente.")
        self.accept()


class DialogoHistorialMovimientos(DialogoModalIntegrado):
    def __init__(self, conexion_db, parent=None):
        super().__init__(parent)
        self.conn = conexion_db
        self.setWindowTitle("Historial de Movimientos de Stock")
        self.setMinimumSize(900, 600)
        self.init_ui()
        self.cargar_datos()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Buscador
        ly_busq = QHBoxLayout()
        self.inp_buscar = QLineEdit()
        self.inp_buscar.setPlaceholderText("Buscar por código, producto o doc...")
        self.inp_buscar.textChanged.connect(self.cargar_datos)
        ly_busq.addWidget(QLabel("🔍 Buscar:"))
        ly_busq.addWidget(self.inp_buscar)
        
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["Todos", "ENTRADA", "SALIDA"])
        self.cmb_tipo.currentTextChanged.connect(self.cargar_datos)
        ly_busq.addWidget(self.cmb_tipo)
        layout.addLayout(ly_busq)
        
        # Tabla
        self.tabla = QTableWidget(0, 8)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Código", "Producto", "Tipo", "Cant.", "Stk Ant.", "Stk Post.", "Origen / Notas"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setStyleSheet(f"QTableWidget {{ border: 1px solid {COLOR_BORDER}; }}")
        
        layout.addWidget(self.tabla)
        self.tabla.itemDoubleClicked.connect(self.abrir_documento_asociado)

    def cargar_datos(self):
        busqueda = f"%{self.inp_buscar.text().strip()}%"
        tipo = self.cmb_tipo.currentText()
        
        sql = """
            WITH CTE_Saldos AS (
                SELECT 
                    m.id_movimiento,
                    m.fecha_hora, 
                    m.codigo_producto, 
                    m.tipo_movimiento, 
                    m.cantidad, 
                    m.id_documento_origen,
                    m.notas,
                    SUM(CASE WHEN m.tipo_movimiento = 'ENTRADA' THEN m.cantidad ELSE -m.cantidad END)
                    OVER (
                        PARTITION BY m.codigo_producto 
                        ORDER BY m.fecha_hora ASC, m.id_movimiento ASC
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ) as stock_posterior
                FROM movimientos_stock m
            )
            SELECT 
                c.fecha_hora, 
                c.codigo_producto, 
                p.descripcion, 
                c.tipo_movimiento, 
                c.cantidad, 
                c.stock_posterior,
                d.numero_interno,
                d.tipo,
                c.notas
            FROM CTE_Saldos c
            JOIN productos p ON c.codigo_producto = p.codigo
            LEFT JOIN documentos d ON c.id_documento_origen = d.id_documento
            WHERE (c.codigo_producto LIKE ? OR p.descripcion LIKE ? OR IFNULL(d.numero_interno, '') LIKE ? OR IFNULL(c.notas, '') LIKE ?)
        """
        params = [busqueda, busqueda, busqueda, busqueda]
        
        if tipo != "Todos":
            sql += " AND c.tipo_movimiento = ?"
            params.append(tipo)
            
        sql += " ORDER BY c.fecha_hora DESC, c.id_movimiento DESC LIMIT 200"
        
        from db.queries_stock import ejecutar_consulta_historial
        filas = ejecutar_consulta_historial(self.conn, sql, params)
        
        self.tabla.setRowCount(len(filas))
        for i, (fecha, cod, desc, tm, cant, stk_post, doc, doc_tipo, notas) in enumerate(filas):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(fecha)[:16]))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(cod)))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(desc)))
            
            it_tm = QTableWidgetItem(str(tm))
            if tm == 'ENTRADA': 
                it_tm.setForeground(QColor("#10b981"))
                delta = cant
            else: 
                it_tm.setForeground(QColor("#ef4444"))
                delta = -cant
            self.tabla.setItem(i, 3, it_tm)
            
            self.tabla.setItem(i, 4, QTableWidgetItem(f"{cant:g}"))
            
            stk_ant = stk_post - delta
            self.tabla.setItem(i, 5, QTableWidgetItem(f"{stk_ant:g}"))
            
            it_post = QTableWidgetItem(f"{stk_post:g}")
            it_post.setFont(QFont("Segoe UI", -1, QFont.Weight.Bold))
            self.tabla.setItem(i, 6, it_post)
            
            if doc_tipo == 'VENTA':
                info_doc = f"Venta #{doc}"
            elif doc_tipo == 'PRESUPUESTO':
                info_doc = f"Presupuesto #{doc} confirmado"
            elif doc_tipo == 'AJUSTE':
                info_doc = f"Ajuste de inventario #{doc}"
            elif doc_tipo == 'COMPRA':
                info_doc = f"Compra #{doc}"
            elif doc:
                info_doc = f"{doc_tipo} #{doc}"
            else:
                info_doc = "Entrada manual / Ajuste directo"
                
            if notas: info_doc += f" ({notas})"
            self.tabla.setItem(i, 7, QTableWidgetItem(info_doc))
            # Save hidden data for double click
            item_hidden = QTableWidgetItem(info_doc)
            item_hidden.setData(Qt.ItemDataRole.UserRole, (doc, doc_tipo, notas, tm, cant, fecha, cod, desc))
            self.tabla.setItem(i, 7, item_hidden)



    def abrir_documento_asociado(self, item):
        row = item.row()
        item_data = self.tabla.item(row, 7)
        if not item_data: return
        data = item_data.data(Qt.ItemDataRole.UserRole)
        if not data: return
        
        doc, doc_tipo, notas, tm, cant, fecha, cod, desc = data
        
        if doc_tipo == 'PRESUPUESTO' and doc:
            from ui.modules.presupuestos.tab_presupuestos import DialogoDetallePresupuesto
            d = DialogoDetallePresupuesto(self.conn, int(doc), self)
            d.exec()
        elif doc_tipo == 'VENTA' and doc:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Detalle de Venta", f"Documento: Venta #{doc}\nFecha: {fecha}\n\nProducto: {desc} ({cod})\nMovimiento: {tm} de {cant:g} unidades.\n\nNotas: {notas or 'Sin notas adicionales'}")
        elif doc_tipo == 'AJUSTE' and doc:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Detalle de Ajuste", f"Documento: Ajuste #{doc}\nFecha: {fecha}\n\nProducto: {desc} ({cod})\nMovimiento: {tm} de {cant:g} unidades.\n\nNotas: {notas or 'Sin notas adicionales'}")
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Detalle del Movimiento", f"Operación Manual o Directa\nFecha: {fecha}\n\nProducto: {desc} ({cod})\nMovimiento: {tm} de {cant:g} unidades.\n\nNotas: {notas or 'Sin notas adicionales'}")

class DialogoVisualizacionInventario(DialogoModalIntegrado):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opciones de Visualización")
        self.setMinimumWidth(300)
        self.settings = QSettings("ConstrusecoPereyra", "StockConfig")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        grp = QGroupBox("Columnas Visibles en Tabla Principal")
        ly_grp = QVBoxLayout()
        
        self.chk_precio = QCheckBox("Mostrar 'Precio'")
        self.chk_precio.setChecked(self.settings.value("col_precio_visible", True, type=bool))
        
        self.chk_minimo = QCheckBox("Mostrar 'Stock Mínimo'")
        self.chk_minimo.setChecked(self.settings.value("col_minimo_visible", True, type=bool))
        
        self.chk_comprometido = QCheckBox("Mostrar desglose 'Físico / Comprometido'")
        self.chk_comprometido.setChecked(self.settings.value("col_desglose_visible", True, type=bool))
        
        ly_grp.addWidget(self.chk_precio)
        ly_grp.addWidget(self.chk_minimo)
        ly_grp.addWidget(self.chk_comprometido)
        grp.setLayout(ly_grp)
        
        layout.addWidget(grp)
        
        self.btn_guardar = QPushButton("Aplicar")
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setStyleSheet(f"background-color: {COLOR_PRIMARY}; color: white; padding: 10px;")
        self.btn_guardar.clicked.connect(self.guardar)
        layout.addWidget(self.btn_guardar)

    def guardar(self):
        self.settings.setValue("col_precio_visible", self.chk_precio.isChecked())
        self.settings.setValue("col_minimo_visible", self.chk_minimo.isChecked())
        self.settings.setValue("col_desglose_visible", self.chk_comprometido.isChecked())
        self.accept()
