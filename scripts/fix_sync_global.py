import os

file_clientes = "ui/modules/clientes/tab_clientes.py"
file_stock = "ui/modules/stock/tab_stock.py"

# Update Clientes
with open(file_clientes, "r", encoding="utf-8") as f:
    content_c = f.read()

# in _on_editar_cliente
content_c = content_c.replace(
    "self._id_cliente_seleccionado = id_cliente\n            self.recargar()",
    "self._id_cliente_seleccionado = id_cliente\n            self._notificar_cambios_globales()"
)

# in _on_desactivar_cliente (both Yes branches)
content_c = content_c.replace(
    "qc.desactivar_cliente(self.conn, id_cliente)\n                self._id_cliente_seleccionado = id_cliente\n                self.recargar()",
    "qc.desactivar_cliente(self.conn, id_cliente)\n                self._id_cliente_seleccionado = id_cliente\n                self._notificar_cambios_globales()"
)
content_c = content_c.replace(
    "qc.reactivar_cliente(self.conn, id_cliente)\n                self._id_cliente_seleccionado = id_cliente\n                self.recargar()",
    "qc.reactivar_cliente(self.conn, id_cliente)\n                self._id_cliente_seleccionado = id_cliente\n                self._notificar_cambios_globales()"
)

# in _on_eliminar_cliente
content_c = content_c.replace(
    "qc.eliminar_cliente(self.conn, id_cliente)\n                self.recargar()",
    "qc.eliminar_cliente(self.conn, id_cliente)\n                self._notificar_cambios_globales()"
)

with open(file_clientes, "w", encoding="utf-8") as f:
    f.write(content_c)


# Update Stock
with open(file_stock, "r", encoding="utf-8") as f:
    content_s = f.read()

content_s = content_s.replace(
    """QMessageBox.information(self, "Reactivado", f"El producto {prod['codigo']} ha sido reactivado.")
            self.cargar_datos()""",
    """QMessageBox.information(self, "Reactivado", f"El producto {prod['codigo']} ha sido reactivado.")
            self._notificar_cambios_globales()"""
)

content_s = content_s.replace(
    """if DialogoConfiguracionGeneral(self).exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()""",
    """if DialogoConfiguracionGeneral(self).exec() == QDialog.DialogCode.Accepted:
            self._notificar_cambios_globales()"""
)

content_s = content_s.replace(
    """QMessageBox.information(self, "Limpieza completada", f"Se han liberado {liberados} presupuestos vencidos. El stock comprometido ha vuelto a estar disponible.")
            self.cargar_datos()""",
    """QMessageBox.information(self, "Limpieza completada", f"Se han liberado {liberados} presupuestos vencidos. El stock comprometido ha vuelto a estar disponible.")
            self._notificar_cambios_globales()"""
)

content_s = content_s.replace(
    """if DialogoVisualizacionInventario(self).exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()""",
    """if DialogoVisualizacionInventario(self).exec() == QDialog.DialogCode.Accepted:
            self._notificar_cambios_globales()"""
)

with open(file_stock, "w", encoding="utf-8") as f:
    f.write(content_s)

print("Updated sync for Clientes and Stock.")
