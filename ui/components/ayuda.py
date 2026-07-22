from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QFrame
from PyQt6.QtCore import Qt
from ui.core.modal import DialogoModalIntegrado
from ui.core.theme import COLOR_TEXT_MAIN, COLOR_TEXT_SEC, COLOR_BG, COLOR_BORDER, COLOR_PRIMARY

class DialogoAyudaContextual(DialogoModalIntegrado):
    def __init__(self, titulo, subtitulo, texto_html, parent=None):
        # We explicitly use parent.window() so the overlay covers the whole app
        # and blocks the sidebar, acting as a true modal.
        main_window = parent.window() if parent else None
        super().__init__(main_window)
        
        self.setWindowTitle(titulo)
        self.setMinimumWidth(800)
        self.setMinimumHeight(650)
        
        ly = QVBoxLayout(self)
        ly.setSpacing(16)
        ly.setContentsMargins(0, 0, 0, 0)
        
        if subtitulo:
            lbl_sub = QLabel(subtitulo)
            lbl_sub.setStyleSheet(f"font-size: 15px; color: {COLOR_PRIMARY}; font-weight: bold; margin-bottom: 8px;")
            ly.addWidget(lbl_sub)
            
        # Contenedor escroleable para el texto
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: 1px solid {COLOR_BORDER}; border-radius: 6px; background-color: {COLOR_BG}; }}")
        
        scroll_content = QFrame()
        scroll_content.setStyleSheet(f"background-color: {COLOR_BG};")
        scroll_ly = QVBoxLayout(scroll_content)
        scroll_ly.setContentsMargins(24, 24, 24, 24)
        
        lbl_info = QLabel(texto_html)
        lbl_info.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_MAIN}; line-height: 1.5;")
        lbl_info.setWordWrap(True)
        lbl_info.setTextFormat(Qt.TextFormat.RichText)
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        scroll_ly.addWidget(lbl_info)
        scroll_ly.addStretch()
        scroll.setWidget(scroll_content)
        
        ly.addWidget(scroll)
        
        # Botón Cerrar explícito en la base
        ly_btn = QHBoxLayout()
        ly_btn.addStretch()
        
        btn_cerrar = QPushButton("Cerrar Ayuda")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY};
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                opacity: 0.9;
                background-color: #1d4ed8;
            }}
        """)
        btn_cerrar.clicked.connect(self.accept)
        
        ly_btn.addWidget(btn_cerrar)
        ly.addLayout(ly_btn)
