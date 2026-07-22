import os

file_path = "ui/modules/presupuestos/tab_presupuestos.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Badges in _PanelDetalle construction (this might not exist since it's probably just a QLabel and updated in cargar)
# Let's search for the exact setProperty for lbl_estado in the table creation first:
old_table = """        lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_estado.setFixedHeight(24)
        if est == 'ACTIVO':
            lbl_estado.setProperty("class", "badge-success")
        elif est == 'VENCIDO':
            lbl_estado.setProperty("class", "badge-danger")
        elif est == 'CONFIRMADO':
            lbl_estado.setProperty("class", "badge-info")
        else:
            lbl_estado.setProperty("class", "badge-neutral")
            
        lbl_estado.style().unpolish(lbl_estado)
        lbl_estado.style().polish(lbl_estado)"""

new_table = """        lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_estado.setFixedHeight(24)
        
        base_style = "padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; border: none; color: white;"
        if est == 'ACTIVO':
            lbl_estado.setStyleSheet(f"background-color: {COLOR_SUCCESS}; {base_style}")
        elif est == 'VENCIDO':
            lbl_estado.setStyleSheet(f"background-color: {COLOR_DANGER}; {base_style}")
        elif est == 'CONFIRMADO':
            lbl_estado.setStyleSheet(f"background-color: {COLOR_PRIMARY}; {base_style}")
        else:
            lbl_estado.setStyleSheet(f"background-color: {COLOR_BORDER}; color: {COLOR_TEXT_MAIN}; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; border: none;")
        """

content = content.replace(old_table, new_table)

old_load = """        est = det['estado']
        if est == 'ACTIVO':
            self._lbl_estado_badge.setProperty("class", "badge-success")
        elif est == 'VENCIDO':
            self._lbl_estado_badge.setProperty("class", "badge-danger")
        elif est == 'CONFIRMADO':
            self._lbl_estado_badge.setProperty("class", "badge-info")
        else:
            self._lbl_estado_badge.setProperty("class", "badge-neutral")
            
        self._lbl_estado_badge.style().unpolish(self._lbl_estado_badge)
        self._lbl_estado_badge.style().polish(self._lbl_estado_badge)"""

new_load = """        est = det['estado']
        base_style = "padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; border: none; color: white;"
        if est == 'ACTIVO':
            self._lbl_estado_badge.setStyleSheet(f"background-color: {COLOR_SUCCESS}; {base_style}")
        elif est == 'VENCIDO':
            self._lbl_estado_badge.setStyleSheet(f"background-color: {COLOR_DANGER}; {base_style}")
        elif est == 'CONFIRMADO':
            self._lbl_estado_badge.setStyleSheet(f"background-color: {COLOR_PRIMARY}; {base_style}")
        else:
            self._lbl_estado_badge.setStyleSheet(f"background-color: {COLOR_BORDER}; color: {COLOR_TEXT_MAIN}; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; border: none;")
        """

content = content.replace(old_load, new_load)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed badges in tab_presupuestos.py")
