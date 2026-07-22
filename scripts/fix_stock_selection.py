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
            if w_img and isinstance(w_img, QLabel):
                color_img = "white" if is_sel else COLOR_TEXT_SEC
                w_img.setStyleSheet(f"color: {color_img}; font-size: 18px;")
            
            # Columna Acciones (10)
            w_acc = self.tabla.cellWidget(r, 10)
            if w_acc:
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

# Find where itemSelectionChanged is connected, or create one.
# Let's search if tab_stock.py connects itemSelectionChanged
if "itemSelectionChanged.connect" not in content:
    old_conn = """        self.tabla.itemDoubleClicked.connect(self._on_item_doble_click)"""
    new_conn = """        self.tabla.itemDoubleClicked.connect(self._on_item_doble_click)
        self.tabla.itemSelectionChanged.connect(self._actualizar_colores_seleccion)"""
    content = content.replace(old_conn, new_conn)

    old_class = """    def _on_item_doble_click(self, item):"""
    new_class = new_method + """
    def _on_item_doble_click(self, item):"""
    content = content.replace(old_class, new_class)

    # Need to call it at the end of cargar_datos too
    old_cargar_end = """        self.tabla.setUpdatesEnabled(True)"""
    new_cargar_end = """        self.tabla.setUpdatesEnabled(True)
        self._actualizar_colores_seleccion()"""
    content = content.replace(old_cargar_end, new_cargar_end)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated stock selection colors")
else:
    print("itemSelectionChanged already connected, check manually")
