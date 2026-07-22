from ui.components.operacion_base import OperacionBaseWidget, DialogoVentaExitosa
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame
from PyQt6.QtCore import Qt

class PestanaNuevaVenta(OperacionBaseWidget):
    def __init__(self, conexion_db, is_edicion=False, id_presupuesto_edicion=None):
        super().__init__(conexion_db, is_edicion=is_edicion, id_presupuesto_edicion=id_presupuesto_edicion)
        self.tipo_documento_seleccionado = 'VENTA'
        self.btn_confirmar.setText('Confirmar Venta [F12]')

    def armar_panel_inferior(self, layout):
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame
        from PyQt6.QtCore import Qt

        ly_main = QVBoxLayout()
        ly_main.setSpacing(6)
        ly_main.setContentsMargins(0, 0, 0, 0)

        # --- FILA 1 ---
        ly_r1 = QHBoxLayout()
        ly_r1.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.input_observaciones.setMinimumWidth(200)
        self.input_observaciones.setMaximumHeight(32)
        self.input_observaciones.setPlaceholderText("Observaciones (opcional)...")
        ly_r1.addWidget(self.input_observaciones)
        
        ly_r1.addStretch()
        
        lbl_desc = QLabel('Desc:')
        lbl_desc.setStyleSheet('color: #64748B; font-weight: 600;')
        ly_r1.addWidget(lbl_desc)
        self.input_desc_gral.setFixedWidth(60)
        self.input_desc_gral.setMaximumHeight(32)
        ly_r1.addWidget(self.input_desc_gral)
        lbl_perc = QLabel('%')
        lbl_perc.setStyleSheet('color: #64748B;')
        ly_r1.addWidget(lbl_perc)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #E2E8F0; margin: 0 8px;")
        ly_r1.addWidget(sep)
        
        self.chk_iva.setStyleSheet("color: #475569; font-weight: 500;")
        ly_r1.addWidget(self.chk_iva)
        self.input_iva_porc.setFixedWidth(60)
        self.input_iva_porc.setMaximumHeight(32)
        ly_r1.addWidget(self.input_iva_porc)
        lbl_perc2 = QLabel('%')
        lbl_perc2.setStyleSheet('color: #64748B;')
        ly_r1.addWidget(lbl_perc2)
        
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("color: #E2E8F0; margin: 0 8px;")
        ly_r1.addWidget(sep2)
        
        lbl_sub = QLabel('Subtotal:')
        lbl_sub.setStyleSheet('color: #64748B; font-weight: 600;')
        ly_r1.addWidget(lbl_sub)
        self.lbl_subtotal.setStyleSheet('color: #64748B; font-size: 13px;')
        self.lbl_subtotal.setMinimumWidth(80)
        self.lbl_subtotal.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        ly_r1.addWidget(self.lbl_subtotal)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.VLine)
        sep3.setStyleSheet("color: #E2E8F0; margin: 0 8px;")
        ly_r1.addWidget(sep3)
        
        lbl_tot = QLabel('TOTAL:')
        lbl_tot.setStyleSheet('font-weight: 900; color: #64748B; font-size: 16px;')
        ly_r1.addWidget(lbl_tot)
        
        self.lbl_total.setStyleSheet('font-weight: 900; color: #2563EB; font-size: 24px;')
        self.lbl_total.setMinimumWidth(120)
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        ly_r1.addWidget(self.lbl_total)
        
        ly_r1.addSpacing(16)
        
        self.btn_confirmar.setMinimumWidth(160)
        self.btn_confirmar.setMaximumHeight(36)
        ly_r1.addWidget(self.btn_confirmar)
        
        ly_main.addLayout(ly_r1)
        
        layout.addLayout(ly_main)
