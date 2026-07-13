import re
filepath = 'ui/modules/stock/dialogs_stock.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. sumar_stock_producto_existente / crear_producto_con_stock_inicial
old_block1 = r'''        c = self\.conn\.cursor\(\)
        
        if self\.es_existente:
            try:
                c\.execute\(\"BEGIN TRANSACTION;\"\)\s*
                fecha = datetime\.now\(\)\.strftime\(\"%Y-%m-%d %H:%M:%S\"\)\s*
                c\.execute\(\"\"\"\s*
                    INSERT INTO documentos \(numero_interno, tipo, estado, fecha_emision, observaciones\)
                    VALUES \(\?, 'AJUSTE', 'CONFIRMADO', \?, 'Ingreso por flujo Nuevo Producto / Sumar Stock'\)
                \"\"\", \(f\"AGR-\{cod\}-\{int\(datetime\.now\(\)\.timestamp\(\)\)\}\", fecha\)\)\s*
                id_doc = c\.lastrowid\s*
                c\.execute\(\"\"\"\s*
                    INSERT INTO movimientos_stock \(codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas\)
                    VALUES \(\?, 'ENTRADA', \?, \?, \?, 'Stock sumado desde formulario de alta'\)
                \"\"\", \(cod, stk_ini, id_doc, fecha\)\)\s*
                self\.conn\.commit\(\)\s*
                QMessageBox\.information\(self, \"Éxito\", f\"Se sumaron \{stk_ini:g\} unidades al producto existente\.\"\)\s*
                self\.accept\(\)\s*
            except Exception as e:
                self\.conn\.rollback\(\)\s*
                QMessageBox\.critical\(self, \"Error\", f\"Error al sumar stock: \{e\}\"\)\s*
        else:
            try:
                c\.execute\(\"BEGIN TRANSACTION;\"\)\s*
                c\.execute\(\"\"\"\s*
                    INSERT INTO productos \(codigo, descripcion, unidad_base, precio_venta, stock_minimo, imagen_path\)
                    VALUES \(\?, \?, \?, \?, \?, \?\)
                \"\"\", \(cod, desc, uni, precio, stk_min, final_img\)\)\s*
                if stk_ini > 0:
                    fecha = datetime\.now\(\)\.strftime\(\"%Y-%m-%d %H:%M:%S\"\)\s*
                    c\.execute\(\"\"\"\s*
                        INSERT INTO documentos \(numero_interno, tipo, estado, fecha_emision, observaciones\)
                        VALUES \(\?, 'AJUSTE', 'CONFIRMADO', \?, 'Stock inicial'\)
                    \"\"\", \(f\"INI-\{cod\}-\{int\(datetime\.now\(\)\.timestamp\(\)\)\}\", fecha\)\)\s*
                    id_doc = c\.lastrowid\s*
                    c\.execute\(\"\"\"\s*
                        INSERT INTO movimientos_stock \(codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas\)
                        VALUES \(\?, 'ENTRADA', \?, \?, \?, 'Inventario inicial'\)
                    \"\"\", \(cod, stk_ini, id_doc, fecha\)\)\s*
                self\.conn\.commit\(\)\s*
                QMessageBox\.information\(self, \"Éxito\", \"Producto registrado correctamente\.\"\)\s*
                self\.accept\(\)\s*
            except sqlite3\.IntegrityError:
                self\.conn\.rollback\(\)\s*
                QMessageBox\.critical\(self, \"Error\", \"Ya existe un producto con ese código o descripción\.\"\)\s*
            except Exception as e:
                self\.conn\.rollback\(\)\s*
                QMessageBox\.critical\(self, \"Error\", str\(e\)\)'''

new_block1 = '''        if self.es_existente:
            try:
                sumar_stock_producto_existente(self.conn, cod, stk_ini)
                QMessageBox.information(self, "Éxito", f"Se sumaron {stk_ini:g} unidades al producto existente.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al sumar stock: {e}")
        else:
            try:
                crear_producto_con_stock_inicial(self.conn, cod, desc, uni, precio, stk_min, final_img, stk_ini)
                QMessageBox.information(self, "Éxito", "Producto registrado correctamente.")
                self.accept()
            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Error", "Ya existe un producto con ese código o descripción.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))'''

content = re.sub(old_block1, new_block1, content)


