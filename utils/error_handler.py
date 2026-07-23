import sys
import os
import traceback
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from ui.core.modal import DialogoModalIntegrado
from ui.core.theme import COLOR_TEXT_MAIN
from utils.paths import get_data_path

class DialogoErrorInesperado(DialogoModalIntegrado):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Error Inesperado")
        
        ly = QVBoxLayout(self)
        
        lbl_msg = QLabel(
            "Ocurrió un error inesperado. Se guardó un registro para revisar.\n"
            "Si podés, guardá tu trabajo y reiniciá el programa."
        )
        lbl_msg.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-size: 14px;")
        lbl_msg.setWordWrap(True)
        
        btn_ok = QPushButton("Entendido")
        btn_ok.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        
        ly.addWidget(lbl_msg)
        ly.addSpacing(16)
        ly.addLayout(btn_layout)

def manejar_excepcion(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    try:
        log_dir = get_data_path("logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "errores.log")
        
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_text = "".join(tb_lines)
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.write(tb_text)
            f.write("\n")
            
        app = QApplication.instance()
        if app:
            parent_window = app.activeWindow()
            if parent_window:
                dialog = DialogoErrorInesperado(parent_window)
                dialog.exec()
            else:
                print("Error capturado, pero no hay ventana activa para mostrar el aviso.")
        else:
            print("Error capturado, pero QApplication no está iniciada.")
            
    except Exception as e:
        print(f"Error crítico al intentar registrar la excepción original: {e}")
