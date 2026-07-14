"""
db/queries_presupuestos.py — Consultas centralizadas para el módulo Presupuestos.

Provee operaciones de lectura paginada, métricas (KPIs) y detalles de presupuestos,
respetando el patrón arquitectónico y los estados reales del sistema ATP.
"""

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — MÉTRICAS GLOBALES (KPIs)
# ══════════════════════════════════════════════════════════════════════════════

def obtener_kpis_presupuestos(conn) -> dict:
    """
    Retorna métricas generales de presupuestos para las tarjetas superiores.
    Respeta los estados reales de la BD: 'ACTIVO', 'VENCIDO', 'ANULADO', 'CONFIRMADO'.
    """
    c = conn.cursor()
    c.execute("""
        SELECT
            COUNT(*),
            SUM(CASE WHEN estado = 'ACTIVO' THEN 1 ELSE 0 END),
            SUM(CASE WHEN estado = 'VENCIDO' THEN 1 ELSE 0 END),
            SUM(CASE WHEN estado = 'ANULADO' THEN 1 ELSE 0 END)
        FROM documentos
        WHERE tipo = 'PRESUPUESTO'
    """)
    row = c.fetchone()
    return {
        "total": int(row[0] or 0) if row else 0,
        "activos": int(row[1] or 0) if row else 0,
        "vencidos": int(row[2] or 0) if row else 0,
        "anulados": int(row[3] or 0) if row else 0,
    }

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — LISTADO PAGINADO
# ══════════════════════════════════════════════════════════════════════════════

