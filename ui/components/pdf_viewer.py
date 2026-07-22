import fitz  # PyMuPDF
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QScrollArea, QWidget, QDialog)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
from ui.core.modal import DialogoModalIntegrado
from ui.core.theme import COLOR_PRIMARY, COLOR_BG, COLOR_BORDER

class DialogoVistaPreviaPDF(DialogoModalIntegrado):
    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.setWindowTitle("Vista Previa del Documento")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)
        self.resize(1100, 850)
        
        ly = QVBoxLayout(self)
        ly.setContentsMargins(24, 24, 24, 24)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: #cbd5e1; border: none;")
        
        self.container = QWidget()
        self.container_ly = QVBoxLayout(self.container)
        self.container_ly.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        try:
            doc = fitz.open(self.pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                lbl = QLabel()
                lbl.setPixmap(QPixmap.fromImage(img))
                lbl.setStyleSheet("background-color: white; border: 1px solid #94a3b8; margin-bottom: 10px;")
                self.container_ly.addWidget(lbl)
            doc.close()
        except Exception as e:
            err = QLabel(f"Error renderizando PDF:\n{e}")
            self.container_ly.addWidget(err)
            
        self.scroll.setWidget(self.container)
        ly.addWidget(self.scroll)
        
        btn_ly = QHBoxLayout()
        btn_ly.addStretch()
        
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet(f"background-color: {COLOR_BG}; border: 1px solid {COLOR_BORDER}; padding: 8px 20px; border-radius: 6px; font-weight: bold;")
        btn_cerrar.clicked.connect(self.reject)
        btn_ly.addWidget(btn_cerrar)
        
        btn_pdf = QPushButton("Exportar PDF")
        btn_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_pdf.setStyleSheet(f"background-color: {COLOR_PRIMARY}; color: white; border: none; padding: 8px 20px; border-radius: 6px; font-weight: bold;")
        btn_pdf.clicked.connect(self.accept)
        btn_ly.addWidget(btn_pdf)
        
        ly.addLayout(btn_ly)
