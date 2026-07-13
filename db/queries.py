"""
db/queries.py — Consultas ATP centralizadas.

Provee la fórmula canónica de stock (Available to Promise) para reutilización
entre pantallas sin duplicar lógica.

NOTA: La lógica ATP se encuentra 100% centralizada aquí y es consumida 
activamente por ui/nueva_venta.py y la vista de stock.
"""

# ─── Unidades canónicas ───────────────────────────────────────────────────────
# Par (valor_bd, etiqueta_ui). Único lugar donde se define el conjunto permitido.
UNIDADES_PERMITIDAS = [
    ("u",  "Unidad"),
    ("m2", "m²"),
]


# ─── Helpers de subconsulta ───────────────────────────────────────────────────

def _sq_entradas(alias: str) -> str:
    return (
        f"IFNULL((SELECT SUM(cantidad) FROM movimientos_stock "
        f"WHERE codigo_producto = {alias}.codigo AND tipo_movimiento = 'ENTRADA'), 0.0)"
    )

def _sq_salidas(alias: str) -> str:
    return (
        f"IFNULL((SELECT SUM(cantidad) FROM movimientos_stock "
        f"WHERE codigo_producto = {alias}.codigo AND tipo_movimiento = 'SALIDA'), 0.0)"
    )

def _sq_comprometido(alias: str) -> str:
    return (
        f"IFNULL((SELECT SUM(cantidad_comprometida) FROM compromisos_stock "
        f"WHERE codigo_producto = {alias}.codigo AND estado = 'ACTIVO'), 0.0)"
    )

def subquery_atp(alias: str = "p") -> str:
    """
    Retorna la expresión SQL embebible para calcular el ATP de un producto.

    Uso típico en un SELECT mayor:
        cursor.execute(f"SELECT p.codigo, ({subquery_atp('p')}) AS atp FROM productos p")

    La fórmula es: ENTRADAS - SALIDAS - COMPROMISOS_ACTIVOS
    """
    return (
        f"({_sq_entradas(alias)}"
        f" - {_sq_salidas(alias)}"
        f" - {_sq_comprometido(alias)})"
    )


# ─── Consultas de stock ───────────────────────────────────────────────────────

def obtener_stock_producto(conn, codigo: str) -> dict:
    """
    Calcula stock_fisico, comprometido y atp para un único producto.

    Retorna dict con claves:
        stock_fisico  : ENTRADAS - SALIDAS
        comprometido  : suma de compromisos_stock con estado='ACTIVO'
        atp           : stock_fisico - comprometido

    Compatible con obtener_stock_disponible() de db/conexion.py,
    pero devuelve los tres componentes por separado (útil para la UI de stock).
    """
    c = conn.cursor()
    c.execute("""
        SELECT
            IFNULL((SELECT SUM(cantidad) FROM movimientos_stock
                     WHERE codigo_producto = ? AND tipo_movimiento = 'ENTRADA'), 0.0),
            IFNULL((SELECT SUM(cantidad) FROM movimientos_stock
                     WHERE codigo_producto = ? AND tipo_movimiento = 'SALIDA'), 0.0),
            IFNULL((SELECT SUM(cantidad_comprometida) FROM compromisos_stock
                     WHERE codigo_producto = ? AND estado = 'ACTIVO'), 0.0)
    """, (codigo, codigo, codigo))
    entradas, salidas, comprometido = c.fetchone()
    fisico = entradas - salidas
    return {
        "stock_fisico":  fisico,
        "comprometido":  comprometido,
        "atp":           fisico - comprometido,
    }


def obtener_stocks_todos(conn, incluir_inactivos=False) -> list[dict]:
    """
    Retorna todos los productos con sus métricas de stock calculadas.

    Optimizado para la pantalla Control de Stock (carga completa del catálogo).

    Cada elemento del resultado es un dict con:
        codigo, descripcion, unidad_base, precio_venta, stock_minimo,
        stock_fisico, comprometido, atp, activo
    """
    c = conn.cursor()
    
    where_clause = "WHERE p.activo = 1" if not incluir_inactivos else ""
    
    c.execute(f"""
        SELECT
            p.codigo,
            p.descripcion,
            p.unidad_base,
            p.precio_venta,
            p.stock_minimo,
            p.activo,
            {_sq_entradas('p')} AS entradas,
            {_sq_salidas('p')}  AS salidas,
            {_sq_comprometido('p')} AS comprometido
        FROM productos p
        {where_clause}
        ORDER BY p.descripcion
    """)
    resultado = []
    for codigo, desc, unidad, precio, stk_min, activo, ent, sal, comp in c.fetchall():
        fisico = ent - sal
        resultado.append({
            "codigo":       codigo,
            "descripcion":  desc,
            "unidad_base":  unidad,
            "precio_venta": precio,
            "stock_minimo": stk_min or 0.0,
            "activo":       activo,
            "stock_fisico": fisico,
            "comprometido": comp,
            "atp":          fisico - comp,
        })
    return resultado


def obtener_metricas_globales(conn) -> dict:
    """
    Retorna métricas agregadas para las tarjetas superiores de la pantalla de stock.

        total_productos   : cantidad de productos activos
        valor_inventario  : SUM(stock_fisico * precio_venta) para todos los productos activos
        bajo_stock        : cantidad de productos con atp <= stock_minimo (excluye stk_min=0)
        sin_stock         : cantidad de productos con atp <= 0
    """
    stocks = obtener_stocks_todos(conn)
    total_productos   = len(stocks)
    valor_inventario  = sum(p["stock_fisico"] * p["precio_venta"] for p in stocks)
    bajo_stock        = sum(
        1 for p in stocks
        if p["stock_minimo"] > 0 and p["atp"] <= p["stock_minimo"]
    )
    sin_stock         = sum(1 for p in stocks if p["atp"] <= 0)
    return {
        "total_productos":  total_productos,
        "valor_inventario": valor_inventario,
        "bajo_stock":       bajo_stock,
        "sin_stock":        sin_stock,
    }

def obtener_productos_frecuentes(conn, limite: int = 4, dias: int = 30) -> list[dict]:
    """
    Retorna los productos con mayor cantidad vendida en los últimos X días.
    """
    c = conn.cursor()
    c.execute(f"""
        SELECT 
            p.codigo, 
            p.descripcion, 
            p.unidad_base, 
            p.stock_minimo,
            SUM(dd.cantidad_base) as total_vendido,
            {_sq_entradas('p')} AS entradas,
            {_sq_salidas('p')}  AS salidas,
            {_sq_comprometido('p')} AS comprometido
        FROM detalle_documentos dd
        JOIN documentos d ON dd.id_documento = d.id_documento
        JOIN productos p ON dd.codigo_producto = p.codigo
        WHERE d.tipo = 'VENTA' 
          AND d.estado = 'CONFIRMADO'
          AND d.fecha_emision >= datetime('now', 'localtime', '-{dias} days')
          AND p.activo = 1
        GROUP BY p.codigo, p.descripcion, p.unidad_base, p.stock_minimo
        ORDER BY total_vendido DESC
        LIMIT ?
    """, (limite,))
    
    resultado = []
    for codigo, desc, unidad, stk_min, _, ent, sal, comp in c.fetchall():
        fisico = ent - sal
        resultado.append({
            "codigo":       codigo,
            "descripcion":  desc,
            "unidad_base":  unidad,
            "stock_minimo": stk_min or 0.0,
            "stock_fisico": fisico,
            "comprometido": comp,
            "atp":          fisico - comp,
        })
    return resultado
