import sqlite3

import os

import unicodedata
import logging
from utils.paths import get_data_path



def normalizar_texto_busqueda(valor) -> str:

    if valor is None:

        return ""

    texto = str(valor).strip().casefold()

    texto = unicodedata.normalize('NFD', texto)

    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')

    return ' '.join(texto.split())



def coincide_busqueda(texto_busqueda: str, campos: list) -> bool:

    """

    Estrategia centralizada de búsqueda en memoria.

    Verifica que todos los términos de la búsqueda existan en alguno de los campos.

    """

    texto = normalizar_texto_busqueda(texto_busqueda)

    if not texto:

        return True

    

    texto_campos = " ".join([normalizar_texto_busqueda(c) for c in campos if c is not None])

    

    for termino in texto.split():

        if termino not in texto_campos:

            return False

    return True





def obtener_conexion():

    """

    # Establece la conexión con la base de datos local y activa las claves foráneas.

    # En un sistema ATP es vital garantizar que no queden registros huérfanos.

    """

    # Creamos la base de datos en la raíz del proyecto

    base_datos = get_data_path("corralon_profesional.db")

    conn = sqlite3.connect(base_datos)

    

    # [CONFIGURACIÓN CRÍTICA]: Activar la integridad referencial.

    # Evita que se elimine un producto si tiene movimientos de stock o facturas asociadas.

    conn.execute("PRAGMA foreign_keys = ON;")

    conn.execute("PRAGMA busy_timeout = 5000;")

    conn.execute("PRAGMA journal_mode=WAL;")

    

    # Registrar función de normalización de búsquedas para SQLite

    conn.create_function("NORMALIZAR", 1, normalizar_texto_busqueda)

    

    return conn



