import sqlite3
from datetime import datetime

# =====================================================================
# CONFIGURACION / ESQUEMA
# =====================================================================

def migrar_esquema_stock(conn):
    """Aplica migraciones idempotentes necesarias para la gestión de stock."""
    c = conn.cursor()
    
    # 1. imagen_path en productos
    c.execute("PRAGMA table_info(productos)")
    columnas = [row[1] for row in c.fetchall()]
    if "imagen_path" not in columnas:
        c.execute("ALTER TABLE productos ADD COLUMN imagen_path TEXT")
        
    # 2. notas en movimientos_stock
    c.execute("PRAGMA table_info(movimientos_stock)")
    columnas = [row[1] for row in c.fetchall()]
    if "notas" not in columnas:
        c.execute("ALTER TABLE movimientos_stock ADD COLUMN notas TEXT")
        
    conn.commit()


# =====================================================================
# LECTURA DE PRODUCTOS
# =====================================================================

def obtener_detalles_producto(conn, codigo):
    c = conn.cursor()
    c.execute("SELECT descripcion, unidad_base, precio_venta, stock_minimo, imagen_path FROM productos WHERE codigo = ?", (codigo,))
    return c.fetchone()

def obtener_imagen_path(conn, codigo):
    c = conn.cursor()
    c.execute("SELECT imagen_path FROM productos WHERE codigo=?", (codigo,))
    row = c.fetchone()
    return row[0] if row else None

def obtener_productos_activos_exportacion(conn):
    c = conn.cursor()
    c.execute("SELECT codigo, lower(descripcion) FROM productos WHERE activo = 1")
    return c.fetchall()

def obtener_codigos_productos_todos(conn):
    c = conn.cursor()
    c.execute("SELECT codigo FROM productos")
    return [r[0] for r in c.fetchall()]

def verificar_existencia_producto(conn, codigo):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM productos WHERE codigo=?", (codigo,))
    return c.fetchone()[0] > 0


# =====================================================================
# CREACIÓN Y EDICIÓN DE PRODUCTOS
# =====================================================================

def crear_producto_con_stock_inicial(conn, cod, desc, uni, precio, stk_min, final_img, stk_ini, commit=True):
    c = conn.cursor()
    if commit:
        c.execute("BEGIN TRANSACTION;")
    try:
        c.execute("""
            INSERT INTO productos (codigo, descripcion, unidad_base, precio_venta, stock_minimo, imagen_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cod, desc, uni, precio, stk_min, final_img))

        if stk_ini > 0:
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""
                INSERT INTO documentos (numero_interno, tipo, estado, fecha_emision, observaciones)
                VALUES (?, 'AJUSTE', 'CONFIRMADO', ?, 'Stock inicial')
            """, (f"INI-{cod}-{int(datetime.now().timestamp())}", fecha))
            id_doc = c.lastrowid

            c.execute("""
                INSERT INTO movimientos_stock (codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas)
                VALUES (?, 'ENTRADA', ?, ?, ?, 'Inventario inicial')
            """, (cod, stk_ini, id_doc, fecha))

        if commit:
            conn.commit()
    except Exception as e:
        if commit:
            conn.rollback()
        raise e

def actualizar_producto_y_registrar(conn, cod, desc, uni, precio, stk_min, final_img):
    c = conn.cursor()
    c.execute("BEGIN TRANSACTION;")
    try:
        c.execute("""
            UPDATE productos 
            SET descripcion = ?, unidad_base = ?, precio_venta = ?, 
                stock_minimo = ?, imagen_path = ?
            WHERE codigo = ?
        """, (desc, uni, precio, stk_min, final_img, cod))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def actualizar_stock_minimo(conn, codigo, stock_minimo):
    c = conn.cursor()
    c.execute("UPDATE productos SET stock_minimo = ? WHERE codigo = ?", (stock_minimo, codigo))
    conn.commit()

def reactivar_producto(conn, codigo):
    c = conn.cursor()
    c.execute("UPDATE productos SET activo = 1 WHERE codigo = ?", (codigo,))
    conn.commit()


# =====================================================================
# ELIMINACIÓN DE PRODUCTOS
# =====================================================================