# 2. actualizar_producto_y_registrar
old_block2 = r'''        c = self\.conn\.cursor\(\)\s*
        try:
            c\.execute\(\"BEGIN TRANSACTION;\"\)\s*
            c\.execute\(\"\"\"\s*
                UPDATE productos 
                SET descripcion = \?, unidad_base = \?, precio_venta = \?, 
                    stock_minimo = \?, imagen_path = \?
                WHERE codigo = \?
            \"\"\", \(desc, uni, precio, stk_min, final_img, cod\)\)\s*
            c\.execute\(\"\"\"\s*
                INSERT INTO movimientos_stock \(codigo_producto, tipo_movimiento, cantidad, fecha_hora, notas\)
                VALUES \(\?, 'ACTUALIZACION', 0, \?, 'Actualización de datos del producto'\)
            \"\"\", \(cod, datetime\.now\(\)\.strftime\(\"%Y-%m-%d %H:%M:%S\"\)\)\)\s*
            self\.conn\.commit\(\)\s*
            QMessageBox\.information\(self, \"Éxito\", \"Producto actualizado correctamente\.\"\)\s*
            self\.accept\(\)\s*
        except sqlite3\.IntegrityError:
            self\.conn\.rollback\(\)\s*
            QMessageBox\.critical\(self, \"Error\", \"Ya existe otro producto con esa descripción\.\"\)\s*
        except Exception as e:
            self\.conn\.rollback\(\)\s*
            QMessageBox\.critical\(self, \"Error\", str\(e\)\)'''

new_block2 = '''        try:
            actualizar_producto_y_registrar(self.conn, cod, desc, uni, precio, stk_min, final_img)
            QMessageBox.information(self, "Éxito", "Producto actualizado correctamente.")
            self.accept()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "Ya existe otro producto con esa descripción.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))'''

content = re.sub(old_block2, new_block2, content)

# 3. obtener_imagen_path
old_block3 = r'''        c = self\.conn\.cursor\(\)\s*
        c\.execute\(\"SELECT imagen_path FROM productos WHERE codigo=\?\", \(self\.p_data\['codigo'\]\,\)\)\s*
        row = c\.fetchone\(\)\s*
        img_path = row\[0\] if row else None'''

new_block3 = '''        img_path = obtener_imagen_path(self.conn, self.p_data['codigo'])'''
content = re.sub(old_block3, new_block3, content)


# 4. intentar_eliminar_producto
old_block4 = r'''        c = self\.conn\.cursor\(\)\s*
        try:
            c\.execute\(\"BEGIN TRANSACTION;\"\)\s*
            # Chequear dependencias
            c\.execute\(\"SELECT COUNT\(\*\) FROM detalle_documentos WHERE codigo_producto=\?\", \(cod,\)\)\s*
            c_doc = c\.fetchone\(\)\[0\]\s*
            c\.execute\(\"SELECT COUNT\(\*\) FROM movimientos_stock WHERE codigo_producto=\?\", \(cod,\)\)\s*
            c_mov = c\.fetchone\(\)\[0\]\s*
            c\.execute\(\"SELECT COUNT\(\*\) FROM compromisos_stock WHERE codigo_producto=\?\", \(cod,\)\)\s*
            c_comp = c\.fetchone\(\)\[0\]\s*
            if c_doc > 0 or c_mov > 0 or c_comp > 0:
                # Tiene historial, desactivar
                c\.execute\(\"UPDATE productos SET activo = 0 WHERE codigo = \?\", \(cod,\)\)\s*
                self\.conn\.commit\(\)\s*
                QMessageBox\.information\(
                    self, \"Producto Desactivado\",
                    \"Este producto tiene historial asociado y no puede eliminarse definitivamente sin perder trazabilidad\. Ha sido desactivado\.\"
                \)\s*
            else:
                # Sin historial, eliminar fisicamente
                c\.execute\(\"DELETE FROM productos WHERE codigo = \?\", \(cod,\)\)\s*
                self\.conn\.commit\(\)\s*
                QMessageBox\.information\(self, \"Eliminado\", \"El producto fue eliminado definitivamente\.\"\)\s*
            self\.accept\(\)\s*
        except Exception as e:
            self\.conn\.rollback\(\)\s*
            QMessageBox\.critical\(self, \"Error\", str\(e\)\)'''

new_block4 = '''        try:
            resultado = intentar_eliminar_producto(self.conn, cod)
            if resultado == "DESACTIVADO":
                QMessageBox.information(
                    self, "Producto Desactivado",
                    "Este producto tiene historial asociado y no puede eliminarse definitivamente sin perder trazabilidad. Ha sido desactivado."
                )
            else:
                QMessageBox.information(self, "Eliminado", "El producto fue eliminado definitivamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))'''

