"""
ui/dialogs_historial.py — Diálogo para visualizar el historial completo de un cliente.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
)
from PyQt6.QtCore import Qt

from ui.core.theme import (
    COLOR_PRIMARY, COLOR_BG, COLOR_CARD_BG, COLOR_TEXT_MAIN,
    COLOR_TEXT_SEC, COLOR_BORDER
)
from db import queries_clientes as qc


class DialogoHistorialCliente(QDialog):
    def __init__(self, conn, id_cliente: int, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.id_cliente = id_cliente
        self.historial_completo = []

        self.setWindowTitle("Historial de Operaciones")
        self.setMinimumWidth(750)
        self.setMinimumHeight(500)
        

        self._construir_ui()
        self._cargar_datos()

    def _construir_ui(self):
        ly = QVBoxLayout(self)
        ly.setContentsMargins(24, 24, 24, 24)
        ly.setSpacing(16)

        # Cabecera
        ly_hdr = QHBoxLayout()
        lbl_titulo = QLabel("Historial de Operaciones")
        lbl_titulo.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {COLOR_TEXT_MAIN};")
        
        lbl_filtro = QLabel("Tipo:")
        lbl_filtro.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 12px; font-weight: bold;")
        self.cb_filtro = QComboBox()
        self.cb_filtro.addItems(["Todos", "Ventas", "Presupuestos"])
        self.cb_filtro.setStyleSheet(
            f"border: 1px solid {COLOR_BORDER}; border-radius: 4px; padding: 4px 8px; "
            f"background-color: {COLOR_BG}; color: {COLOR_TEXT_MAIN};"
        )
        self.cb_filtro.currentTextChanged.connect(self._aplicar_filtro)

        ly_hdr.addWidget(lbl_titulo)
        ly_hdr.addStretch()
        ly_hdr.addWidget(lbl_filtro)
        ly_hdr.addWidget(self.cb_filtro)
        ly.addLayout(ly_hdr)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Documento", "Número", "Total", "Estado"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setStyleSheet(
            f"QTableWidget {{ background-color: {COLOR_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 6px; }}"
            f"QHeaderView::section {{ background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_SEC}; font-weight: 600; font-size: 12px; padding: 8px; border: none; border-bottom: 1px solid {COLOR_BORDER}; }}"
        )
        ly.addWidget(self.tabla)

        # Totales
        self.lbl_totales = QLabel("")
        self.lbl_totales.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-size: 13px; font-weight: bold;")
        self.lbl_totales.setAlignment(Qt.AlignmentFlag.AlignRight)
        ly.addWidget(self.lbl_totales)

        # Botón Cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet(
            f"background-color: {COLOR_PRIMARY}; color: white; border-radius: 6px; "
            f"font-weight: bold; padding: 8px 16px;"
        )
        btn_cerrar.clicked.connect(self.accept)
        ly_btn = QHBoxLayout()
        ly_btn.addStretch()
        ly_btn.addWidget(btn_cerrar)
        ly.addLayout(ly_btn)

    def _cargar_datos(self):
        self.historial_completo = qc.obtener_historial_cliente(self.conn, self.id_cliente, limite=1000)
        self._aplicar_filtro()

    def _aplicar_filtro(self):
        tipo_filtro = self.cb_filtro.currentText()
        if tipo_filtro == "Ventas": tipo_filtro = "VENTA"
        elif tipo_filtro == "Presupuestos": tipo_filtro = "PRESUPUESTO"
        else: tipo_filtro = "TODOS"
        
        filtrados = []
        for doc in self.historial_completo:
            if tipo_filtro == "TODOS" or doc["tipo"] == tipo_filtro:
                filtrados.append(doc)
                
        self.tabla.setRowCount(0)
        total_monto = 0.0

        for doc in filtrados:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            self.tabla.setRowHeight(row, 36)
            
            i_fecha = QTableWidgetItem(doc["fecha_emision"])
            i_tipo  = QTableWidgetItem(doc["tipo"])
            i_num   = QTableWidgetItem(doc["numero_interno"])
            
            val = float(doc["total_final"])
            i_tot   = QTableWidgetItem(f"$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            i_est   = QTableWidgetItem(doc["estado"])
            
            for col, item in enumerate([i_fecha, i_tipo, i_num, i_tot, i_est]):
                if col == 3: # i_tot
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(row, col, item)

            if doc["estado"] == "CONFIRMADO" and doc["tipo"] == "VENTA":
                total_monto += val

        texto_tot = f"Total en Ventas Confirmadas: $ {total_monto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        self.lbl_totales.setText(texto_tot)
        self.lbl_totales.setWordWrap(True)
