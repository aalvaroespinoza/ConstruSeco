import os

file_path = "ui/modules/presupuestos/tab_presupuestos.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_method = """    def _actualizar_colores_seleccion(self):
        sel_rows = {item.row() for item in self._tabla.selectedItems()}
        for r in range(self._tabla.rowCount()):
            is_sel = r in sel_rows
            
            # Columna Validez (3)
            w_val = self._tabla.cellWidget(r, 3)
            if w_val:
                lbls = w_val.findChildren(QLabel)
                if len(lbls) >= 2:
                    lbl_f = lbls[0]
                    lbl_t = lbls[1]
                    color_f = "white" if is_sel else COLOR_TEXT_SEC
                    lbl_f.setStyleSheet(f"color: {color_f}; font-size: 11px;")
                    
                    # If lbl_t has no background (ANULADO/CONFIRMADO), update it too
                    # We can check its current text or style
                    if "background-color" not in lbl_t.styleSheet():
                        lbl_t.setStyleSheet(f"color: {color_f}; font-weight: bold; font-size: 12px;")
            
            # Columna Acciones (6)
            w_acc = self._tabla.cellWidget(r, 6)
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
                            color: {COLOR_TEXT_MAIN};
                        }}
                        QPushButton::menu-indicator {{ image: none; width: 0px; }}
                    \"\"\")
"""

# Insert _actualizar_colores_seleccion before _on_seleccion_cambiada
old_on_sel = """    def _on_seleccion_cambiada(self):
        sel = self._tabla.selectedItems()
        if not sel:"""

new_on_sel = new_method + """
    def _on_seleccion_cambiada(self):
        self._actualizar_colores_seleccion()
        sel = self._tabla.selectedItems()
        if not sel:"""

content = content.replace(old_on_sel, new_on_sel)

# Also need to call it at the end of _cargar_tabla so the initial state is correct (in case there is a selection restored)
old_cargar_end = """        if id_sel_encontrado and fila_seleccionar >= 0:
            self._tabla.selectRow(fila_seleccionar)
        else:
            self._tabla.clearSelection()"""

new_cargar_end = """        if id_sel_encontrado and fila_seleccionar >= 0:
            self._tabla.selectRow(fila_seleccionar)
        else:
            self._tabla.clearSelection()
        self._actualizar_colores_seleccion()"""

content = content.replace(old_cargar_end, new_cargar_end)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated selection colors for custom widgets in tab_presupuestos.py")