def inicializar_base_datos():

    """

    # Crea el motor transaccional de documentos e inventario ATP.

    # Si las tablas no existen, se generan con estricta integridad de datos.

    """

    conn = obtener_conexion()

    cursor = conn.cursor()

    

    # 1. TABLA DE PRODUCTOS (Catálogo Maestro)

    # NOTA: Ya no almacenamos 'stock' estático aquí. En una arquitectura ATP (Available to Promise),

    # el stock neto se calcula dinámicamente consultando el ledger de movimientos (entradas/salidas)

    # y restando los compromisos (presupuestos activos). Esto previene condiciones de carrera

    # y lecturas fantasma en escenarios de alta concurrencia.

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS productos (

            codigo TEXT PRIMARY KEY,

            descripcion TEXT UNIQUE NOT NULL,

            unidad_base TEXT DEFAULT 'u',

            precio_venta REAL NOT NULL,

            stock_minimo REAL DEFAULT 0.0,

            activo INTEGER DEFAULT 1

        )

    """)

    

    # 2. TABLA CONVERSIONES_UNIDAD (Transformación de Formatos)

    # NOTA: Resuelve el problema de vender en distintas métricas físicas.

    # Ejemplo: En la BD el stock se guarda en 'm2', pero el cliente compra en 'placas'.

    # El factor de conversión permite al sistema saber cuánto equivale 1 placa en m2.

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS conversiones_unidad (

            id_conversion INTEGER PRIMARY KEY AUTOINCREMENT,

            codigo_producto TEXT NOT NULL,

            unidad_venta TEXT NOT NULL,

            factor_conversion REAL NOT NULL,

            operacion TEXT NOT NULL CHECK(operacion IN ('MULTIPLICAR', 'DIVIDIR')),

            FOREIGN KEY(codigo_producto) REFERENCES productos(codigo) ON DELETE CASCADE

        )

    """)

    

    # Tabla Clientes (Mantenida por integridad estructural)

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS clientes (

            id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,

            nombre_completo TEXT NOT NULL,

            cuit_dni TEXT UNIQUE,

            telefono TEXT,

            email TEXT

        )

    """)



    # 3. TABLA DOCUMENTOS (Unificación de Comprobantes)

    # NOTA: Unifica todo comprobante comercial (Presupuesto, Venta, Compra, Ajuste)

    # en una sola tabla cabecera. Es la piedra angular de un ERP.

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS documentos (

            id_documento INTEGER PRIMARY KEY AUTOINCREMENT,

            numero_interno TEXT UNIQUE NOT NULL,

            tipo TEXT NOT NULL CHECK(tipo IN ('PRESUPUESTO', 'VENTA', 'COMPRA', 'AJUSTE')),

            estado TEXT NOT NULL CHECK(estado IN ('BORRADOR', 'ACTIVO', 'CONFIRMADO', 'VENCIDO', 'ANULADO')),

            fecha_emision TEXT NOT NULL,

            fecha_vencimiento TEXT,

            id_cliente INTEGER,
                   
            observaciones TEXT,

            total_neto REAL NOT NULL DEFAULT 0.0,

            total_descuento REAL NOT NULL DEFAULT 0.0,

            total_final REAL NOT NULL DEFAULT 0.0,

            FOREIGN KEY(id_cliente) REFERENCES clientes(id_cliente) ON DELETE SET NULL

        )

    """)

    

    # 4. TABLA DETALLE_DOCUMENTOS (Cuerpo del Documento)

    # NOTA: Almacena el snapshot exacto de la línea de venta, incluyendo la unidad física vendida,

    # la conversión exacta en unidad base (para descontar stock real), y descuentos aplicados.

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS detalle_documentos (

            id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,

            id_documento INTEGER NOT NULL,

            codigo_producto TEXT NOT NULL,

            unidad_venta TEXT NOT NULL,

            cantidad_unidad_venta REAL NOT NULL,

            cantidad_base REAL NOT NULL,

            precio_unitario REAL NOT NULL,

            descuento_porcentaje REAL DEFAULT 0.0,

            subtotal REAL NOT NULL,

            FOREIGN KEY(id_documento) REFERENCES documentos(id_documento) ON DELETE CASCADE,

            FOREIGN KEY(codigo_producto) REFERENCES productos(codigo)

        )

    """)

    

    # 5. TABLA MOVIMIENTOS_STOCK (Ledger Inmutable de Depósito)

    # NOTA: Aquí NUNCA se hace UPDATE sobre la cantidad. Es un libro mayor contable (Append-Only).

    # Las auditorías de stock cuadran perfectamente agrupando entradas y restando salidas.

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS movimientos_stock (

            id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,

            codigo_producto TEXT NOT NULL,

            tipo_movimiento TEXT NOT NULL CHECK(tipo_movimiento IN ('ENTRADA', 'SALIDA')),

            cantidad REAL NOT NULL,

            id_documento_origen INTEGER NOT NULL,

            fecha_hora TEXT NOT NULL,

            FOREIGN KEY(codigo_producto) REFERENCES productos(codigo),

            FOREIGN KEY(id_documento_origen) REFERENCES documentos(id_documento)

        )

    """)

    

    # 6. TABLA COMPROMISOS_STOCK (Reservas de Presupuestos)

    # NOTA: En un modelo ATP, si haces un presupuesto, ese material queda "reservado" temporalmente

    # para que otro vendedor no venda el mismo stock. Si el presupuesto vence o se concreta, el estado cambia.

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS compromisos_stock (

            id_compromiso INTEGER PRIMARY KEY AUTOINCREMENT,

            codigo_producto TEXT NOT NULL,

            id_documento INTEGER NOT NULL,

            cantidad_comprometida REAL NOT NULL,

            fecha_vencimiento TEXT NOT NULL,

            estado TEXT NOT NULL CHECK(estado IN ('ACTIVO', 'LIBERADO', 'CONSUMIDO')),

            FOREIGN KEY(codigo_producto) REFERENCES productos(codigo),

            FOREIGN KEY(id_documento) REFERENCES documentos(id_documento) ON DELETE CASCADE

        )

    """)

    

    # ── Índices de rendimiento para subconsultas ATP ─────────────────────────

    # Cubren exactamente los patrones de filtrado usados en la fórmula ATP:

    #   WHERE codigo_producto = ? AND tipo_movimiento = 'ENTRADA'/'SALIDA'

    #   WHERE codigo_producto = ? AND estado = 'ACTIVO'

    # CREATE INDEX IF NOT EXISTS es idempotente: no falla si ya existen.

    cursor.execute("""

        CREATE INDEX IF NOT EXISTS idx_mov_codigo_tipo

        ON movimientos_stock(codigo_producto, tipo_movimiento)

    """)

    cursor.execute("""

        CREATE INDEX IF NOT EXISTS idx_comp_codigo_estado

        ON compromisos_stock(codigo_producto, estado)

    """)



    # ── Módulo Clientes: migraciones y tablas complementarias ────────────────

    _migrar_clientes(cursor)



    conn.commit()

    conn.close()

    print("Motor ERP/ATP inicializado con éxito.")





def _migrar_clientes(cursor):

    """

    Migración idempotente de la infraestructura de datos de Clientes.



    Extiende la tabla clientes con columnas adicionales necesarias para la

    pestaña Clientes, y crea las tablas contactos_cliente y notas_cliente.



    Todas las operaciones son idempotentes: se ejecutan con seguridad en cada

    arranque sin importar si ya se aplicaron previamente.



    Esta función centraliza TODO el DDL relacionado con clientes. Ningún

    archivo de UI debe ejecutar ALTER TABLE ni CREATE TABLE.

    """

    # ── 1. Columnas adicionales en tabla clientes ─────────────────────────

    cursor.execute("PRAGMA table_info(clientes)")

    columnas_existentes = {row[1] for row in cursor.fetchall()}



    if "activo" not in columnas_existentes:

        cursor.execute(

            "ALTER TABLE clientes ADD COLUMN activo INTEGER DEFAULT 1"

        )

    if "ciudad" not in columnas_existentes:

        cursor.execute(

            "ALTER TABLE clientes ADD COLUMN ciudad TEXT"

        )

    if "direccion" not in columnas_existentes:

        cursor.execute(

            "ALTER TABLE clientes ADD COLUMN direccion TEXT"

        )

    if "condicion_iva" not in columnas_existentes:

        cursor.execute(

            "ALTER TABLE clientes ADD COLUMN condicion_iva "

            "TEXT DEFAULT 'Consumidor Final'"

        )



    # ── 2. Tabla contactos_cliente ────────────────────────────────────────

    # Permite registrar múltiples contactos por cliente (persona de contacto,

    # cargo, teléfono directo, email propio). El campo 'principal' distingue

    # al contacto de referencia principal del resto.

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS contactos_cliente (

            id_contacto INTEGER PRIMARY KEY AUTOINCREMENT,

            id_cliente  INTEGER NOT NULL,

            nombre      TEXT NOT NULL,

            cargo       TEXT,

            telefono    TEXT,

            email       TEXT,

            principal   INTEGER DEFAULT 0

                        CHECK(principal IN (0, 1)),

            FOREIGN KEY(id_cliente)

                REFERENCES clientes(id_cliente) ON DELETE CASCADE

        )

    """)



    # ── 3. Tabla notas_cliente ────────────────────────────────────────────

    # Observaciones internas por cliente (acuerdos, condiciones especiales,

    # historial de interacciones, etc.). Append-only recomendado; el DELETE

    # está disponible pero no es el flujo principal.

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS notas_cliente (

            id_nota    INTEGER PRIMARY KEY AUTOINCREMENT,

            id_cliente INTEGER NOT NULL,

            contenido  TEXT NOT NULL,

            fecha_hora TEXT NOT NULL,

            FOREIGN KEY(id_cliente)

                REFERENCES clientes(id_cliente) ON DELETE CASCADE

        )

    """)



    # ── 4. Índices de rendimiento ─────────────────────────────────────────

    # idx_doc_cliente: acelera el cálculo de métricas (ventas, ticket

    # promedio) y el historial por cliente desde la tabla documentos.

    cursor.execute("""

        CREATE INDEX IF NOT EXISTS idx_doc_cliente

        ON documentos(id_cliente, tipo, estado)

    """)

    cursor.execute("""

        CREATE INDEX IF NOT EXISTS idx_contactos_cliente

        ON contactos_cliente(id_cliente)

    """)

    cursor.execute("""

        CREATE INDEX IF NOT EXISTS idx_notas_cliente

        ON notas_cliente(id_cliente)

    """)



def obtener_stock_disponible(conn, codigo_producto):

    """

    # Calcula en tiempo real el Stock 'Available to Promise' (ATP).

    # Fórmula Matemática en SQL: 

    #   ATP = (SUMA Entradas - SUMA Salidas) - (SUMA Compromisos Activos)

    #

    # 1. Se suma el volumen de todas las 'ENTRADA' en movimientos_stock.

    # 2. Se resta el volumen de todas las 'SALIDA' en movimientos_stock.

    #    (El resultado de 1-2 es el Stock Físico Real actual en galpón).

    # 3. Se resta la suma de las reservas pendientes en compromisos_stock (estado 'ACTIVO').

    #    (El resultado de 1-2-3 es el Stock Neto Comercializable por el vendedor).

    """

    cursor = conn.cursor()

    

    # Consulta optimizada que consolida las 3 variables usando IFNULL para prever nulos

    cursor.execute("""

        SELECT 

            (SELECT IFNULL(SUM(cantidad), 0.0) FROM movimientos_stock 

             WHERE codigo_producto = ? AND tipo_movimiento = 'ENTRADA') 

            -

            (SELECT IFNULL(SUM(cantidad), 0.0) FROM movimientos_stock 

             WHERE codigo_producto = ? AND tipo_movimiento = 'SALIDA')

            -

            (SELECT IFNULL(SUM(cantidad_comprometida), 0.0) FROM compromisos_stock 

             WHERE codigo_producto = ? AND estado = 'ACTIVO')

    """, (codigo_producto, codigo_producto, codigo_producto))

    

    resultado = cursor.fetchone()[0]

    return float(resultado) if resultado else 0.0



def limpiar_presupuestos_vencidos(conn):

    """

    # Proceso cron de limpieza para el modelo ATP.

    # Aquellos presupuestos que pasaron su fecha de vencimiento sin concretarse

    # deben ser anulados para liberar la mercadería comprometida, devolviéndola al pool de venta.

    """

    cursor = conn.cursor()

    try:

        # Iniciamos transacción explícita

        cursor.execute("BEGIN TRANSACTION;")

        

        # 1. Identificar presupuestos vencidos que siguen activos

        cursor.execute("""

            SELECT id_documento FROM documentos 

            WHERE tipo = 'PRESUPUESTO' 

            AND estado = 'ACTIVO' 

            AND datetime(fecha_vencimiento) < datetime('now', 'localtime')

        """)

        presupuestos_expirados = cursor.fetchall()

        

        if presupuestos_expirados:

            for (id_doc,) in presupuestos_expirados:

                # 2. Liberar el stock comprometido

                # Cambiamos estado de ACTIVO a LIBERADO en los registros del inventario reservado

                cursor.execute("""

                    UPDATE compromisos_stock 

                    SET estado = 'LIBERADO' 

                    WHERE id_documento = ? AND estado = 'ACTIVO'

                """, (id_doc,))

                

                # 3. Marcar el presupuesto (cabecera) como VENCIDO

                cursor.execute("""

                    UPDATE documentos 

                    SET estado = 'VENCIDO' 

                    WHERE id_documento = ?

                """, (id_doc,))

                

        conn.commit()

        print(f"Limpieza ATP completada: {len(presupuestos_expirados)} presupuestos liberados.")

        return len(presupuestos_expirados)

    except Exception as e:

        conn.rollback()

        print(f"Error crítico al limpiar presupuestos vencidos: {e}")
        logging.warning(f"Error crítico al limpiar presupuestos vencidos: {e}")

        return -1



# Si ejecutamos este archivo directamente, inicializamos la estructura

if __name__ == "__main__":

    inicializar_base_datos()


