import re
filepath = 'ui/modules/ventas/tab_ventas.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. migrar_esquema
old_migrar = r'''    def migrar_esquema\(self\):
        cursor = self\.conn\.cursor\(\)
        
        # 1\. Tabla conversiones_unidad
        # Chequear si existe la columna operacion
        if 'conversiones_unidad' in \[fila\[1\] for fila in cursor\.execute\(\"SELECT name FROM sqlite_master WHERE type='table'\"\)]:
            columnas_conv = \[
                fila\[1\] for fila in cursor\.execute\(\"PRAGMA table_info\(conversiones_unidad\)\"\)
            \]
            if 'operacion' not in columnas_conv:
                cursor\.execute\(
                    \"ALTER TABLE conversiones_unidad ADD COLUMN operacion TEXT DEFAULT 'DIVIDE'\"
                \)
                
        # 2\. Tabla documentos
        if 'documentos' in \[fila\[1\] for fila in cursor\.execute\(\"SELECT name FROM sqlite_master WHERE type='table'\"\)]:
            columnas_doc = \[
                fila\[1\] for fila in cursor\.execute\(\"PRAGMA table_info\(documentos\)\"\)
            \]
            nuevas_columnas_doc = \{
                'subtotal_bruto': 'REAL DEFAULT 0',
                'descuento_general_porcentaje': 'REAL DEFAULT 0',
                'iva_aplicado': 'INTEGER DEFAULT 0',
                'iva_porcentaje': 'REAL DEFAULT 21\.0',
                'iva_monto': 'REAL DEFAULT 0'
            \}
            for nombre, tipo in nuevas_columnas_doc\.items\(\):
                if nombre not in columnas_doc:
                    cursor\.execute\(f\"ALTER TABLE documentos ADD COLUMN \{nombre\} \{tipo\}\"\)
                    
        self\.conn\.commit\(\)'''

new_migrar = '''    def migrar_esquema(self):
        from db.queries_ventas import migrar_esquema_ventas
        migrar_esquema_ventas(self.conn)'''

text = re.sub(old_migrar, new_migrar, text)


# 2. cargar_clientes
old_cli = r'''        try:
            cursor = self\.conn\.cursor\(\)
            cursor\.execute\(\"SELECT id_cliente, nombre_completo, cuit_dni, telefono FROM clientes WHERE activo = 1\"\)
            self\.clientes_db = cursor\.fetchall\(\)'''

new_cli = '''        try:
            from db.queries_ventas import obtener_clientes_activos_resumen
            self.clientes_db = obtener_clientes_activos_resumen(self.conn)'''

text = re.sub(old_cli, new_cli, text)


# 3. cargar_catalogo_memoria
old_cat = r'''        try:
            cursor = self\.conn\.cursor\(\)
            subquery_stock = subquery_atp\('p'\)
            cursor\.execute\(f\"\"\"
                SELECT p\.codigo, p\.descripcion, p\.unidad_base,
                       \(\{subquery_stock\}\) as stock,
                       p\.precio_venta,
                       c\.unidad_venta, c\.factor_conversion, c\.operacion
                FROM productos p
                LEFT JOIN conversiones_unidad c ON c\.codigo_producto = p\.codigo
                WHERE p\.activo = 1
            \"\"\"\)
            filas = cursor\.fetchall\(\)'''

new_cat = '''        try:
            from db.queries_ventas import obtener_catalogo_venta
            filas = obtener_catalogo_venta(self.conn)'''

text = re.sub(old_cat, new_cat, text)

