"""Tema visual común de la aplicación."""

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import Qt, QObject, QEvent, QSettings
from PyQt6.QtWidgets import QPushButton, QTableWidget, QHeaderView, QLabel

PALETA_CLARO = {
    "PRIMARY":   "#2563eb",
    "BG":        "#f8fafc",
    "CARD_BG":   "#ffffff",
    "TEXT_MAIN": "#1e293b",
    "TEXT_SEC":  "#64748b",
    "BORDER":    "#e2e8f0",
    "SUCCESS":   "#10b981",
    "WARNING":   "#f59e0b",
    "DANGER":    "#ef4444",
}

COLOR_PRIMARY, COLOR_BG, COLOR_CARD_BG = PALETA_CLARO["PRIMARY"], PALETA_CLARO["BG"], PALETA_CLARO["CARD_BG"]
COLOR_TEXT_MAIN, COLOR_TEXT_SEC, COLOR_BORDER = PALETA_CLARO["TEXT_MAIN"], PALETA_CLARO["TEXT_SEC"], PALETA_CLARO["BORDER"]
COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER = PALETA_CLARO["SUCCESS"], PALETA_CLARO["WARNING"], PALETA_CLARO["DANGER"]

class UIGlobalPolisher(QObject):
    """Filtro global de eventos para asegurar uniformidad visual sin modificar todos los archivos."""
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Polish:
            if isinstance(obj, QPushButton):
                obj.setCursor(Qt.CursorShape.PointingHandCursor)
                text = obj.text().lower()
                name = obj.objectName().lower()
                is_danger = any(k in text for k in ['cancelar', 'eliminar', 'anular', 'desactivar']) or \
                            any(k in name for k in ['cancelar', 'eliminar', 'anular', 'desactivar'])
                
                if is_danger and not obj.property("class"):
                    obj.setProperty("class", "danger")
            
            elif isinstance(obj, QTableWidget):
                # Ocultar la grilla para un look más limpio o suavizarla
                obj.setShowGrid(True)
                obj.setGridStyle(Qt.PenStyle.SolidLine)
                # Alineación y comportamiento consistente
                obj.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                obj.setAlternatingRowColors(True)
                if obj.horizontalHeader():
                    obj.horizontalHeader().setHighlightSections(False)
                    # Forzar cursor normal en headers
                    obj.horizontalHeader().setCursor(Qt.CursorShape.ArrowCursor)

        return super().eventFilter(obj, event)

