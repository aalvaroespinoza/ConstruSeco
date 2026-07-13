import re
filepath = 'ui/modules/stock/excel_stock.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. obtener_productos_activos_exportacion
old1 = r'''        c = conn\.cursor\(\)
        c\.execute\(\"SELECT codigo, lower\(descripcion\) FROM productos WHERE activo = 1\"\)
        productos_bd = c\.fetchall\(\)'''
new1 = '''        from db.queries_stock import obtener_productos_activos_exportacion
        productos_bd = obtener_productos_activos_exportacion(conn)'''
content = re.sub(old1, new1, content)

# 2. ejecutar_importacion
old2 = r'''        c = self\.conn\.cursor\(\)
        try:
            c\.execute\(\"BEGIN TRANSACTION;\"\)
            fecha = datetime\.now\(\)\.strftime\(\"%Y-%m-%d %H:%M:%S\"\)
            ts = int\(datetime\.now\(\)\.timestamp\(\)\)

            if self\.modo_importacion == \"SUSTITUIR\":
                # Auditar y desactivar/eliminar actuales
                c\.execute\(\"SELECT codigo FROM productos\"\)
                todos_actuales = \[r\[0\] for r in c\.fetchall\(\)\]
                nuevos_codigos = set\(p\[0\] for p in self\.filas_validas\)

                for cod in todos_actuales:
                    if cod not in nuevos_codigos:
                        c\.execute\(\"SELECT COUNT\(\*\) FROM detalle_documentos WHERE codigo_producto=\?\", \(cod,\)\)
                        c_doc = c\.fetchone\(\)\[0\]
                        c\.execute\(\"SELECT COUNT\(\*\) FROM movimientos_stock WHERE codigo_producto=\?\", \(cod,\)\)
                        c_mov = c\.fetchone\(\)\[0\]
                        c\.execute\(\"SELECT COUNT\(\*\) FROM compromisos_stock WHERE codigo_producto=\?\", \(cod,\)\)
                        c_comp = c\.fetchone\(\)\[0\]

                        if c_doc > 0 or c_mov > 0 or c_comp > 0:
                            c\.execute\(\"UPDATE productos SET activo = 0 WHERE codigo = \?\", \(cod,\)\)
                        else:
                            c\.execute\(\"DELETE FROM productos WHERE codigo = \?\", \(cod,\)\)

            for \(cod, desc, uni, precio, stk_ini, stk_min, estado_update\) in self\.filas_validas:
                if estado_update == \"ACTUALIZAR\" and self\.modo_importacion != \"SUSTITUIR\":
                    c\.execute\(\"\"\"
                        UPDATE productos SET descripcion=\?, unidad_base=\?, precio_venta=\?, stock_minimo=\?, activo=1
                        WHERE codigo=\?
                    \"\"\", \(desc, uni, precio, stk_min, cod\)\)
                    # NO agregamos stock inicial para actualizaciones en modo AGREGAR para evitar duplicar
                else:
                    # Insertar o actualizar
                    c\.execute\(\"SELECT COUNT\(\*\) FROM productos WHERE codigo=\?\", \(cod,\)\)
                    if c\.fetchone\(\)\[0\] > 0:
                        c\.execute\(\"\"\"
                            UPDATE productos SET descripcion=\?, unidad_base=\?, precio_venta=\?, stock_minimo=\?, activo=1
                            WHERE codigo=\?
                        \"\"\", \(desc, uni, precio, stk_min, cod\)\)
                    else:
                        c\.execute\(\"\"\"
                            INSERT INTO productos \(codigo, descripcion, unidad_base, precio_venta, stock_minimo, activo\)
                            VALUES \(\?, \?, \?, \?, \?, 1\)
                        \"\"\", \(cod, desc, uni, precio, stk_min\)\)

                    if stk_ini > 0:
                        c\.execute\(\"\"\"
                            INSERT INTO documentos \(numero_interno, tipo, estado, fecha_emision, observaciones\)
                            VALUES \(\?, 'AJUSTE', 'CONFIRMADO', \?, 'Importacin Excel \(Stock inicial\)'\)
                        \"\"\", \(f\"IMP-\{cod\}-\{ts\}\", fecha\)\)
                        id_doc = c\.lastrowid

                        c\.execute\(\"\"\"
                            INSERT INTO movimientos_stock \(codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas\)
                            VALUES \(\?, 'ENTRADA', \?, \?, \?, 'Importacin Excel'\)
                        \"\"\", \(cod, stk_ini, id_doc, fecha\)\)

            self\.conn\.commit\(\)
            QMessageBox\.information\(self, \"xito\", f\"Se procesaron \{len\(self\.filas_validas\)\} productos exitosamente\.\"\)
            self\.accept\(\)
        except Exception as e:
            self\.conn\.rollback\(\)
            QMessageBox\.critical\(self, \"Error Fatal\", f\"La importacin fall y se revirti\. Detalles:\\n\{e\}\"\)'''

new2 = '''        try:
            from db.queries_stock import ejecutar_importacion_excel
            ejecutar_importacion_excel(self.conn, self.modo_importacion, self.filas_validas)
            QMessageBox.information(self, "xito", f"Se procesaron {len(self.filas_validas)} productos exitosamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error Fatal", f"La importacin fall y se revirti. Detalles:\\n{e}")'''

content = re.sub(old2, new2, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated excel_stock.py')