# 4. confirmar_operacion
old_conf = r'''        try:
            cursor = self\.conn\.cursor\(\)
            cursor\.execute\(\"BEGIN IMMEDIATE;\"\)

            # El catálogo es una foto tomada al abrir la pantalla\. Revalidamos el
            # ATP dentro de la transacción para impedir sobreventa por líneas
            # repetidas o por cambios realizados desde otra ventana\.
            if tipo == 'PRESUPUESTO' or descontar_stock:
                requeridos = \{\}
                for item in self\.carrito:
                    requeridos\[item\['codigo'\]\] = requeridos\.get\(item\['codigo'\], 0\.0\) \+ \(
                        item\['cantidad'\] \* item\['factor_conversion'\]
                    \)
                for codigo, cantidad_requerida in requeridos\.items\(\):
                    disponible = obtener_stock_producto\(self\.conn, codigo\)\[\"atp\"\]
                    if cantidad_requerida > disponible:
                        raise ValueError\(
                            f\"Stock insuficiente para \{codigo\}: disponibles \{disponible:g\}, \"
                            f\"requeridos \{cantidad_requerida:g\}\.\"
                        \)
            
            subtotal_bruto = sum\(\[p\['cantidad'\] \* p\['precio_unit_mostrado'\] \* \(1 - \(p\['descuento'\] / 100\.0\)\) for p in self\.carrito\]\)
            subtotal_neto = subtotal_bruto \* \(1 - \(self\.descuento_general / 100\.0\)\)
            iva_monto = subtotal_neto \* \(self\.iva_porcentaje / 100\.0\) if self\.iva_aplicado else 0\.0
            total_operacion = subtotal_neto \+ iva_monto
            numero_interno = f\"\{tipo\[:3\]\}-\{fecha_actual\.strftime\('%Y%m%d%H%M%S%f'\)\}\"
            
            id_cliente_final = self\.cliente_seleccionado\['id'\] if self\.cliente_seleccionado else None

            obs = self\.input_observaciones\.text\(\)\.strip\(\)
            if not obs:
                obs = None
                
            # 1\. Cabecera
            cursor\.execute\(\"\"\"
                INSERT INTO documentos \(numero_interno, tipo, estado, fecha_emision, fecha_vencimiento, id_cliente, total_final, subtotal_bruto, descuento_general_porcentaje, iva_aplicado, iva_porcentaje, iva_monto, observaciones\)
                VALUES \(\?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?\)
            \"\"\", \(
                numero_interno, 
                tipo, 
                estado_doc, 
                fecha_actual\.strftime\(\"%Y-%m-%d %H:%M:%S\"\),
                \(fecha_actual \+ timedelta\(hours=48\)\)\.strftime\(\"%Y-%m-%d %H:%M:%S\"\) if tipo == 'PRESUPUESTO' else None,
                id_cliente_final,
                total_operacion,
                subtotal_bruto,
                self\.descuento_general,
                1 if self\.iva_aplicado else 0,
                self\.iva_porcentaje,
                iva_monto,
                obs
            \)\)
            id_doc = cursor\.lastrowid
            
            for item in self\.carrito:
                subtotal_item = item\['cantidad'\] \* item\['precio_unit_mostrado'\] \* \(1 - \(item\['descuento'\] / 100\.0\)\)
                cantidad_base = item\['cantidad'\] \* item\['factor_conversion'\]
                
                # 2\. Detalle
                cursor\.execute\(\"\"\"
                    INSERT INTO detalle_documentos \(id_documento, codigo_producto, unidad_venta, cantidad_unidad_venta, cantidad_base, precio_unitario, descuento_porcentaje, subtotal\)
                    VALUES \(\?, \?, \?, \?, \?, \?, \?, \?\)
                \"\"\", \(
                    id_doc, item\['codigo'\], item\['unidad_venta'\], item\['cantidad'\],
                    cantidad_base, item\['precio_unit_mostrado'\], item\['descuento'\], subtotal_item
                \)\)
                
                # 3\. Stock ATP
                if tipo == 'VENTA' and descontar_stock:
                    cursor\.execute\(\"\"\"
                        INSERT INTO movimientos_stock \(codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora\)
                        VALUES \(\?, 'SALIDA', \?, \?, \?\)
                    \"\"\", \(item\['codigo'\], cantidad_base, id_doc, fecha_actual\.strftime\(\"%Y-%m-%d %H:%M:%S\"\)\)\)
                elif tipo == 'PRESUPUESTO':
                    cursor\.execute\(\"\"\"
                        INSERT INTO compromisos_stock \(codigo_producto, id_documento, cantidad_comprometida, fecha_vencimiento, estado\)
                        VALUES \(\?, \?, \?, \?, 'ACTIVO'\)
                    \"\"\", \(item\['codigo'\], id_doc, cantidad_base, \(fecha_actual \+ timedelta\(hours=48\)\)\.strftime\(\"%Y-%m-%d %H:%M:%S\"\)\)\)
                    
            self\.conn\.commit\(\)
            
            if tipo == 'PRESUPUESTO':
                msg = f\"Presupuesto #\{numero_interno\} generado\.\\n\\nVálido hasta: \{\(fecha_actual \+ timedelta\(hours=48\)\)\.strftime\('%d/%m/%Y %H:%M'\)\}\"
            else:
                msg = f\"Venta #\{numero_interno\} confirmada con éxito\.\"
                
            QMessageBox\.information\(self, \"Operación Exitosa\", msg\)'''

new_conf = '''        try:
            id_cliente_final = self.cliente_seleccionado['id'] if self.cliente_seleccionado else None
            obs = self.input_observaciones.text().strip()
            
            from db.queries_ventas import registrar_operacion_venta
            numero_interno, msg = registrar_operacion_venta(
                self.conn, tipo, descontar_stock, self.carrito,
                self.descuento_general, self.iva_aplicado, self.iva_porcentaje,
                id_cliente_final, obs
            )
            QMessageBox.information(self, "Operación Exitosa", msg)'''

text = re.sub(old_conf, new_conf, text)


with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print('Updated tab_ventas.py')
