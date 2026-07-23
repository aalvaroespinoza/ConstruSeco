from PyQt6.QtWidgets import QMessageBox

def mostrar_confirmacion(parent, titulo, mensaje, texto_ok="Sí", texto_cancel="Cancelar"):
    """
    Muestra un cuadro de diálogo de confirmación unificado con botones en español
    y estilos coherentes.
    Retorna True si el usuario confirma (texto_ok), o False si cancela.
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Question)
    msg_box.setWindowTitle(titulo)
    msg_box.setText(mensaje)
    
    # Usar botones estándar pero traducidos
    btn_ok = msg_box.addButton(texto_ok, QMessageBox.ButtonRole.AcceptRole)
    btn_cancel = msg_box.addButton(texto_cancel, QMessageBox.ButtonRole.RejectRole)
    
    msg_box.setDefaultButton(btn_cancel)
    
    # Aplicar el estilo para asegurar visibilidad en temas claros
    msg_box.setStyleSheet("QPushButton { color: #172033; background-color: #f1f5f9; padding: 6px 12px; border: 1px solid #cbd5e1; border-radius: 4px; } QPushButton:hover { background-color: #e2e8f0; }")
    
    msg_box.exec()
    
    return msg_box.clickedButton() == btn_ok
