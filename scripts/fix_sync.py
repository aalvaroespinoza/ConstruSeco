import os

def fix_ventana_principal():
    path = "ui/ventana_principal.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    method = """    def notificar_cambios(self, modulos):
        \"\"\"
        Sistema centralizado de eventos para refrescar la UI.
        Recibe una lista de módulos afectados, ej: ['STOCK', 'CLIENTES']
        \"\"\"
        if "STOCK" in modulos:
            if hasattr(self, 'pestana_stock'):
                self.pestana_stock.cargar_datos()
        if "CLIENTES" in modulos:
            if hasattr(self, 'pestana_clientes'):
                self.pestana_clientes.recargar()
        if "PRESUPUESTOS" in modulos:
            if hasattr(self, 'pestana_presupuestos'):
                self.pestana_presupuestos.recargar()
        
        # Inicio actualiza sus tarjetas siempre
        if hasattr(self, 'pestana_inicio'):
            self.pestana_inicio.cargar_datos()
            
        # Recargar operaciones (Ventas/Presupuestos nuevos)
        self.actualizar_catalogos_operaciones()

"""
    if "def notificar_cambios(" not in content:
        # insert after actualizar_catalogos_operaciones
        target = "    def actualizar_catalogos_operaciones(self):\n        for id_op, (widget, tarjeta) in self.operaciones_abiertas.items():\n            if hasattr(widget, 'cargar_catalogo_memoria'):\n                widget.cargar_catalogo_memoria()\n"
        content = content.replace(target, target + "\n" + method)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("VentanaPrincipal fixed")

def fix_tab_clientes():
    path = "ui/modules/clientes/tab_clientes.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    old_code = """        # Re-seleccionar el cliente activo si aún está en la página
        if self._id_cliente_seleccionado is not None:
            encontrado = self._seleccionar_por_id(self._id_cliente_seleccionado)
            if not encontrado:
                self._stack_panel.setCurrentIndex(0)"""
                
    new_code = """        # Re-seleccionar el cliente activo si aún está en la página
        if self._id_cliente_seleccionado is not None:
            encontrado = self._seleccionar_por_id(self._id_cliente_seleccionado)
            if not encontrado:
                self._stack_panel.setCurrentIndex(0)
                self._id_cliente_seleccionado = None
            else:
                # Forzar recarga del panel ya que _seleccionar_por_id bloquea señales
                self._panel_detalle.cargar(self.conn, self._id_cliente_seleccionado)"""
                
    if old_code in content:
        content = content.replace(old_code, new_code)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("tab_clientes fixed")

def fix_tab_presupuestos():
    path = "ui/modules/presupuestos/tab_presupuestos.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    old_code = """        if id_sel_encontrado and fila_seleccionar >= 0:
            self._tabla.selectRow(fila_seleccionar)
        else:
            self._id_seleccionado = None
            self._panel_detalle.hide()
            self._panel_vacio.show()"""
            
    new_code = """        if id_sel_encontrado and fila_seleccionar >= 0:
            self._tabla.selectRow(fila_seleccionar)
            # Forzar actualización del panel porque signals están bloqueadas
            self._panel_detalle.cargar(self.conn, self._id_seleccionado)
        else:
            self._id_seleccionado = None
            self._panel_detalle.hide()
            self._panel_vacio.show()"""
            
    if old_code in content:
        content = content.replace(old_code, new_code)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("tab_presupuestos fixed")

fix_ventana_principal()
fix_tab_clientes()
fix_tab_presupuestos()
