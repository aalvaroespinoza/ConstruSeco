"""Tema visual común de la aplicación."""

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import Qt, QObject, QEvent
from PyQt6.QtWidgets import QPushButton, QTableWidget, QHeaderView, QLabel

# Constantes Visuales Centralizadas (Extraidas de módulos duplicados)
COLOR_PRIMARY = "#2563eb"
COLOR_BG = "#f8fafc"
COLOR_CARD_BG = "#ffffff"
COLOR_TEXT_MAIN = "#1e293b"
COLOR_TEXT_SEC = "#64748b"
COLOR_BORDER = "#e2e8f0"
COLOR_SUCCESS = "#10b981"
COLOR_WARNING = "#f59e0b"
COLOR_DANGER = "#ef4444"

class UIGlobalPolisher(QObject):
    """Filtro global de eventos para asegurar uniformidad visual sin modificar todos los archivos."""
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Polish:
            if isinstance(obj, QPushButton):
                obj.setCursor(Qt.CursorShape.PointingHandCursor)
                text = obj.text().lower()
                name = obj.objectName().lower()
                is_danger = any(k in text for k in ['cerrar', 'cancelar', 'eliminar', 'anular']) or \
                            any(k in name for k in ['cerrar', 'cancelar', 'eliminar', 'anular'])
                
                if is_danger and not obj.property("class"):
                    obj.setProperty("class", "danger")
            
            elif isinstance(obj, QTableWidget):
                # Ocultar la grilla para un look más limpio o suavizarla
                obj.setShowGrid(True)
                obj.setGridStyle(Qt.PenStyle.SolidLine)
                # Alineación y comportamiento consistente
                obj.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                if obj.horizontalHeader():
                    obj.horizontalHeader().setHighlightSections(False)
                    # Forzar cursor normal en headers
                    obj.horizontalHeader().setCursor(Qt.CursorShape.ArrowCursor)

        return super().eventFilter(obj, event)

