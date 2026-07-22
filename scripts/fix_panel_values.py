import os

file_path = "ui/modules/clientes/tab_clientes.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_fila_set = """    def set_valor(self, valor):
        self._lbl_v.setText(str(valor) if valor else "—")"""
new_fila_set = """    def set_valor(self, valor):
        self._lbl_v.setText(str(valor) if valor is not None and valor != "" else "—")"""

content = content.replace(old_fila_set, new_fila_set)

# Also fix the __init__ of _FilaDetalle where it sets the initial value
old_fila_init = """    def __init__(self, etiqueta: str, valor: str = "—"):
        super().__init__()
        self.setStyleSheet("QFrame { border: none; }")
        ly = QHBoxLayout(self)
        ly.setContentsMargins(0, 2, 0, 2)
        ly.setSpacing(8)

        lbl_e = QLabel(etiqueta)
        lbl_e.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 12px; border: none;")
        lbl_e.setFixedWidth(100)
        lbl_e.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self._lbl_v = QLabel(valor)"""

new_fila_init = """    def __init__(self, etiqueta: str, valor: str = "—"):
        super().__init__()
        self.setStyleSheet("QFrame { border: none; }")
        ly = QHBoxLayout(self)
        ly.setContentsMargins(0, 2, 0, 2)
        ly.setSpacing(8)

        lbl_e = QLabel(etiqueta)
        lbl_e.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 12px; border: none;")
        lbl_e.setFixedWidth(100)
        lbl_e.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self._lbl_v = QLabel(str(valor) if valor is not None and valor != "" else "—")"""

content = content.replace(old_fila_init, new_fila_init)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed FilaDetalle values")
