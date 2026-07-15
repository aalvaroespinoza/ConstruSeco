"""
ui/modal.py — Infraestructura de Modales Integrados.

Proporciona un overlay oscuro y centrado que captura eventos,
oscurece la ventana principal y puede comportarse sincrónicamente
mediante un QEventLoop local para reemplazar a QDialog.
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QWidget, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QEventLoop, QEvent, QObject
from PyQt6.QtGui import QColor, QKeyEvent

from ui.core.theme import COLOR_BORDER

class ModalResult:
    Rejected = 0
    Accepted = 1

class DialogoModalIntegrado(QFrame):
    """
    Clase base para formularios modales que reemplaza a QDialog.
    Proporciona un contenedor estilizado y maneja su propio exec()
    para renderizarse dentro de un ModalOverlay sin romper el contrato
    funcional de QDialog.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._modal_parent = None
        self._titulo_inyectado = False
        
        from ui.core.theme import COLOR_CARD_BG, COLOR_BORDER
        self.setObjectName("dialogo_modal_card")
        self.setStyleSheet(f"""
            QFrame#dialogo_modal_card {{
                background-color: {COLOR_CARD_BG};
                border-radius: 12px;
                border: 1px solid {COLOR_BORDER};
            }}
        """)
        
    def exec(self):
        # Inyectar título si existe
        ly = self.layout()
        if ly:
            ly.setContentsMargins(24, 24, 24, 24)
            
        if ly and self.windowTitle() and not self._titulo_inyectado:
            from PyQt6.QtWidgets import QLabel, QPushButton, QHBoxLayout, QWidget
            from PyQt6.QtCore import Qt
            from ui.core.theme import COLOR_TEXT_MAIN, COLOR_BORDER
            
            header_widget = QWidget()
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(0, 0, 0, 12)
            
            lbl_title = QLabel(self.windowTitle())
            lbl_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
            
            btn_close = QPushButton("✕")
            btn_close.setFixedSize(24, 24)
            btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_close.setStyleSheet("""
                QPushButton { border: none; font-size: 16px; font-weight: bold; color: #94a3b8; background: transparent; border-radius: 4px; }
                QPushButton:hover { background-color: #ef4444; color: white; }
                QPushButton:pressed { background-color: #b91c1c; color: white; }
            """)
            btn_close.clicked.connect(self.reject)
            
            header_layout.addWidget(lbl_title)
            header_layout.addStretch()
            header_layout.addWidget(btn_close)
            
            header_widget.setStyleSheet(f"border-bottom: 1px solid {COLOR_BORDER}; margin-bottom: 12px;")
            
            ly.insertWidget(0, header_widget)
            self._titulo_inyectado = True
            
        modal = ModalOverlay(self.parent(), self)
        res = modal.exec()
        
        from PyQt6.QtWidgets import QDialog
        if res == ModalResult.Accepted:
            return QDialog.DialogCode.Accepted
        return QDialog.DialogCode.Rejected
        
    def set_modal_parent(self, modal):
        self._modal_parent = modal
        
    def accept(self):
        if self._modal_parent:
            self._modal_parent.accept()
            
    def reject(self):
        if self._modal_parent:
            self._modal_parent.reject()

class ModalOverlay(QFrame):

    """
    Overlay reutilizable que oscurece el fondo y bloquea la interacción.
    Puede ejecutar un QEventLoop local para emular el comportamiento de QDialog.exec().
    """
    def __init__(self, parent: QWidget, content_widget: QWidget):
        super().__init__(parent)
        self.parent_widget = parent
        self._loop = None
        self._result = ModalResult.Rejected
        
        self.setObjectName("modal_overlay")
        self.setStyleSheet("""
            QFrame#modal_overlay {
                background-color: rgba(15, 23, 42, 0.7); 
            }
        """)
        
        # Bloquear interacción con el fondo
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        # Ocultar por defecto
        self.setVisible(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Interceptar eventos del padre para redimensionar el overlay
        self.parent_widget.installEventFilter(self)
        
        main_layout = QVBoxLayout(self)
        
        # Contenedor del contenido (la "tarjeta" blanca)
        self.card = QFrame()
        self.card.setObjectName("modal_card")
        self.card.setStyleSheet(f"""
            QFrame#modal_card {{
                background-color: transparent;
                border: none;
            }}
        """)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.addWidget(content_widget)
        
        # Permitir al content_widget comunicarse con el modal
        if hasattr(content_widget, 'set_modal_parent'):
            content_widget.set_modal_parent(self)
            
        main_layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj == self.parent_widget:
            if event.type() == QEvent.Type.Resize:
                self.setGeometry(self.parent_widget.rect())
            elif event.type() == QEvent.Type.Hide:
                self.reject()
        return super().eventFilter(obj, event)

    def exec(self) -> int:
        self.setGeometry(self.parent_widget.rect())
        self.setVisible(True)
        self.raise_()
        self.setFocus()
        
        self._loop = QEventLoop()
        self._loop.exec()
        
        self.setVisible(False)
        self.setParent(None) # Cleanup
        self.deleteLater()
        return self._result

    def accept(self):
        self._result = ModalResult.Accepted
        if self._loop:
            self._loop.quit()

    def reject(self):
        self._result = ModalResult.Rejected
        if self._loop:
            self._loop.quit()
            
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
