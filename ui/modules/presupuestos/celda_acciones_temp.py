import sys
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QPushButton, QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from ui.core.theme import COLOR_BORDER, COLOR_BG, COLOR_TEXT_MAIN

class _CeldaAcciones(QWidget):
    ver_solicitado = pyqtSignal(int)
    editar_solicitado = pyqtSignal(int)
    pdf_solicitado = pyqtSignal(int)
    preview_solicitado = pyqtSignal(int)
    confirmar_solicitado = pyqtSignal(int)
    anular_solicitado = pyqtSignal(int)
    
    def __init__(self, id_documento: int, estado: str):
        super().__init__()
        self._id = id_documento
        self._estado = estado
        
        ly = QHBoxLayout(self)
        ly.setContentsMargins(4, 2, 4, 2)
        ly.setSpacing(4)
        ly.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Ojo: Ver
        btn_ver = QPushButton("👁")
        btn_ver.setToolTip("Ver detalle completo")
        btn_ver.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ver.setFixedSize(28, 28)
        btn_ver.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 4px; background-color: {COLOR_BG}; color: {COLOR_TEXT_MAIN};")
        btn_ver.clicked.connect(lambda: self.ver_solicitado.emit(self._id))
        ly.addWidget(btn_ver)
        
        # Lápiz: Editar
        btn_editar = QPushButton("✎")
        btn_editar.setToolTip("Editar presupuesto")
        btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_editar.setFixedSize(28, 28)
        
        if estado == "ACTIVO":
            btn_editar.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 4px; background-color: {COLOR_BG}; color: {COLOR_TEXT_MAIN};")
            btn_editar.clicked.connect(lambda: self.editar_solicitado.emit(self._id))
        else:
            btn_editar.setEnabled(False)
            btn_editar.setStyleSheet(f"border: 1px solid #e2e8f0; border-radius: 4px; background-color: #f8fafc; color: #cbd5e1;")
            
        ly.addWidget(btn_editar)
        
        # Tres puntos: Menú
        btn_menu = QPushButton("⋮")
        btn_menu.setToolTip("Más acciones")
        btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_menu.setFixedSize(28, 28)
        btn_menu.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 4px; background-color: {COLOR_BG}; color: {COLOR_TEXT_MAIN}; font-weight: bold;")
        
        # Construir menú según estado
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu {{ background-color: {COLOR_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 4px; }} QMenu::item {{ padding: 6px 24px 6px 12px; }} QMenu::item:selected {{ background-color: #f1f5f9; }}")
        
        if estado == "ACTIVO":
            act_conf = menu.addAction("Confirmar como Venta")
            act_conf.triggered.connect(lambda: self.confirmar_solicitado.emit(self._id))
            menu.addSeparator()
            
        act_prev = menu.addAction("Vista Previa")
        act_prev.triggered.connect(lambda: self.preview_solicitado.emit(self._id))
        
        act_pdf = menu.addAction("Generar PDF")
        act_pdf.triggered.connect(lambda: self.pdf_solicitado.emit(self._id))
        
        if estado == "ACTIVO":
            menu.addSeparator()
            act_anul = menu.addAction("Anular Presupuesto")
            act_anul.triggered.connect(lambda: self.anular_solicitado.emit(self._id))
            
        btn_menu.setMenu(menu)
        ly.addWidget(btn_menu)