def intentar_eliminar_producto(conn, cod):
    """
    Intenta eliminar un producto. Si tiene dependencias, lo desactiva.
    Devuelve "DESACTIVADO" o "ELIMINADO".
    """
    c = conn.cursor()
    c.execute("BEGIN TRANSACTION;")
    try:
        c.execute("SELECT COUNT(*) FROM detalle_documentos WHERE codigo_producto=?", (cod,))
        c_doc = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM movimientos_stock WHERE codigo_producto=?", (cod,))
        c_mov = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM compromisos_stock WHERE codigo_producto=?", (cod,))
        c_comp = c.fetchone()[0]

        if c_doc > 0 or c_mov > 0 or c_comp > 0:
            c.execute("UPDATE productos SET activo = 0 WHERE codigo = ?", (cod,))
            conn.commit()
            return "DESACTIVADO"
        else:
            c.execute("DELETE FROM productos WHERE codigo = ?", (cod,))
            conn.commit()
            return "ELIMINADO"
    except Exception as e:
        conn.rollback()
        raise e


# =====================================================================
# MOVIMIENTOS Y AJUSTES DE STOCK
# =====================================================================

def registrar_ingreso_manual(conn, cod, cant, notas):
    c = conn.cursor()
    c.execute("BEGIN TRANSACTION;")
    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        num_int = f"ENT-{cod}-{int(datetime.now().timestamp())}"

        c.execute("""
            INSERT INTO documentos (numero_interno, tipo, estado, fecha_emision, observaciones)
            VALUES (?, 'AJUSTE', 'CONFIRMADO', ?, ?)
        """, (num_int, fecha, f"Ingreso manual: {notas}" if notas else "Ingreso manual"))
        id_doc = c.lastrowid

        c.execute("""
            INSERT INTO movimientos_stock (codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas)
            VALUES (?, 'ENTRADA', ?, ?, ?, ?)
        """, (cod, cant, id_doc, fecha, notas))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def sumar_stock_producto_existente(conn, cod, stk_ini):
    c = conn.cursor()
    c.execute("BEGIN TRANSACTION;")
    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
            INSERT INTO documentos (numero_interno, tipo, estado, fecha_emision, observaciones)
            VALUES (?, 'AJUSTE', 'CONFIRMADO', ?, 'Ingreso por flujo Nuevo Producto / Sumar Stock')
        """, (f"AGR-{cod}-{int(datetime.now().timestamp())}", fecha))
        id_doc = c.lastrowid

        c.execute("""
            INSERT INTO movimientos_stock (codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas)
            VALUES (?, 'ENTRADA', ?, ?, ?, 'Stock sumado desde formulario de alta')
        """, (cod, stk_ini, id_doc, fecha))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def registrar_ajuste_inventario(conn, cod, diferencia, motivo):
    tipo_mov = 'ENTRADA' if diferencia > 0 else 'SALIDA'
    cant_absoluta = abs(diferencia)

    c = conn.cursor()
    c.execute("BEGIN TRANSACTION;")
    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        num_int = f"AJU-{cod}-{int(datetime.now().timestamp())}"

        c.execute("""
            INSERT INTO documentos (numero_interno, tipo, estado, fecha_emision, observaciones)
            VALUES (?, 'AJUSTE', 'CONFIRMADO', ?, ?)
        """, (num_int, fecha, f"Ajuste inventario: {motivo}"))
        id_doc = c.lastrowid

        c.execute("""
            INSERT INTO movimientos_stock (codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cod, tipo_mov, cant_absoluta, id_doc, fecha, motivo))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def ejecutar_consulta_historial(conn, sql, params):
    c = conn.cursor()
    c.execute(sql, params)
    return c.fetchall()


# =====================================================================
# IMPORTACIÓN EXCEL
# =====================================================================

def ejecutar_importacion_excel_segura(conn, filas_procesadas):
    c = conn.cursor()
    c.execute("BEGIN TRANSACTION;")
    try:
        from datetime import datetime
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ts = int(datetime.now().timestamp())

        for (cod, desc, uni, precio, stk_ini, stk_min, img, estado) in filas_procesadas:
            if estado == "ACTUALIZAR":
                if img:
                    c.execute("""
                        UPDATE productos SET descripcion=?, unidad_base=?, precio_venta=?, stock_minimo=?, activo=1, imagen_path=?
                        WHERE codigo=?
                    """, (desc, uni, precio, stk_min, img, cod))
                else:
                    c.execute("""
                        UPDATE productos SET descripcion=?, unidad_base=?, precio_venta=?, stock_minimo=?, activo=1
                        WHERE codigo=?
                    """, (desc, uni, precio, stk_min, cod))
            elif estado == "NUEVO":
                if img:
                    c.execute("""
                        INSERT INTO productos (codigo, descripcion, unidad_base, precio_venta, stock_minimo, imagen_path, activo)
                        VALUES (?, ?, ?, ?, ?, ?, 1)
                    """, (cod, desc, uni, precio, stk_min, img))
                else:
                    c.execute("""
                        INSERT INTO productos (codigo, descripcion, unidad_base, precio_venta, stock_minimo, activo)
                        VALUES (?, ?, ?, ?, ?, 1)
                    """, (cod, desc, uni, precio, stk_min))

                if stk_ini > 0:
                    c.execute("""
                        INSERT INTO documentos (numero_interno, tipo, estado, fecha_emision, observaciones)
                        VALUES (?, 'AJUSTE', 'CONFIRMADO', ?, 'Importación Excel (Stock inicial)')
                    """, (f"IMP-{cod}-{ts}", fecha))
                    id_doc = c.lastrowid

                    c.execute("""
                        INSERT INTO movimientos_stock (codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas)
                        VALUES (?, 'ENTRADA', ?, ?, ?, 'Importación Excel')
                    """, (cod, stk_ini, id_doc, fecha))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def obtener_productos_activos_exportacion(conn):
    c = conn.cursor()
    c.execute("SELECT codigo, lower(descripcion) FROM productos WHERE activo = 1")
    return c.fetchall()

