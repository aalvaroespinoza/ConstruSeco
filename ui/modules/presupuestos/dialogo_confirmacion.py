from ui.core.modal import DialogoModalIntegrado
from ui.core.theme import COLOR_PRIMARY, COLOR_DANGER, COLOR_BG, COLOR_TEXT_MAIN, COLOR_TEXT_SEC, COLOR_BORDER
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QDialog
from PyQt6.QtCore import Qt

class DialogoConfirmacionPresupuesto(DialogoModalIntegrado):
    def __init__(self, titulo, mensaje_principal, detalles_html, color_confirmar=COLOR_PRIMARY, txt_confirmar="Confirmar", parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(400)
        
        ly = QVBoxLayout(self)
        ly.setSpacing(16)
        
        lbl_msg = QLabel(mensaje_principal)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_MAIN}; font-weight: bold;")
        ly.addWidget(lbl_msg)
        
        frm_det = QFrame()
        frm_det.setStyleSheet(f"background-color: #f8fafc; border: 1px solid {COLOR_BORDER}; border-radius: 6px;")
        ly_det = QVBoxLayout(frm_det)
        lbl_det = QLabel(detalles_html)
        lbl_det.setWordWrap(True)
        lbl_det.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_SEC}; border: none;")
        ly_det.addWidget(lbl_det)
        ly.addWidget(frm_det)
        
        ly_btns = QHBoxLayout()
        ly_btns.addStretch()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                border: 1px solid {COLOR_BORDER};
                color: {COLOR_TEXT_MAIN};
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #f1f5f9; }}
        """)
        btn_cancelar.clicked.connect(self.reject)
        
        btn_conf = QPushButton(txt_confirmar)
        btn_conf.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_conf.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_confirmar};
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        btn_conf.clicked.connect(self.accept)
        
        ly_btns.addWidget(btn_cancelar)
        ly_btns.addWidget(btn_conf)
        ly.addLayout(ly_btns)