def aplicar_tema_claro(app):
    """Evita que popups y diálogos dependan de la paleta del sistema."""
    paleta = QPalette()
    paleta.setColor(QPalette.ColorRole.Window, QColor("#F4F7FB"))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor("#172033"))
    paleta.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
    paleta.setColor(QPalette.ColorRole.AlternateBase, QColor("#F8FAFC"))
    paleta.setColor(QPalette.ColorRole.Text, QColor("#172033"))
    paleta.setColor(QPalette.ColorRole.Button, QColor("#FFFFFF"))
    paleta.setColor(QPalette.ColorRole.ButtonText, QColor("#172033"))
    paleta.setColor(QPalette.ColorRole.ToolTipBase, QColor("#172033"))
    paleta.setColor(QPalette.ColorRole.ToolTipText, QColor("#FFFFFF"))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor("#2563EB"))
    paleta.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    paleta.setColor(QPalette.ColorRole.PlaceholderText, QColor("#667085"))
    app.setPalette(paleta)

    # Instalamos el pulidor visual global
    polisher = UIGlobalPolisher(app)
    app.installEventFilter(polisher)

    # Estas reglas no afectan la sidebar, que conserva sus estilos locales.
    app.setStyleSheet("""
        QDialog, QMessageBox { background-color: #FFFFFF; color: #172033; }
        QDialog QLabel, QMessageBox QLabel { background: transparent; color: #172033; }
        QDialog QLineEdit, QDialog QTextEdit, QDialog QPlainTextEdit,
        QMessageBox QLineEdit, QMessageBox QTextEdit, QMessageBox QPlainTextEdit,
        QComboBox {
            background-color: #FFFFFF; color: #172033; border: 1px solid #E4E7EC;
            border-radius: 6px; padding: 6px 8px; selection-background-color: #2563EB;
            selection-color: #FFFFFF;
        }
        QDialog QLineEdit:focus, QDialog QTextEdit:focus,
        QDialog QPlainTextEdit:focus, QComboBox:focus { border-color: #2563EB; }
        
        /* Botones Generales */
        QPushButton {
            min-height: 30px; background-color: #FFFFFF; color: #172033;
            border: 1px solid #E4E7EC; border-radius: 6px; padding: 6px 14px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #F8FAFC; border-color: #CBD5E1;
        }
        QPushButton:pressed {
            background-color: #F1F5F9;
        }
        
        QDialog QPushButton:default, QMessageBox QPushButton:default {
            background-color: #2563EB; color: #FFFFFF; border-color: #2563EB;
        }
        QDialog QPushButton:default:hover, QMessageBox QPushButton:default:hover {
            background-color: #1D4ED8; border-color: #1D4ED8;
        }
        
        /* Botones Danger (Cerrar, Cancelar, Eliminar) */
        QPushButton[class="danger"] {
            color: #EF4444; border: 1px solid #FECACA; background-color: #FEF2F2;
        }
        QPushButton[class="danger"]:hover {
            background-color: #EF4444; color: #FFFFFF; border-color: #EF4444;
        }
        
        QComboBox::drop-down { border: none; width: 24px; }
        QComboBox QAbstractItemView, QListView, QListWidget {
            background-color: #FFFFFF; color: #172033; border: 1px solid #E4E7EC;
            outline: none; selection-background-color: #DBEAFE; selection-color: #172033;
        }
        QComboBox QAbstractItemView::item, QListView::item, QListWidget::item {
            min-height: 24px; padding: 5px 8px;
        }
        QComboBox QAbstractItemView::item:hover, QListView::item:hover,
        QListWidget::item:hover { background-color: #EFF6FF; }
        
        QMenu { background-color: #FFFFFF; color: #172033; border: 1px solid #E4E7EC; padding: 4px; border-radius: 6px; }
        QMenu::item { padding: 7px 26px 7px 18px; border-radius: 4px; }
        QMenu::item:selected { background-color: #EFF6FF; color: #172033; }
        
        QToolTip { 
            background-color: #1E293B; color: #FFFFFF; 
            border: 1px solid #0F172A; padding: 6px 10px; 
            border-radius: 4px; font-size: 12px;
        }
        
        /* Tablas Consistentes */
        QTableWidget {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            gridline-color: #F1F5F9;
            selection-background-color: #F8FAFC;
            selection-color: #0F172A;
            alternate-background-color: #FAFAF9;
        }
        QTableWidget::item {
            padding: 4px 8px;
            border-bottom: 1px solid #F1F5F9;
        }
        QTableWidget::item:selected {
            background-color: #EFF6FF;
            color: #1D4ED8;
        }
        QHeaderView::section {
            background-color: #F8FAFC;
            color: #475569;
            padding: 8px;
            border: none;
            border-bottom: 1px solid #E2E8F0;
            border-right: 1px solid #F1F5F9;
            font-weight: 600;
            font-size: 12px;
        }
        
        /* Scrollbars Modernos */
        QScrollBar:vertical {
            border: none; background: #F8FAFC; width: 8px; border-radius: 4px; margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #CBD5E1; min-height: 20px; border-radius: 4px;
        }
        QScrollBar::handle:vertical:hover { background: #94A3B8; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
        
        QScrollBar:horizontal {
            border: none; background: #F8FAFC; height: 8px; border-radius: 4px; margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background: #CBD5E1; min-width: 20px; border-radius: 4px;
        }
        QScrollBar::handle:horizontal:hover { background: #94A3B8; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { border: none; background: none; }
        
        /* Badges Uniformes */
        QLabel[class="badge-success"] {
            background-color: #DCFCE7; color: #166534; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold;
        }
        QLabel[class="badge-danger"] {
            background-color: #FEE2E2; color: #991B1B; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold;
        }
        QLabel[class="badge-info"] {
            background-color: #EFF6FF; color: #1D4ED8; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold;
        }
        QLabel[class="badge-neutral"] {
            background-color: #F1F5F9; color: #475569; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold;
        }
    """)

