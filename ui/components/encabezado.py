from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from ui.core.theme import COLOR_TEXT_MAIN, COLOR_TEXT_SEC

def crear_encabezado_estandar(icono_txt, titulo_txt, subtitulo_txt):
    """
    Retorna (layout_izquierdo, btn_ayuda).
    El módulo anfitrión puede agregar este layout_izquierdo a su propio layout_top,
    y luego agregar sus propios botones a la derecha (junto al btn_ayuda).
    """
    ly_izq = QHBoxLayout()
    ly_izq.setSpacing(12)
    ly_izq.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    
    lbl_icono = QLabel(icono_txt)
    lbl_icono.setStyleSheet("font-size: 24px; border: none; background: transparent;")
    lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    ly_tit = QVBoxLayout()
    ly_tit.setSpacing(2)
    lbl_titulo = QLabel(titulo_txt)
    lbl_titulo.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLOR_TEXT_MAIN}; letter-spacing: -0.5px;")
    lbl_subtitulo = QLabel(subtitulo_txt)
    lbl_subtitulo.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLOR_TEXT_SEC};")
    ly_tit.addWidget(lbl_titulo)
    ly_tit.addWidget(lbl_subtitulo)
    
    ly_izq.addWidget(lbl_icono)
    ly_izq.addLayout(ly_tit)
    
    btn_ayuda = QPushButton("ⓘ Ayuda")
    btn_ayuda.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_ayuda.setStyleSheet("""
        QPushButton {
            background-color: transparent;
            color: #64748B;
            font-size: 14px;
            font-weight: bold;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background-color: #F8FAFC;
            color: #0F172A;
            border-color: #CBD5E1;
        }
    """)
    
    return ly_izq, btn_ayuda
