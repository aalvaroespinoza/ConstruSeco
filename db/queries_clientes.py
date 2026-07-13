"""
db/queries_clientes.py — Consultas centralizadas para el módulo Clientes.

Provee todas las operaciones de lectura y escritura sobre las tablas:
  - clientes
  - contactos_cliente
  - notas_cliente
  - documentos (historial y métricas calculadas)

REGLAS:
- Ningún archivo UI importa SQL directamente; usan estas funciones.
- Ningún dato derivado (totales, promedios) se almacena; se calcula en tiempo real.
- Las operaciones compuestas se envuelven en transacciones explícitas.
- La paginación se implementa en SQL (LIMIT / OFFSET), no en Python.
"""

from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — MÉTRICAS GLOBALES
# ══════════════════════════════════════════════════════════════════════════════

def obtener_metricas_clientes(conn) -> dict:
    """
    Calcula en tiempo real las métricas del encabezado de la pestaña Clientes.

    Retorna un dict con:
        total           : cantidad total de clientes registrados
        activos         : clientes con activo = 1
        con_compras     : clientes distintos que tienen al menos una VENTA CONFIRMADA
        ventas_mes      : suma de total_final de VENTAS CONFIRMADAS del mes en curso
        ticket_promedio : promedio de total_final de todas las VENTAS CONFIRMADAS con cliente
    """
    c = conn.cursor()
    c.execute("""
        SELECT
            COUNT(*),
            IFNULL(SUM(activo), 0),
            (SELECT COUNT(DISTINCT id_cliente)
             FROM documentos
             WHERE tipo = 'VENTA'
               AND estado = 'CONFIRMADO'
               AND id_cliente IS NOT NULL),
            (SELECT IFNULL(SUM(total_final), 0.0)
             FROM documentos
             WHERE tipo = 'VENTA'
               AND estado = 'CONFIRMADO'
               AND id_cliente IS NOT NULL
               AND strftime('%Y-%m', fecha_emision)
                   = strftime('%Y-%m', 'now', 'localtime')),
            (SELECT IFNULL(AVG(total_final), 0.0)
             FROM documentos
             WHERE tipo = 'VENTA'
               AND estado = 'CONFIRMADO'
               AND id_cliente IS NOT NULL)
        FROM clientes
    """)
    total, activos, con_compras, ventas_mes, ticket_promedio = c.fetchone()
    return {
        "total":           int(total or 0),
        "activos":         int(activos or 0),
        "con_compras":     int(con_compras or 0),
        "ventas_mes":      float(ventas_mes or 0.0),
        "ticket_promedio": float(ticket_promedio or 0.0),
    }


