import os

def patch_presupuestos():
    path = "ui/modules/presupuestos/tab_presupuestos.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    old_code = """                num_venta = qp.confirmar_presupuesto(self.conn, id_documento)
                self.recargar()
                
                try:
                    vp = self.window()
                    if hasattr(vp, 'pestana_stock'):
                        vp.pestana_stock.cargar_datos()
                    if hasattr(vp, 'actualizar_catalogos_operaciones'):
                        vp.actualizar_catalogos_operaciones()
                except Exception:
                    pass"""
                    
    new_code = """                num_venta = qp.confirmar_presupuesto(self.conn, id_documento)
                self._notificar_cambios_globales()"""
                
    if old_code in content:
        content = content.replace(old_code, new_code)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Patched_confirmar_como_venta")
    else:
        print("Code not found in confirmar_como_venta")
        
patch_presupuestos()