def obtener_codigos_productos_todos(conn):
    c = conn.cursor()
    c.execute("SELECT codigo FROM productos")
    return [r[0] for r in c.fetchall()]

def verificar_existencia_producto(conn, codigo):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM productos WHERE codigo=?", (codigo,))
    return c.fetchone()[0] > 0


# =====================================================================
# CREACIÓN Y EDICIÓN DE PRODUCTOS
# =====================================================================

def crear_producto_con_stock_inicial(conn, cod, desc, uni, precio, stk_min, final_img, stk_ini, commit=True):
    c = conn.cursor()
    if commit:
        c.execute("BEGIN TRANSACTION;")
    try:
        c.execute("""
            INSERT INTO productos (codigo, descripcion, unidad_base, precio_venta, stock_minimo, imagen_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cod, desc, uni, precio, stk_min, final_img))

        if stk_ini > 0:
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""
                INSERT INTO documentos (numero_interno, tipo, estado, fecha_emision, observaciones)
                VALUES (?, 'AJUSTE', 'CONFIRMADO', ?, 'Stock inicial')
            """, (f"INI-{cod}-{int(datetime.now().timestamp())}", fecha))
            id_doc = c.lastrowid

            c.execute("""
                INSERT INTO movimientos_stock (codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas)
                VALUES (?, 'ENTRADA', ?, ?, ?, 'Inventario inicial')
            """, (cod, stk_ini, id_doc, fecha))

        if commit:
            conn.commit()
    except Exception as e:
        if commit:
            conn.rollback()
        raise e

def actualizar_producto_y_registrar(conn, cod, desc, uni, precio, stk_min, final_img):
    c = conn.cursor()
    c.execute("BEGIN TRANSACTION;")
    try:
        c.execute("""
            UPDATE productos 
            SET descripcion = ?, unidad_base = ?, precio_venta = ?, 
                stock_minimo = ?, imagen_path = ?
            WHERE codigo = ?
        """, (desc, uni, precio, stk_min, final_img, cod))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def actualizar_stock_minimo(conn, codigo, stock_minimo):
    c = conn.cursor()
    c.execute("UPDATE productos SET stock_minimo = ? WHERE codigo = ?", (stock_minimo, codigo))
    conn.commit()

def reactivar_producto(conn, codigo):
    c = conn.cursor()
    c.execute("UPDATE productos SET activo = 1 WHERE codigo = ?", (codigo,))
    conn.commit()


# =====================================================================
# ELIMINACIÓN DE PRODUCTOS
# =====================================================================

def intentar_eliminar_producto(conn, cod):
    """
    Intenta eliminar un producto. Si tiene dependencias, lo desactiva.
    Devuelve "DESACTIVADO" o "ELIMINADO".
    """
    c = conn.cursor()
    c.execute("BEGIN TRANSACTION;")
    try:
        c.execute("SELECT COUNT(*) FROM detalle_documentos WHERE codigo_producto=?", (cod,))
        c_doc = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM movimientos_stock WHERE codigo_producto=?", (cod,))
        c_mov = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM compromisos_stock WHERE codigo_producto=?", (cod,))
        c_comp = c.fetchone()[0]

        if c_doc > 0 or c_mov > 0 or c_comp > 0:
            c.execute("UPDATE productos SET activo = 0 WHERE codigo = ?", (cod,))
            conn.commit()
            return "DESACTIVADO"
        else:
            c.execute("DELETE FROM productos WHERE codigo = ?", (cod,))
            conn.commit()
            return "ELIMINADO"
    except Exception as e:
        conn.rollback()
        raise e