def obtener_ciudades(conn) -> list[str]:
    """
    Retorna una lista con todas las ciudades distintas registradas en clientes,
    ordenadas alfabéticamente (ignorando vacías/nulas).
    """
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT ciudad
        FROM clientes
        WHERE ciudad IS NOT NULL AND ciudad != ''
        ORDER BY ciudad
    """)
    return [row[0] for row in c.fetchall()]


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — LISTADO PAGINADO
# ══════════════════════════════════════════════════════════════════════════════

def obtener_clientes(
    conn,
    filtro: str = "",
    estado: str = "TODOS",         # 'TODOS', 'ACTIVOS', 'INACTIVOS'
    con_compras: str = "TODOS",    # 'TODOS', 'SI', 'NO'
    ciudad: str = "TODAS",
    condicion_iva: str = "TODAS",
    pagina: int = 1,
    por_pagina: int = 50,
    orden: str = "nombre_completo",
) -> dict:
    """
    Retorna una página de clientes con sus métricas calculadas.
    """
    columnas_permitidas = {"nombre_completo", "ciudad", "total_gastado", "id_cliente"}
    if orden not in columnas_permitidas:
        orden = "nombre_completo"

    c = conn.cursor()
    from db.conexion import normalizar_texto_busqueda
    busqueda_norm = normalizar_texto_busqueda(filtro)
    
    clausulas_where = []
    params = []
    
    if busqueda_norm:
        terminos = busqueda_norm.split()
        for term in terminos:
            patron = f"%{term}%"
            clausulas_where.append(
                "(NORMALIZAR(c.nombre_completo) LIKE ? OR NORMALIZAR(c.cuit_dni) LIKE ? OR NORMALIZAR(c.telefono) LIKE ? OR NORMALIZAR(c.email) LIKE ? OR NORMALIZAR(c.ciudad) LIKE ? OR NORMALIZAR(c.direccion) LIKE ? OR NORMALIZAR(c.condicion_iva) LIKE ? OR EXISTS (SELECT 1 FROM notas_cliente n WHERE n.id_cliente = c.id_cliente AND NORMALIZAR(n.contenido) LIKE ?))"
            )
            params.extend([patron] * 8)
    else:
        # Dummy condition if no search text
        clausulas_where.append("1=1")

    if estado == "ACTIVOS":
        clausulas_where.append("c.activo = 1")
    elif estado == "INACTIVOS":
        clausulas_where.append("c.activo = 0")

    if ciudad != "TODAS":
        clausulas_where.append("c.ciudad = ?")
        params.append(ciudad)

    if condicion_iva != "TODAS":
        clausulas_where.append("c.condicion_iva = ?")
        params.append(condicion_iva)

    if con_compras == "SI":
        clausulas_where.append("EXISTS (SELECT 1 FROM documentos d WHERE d.id_cliente = c.id_cliente AND d.tipo = 'VENTA' AND d.estado = 'CONFIRMADO')")
    elif con_compras == "NO":
        clausulas_where.append("NOT EXISTS (SELECT 1 FROM documentos d WHERE d.id_cliente = c.id_cliente AND d.tipo = 'VENTA' AND d.estado = 'CONFIRMADO')")

    where_sql = " AND ".join(clausulas_where)

    # Total de filas que coinciden (para la paginación)
    c.execute(f"""
        SELECT COUNT(*)
        FROM clientes c
        WHERE {where_sql}
    """, params)
    total_filas = c.fetchone()[0]

    offset = (pagina - 1) * por_pagina

    # Reusamos params para la consulta principal
    params.extend([por_pagina, offset])

    c.execute(f"""
        SELECT
            c.id_cliente,
            c.nombre_completo,
            c.cuit_dni,
            c.email,
            c.telefono,
            c.ciudad,
            c.activo,
            c.condicion_iva,
            (SELECT COUNT(*)
             FROM documentos d
             WHERE d.id_cliente = c.id_cliente
               AND d.tipo = 'VENTA'
               AND d.estado = 'CONFIRMADO') AS total_compras,
            (SELECT IFNULL(SUM(d.total_final), 0.0)
             FROM documentos d
             WHERE d.id_cliente = c.id_cliente
               AND d.tipo = 'VENTA'
               AND d.estado = 'CONFIRMADO') AS total_gastado,
            (SELECT MAX(d.fecha_emision)
             FROM documentos d
             WHERE d.id_cliente = c.id_cliente
               AND d.tipo = 'VENTA'
               AND d.estado = 'CONFIRMADO') AS ultima_compra
        FROM clientes c
        WHERE {where_sql}
        ORDER BY {orden}
        LIMIT ? OFFSET ?
    """, params)

    filas = []
    for row in c.fetchall():
        filas.append({
            "id_cliente":    row[0],
            "nombre":        row[1] or "",
            "cuit_dni":      row[2] or "",
            "email":         row[3] or "",
            "telefono":      row[4] or "",
            "ciudad":        row[5] or "",
            "activo":        bool(row[6]),
            "condicion_iva": row[7] or "Consumidor Final",
            "total_compras": int(row[8] or 0),
            "total_gastado": float(row[9] or 0.0),
            "ultima_compra": row[10] or None,
        })

    total_paginas = max(1, -(-total_filas // por_pagina))  # ceil division
    return {
        "filas":        filas,
        "total_filas":  total_filas,
        "pagina":       pagina,
        "por_pagina":   por_pagina,
        "total_paginas": total_paginas,
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — DETALLE DE UN CLIENTE
# ══════════════════════════════════════════════════════════════════════════════

def obtener_detalle_cliente(conn, id_cliente: int) -> dict | None:
    """
    Retorna todos los datos de un cliente junto con sus métricas calculadas.
    Retorna None si el cliente no existe.

    El dict incluye:
        id_cliente, nombre, cuit_dni, email, telefono, ciudad, direccion,
        condicion_iva, activo,
        total_compras, total_gastado, ticket_promedio,
        ventas_mes_actual, ultima_compra,
        presupuestos_activos
    """
    c = conn.cursor()
    c.execute("""
        SELECT
            c.id_cliente,
            c.nombre_completo,
            c.cuit_dni,
            c.email,
            c.telefono,
            c.ciudad,
            c.direccion,
            c.condicion_iva,
            c.activo,
            -- Métricas calculadas
            (SELECT COUNT(*)
             FROM documentos d
             WHERE d.id_cliente = c.id_cliente
               AND d.tipo = 'VENTA' AND d.estado = 'CONFIRMADO') AS total_compras,
            (SELECT IFNULL(SUM(d.total_final), 0.0)
             FROM documentos d
             WHERE d.id_cliente = c.id_cliente
               AND d.tipo = 'VENTA' AND d.estado = 'CONFIRMADO') AS total_gastado,
            (SELECT IFNULL(AVG(d.total_final), 0.0)
             FROM documentos d
             WHERE d.id_cliente = c.id_cliente
               AND d.tipo = 'VENTA' AND d.estado = 'CONFIRMADO') AS ticket_promedio,
            (SELECT IFNULL(SUM(d.total_final), 0.0)
             FROM documentos d
             WHERE d.id_cliente = c.id_cliente
               AND d.tipo = 'VENTA' AND d.estado = 'CONFIRMADO'
               AND strftime('%Y-%m', d.fecha_emision)
                   = strftime('%Y-%m', 'now', 'localtime')) AS ventas_mes_actual,
            (SELECT MAX(d.fecha_emision)
             FROM documentos d
             WHERE d.id_cliente = c.id_cliente
               AND d.tipo = 'VENTA' AND d.estado = 'CONFIRMADO') AS ultima_compra,
            (SELECT COUNT(*)
             FROM documentos d
             WHERE d.id_cliente = c.id_cliente
               AND d.tipo = 'PRESUPUESTO' AND d.estado = 'ACTIVO') AS presupuestos_activos
        FROM clientes c
        WHERE c.id_cliente = ?
    """, (id_cliente,))
    row = c.fetchone()
    if row is None:
        return None
    return {
        "id_cliente":          row[0],
        "nombre":              row[1] or "",
        "cuit_dni":            row[2] or "",
        "email":               row[3] or "",
        "telefono":            row[4] or "",
        "ciudad":              row[5] or "",
        "direccion":           row[6] or "",
        "condicion_iva":       row[7] or "Consumidor Final",
        "activo":              bool(row[8]),
        "total_compras":       int(row[9] or 0),
        "total_gastado":       float(row[10] or 0.0),
        "ticket_promedio":     float(row[11] or 0.0),
        "ventas_mes_actual":   float(row[12] or 0.0),
        "ultima_compra":       row[13] or None,
        "presupuestos_activos": int(row[14] or 0),
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — HISTORIAL Y ACTIVIDAD RECIENTE
# ══════════════════════════════════════════════════════════════════════════════

def obtener_historial_cliente(conn, id_cliente: int, limite: int = 50) -> list[dict]:
    """
    Retorna el historial de documentos (VENTA y PRESUPUESTO) del cliente,
    ordenados del más reciente al más antiguo.

    No incluye COMPRA ni AJUSTE ya que no son generados por el cliente.
    """
    c = conn.cursor()
    c.execute("""
        SELECT
            d.id_documento,
            d.numero_interno,
            d.tipo,
            d.estado,
            d.fecha_emision,
            d.fecha_vencimiento,
            d.total_final,
            d.total_descuento,
            d.observaciones
        FROM documentos d
        WHERE d.id_cliente = ?
          AND d.tipo IN ('VENTA', 'PRESUPUESTO')
        ORDER BY d.fecha_emision DESC
        LIMIT ?
    """, (id_cliente, limite))
    resultado = []
    for row in c.fetchall():
        resultado.append({
            "id_documento":      row[0],
            "numero_interno":    row[1],
            "tipo":              row[2],
            "estado":            row[3],
            "fecha_emision":     row[4],
            "fecha_vencimiento": row[5],
            "total_final":       float(row[6] or 0.0),
            "total_descuento":   float(row[7] or 0.0),
            "observaciones":     row[8] or "",
        })
    return resultado


def obtener_actividad_reciente_cliente(conn, id_cliente: int, limite: int = 5) -> list[dict]:
    """
    Retorna los últimos N documentos del cliente para el panel lateral.
    Subconjunto liviano de obtener_historial_cliente.
    """
    return obtener_historial_cliente(conn, id_cliente, limite=limite)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — CRUD DE CLIENTES
# ══════════════════════════════════════════════════════════════════════════════

def guardar_cliente(conn, datos: dict) -> int:
    """
    Inserta un nuevo cliente. Retorna el id_cliente generado.

    El dict datos puede contener:
        nombre_completo (obligatorio), cuit_dni, telefono, email,
        ciudad, direccion, condicion_iva, activo

    Lanza Exception si falla (el llamador debe capturarla para mostrar error en UI).
    """
    c = conn.cursor()
    c.execute("""
        INSERT INTO clientes
            (nombre_completo, cuit_dni, telefono, email, ciudad, direccion, condicion_iva, activo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datos.get("nombre_completo", "").strip(),
        datos.get("cuit_dni") or None,
        datos.get("telefono") or None,
        datos.get("email") or None,
        datos.get("ciudad") or None,
        datos.get("direccion") or None,
        datos.get("condicion_iva") or "Consumidor Final",
        int(datos.get("activo", 1)),
    ))
    conn.commit()
    return c.lastrowid