content = re.sub(old_block4, new_block4, content)

# 5. actualizar_stock_minimo
old_block5 = r'''        try:
            c = self\.conn\.cursor\(\)\s*
            c\.execute\(\"UPDATE productos SET stock_minimo = \? WHERE codigo = \?\", \(stk, self\.p_data\['codigo'\]\)\)\s*
            self\.conn\.commit\(\)\s*
            self\.accept\(\)\s*
        except Exception as e:
            QMessageBox\.critical\(self, \"Error\", str\(e\)\)'''

new_block5 = '''        try:
            actualizar_stock_minimo(self.conn, self.p_data['codigo'], stk)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))'''

content = re.sub(old_block5, new_block5, content)

# 6. registrar_ingreso_manual
old_block6 = r'''        c = self\.conn\.cursor\(\)\s*
        try:
            c\.execute\(\"BEGIN TRANSACTION;\"\)\s*
            fecha = datetime\.now\(\)\.strftime\(\"%Y-%m-%d %H:%M:%S\"\)\s*
            num_int = f\"ENT-\{cod\}-\{int\(datetime\.now\(\)\.timestamp\(\)\)\}\"\s*
            c\.execute\(\"\"\"\s*
                INSERT INTO documentos \(numero_interno, tipo, estado, fecha_emision, observaciones\)
                VALUES \(\?, 'AJUSTE', 'CONFIRMADO', \?, \?\)
            \"\"\", \(num_int, fecha, f\"Ingreso manual: \{notas\}\" if notas else \"Ingreso manual\"\)\)\s*
            id_doc = c\.lastrowid\s*
            c\.execute\(\"\"\"\s*
                INSERT INTO movimientos_stock \(codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas\)
                VALUES \(\?, 'ENTRADA', \?, \?, \?, \?\)
            \"\"\", \(cod, cant, id_doc, fecha, notas\)\)\s*
            self\.conn\.commit\(\)\s*
            QMessageBox\.information\(self, \"Éxito\", \"Entrada registrada correctamente\.\"\)\s*
            self\.accept\(\)\s*
        except Exception as e:
            self\.conn\.rollback\(\)\s*
            QMessageBox\.critical\(self, \"Error\", str\(e\)\)'''

new_block6 = '''        try:
            registrar_ingreso_manual(self.conn, cod, cant, notas)
            QMessageBox.information(self, "Éxito", "Entrada registrada correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))'''
content = re.sub(old_block6, new_block6, content)

# 7. registrar_ajuste_inventario
old_block7 = r'''        c = self\.conn\.cursor\(\)\s*
        try:
            c\.execute\(\"BEGIN TRANSACTION;\"\)\s*
            fecha = datetime\.now\(\)\.strftime\(\"%Y-%m-%d %H:%M:%S\"\)\s*
            num_int = f\"AJU-\{cod\}-\{int\(datetime\.now\(\)\.timestamp\(\)\)\}\"\s*
            c\.execute\(\"\"\"\s*
                INSERT INTO documentos \(numero_interno, tipo, estado, fecha_emision, observaciones\)
                VALUES \(\?, 'AJUSTE', 'CONFIRMADO', \?, \?\)
            \"\"\", \(num_int, fecha, f\"Ajuste inventario: \{motivo\}\"\)\)\s*
            id_doc = c\.lastrowid\s*
            c\.execute\(\"\"\"\s*
                INSERT INTO movimientos_stock \(codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas\)
                VALUES \(\?, \?, \?, \?, \?, \?\)
            \"\"\", \(cod, tipo_mov, cant_absoluta, id_doc, fecha, motivo\)\)\s*
            self\.conn\.commit\(\)\s*
            QMessageBox\.information\(self, \"Éxito\", f\"Inventario ajustado\. \{tipo_mov\} de \{cant_absoluta:g\} aplicada\.\"\)\s*
            self\.accept\(\)\s*
        except Exception as e:
            self\.conn\.rollback\(\)\s*
            QMessageBox\.critical\(self, \"Error\", str\(e\)\)'''

new_block7 = '''        try:
            registrar_ajuste_inventario(self.conn, cod, self.diferencia, motivo)
            QMessageBox.information(self, "Éxito", f"Inventario ajustado. {tipo_mov} de {cant_absoluta:g} aplicada.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))'''
content = re.sub(old_block7, new_block7, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated dialogs_stock.py')
