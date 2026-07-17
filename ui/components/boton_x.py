from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt

class BotonCerrarX(QPushButton):
    """
    Botón de cierre estandarizado (X) para paneles, diálogos y tarjetas.
    Cumple con el estilo Windows moderno:
    - Área clickeable ampliada.
    - Hover rojo suave, texto blanco.
    - Press rojo oscuro.
    """
    def __init__(self, parent=None):
        super().__init__("✕", parent)
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton { 
                border: none; 
                font-size: 16px; 
                font-weight: bold; 
                color: #94a3b8; 
                background: transparent; 
                border-radius: 6px; 
            }
            QPushButton:hover { 
                background-color: #ef4444; 
                color: white; 
            }
            QPushButton:pressed { 
                background-color: #dc2626; 
                color: white; 
            }
        """)