def actualizar_cliente(conn, id_cliente: int, datos: dict) -> bool:
    """
    Actualiza los datos de un cliente existente.
    Retorna True si se modificó exactamente 1 fila, False en caso contrario.
    """
    c = conn.cursor()
    c.execute("""
        UPDATE clientes SET
            nombre_completo = ?,
            cuit_dni        = ?,
            telefono        = ?,
            email           = ?,
            ciudad          = ?,
            direccion       = ?,
            condicion_iva   = ?
        WHERE id_cliente = ?
    """, (
        datos.get("nombre_completo", "").strip(),
        datos.get("cuit_dni") or None,
        datos.get("telefono") or None,
        datos.get("email") or None,
        datos.get("ciudad") or None,
        datos.get("direccion") or None,
        datos.get("condicion_iva") or "Consumidor Final",
        id_cliente,
    ))
    conn.commit()
    return c.rowcount == 1


def desactivar_cliente(conn, id_cliente: int) -> bool:
    """
    Marca el cliente como inactivo (soft-delete).
    No elimina el cliente ni sus documentos asociados.
    Retorna True si se modificó la fila.
    """
    c = conn.cursor()
    c.execute(
        "UPDATE clientes SET activo = 0 WHERE id_cliente = ?",
        (id_cliente,)
    )
    conn.commit()
    return c.rowcount == 1


