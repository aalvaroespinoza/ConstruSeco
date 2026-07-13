import sqlite3
from datetime import datetime, timedelta
from db.queries import subquery_atp, obtener_stock_producto

def migrar_esquema_ventas(conn):
    """Aplica migraciones idempotentes al esquema relacionadas con ventas."""
    cursor = conn.cursor()
    # 1. conversiones_unidad
    cursor.execute("PRAGMA table_info(conversiones_unidad)")
    if not any(fila[1] == 'operacion' for fila in cursor.fetchall()):
        cursor.execute("ALTER TABLE conversiones_unidad ADD COLUMN operacion TEXT DEFAULT 'DIVIDE'")
        
    # 2. documentos
    cursor.execute("PRAGMA table_info(documentos)")
    columnas_doc = {fila[1] for fila in cursor.fetchall()}
    nuevas_columnas_doc = {
        'subtotal_bruto': 'REAL DEFAULT 0',
        'descuento_general_porcentaje': 'REAL DEFAULT 0',
        'iva_aplicado': 'INTEGER DEFAULT 0',
        'iva_porcentaje': 'REAL DEFAULT 21.0',
        'iva_monto': 'REAL DEFAULT 0'
    }
    for nombre, tipo in nuevas_columnas_doc.items():
        if nombre not in columnas_doc:
            cursor.execute(f"ALTER TABLE documentos ADD COLUMN {nombre} {tipo}")
            
    conn.commit()


def obtener_clientes_activos_resumen(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id_cliente, nombre_completo, cuit_dni, telefono FROM clientes WHERE activo = 1")
    return cursor.fetchall()


def obtener_catalogo_venta(conn):
    cursor = conn.cursor()
    sql_atp = subquery_atp('p')
    cursor.execute(f"""
        SELECT p.codigo, p.descripcion, p.unidad_base,
               ({sql_atp}) as stock,
               p.precio_venta,
               c.unidad_venta, c.factor_conversion, c.operacion
        FROM productos p
        LEFT JOIN conversiones_unidad c ON c.codigo_producto = p.codigo
        WHERE p.activo = 1
    """)
    return cursor.fetchall()


def registrar_operacion_venta(conn, tipo, descontar_stock, carrito, descuento_general, iva_aplicado, iva_porcentaje, id_cliente_final, obs):
    """
    Registra atómicamente la venta o presupuesto con todo su detalle, actualizando
    movimientos o compromisos de stock y validando ATP para no sobre-vender.
    Retorna (numero_interno, msg_exito).
    """
    if tipo == 'PRESUPUESTO':
        descontar_stock = False
        estado_doc = 'ACTIVO'
    else:
        estado_doc = 'CONFIRMADO'
        
    fecha_actual = datetime.now()
    
    cursor = conn.cursor()
    cursor.execute("BEGIN IMMEDIATE;")
    try:
        # 1. Validar ATP dentro de la transacción
        if tipo == 'PRESUPUESTO' or descontar_stock:
            requeridos = {}
            for item in carrito:
                requeridos[item['codigo']] = requeridos.get(item['codigo'], 0.0) + (
                    item['cantidad'] * item['factor_conversion']
                )
            for codigo, cantidad_requerida in requeridos.items():
                disponible = obtener_stock_producto(conn, codigo)["atp"]
                if cantidad_requerida > disponible:
                    raise ValueError(
                        f"Stock insuficiente para {codigo}: disponibles {disponible:g}, "
                        f"requeridos {cantidad_requerida:g}."
                    )
        
        # 2. Calcular montos
        subtotal_bruto = sum([p['cantidad'] * p['precio_unit_mostrado'] * (1 - (p['descuento'] / 100.0)) for p in carrito])
        subtotal_neto = subtotal_bruto * (1 - (descuento_general / 100.0))
        iva_monto = subtotal_neto * (iva_porcentaje / 100.0) if iva_aplicado else 0.0
        total_operacion = subtotal_neto + iva_monto
        numero_interno = f"{tipo[:3]}-{fecha_actual.strftime('%Y%m%d%H%M%S%f')}"
        
        # 3. Insertar Cabecera
        cursor.execute("""
            INSERT INTO documentos (numero_interno, tipo, estado, fecha_emision, fecha_vencimiento, id_cliente, total_final, subtotal_bruto, descuento_general_porcentaje, iva_aplicado, iva_porcentaje, iva_monto, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            numero_interno, 
            tipo, 
            estado_doc, 
            fecha_actual.strftime("%Y-%m-%d %H:%M:%S"),
            (fecha_actual + timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S") if tipo == 'PRESUPUESTO' else None,
            id_cliente_final,
            total_operacion,
            subtotal_bruto,
            descuento_general,
            1 if iva_aplicado else 0,
            iva_porcentaje,
            iva_monto,
            obs if obs else None
        ))
        id_doc = cursor.lastrowid
        
        # 4. Insertar Detalle e Impactar Stock
        for item in carrito:
            subtotal_item = item['cantidad'] * item['precio_unit_mostrado'] * (1 - (item['descuento'] / 100.0))
            cantidad_base = item['cantidad'] * item['factor_conversion']
            
            cursor.execute("""
                INSERT INTO detalle_documentos (id_documento, codigo_producto, unidad_venta, cantidad_unidad_venta, cantidad_base, precio_unitario, descuento_porcentaje, subtotal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                id_doc, item['codigo'], item['unidad_venta'], item['cantidad'],
                cantidad_base, item['precio_unit_mostrado'], item['descuento'], subtotal_item
            ))
            
            if tipo == 'VENTA' and descontar_stock:
                cursor.execute("""
                    INSERT INTO movimientos_stock (codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora)
                    VALUES (?, 'SALIDA', ?, ?, ?)
                """, (item['codigo'], cantidad_base, id_doc, fecha_actual.strftime("%Y-%m-%d %H:%M:%S")))
            elif tipo == 'PRESUPUESTO':
                cursor.execute("""
                    INSERT INTO compromisos_stock (codigo_producto, id_documento, cantidad_comprometida, fecha_vencimiento, estado)
                    VALUES (?, ?, ?, ?, 'ACTIVO')
                """, (item['codigo'], id_doc, cantidad_base, (fecha_actual + timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")))
                
        conn.commit()
        
        if tipo == 'PRESUPUESTO':
            msg = f"Presupuesto #{numero_interno} generado.\n\nVálido hasta: {(fecha_actual + timedelta(hours=48)).strftime('%d/%m/%Y %H:%M')}"
        else:
            msg = f"Venta #{numero_interno} confirmada con éxito."
            
        return numero_interno, msg
    except Exception as e:
        conn.rollback()
        raise e
