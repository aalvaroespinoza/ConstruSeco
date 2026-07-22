import os

file_path = "ui/modules/clientes/tab_clientes.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace construction
old_build = """        # Badge de estado
        self._badge_estado = QLabel("ACTIVO")
        self._badge_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge_estado.setFixedHeight(22)
        self._badge_estado.setProperty("class", "badge-success")"""

new_build = """        # Badge de estado
        self._badge_estado = QLabel("ACTIVO")
        self._badge_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge_estado.setFixedHeight(22)
        self._badge_estado.setStyleSheet(
            f"background-color: {COLOR_SUCCESS}; color: white; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; border: none;"
        )"""
content = content.replace(old_build, new_build)

# Replace cargar
old_load = """        if det["activo"]:
            self._badge_estado.setText("ACTIVO")
            self._badge_estado.setProperty("class", "badge-success")
        else:
            self._badge_estado.setText("INACTIVO")
            self._badge_estado.setProperty("class", "badge-danger")
        
        self._badge_estado.style().unpolish(self._badge_estado)
        self._badge_estado.style().polish(self._badge_estado)"""

new_load = """        if det["activo"]:
            self._badge_estado.setText("ACTIVO")
            self._badge_estado.setStyleSheet(
                f"background-color: {COLOR_SUCCESS}; color: white; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; border: none;"
            )
        else:
            self._badge_estado.setText("INACTIVO")
            self._badge_estado.setStyleSheet(
                f"background-color: {COLOR_DANGER}; color: white; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; border: none;"
            )"""
content = content.replace(old_load, new_load)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed badge styling in tab_clientes.py")