def reactivar_cliente(conn, id_cliente: int) -> bool:
    """Reactiva un cliente previamente desactivado."""
    c = conn.cursor()
    c.execute(
        "UPDATE clientes SET activo = 1 WHERE id_cliente = ?",
        (id_cliente,)
    )
    conn.commit()
    return c.rowcount == 1


def eliminar_cliente(conn, id_cliente: int) -> bool:
    """
    Elimina físicamente un cliente SI no tiene documentos asociados.
    Si tiene documentos, la FK ON DELETE SET NULL los preserva (con id_cliente=NULL),
    pero se recomienda verificar antes de llamar a esta función.

    Retorna True si se eliminó, False si no existía.
    Lanza Exception si la BD rechaza la operación por integridad referencial.
    """
    c = conn.cursor()
    c.execute("DELETE FROM clientes WHERE id_cliente = ?", (id_cliente,))
    conn.commit()
    return c.rowcount == 1


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — CONTACTOS
# ══════════════════════════════════════════════════════════════════════════════

def obtener_contactos_cliente(conn, id_cliente: int) -> list[dict]:
    """
    Retorna todos los contactos asociados al cliente.
    El contacto principal aparece primero.
    """
    c = conn.cursor()
    c.execute("""
        SELECT id_contacto, id_cliente, nombre, cargo, telefono, email, principal
        FROM contactos_cliente
        WHERE id_cliente = ?
        ORDER BY principal DESC, nombre
    """, (id_cliente,))
    resultado = []
    for row in c.fetchall():
        resultado.append({
            "id_contacto": row[0],
            "id_cliente":  row[1],
            "nombre":      row[2] or "",
            "cargo":       row[3] or "",
            "telefono":    row[4] or "",
            "email":       row[5] or "",
            "principal":   bool(row[6]),
        })
    return resultado