# =====================================================================
# MOVIMIENTOS Y AJUSTES DE STOCK
# =====================================================================

def registrar_ingreso_manual(conn, cod, cant, notas):
    c = conn.cursor()
    c.execute("BEGIN TRANSACTION;")
    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        num_int = f"ENT-{cod}-{int(datetime.now().timestamp())}"

        c.execute("""
            INSERT INTO documentos (numero_interno, tipo, estado, fecha_emision, observaciones)
            VALUES (?, 'AJUSTE', 'CONFIRMADO', ?, ?)
        """, (num_int, fecha, f"Ingreso manual: {notas}" if notas else "Ingreso manual"))
        id_doc = c.lastrowid

        c.execute("""
            INSERT INTO movimientos_stock (codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas)
            VALUES (?, 'ENTRADA', ?, ?, ?, ?)
        """, (cod, cant, id_doc, fecha, notas))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def sumar_stock_producto_existente(conn, cod, stk_ini):
    c = conn.cursor()
    c.execute("BEGIN TRANSACTION;")
    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
            INSERT INTO documentos (numero_interno, tipo, estado, fecha_emision, observaciones)
            VALUES (?, 'AJUSTE', 'CONFIRMADO', ?, 'Ingreso por flujo Nuevo Producto / Sumar Stock')
        """, (f"AGR-{cod}-{int(datetime.now().timestamp())}", fecha))
        id_doc = c.lastrowid

        c.execute("""
            INSERT INTO movimientos_stock (codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas)
            VALUES (?, 'ENTRADA', ?, ?, ?, 'Stock sumado desde formulario de alta')
        """, (cod, stk_ini, id_doc, fecha))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def registrar_ajuste_inventario(conn, cod, diferencia, motivo):
    tipo_mov = 'ENTRADA' if diferencia > 0 else 'SALIDA'
    cant_absoluta = abs(diferencia)

    c = conn.cursor()
    c.execute("BEGIN TRANSACTION;")
    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        num_int = f"AJU-{cod}-{int(datetime.now().timestamp())}"

        c.execute("""
            INSERT INTO documentos (numero_interno, tipo, estado, fecha_emision, observaciones)
            VALUES (?, 'AJUSTE', 'CONFIRMADO', ?, ?)
        """, (num_int, fecha, f"Ajuste inventario: {motivo}"))
        id_doc = c.lastrowid

        c.execute("""
            INSERT INTO movimientos_stock (codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cod, tipo_mov, cant_absoluta, id_doc, fecha, motivo))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def ejecutar_consulta_historial(conn, sql, params):
    c = conn.cursor()
    c.execute(sql, params)
    return c.fetchall()


# =====================================================================
# IMPORTACIÓN EXCEL
# =====================================================================

def ejecutar_importacion_excel(conn, modo_importacion, filas_validas):
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
                c.execute("""
                    UPDATE productos SET descripcion=?, unidad_base=?, precio_venta=?, stock_minimo=?, activo=1
                    WHERE codigo=?
                """, (desc, uni, precio, stk_min, cod))
                # NO agregamos stock inicial para actualizaciones en modo AGREGAR
            else:
                c.execute("SELECT COUNT(*) FROM productos WHERE codigo=?", (cod,))
                if c.fetchone()[0] > 0:
                    c.execute("""
                        UPDATE productos SET descripcion=?, unidad_base=?, precio_venta=?, stock_minimo=?, activo=1
                        WHERE codigo=?
                    """, (desc, uni, precio, stk_min, cod))
                else:
                    c.execute("""
                        INSERT INTO productos (codigo, descripcion, unidad_base, precio_venta, stock_minimo, activo)
                        VALUES (?, ?, ?, ?, ?, 1)
                    """, (cod, desc, uni, precio, stk_min))

                if stk_ini > 0:
                    c.execute("""
                        INSERT INTO documentos (numero_interno, tipo, estado, fecha_emision, observaciones)
                        VALUES (?, 'AJUSTE', 'CONFIRMADO', ?, 'Importación Excel (Stock inicial)')
                    """, (f"IMP-{cod}-{ts}", fecha))
                    id_doc = c.lastrowid

                    c.execute("""
                        INSERT INTO movimientos_stock (codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora, notas)
                        VALUES (?, 'ENTRADA', ?, ?, ?, 'Importación Excel')
                    """, (cod, stk_ini, id_doc, fecha))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