def aplicar_tema_claro(app):
    """Evita que popups y diálogos dependan de la paleta del sistema."""
    paleta = QPalette()
    paleta.setColor(QPalette.ColorRole.Window, QColor(COLOR_BG))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor(COLOR_TEXT_MAIN))
    paleta.setColor(QPalette.ColorRole.Base, QColor(COLOR_CARD_BG))
    paleta.setColor(QPalette.ColorRole.AlternateBase, QColor(COLOR_BG))
    paleta.setColor(QPalette.ColorRole.Text, QColor(COLOR_TEXT_MAIN))
    paleta.setColor(QPalette.ColorRole.Button, QColor(COLOR_CARD_BG))
    paleta.setColor(QPalette.ColorRole.ButtonText, QColor(COLOR_TEXT_MAIN))
    paleta.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLOR_TEXT_MAIN))
    paleta.setColor(QPalette.ColorRole.ToolTipText, QColor(COLOR_CARD_BG))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor(COLOR_PRIMARY))
    paleta.setColor(QPalette.ColorRole.HighlightedText, QColor(COLOR_CARD_BG))
    paleta.setColor(QPalette.ColorRole.PlaceholderText, QColor(COLOR_TEXT_SEC))
    app.setPalette(paleta)

    # Instalamos el pulidor visual global
    polisher = UIGlobalPolisher(app)
    app.installEventFilter(polisher)

    # Estas reglas no afectan la sidebar, que conserva sus estilos locales.
    app.setStyleSheet(f"""
        QDialog, QMessageBox {{ background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN}; }}
        QDialog QLabel, QMessageBox QLabel {{ background: transparent; color: {COLOR_TEXT_MAIN}; }}
        QDialog QLineEdit, QDialog QTextEdit, QDialog QPlainTextEdit,
        QMessageBox QLineEdit, QMessageBox QTextEdit, QMessageBox QPlainTextEdit,
        QComboBox {{
            background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN}; border: 1px solid {COLOR_BORDER};
            border-radius: 6px; padding: 6px 8px; selection-background-color: {COLOR_PRIMARY};
            selection-color: {COLOR_CARD_BG};
        }}
        QDialog QLineEdit:focus, QDialog QTextEdit:focus,
        QDialog QPlainTextEdit:focus, QComboBox:focus {{ border-color: {COLOR_PRIMARY}; }}
        
        /* Botones Generales */
        QPushButton {{
            min-height: 32px; background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN};
            border: 1px solid {COLOR_BORDER}; border-radius: 6px; padding: 6px 14px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {COLOR_BG}; border-color: {COLOR_BORDER};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_BORDER};
        }}
        
        QDialog QPushButton:default, QMessageBox QPushButton:default {{
            background-color: {COLOR_PRIMARY}; color: {COLOR_CARD_BG}; border-color: {COLOR_PRIMARY};
        }}
        QDialog QPushButton:default:hover, QMessageBox QPushButton:default:hover {{
            background-color: #1d4ed8; border-color: #1d4ed8;
        }}
        
        /* Botones Danger (Cerrar, Cancelar, Eliminar) */
        QPushButton[class="danger"] {{
            color: {COLOR_DANGER}; border: 1px solid {COLOR_DANGER}; background-color: {COLOR_CARD_BG};
        }}
        QPushButton[class="danger"]:hover {{
            background-color: {COLOR_DANGER}; color: {COLOR_CARD_BG}; border-color: {COLOR_DANGER};
        }}
        
        QComboBox::drop-down {{ border: none; width: 24px; }}
        QComboBox QAbstractItemView, QListView, QListWidget {{
            background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN}; border: 1px solid {COLOR_BORDER};
            outline: none; selection-background-color: {COLOR_PRIMARY}; selection-color: {COLOR_CARD_BG};
        }}
        QComboBox QAbstractItemView::item, QListView::item, QListWidget::item {{
            min-height: 24px; padding: 5px 8px;
        }}
        QComboBox QAbstractItemView::item:hover, QListView::item:hover,
        QListWidget::item:hover {{ background-color: {COLOR_BG}; color: {COLOR_TEXT_MAIN}; }}
        
        QMenu {{ background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN}; border: 1px solid {COLOR_BORDER}; padding: 4px; border-radius: 6px; }}
        QMenu::item {{ padding: 7px 26px 7px 18px; border-radius: 4px; }}
        QMenu::item:selected {{ background-color: {COLOR_BG}; color: {COLOR_TEXT_MAIN}; }}
        
        QToolTip {{ 
            background-color: {COLOR_TEXT_MAIN}; color: {COLOR_CARD_BG}; 
            border: 1px solid {COLOR_BORDER}; padding: 6px 10px; 
            border-radius: 4px; font-size: 12px;
        }}
        
        /* Tablas Consistentes */
        QTableWidget {{
            background-color: {COLOR_CARD_BG};
            border: 1px solid {COLOR_BORDER};
            border-radius: 6px;
            gridline-color: {COLOR_BORDER};
            selection-background-color: #eff6ff;
            selection-color: {COLOR_PRIMARY};
            alternate-background-color: #f1f5f9;
            outline: none;
        }}
        QTableWidget::item {{
            padding: 8px 10px;
            border-bottom: 1px solid {COLOR_BORDER};
        }}
        QTableWidget::item:selected {{
            background-color: {COLOR_PRIMARY};
            color: white;
        }}
        QHeaderView::section {{
            background-color: {COLOR_BG};
            color: {COLOR_TEXT_SEC};
            padding: 8px;
            border: none;
            border-bottom: 1px solid {COLOR_BORDER};
            border-right: 1px solid {COLOR_BORDER};
            font-weight: 600;
            font-size: 12px;
        }}
        
        /* Scrollbars Modernos */
        QScrollBar:vertical {{
            border: none; background: {COLOR_BG}; width: 8px; border-radius: 4px; margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {COLOR_BORDER}; min-height: 20px; border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {COLOR_TEXT_SEC}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ border: none; background: none; }}
        
        QScrollBar:horizontal {{
            border: none; background: {COLOR_BG}; height: 8px; border-radius: 4px; margin: 0px;
        }}
        QScrollBar::handle:horizontal {{
            background: {COLOR_BORDER}; min-width: 20px; border-radius: 4px;
        }}
        QScrollBar::handle:horizontal:hover {{ background: {COLOR_TEXT_SEC}; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ border: none; background: none; }}
        
        /* Badges Uniformes */
        QLabel[class="badge-success"] {{
            background-color: {COLOR_SUCCESS}; color: {COLOR_CARD_BG}; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold;
        }}
        QLabel[class="badge-danger"] {{
            background-color: {COLOR_DANGER}; color: {COLOR_CARD_BG}; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold;
        }}
        QLabel[class="badge-info"] {{
            background-color: {COLOR_PRIMARY}; color: {COLOR_CARD_BG}; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold;
        }}
        QLabel[class="badge-neutral"] {{
            background-color: {COLOR_BG}; color: {COLOR_TEXT_MAIN}; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold;
        }}
    """)

