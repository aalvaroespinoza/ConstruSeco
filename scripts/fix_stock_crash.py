import os

file_path = "ui/modules/stock/tab_stock.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_method = """    def _actualizar_colores_seleccion(self):
        sel_rows = {item.row() for item in self.tabla.selectedItems()}
        for r in range(self.tabla.rowCount()):
            is_sel = r in sel_rows
            
            # Columna Imagen (1)
            w_img = self.tabla.cellWidget(r, 1)
            if w_img and hasattr(w_img, "setStyleSheet"):
                color_img = "white" if is_sel else COLOR_TEXT_SEC
                w_img.setStyleSheet(f"color: {color_img}; font-size: 18px;")
            
            # Columna Acciones (10)
            w_acc = self.tabla.cellWidget(r, 10)
            if w_acc:
                from PyQt6.QtWidgets import QPushButton
                btns = w_acc.findChildren(QPushButton)
                if btns:
                    btn = btns[0]
                    color_btn = "white" if is_sel else COLOR_TEXT_MAIN
                    btn.setStyleSheet(f\"\"\"
                        QPushButton {{
                            background-color: transparent;
                            border: 1px solid transparent;
                            border-radius: 4px;
                            font-size: 18px;
                            font-weight: bold;
                            color: {color_btn};
                        }}
                        QPushButton:hover {{
                            background-color: {COLOR_BG};
                            border: 1px solid {COLOR_BORDER};
                        }}
                        QPushButton::menu-indicator {{ image: none; width: 0px; }}
                    \"\"\")

"""

old_conn = """        self.tabla.cellDoubleClicked.connect(self.on_tabla_double_click)"""
new_conn = """        self.tabla.cellDoubleClicked.connect(self.on_tabla_double_click)
        self.tabla.itemSelectionChanged.connect(self._actualizar_colores_seleccion)"""
content = content.replace(old_conn, new_conn)

old_class = """    def on_tabla_double_click(self, row, col):"""
new_class = new_method + """    def on_tabla_double_click(self, row, col):"""
content = content.replace(old_class, new_class)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed PestanaStock AttributeError")
