from ui.modal import DialogoModalIntegrado
import sqlite3
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QColor

from db.conexion import limpiar_presupuestos_vencidos

from ui.theme import (
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
        self.btn_guardar.setStyleSheet(f"background-color: {COLOR_PRIMARY}; color: white; padding: 10px; font-weight: bold;")
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
        self.setMinimumSize(1050, 650)
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
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Código", "Producto", "Tipo", "Cant.", "Documento / Notas"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setStyleSheet(f"QTableWidget {{ border: 1px solid {COLOR_BORDER}; }}")
        
        layout.addWidget(self.tabla)

    def cargar_datos(self):
        busqueda = f"%{self.inp_buscar.text().strip()}%"
        tipo = self.cmb_tipo.currentText()
        
        sql = """
            SELECT 
                m.fecha_hora, 
                m.codigo_producto, 
                p.descripcion, 
                m.tipo_movimiento, 
                m.cantidad, 
                d.numero_interno,
                m.notas
            FROM movimientos_stock m
            JOIN productos p ON m.codigo_producto = p.codigo
            LEFT JOIN documentos d ON m.id_documento_origen = d.id_documento
            WHERE (m.codigo_producto LIKE ? OR p.descripcion LIKE ? OR IFNULL(d.numero_interno, '') LIKE ?)
        """
        params = [busqueda, busqueda, busqueda]
        
        if tipo != "Todos":
            sql += " AND m.tipo_movimiento = ?"
            params.append(tipo)
            
        sql += " ORDER BY m.fecha_hora DESC LIMIT 200"
        
        c = self.conn.cursor()
        c.execute(sql, params)
        filas = c.fetchall()
        
        self.tabla.setRowCount(len(filas))
        for i, (fecha, cod, desc, tm, cant, doc, notas) in enumerate(filas):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(fecha)[:16]))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(cod)))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(desc)))
            
            it_tm = QTableWidgetItem(str(tm))
            if tm == 'ENTRADA': it_tm.setForeground(QColor("#10b981"))
            else: it_tm.setForeground(QColor("#ef4444"))
            self.tabla.setItem(i, 3, it_tm)
            
            self.tabla.setItem(i, 4, QTableWidgetItem(f"{cant:g}"))
            
            info_doc = doc if doc else "Ajuste Directo"
            if notas: info_doc += f" | {notas}"
            self.tabla.setItem(i, 5, QTableWidgetItem(info_doc))


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
        self.btn_guardar.setStyleSheet(f"background-color: {COLOR_PRIMARY}; color: white; padding: 10px;")
        self.btn_guardar.clicked.connect(self.guardar)
        layout.addWidget(self.btn_guardar)

    def guardar(self):
        self.settings.setValue("col_precio_visible", self.chk_precio.isChecked())
        self.settings.setValue("col_minimo_visible", self.chk_minimo.isChecked())
        self.settings.setValue("col_desglose_visible", self.chk_comprometido.isChecked())
        self.accept()
