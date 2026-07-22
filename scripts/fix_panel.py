import os

file_path = "ui/modules/clientes/tab_clientes.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: _FilaDetalle style and set_valor
old_fila = """class _FilaDetalle(QFrame):
    def __init__(self, etiqueta: str, valor: str = "—"):
        super().__init__()
        self.setStyleSheet("border: none;")"""
new_fila = """class _FilaDetalle(QFrame):
    def __init__(self, etiqueta: str, valor: str = "—"):
        super().__init__()
        self.setStyleSheet("QFrame { border: none; }")"""
content = content.replace(old_fila, new_fila)

old_fila_set = """    def set_valor(self, valor: str):
        self._lbl_v.setText(valor or "—")"""
new_fila_set = """    def set_valor(self, valor):
        self._lbl_v.setText(str(valor) if valor else "—")"""
content = content.replace(old_fila_set, new_fila_set)

# Fix 2: _SeccionPanel style
old_sec = """class _SeccionPanel(QFrame):
    def __init__(self, titulo: str):
        super().__init__()
        self.setStyleSheet("border: none;")"""
new_sec = """class _SeccionPanel(QFrame):
    def __init__(self, titulo: str):
        super().__init__()
        self.setStyleSheet("QFrame { border: none; }")"""
content = content.replace(old_sec, new_sec)

# Fix 3: _btn_menu
old_menu = """        # Botón de menú de acciones (⋯)
        self._btn_menu = QPushButton("⋯")
        self._btn_menu.setFixedSize(30, 30)
        self._btn_menu.setStyleSheet(
            f"QPushButton {{ background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_SEC}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 15px; "
            f"font-size: 16px; font-weight: 900; }}"
            f"QPushButton:hover {{ background-color: {COLOR_BG}; color: {COLOR_TEXT_MAIN}; }}"
        )"""
new_menu = """        # Botón de menú de acciones (⋯)
        self._btn_menu = QPushButton("⋮")
        self._btn_menu.setFixedSize(30, 30)
        self._btn_menu.setStyleSheet(
            f"QPushButton {{ background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_SEC}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 15px; "
            f"font-size: 18px; font-weight: bold; padding: 0px; padding-bottom: 2px; }}"
            f"QPushButton:hover {{ background-color: {COLOR_BG}; color: {COLOR_TEXT_MAIN}; }}"
        )"""
content = content.replace(old_menu, new_menu)

# Fix 4: _mini_metrica
old_mini = """    def _mini_metrica(self, label: str, valor: str) -> QFrame:
        f = QFrame()
        f.setStyleSheet(
            f"background-color: {COLOR_BG}; border-radius: 6px; border: 1px solid {COLOR_BORDER};"
        )"""
new_mini = """    def _mini_metrica(self, label: str, valor: str) -> QFrame:
        f = QFrame()
        f.setStyleSheet(
            f"QFrame {{ background-color: {COLOR_BG}; border-radius: 6px; border: 1px solid {COLOR_BORDER}; }}"
        )"""
content = content.replace(old_mini, new_mini)

# Fix 5: _btn_editar
old_btn_editar = """        self._btn_editar = QPushButton("✏  Editar cliente")
        self._btn_editar.setStyleSheet(
            f"background-color: {COLOR_PRIMARY}; color: white; border-radius: 6px; "
            f"font-weight: bold; font-size: 13px; padding: 8px 16px; border: none;"
        )"""
new_btn_editar = """        self._btn_editar = QPushButton("✏  Editar cliente")
        self._btn_editar.setStyleSheet(
            f"QPushButton {{ background-color: {COLOR_PRIMARY}; color: white; border-radius: 6px; "
            f"font-weight: bold; font-size: 13px; padding: 8px 16px; border: none; }}"
            f"QPushButton:hover {{ background-color: #1d4ed8; }}"
        )"""
content = content.replace(old_btn_editar, new_btn_editar)

# Fix 6: _btn_historial
old_btn_hist = """        self._btn_historial = QPushButton("📋  Ver historial completo")
        self._btn_historial.setStyleSheet(
            f"background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; "
            f"font-weight: 600; font-size: 13px; padding: 8px 16px;"
        )"""
new_btn_hist = """        self._btn_historial = QPushButton("📋  Ver historial completo")
        self._btn_historial.setStyleSheet(
            f"QPushButton {{ background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; "
            f"font-weight: 600; font-size: 13px; padding: 8px 16px; }}"
            f"QPushButton:hover {{ background-color: {COLOR_BG}; }}"
        )"""
content = content.replace(old_btn_hist, new_btn_hist)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Finished patching tab_clientes.py")
