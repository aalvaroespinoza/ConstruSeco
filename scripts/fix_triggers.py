import os

def fix_tab_stock():
    path = "ui/modules/stock/tab_stock.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    method_str = """    def actualizar_vista(self):
        \"\"\"Coordina la recarga manual de toda la vista de stock, reutilizando la lógica principal.\"\"\"
        self._notificar_cambios_globales()

    def _notificar_cambios_globales(self):
        vp = self.window()
        if hasattr(vp, 'notificar_cambios'):
            vp.notificar_cambios(["STOCK"])
        else:
            self.cargar_datos()"""
            
    content = content.replace("""    def actualizar_vista(self):
        \"\"\"Coordina la recarga manual de toda la vista de stock, reutilizando la lógica principal.\"\"\"
        self.cargar_datos()""", method_str)
        
    # Replace all self.cargar_datos() that happen on dialog accepts
    content = content.replace("""        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()""", """        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self._notificar_cambios_globales()""")
            
    content = content.replace("""        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()""", """        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._notificar_cambios_globales()""")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        
def fix_tab_clientes():
    path = "ui/modules/clientes/tab_clientes.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    method_str = """    def recargar(self):
        \"\"\"Recarga métricas y tabla conservando filtro, página y selección actuales.\"\"\"
        self._cargar_metricas()
        self._cargar_tabla()

    def _notificar_cambios_globales(self):
        vp = self.window()
        if hasattr(vp, 'notificar_cambios'):
            vp.notificar_cambios(["CLIENTES", "PRESUPUESTOS"])
        else:
            self.recargar()"""
            
    content = content.replace("""    def recargar(self):
        \"\"\"Recarga métricas y tabla conservando filtro, página y selección actuales.\"\"\"
        self._cargar_metricas()
        self._cargar_tabla()""", method_str)

    # Patch modal results
    content = content.replace("""        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.recargar()""", """        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._notificar_cambios_globales()""")
            
    content = content.replace("""        if result == QDialog.DialogCode.Accepted:
            self.recargar()""", """        if result == QDialog.DialogCode.Accepted:
            self._notificar_cambios_globales()""")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def fix_tab_presupuestos():
    path = "ui/modules/presupuestos/tab_presupuestos.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    method_str = """    def recargar(self):
        kpis = qp.obtener_kpis_presupuestos(self.conn)"""
            
    new_method = """    def _notificar_cambios_globales(self):
        vp = self.window()
        if hasattr(vp, 'notificar_cambios'):
            vp.notificar_cambios(["PRESUPUESTOS", "STOCK"])
        else:
            self.recargar()

    def recargar(self):
        kpis = qp.obtener_kpis_presupuestos(self.conn)"""
        
    content = content.replace(method_str, new_method)
    
    # anular presupuesto replaces recargar with _notificar_cambios_globales
    content = content.replace("""                qp.anular_presupuesto(self.conn, id_documento)
                self.recargar()
                
                # Intentar recargar la pestaña de stock usando una llamada segura al parent
                try:
                    vp = self.window()
                    if hasattr(vp, 'pestana_stock'):
                        vp.pestana_stock.cargar_datos()
                    if hasattr(vp, 'actualizar_catalogos_operaciones'):
                        vp.actualizar_catalogos_operaciones()
                except Exception:
                    pass""", """                qp.anular_presupuesto(self.conn, id_documento)
                self._notificar_cambios_globales()""")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

fix_tab_stock()
fix_tab_clientes()
fix_tab_presupuestos()
print("Triggers fixed")
