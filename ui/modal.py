"""
ui/modal.py — Infraestructura de Modales Integrados.

Proporciona un overlay oscuro y centrado que captura eventos,
oscurece la ventana principal y puede comportarse sincrónicamente
mediante un QEventLoop local para reemplazar a QDialog.
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QWidget, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QEventLoop, QEvent, QObject
from PyQt6.QtGui import QColor, QKeyEvent

from ui.theme import COLOR_BORDER

class ModalResult:
    Rejected = 0
    Accepted = 1

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
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
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
            
        main_layout.addWidget(self.card)
        
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj == self.parent_widget and event.type() == QEvent.Type.Resize:
            self.setGeometry(self.parent_widget.rect())
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