def obtener_presupuestos_paginados(
    conn,
    filtro: str = "",
    estado: str = "TODOS",         # 'TODOS', 'ACTIVO', 'VENCIDO', 'ANULADO', 'CONFIRMADO'
    fecha_desde: str = None,       # Formato 'YYYY-MM-DD'
    fecha_hasta: str = None,       # Formato 'YYYY-MM-DD'
    pagina: int = 1,
    por_pagina: int = 50
) -> dict:
    """
    Retorna una página de presupuestos con sus atributos principales.
    """
    c = conn.cursor()
    from db.conexion import normalizar_texto_busqueda
    busqueda_norm = normalizar_texto_busqueda(filtro)
    
    clausulas_where = ["d.tipo = 'PRESUPUESTO'"]
    params = []
    
    if busqueda_norm:
        terminos = busqueda_norm.split()
        for term in terminos:
            patron = f"%{term}%"
            clausulas_where.append(
                "(NORMALIZAR(d.numero_interno) LIKE ? OR NORMALIZAR(c.nombre_completo) LIKE ? OR NORMALIZAR(c.cuit_dni) LIKE ? OR NORMALIZAR(d.estado) LIKE ?)"
            )
            params.extend([patron] * 4)
            
    if estado != "TODOS":
        clausulas_where.append("d.estado = ?")
        params.append(estado)
        
    if fecha_desde:
        clausulas_where.append("date(d.fecha_emision) >= ?")
        params.append(fecha_desde)
        
    if fecha_hasta:
        clausulas_where.append("date(d.fecha_emision) <= ?")
        params.append(fecha_hasta)
        
    where_sql = " AND ".join(clausulas_where)
    
    # Conteo Total
    c.execute(f"""
        SELECT COUNT(*)
        FROM documentos d
        LEFT JOIN clientes c ON d.id_cliente = c.id_cliente
        WHERE {where_sql}
    """, params)
    total_filas = c.fetchone()[0]
    
    offset = (pagina - 1) * por_pagina
    
    # Consulta Principal
    c.execute(f"""
        SELECT
            d.id_documento,
            d.numero_interno,
            c.nombre_completo,
            c.cuit_dni,
            d.fecha_emision,
            d.fecha_vencimiento,
            d.total_final,
            d.estado,
            (SELECT COUNT(*) FROM detalle_documentos dd WHERE dd.id_documento = d.id_documento) as cant_items
        FROM documentos d
        LEFT JOIN clientes c ON d.id_cliente = c.id_cliente
        WHERE {where_sql}
        ORDER BY d.fecha_emision DESC
        LIMIT ? OFFSET ?
    """, params + [por_pagina, offset])
    
    filas = []
    for row in c.fetchall():
        filas.append({
            "id_documento": row[0],
            "numero_interno": row[1],
            "cliente": row[2] or "Consumidor Final",
            "cuit_dni": row[3] or "",
            "fecha_emision": row[4],
            "fecha_vencimiento": row[5],
            "total_final": float(row[6] or 0.0),
            "estado": row[7],
            "cant_items": int(row[8] or 0),
        })
        
    total_paginas = max(1, -(-total_filas // por_pagina)) # ceil
    return {
        "filas": filas,
        "total_filas": total_filas,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total_paginas": total_paginas,
    }

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — DETALLE
# ══════════════════════════════════════════════════════════════════════════════

def obtener_detalle_presupuesto(conn, id_documento: int) -> dict | None:
    """
    Retorna el detalle completo de un presupuesto, incluyendo líneas y reservas (ATP).
    """
    c = conn.cursor()
    # 1. Cabecera
    c.execute("""
        SELECT
            d.id_documento,
            d.numero_interno,
            d.estado,
            d.fecha_emision,
            d.fecha_vencimiento,
            d.total_neto,
            d.total_descuento,
            d.total_final,
            d.subtotal_bruto,
            d.descuento_general_porcentaje,
            d.iva_aplicado,
            d.iva_porcentaje,
            d.iva_monto,
            d.observaciones,
            c.id_cliente,
            c.nombre_completo,
            c.cuit_dni,
            c.telefono,
            c.email,
            c.direccion,
            c.ciudad,
            c.condicion_iva
        FROM documentos d
        LEFT JOIN clientes c ON d.id_cliente = c.id_cliente
        WHERE d.id_documento = ? AND d.tipo = 'PRESUPUESTO'
    """, (id_documento,))
    row = c.fetchone()
    if not row:
        return None
        
    cabecera = {
        "id_documento": row[0],
        "numero_interno": row[1],
        "estado": row[2],
        "fecha_emision": row[3],
        "fecha_vencimiento": row[4],
        "total_neto": float(row[5] or 0.0),
        "total_descuento": float(row[6] or 0.0),
        "total_final": float(row[7] or 0.0),
        "subtotal_bruto": float(row[8] or 0.0),
        "descuento_general_porcentaje": float(row[9] or 0.0),
        "iva_aplicado": bool(row[10]),
        "iva_porcentaje": float(row[11] or 0.0),
        "iva_monto": float(row[12] or 0.0),
        "observaciones": row[13] or "",
        "cliente": {
            "id_cliente": row[14],
            "nombre_completo": row[15] or "Consumidor Final",
            "cuit_dni": row[16] or "",
            "telefono": row[17] or "",
            "email": row[18] or "",
            "direccion": row[19] or "",
            "ciudad": row[20] or "",
            "condicion_iva": row[21] or ""
        }
    }
    
    # 2. Detalles de productos
    c.execute("""
        SELECT
            dd.id_detalle,
            dd.codigo_producto,
            p.descripcion,
            dd.unidad_venta,
            dd.cantidad_unidad_venta,
            dd.cantidad_base,
            dd.precio_unitario,
            dd.descuento_porcentaje,
            dd.subtotal
        FROM detalle_documentos dd
        LEFT JOIN productos p ON dd.codigo_producto = p.codigo
        WHERE dd.id_documento = ?
    """, (id_documento,))
    detalles = []
    for drow in c.fetchall():
        detalles.append({
            "id_detalle": drow[0],
            "codigo_producto": drow[1],
            "descripcion": drow[2] or "Producto eliminado",
            "unidad_venta": drow[3],
            "cantidad_unidad_venta": float(drow[4] or 0.0),
            "cantidad_base": float(drow[5] or 0.0),
            "precio_unitario": float(drow[6] or 0.0),
            "descuento_porcentaje": float(drow[7] or 0.0),
            "subtotal": float(drow[8] or 0.0)
        })
    cabecera["detalles"] = detalles
    
    # 3. Compromisos de Stock (Reservas ATP)
    c.execute("""
        SELECT
            cs.id_compromiso,
            cs.codigo_producto,
            cs.cantidad_comprometida,
            cs.estado,
            cs.fecha_vencimiento
        FROM compromisos_stock cs
        WHERE cs.id_documento = ?
    """, (id_documento,))
    compromisos = []
    for crow in c.fetchall():
        compromisos.append({
            "id_compromiso": crow[0],
            "codigo_producto": crow[1],
            "cantidad_comprometida": float(crow[2] or 0.0),
            "estado": crow[3],
            "fecha_vencimiento": crow[4]
        })
    cabecera["compromisos"] = compromisos
    
    return cabecera

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — TRANSACCIONES OPERATIVAS
# ══════════════════════════════════════════════════════════════════════════════

def anular_presupuesto(conn, id_documento: int) -> bool:
    """
    Anula un presupuesto en estado ACTIVO.
    - Cambia el estado del documento a 'ANULADO'.
    - Libera los compromisos de stock relacionados (estado 'LIBERADO').
    Todo ocurre en una transacción atómica.
    No toca el stock físico.
    """
    c = conn.cursor()
    try:
        c.execute("BEGIN TRANSACTION;")
        
        # 1. Verificar estado actual
        c.execute("SELECT estado FROM documentos WHERE id_documento = ? AND tipo = 'PRESUPUESTO'", (id_documento,))
        row = c.fetchone()
        if not row:
            raise ValueError("El presupuesto no existe.")
        if row[0] != 'ACTIVO':
            raise ValueError(f"El presupuesto está en estado {row[0]}, solo se pueden anular presupuestos ACTIVOS.")
            
        # 2. Liberar compromisos de ATP
        c.execute("""
            UPDATE compromisos_stock
            SET estado = 'LIBERADO'
            WHERE id_documento = ? AND estado = 'ACTIVO'
        """, (id_documento,))
        
        # 3. Anular documento (cabecera)
        c.execute("""
            UPDATE documentos
            SET estado = 'ANULADO'
            WHERE id_documento = ?
        """, (id_documento,))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e

def confirmar_presupuesto(conn, id_documento: int) -> str:
    """
    Confirma un presupuesto ACTIVO como venta.
    - Cambia el estado del documento a 'CONFIRMADO'.
    - Consume los compromisos de stock ('CONSUMIDO').
    - Registra las salidas en movimientos_stock (stock físico).
    Todo ocurre en una transacción atómica.
    """
    c = conn.cursor()
    from datetime import datetime
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        c.execute("BEGIN IMMEDIATE;")
        
        # 1. Verificar estado actual
        c.execute("SELECT estado, numero_interno FROM documentos WHERE id_documento = ? AND tipo = 'PRESUPUESTO'", (id_documento,))
        row = c.fetchone()
        if not row:
            raise ValueError("El presupuesto no existe.")
        if row[0] != 'ACTIVO':
            raise ValueError(f"El presupuesto está en estado {row[0]}, solo se pueden confirmar presupuestos ACTIVOS.")
            
        numero_interno = row[1]
        
        # 2. Obtener compromisos a consumir
        c.execute("""
            SELECT id_compromiso, codigo_producto, cantidad_comprometida 
            FROM compromisos_stock 
            WHERE id_documento = ? AND estado = 'ACTIVO'
        """, (id_documento,))
        compromisos = c.fetchall()
        
        # 3. Consumir compromisos y generar salidas físicas
        for comp in compromisos:
            id_comp, codigo, cantidad = comp
            
            # Cambiar estado del compromiso a CONSUMIDO
            c.execute("""
                UPDATE compromisos_stock
                SET estado = 'CONSUMIDO'
                WHERE id_compromiso = ?
            """, (id_comp,))
            
            # Generar movimiento de salida real
            c.execute("""
                INSERT INTO movimientos_stock (codigo_producto, tipo_movimiento, cantidad, id_documento_origen, fecha_hora)
                VALUES (?, 'SALIDA', ?, ?, ?)
            """, (codigo, cantidad, id_documento, fecha_actual))
            
        # 4. Cambiar estado del documento a CONFIRMADO
        c.execute("""
            UPDATE documentos
            SET estado = 'CONFIRMADO'
            WHERE id_documento = ?
        """, (id_documento,))
        
        conn.commit()
        return numero_interno
    except Exception as e:
        conn.rollback()
        raise e