def guardar_contacto(conn, id_cliente: int, datos: dict) -> int:
    """
    Inserta un nuevo contacto. Retorna id_contacto generado.
    Si datos["principal"] == True, primero limpia el flag principal de los demás.
    """
    c = conn.cursor()
    if datos.get("principal"):
        c.execute(
            "UPDATE contactos_cliente SET principal = 0 WHERE id_cliente = ?",
            (id_cliente,)
        )
    c.execute("""
        INSERT INTO contactos_cliente
            (id_cliente, nombre, cargo, telefono, email, principal)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        id_cliente,
        datos.get("nombre", "").strip(),
        datos.get("cargo") or None,
        datos.get("telefono") or None,
        datos.get("email") or None,
        int(bool(datos.get("principal", False))),
    ))
    conn.commit()
    return c.lastrowid


def actualizar_contacto(conn, id_contacto: int, datos: dict) -> bool:
    """Actualiza un contacto existente. Retorna True si se modificó."""
    c = conn.cursor()
    id_cliente = datos.get("id_cliente")
    if datos.get("principal") and id_cliente:
        c.execute(
            "UPDATE contactos_cliente SET principal = 0 WHERE id_cliente = ?",
            (id_cliente,)
        )
    c.execute("""
        UPDATE contactos_cliente SET
            nombre    = ?,
            cargo     = ?,
            telefono  = ?,
            email     = ?,
            principal = ?
        WHERE id_contacto = ?
    """, (
        datos.get("nombre", "").strip(),
        datos.get("cargo") or None,
        datos.get("telefono") or None,
        datos.get("email") or None,
        int(bool(datos.get("principal", False))),
        id_contacto,
    ))
    conn.commit()
    return c.rowcount == 1


def eliminar_contacto(conn, id_contacto: int) -> bool:
    """Elimina un contacto. Retorna True si se eliminó."""
    c = conn.cursor()
    c.execute("DELETE FROM contactos_cliente WHERE id_contacto = ?", (id_contacto,))
    conn.commit()
    return c.rowcount == 1


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — NOTAS
# ══════════════════════════════════════════════════════════════════════════════

def obtener_notas_cliente(conn, id_cliente: int) -> list[dict]:
    """Retorna las notas del cliente, ordenadas de la más reciente a la más antigua."""
    c = conn.cursor()
    c.execute("""
        SELECT id_nota, id_cliente, contenido, fecha_hora
        FROM notas_cliente
        WHERE id_cliente = ?
        ORDER BY fecha_hora DESC
    """, (id_cliente,))
    resultado = []
    for row in c.fetchall():
        resultado.append({
            "id_nota":    row[0],
            "id_cliente": row[1],
            "contenido":  row[2] or "",
            "fecha_hora": row[3] or "",
        })
    return resultado


def guardar_nota(conn, id_cliente: int, contenido: str) -> int:
    """
    Inserta una nueva nota con timestamp actual (localtime).
    Retorna el id_nota generado.
    """
    c = conn.cursor()
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO notas_cliente (id_cliente, contenido, fecha_hora)
        VALUES (?, ?, ?)
    """, (id_cliente, contenido.strip(), fecha_hora))
    conn.commit()
    return c.lastrowid


def actualizar_nota(conn, id_nota: int, contenido: str) -> bool:
    """Edita el contenido de una nota existente. Retorna True si se modificó."""
    c = conn.cursor()
    c.execute(
        "UPDATE notas_cliente SET contenido = ? WHERE id_nota = ?",
        (contenido.strip(), id_nota)
    )
    conn.commit()
    return c.rowcount == 1


def eliminar_nota(conn, id_nota: int) -> bool:
    """Elimina una nota. Retorna True si se eliminó."""
    c = conn.cursor()
    c.execute("DELETE FROM notas_cliente WHERE id_nota = ?", (id_nota,))
    conn.commit()
    return c.rowcount == 1


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 8 — UTILIDADES DE INTEGRIDAD
# ══════════════════════════════════════════════════════════════════════════════

def tiene_documentos(conn, id_cliente: int) -> bool:
    """
    Devuelve True si el cliente tiene al menos un documento asociado.

    Usada antes de intentar una eliminación física para proteger el historial
    comercial: si el cliente tiene documentos, se debe preferir desactivar.
    """
    c = conn.cursor()
    c.execute(
        "SELECT COUNT(*) FROM documentos WHERE id_cliente = ?",
        (id_cliente,)
    )
    return c.fetchone()[0] > 0
