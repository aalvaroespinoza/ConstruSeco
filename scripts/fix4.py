import re
filepath = 'db/queries_stock.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = r'''def ejecutar_transaccion_importacion_excel\(conn, lineas_validas\):
    \"\"\"
    Ejecuta el bloque transaccional gigante de importación\.
    lineas_validas = \[\(cod, desc, uni, str_precio, stk_min, stock_inicial\), \.\.\.\]
    \"\"\"
    c = conn\.cursor\(\)
    c\.execute\(\"BEGIN TRANSACTION;\"\)
    try:
        c\.execute\(\"SELECT codigo FROM productos\"\)
        codigos_bd = \{row\[0\] for row in c\.fetchall\(\)\}

        agregados = 0
        actualizados = 0
        fecha = datetime\.now\(\)\.strftime\(\"%Y-%m-%d %H:%M:%S\"\)

        for row in lineas_validas:
            cod, desc, uni, precio_val, min_val, stk_ini = row

            if cod in codigos_bd:
                c\.execute\(\"\"\"
                    UPDATE productos 
                    SET descripcion=\?, unidad_base=\?, precio_venta=\?, stock_minimo=\?, activo=1 
                    WHERE codigo=\?
                \"\"\", \(desc, uni, precio_val, min_val, cod\)\)
                actualizados \+= 1
            else:
                c\.execute\(\"\"\"
                    INSERT INTO productos \(codigo, descripcion, unidad_base, precio_venta, stock_minimo\)
                    VALUES \(\?, \?, \?, \?, \?\)
                \"\"\", \(cod, desc, uni, precio_val, min_val\)\)
                agregados \+= 1

                if stk_ini > 0:
                    c\.execute\(\"\"\"
                        INSERT INTO documentos \(numero_interno, tipo, estado, fecha_emision, observaciones\)
                        VALUES \(\?, 'AJUSTE', 'CONFIRMADO', \?, 'Inventario inicial Excel'\)
                    \"\"\", \(f\"INI-EXCEL-\{cod\}-\{int\(datetime\.now\(\)\.timestamp\(\)\)\}\", fecha\)\)
                    id_doc = c\.lastrowid

                    c\.execute\(\"\"\"
                        INSERT INTO movimientos_stock \(codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas\)
                        VALUES \(\?, 'ENTRADA', \?, \?, \?, 'Importación Excel'\)
                    \"\"\", \(cod, stk_ini, id_doc, fecha\)\)
        
        conn\.commit\(\)
        return agregados, actualizados
    except Exception as e:
        conn\.rollback\(\)
        raise e'''

new = '''def ejecutar_importacion_excel(conn, modo_importacion, filas_validas):
    c = conn.cursor()
    c.execute("BEGIN TRANSACTION;")
    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ts = int(datetime.now().timestamp())

        if modo_importacion == "SUSTITUIR":
            # Auditar y desactivar/eliminar actuales
            c.execute("SELECT codigo FROM productos")
            todos_actuales = [r[0] for r in c.fetchall()]
            nuevos_codigos = set(p[0] for p in filas_validas)

            for cod in todos_actuales:
                if cod not in nuevos_codigos:
                    c.execute("SELECT COUNT(*) FROM detalle_documentos WHERE codigo_producto=?", (cod,))
                    c_doc = c.fetchone()[0]
                    c.execute("SELECT COUNT(*) FROM movimientos_stock WHERE codigo_producto=?", (cod,))
                    c_mov = c.fetchone()[0]
                    c.execute("SELECT COUNT(*) FROM compromisos_stock WHERE codigo_producto=?", (cod,))
                    c_comp = c.fetchone()[0]

                    if c_doc > 0 or c_mov > 0 or c_comp > 0:
                        c.execute("UPDATE productos SET activo = 0 WHERE codigo = ?", (cod,))
                    else:
                        c.execute("DELETE FROM productos WHERE codigo = ?", (cod,))

        for (cod, desc, uni, precio, stk_ini, stk_min, estado_update) in filas_validas:
            if estado_update == "ACTUALIZAR" and modo_importacion != "SUSTITUIR":
                c.execute(\"\"\"
                    UPDATE productos SET descripcion=?, unidad_base=?, precio_venta=?, stock_minimo=?, activo=1
                    WHERE codigo=?
                \"\"\", (desc, uni, precio, stk_min, cod))
                # NO agregamos stock inicial para actualizaciones en modo AGREGAR
            else:
                c.execute("SELECT COUNT(*) FROM productos WHERE codigo=?", (cod,))
                if c.fetchone()[0] > 0:
                    c.execute(\"\"\"
                        UPDATE productos SET descripcion=?, unidad_base=?, precio_venta=?, stock_minimo=?, activo=1
                        WHERE codigo=?
                    \"\"\", (desc, uni, precio, stk_min, cod))
                else:
                    c.execute(\"\"\"
                        INSERT INTO productos (codigo, descripcion, unidad_base, precio_venta, stock_minimo, activo)
                        VALUES (?, ?, ?, ?, ?, 1)
                    \"\"\", (cod, desc, uni, precio, stk_min))

                if stk_ini > 0:
                    c.execute(\"\"\"
                        INSERT INTO documentos (numero_interno, tipo, estado, fecha_emision, observaciones)
                        VALUES (?, 'AJUSTE', 'CONFIRMADO', ?, 'Importación Excel (Stock inicial)')
                    \"\"\", (f"IMP-{cod}-{ts}", fecha))
                    id_doc = c.lastrowid

                    c.execute(\"\"\"
                        INSERT INTO movimientos_stock (codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas)
                        VALUES (?, 'ENTRADA', ?, ?, ?, 'Importación Excel')
                    \"\"\", (cod, stk_ini, id_doc, fecha))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e'''

content = re.sub(old, new, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated queries_stock.py')
