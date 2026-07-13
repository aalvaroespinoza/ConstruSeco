"""Tema visual común de la aplicación."""

from PyQt6.QtGui import QColor, QPalette

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
        QDialog QPushButton, QMessageBox QPushButton {
            min-height: 30px; background-color: #FFFFFF; color: #172033;
            border: 1px solid #E4E7EC; border-radius: 6px; padding: 5px 12px;
        }
        QDialog QPushButton:hover, QMessageBox QPushButton:hover {
            background-color: #F4F7FB; border-color: #2563EB;
        }
        QDialog QPushButton:default, QMessageBox QPushButton:default {
            background-color: #2563EB; color: #FFFFFF; border-color: #2563EB;
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
        QMenu { background-color: #FFFFFF; color: #172033; border: 1px solid #E4E7EC; padding: 4px; }
        QMenu::item { padding: 7px 26px 7px 18px; border-radius: 4px; }
        QMenu::item:selected { background-color: #EFF6FF; color: #172033; }
        QToolTip { background-color: #172033; color: #FFFFFF; border: 1px solid #344054; padding: 5px; }
    """)
