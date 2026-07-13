# PLAN DE IMPLEMENTACION — PESTANA CLIENTES
**Proyecto:** ConstruSeco Pereyra
**Fecha de analisis:** 2026-07-13
**Estado:** DOCUMENTO DE PLANIFICACION — Sin modificar codigo productivo

---

## A. Estado Actual de ui/clientes.py

El archivo existe pero esta **completamente vacio** (0 bytes, 1 linea en blanco).
Es un placeholder deliberado, confirmado por el comentario en ventana_principal.py:

    self.vista_clientes_temp = QLabel("Pantalla de Clientes (Thomas)")

La pestana Clientes ocupa el **indice 2** del QStackedWidget. La implementacion real
consiste en reemplazar ese QLabel placeholder por la clase PestanaClientes(self.conn).

---

## B. Esquema Real Actual de clientes

    CREATE TABLE clientes (
        id_cliente      INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_completo TEXT NOT NULL,
        cuit_dni        TEXT UNIQUE,
        telefono        TEXT,
        email           TEXT
    )

Observaciones:
- No hay columna activo  -> imposible filtrar Activos sin ALTER TABLE.
- No hay ciudad          -> la columna Ciudad del wireframe requiere nueva columna.
- No hay notas           -> requiere tabla separada.
- No hay multiples contactos -> requiere tabla separada.
- Actualmente hay 1 cliente de prueba (Testeando, sin CUIT, sin email, sin telefono).

---

## C. Relaciones Actuales con Ventas/Documentos

    clientes --(1:N)--> documentos  (via id_cliente, ON DELETE SET NULL)
    documentos --(1:N)--> detalle_documentos  (ON DELETE CASCADE)
    documentos --(1:N)--> movimientos_stock
    documentos --(1:N)--> compromisos_stock (ON DELETE CASCADE)

Estado de datos reales inspeccionados:
- 7 ventas CONFIRMADAS en total ($ 570.000 acumulado)
- 6 ventas SIN id_cliente asignado (campo NULL)
- 1 venta con cliente (Testeando - $ 20.000)
- La BD soporta documentos anonimos via ON DELETE SET NULL

RIESGO: Las ventas historicas sin cliente no apareceran en el historial del cliente.
Esto es comportamiento correcto, no un bug.

---

## D. Datos Calculables AHORA (sin nuevas tablas)

- Total Ventas del Cliente : SUM(total_final) WHERE id_cliente=? AND tipo=VENTA AND estado=CONFIRMADO
- Cantidad de compras      : COUNT(*)
- Ticket Promedio          : AVG(total_final)
- Ventas del Mes           : filtro por fecha_emision del mes actual
- Ultima compra            : MAX(fecha_emision)
- Actividad reciente       : ORDER BY fecha_emision DESC LIMIT 10
- Presupuestos pendientes  : WHERE tipo=PRESUPUESTO AND estado=ACTIVO

---

## E. Datos que NO Existen Actualmente

| Campo deseado           | Estado | Solucion                       |
|-------------------------|--------|-------------------------------|
| Activo / Inactivo       | No     | ALTER TABLE + columna nueva    |
| Ciudad                  | No     | ALTER TABLE + columna nueva    |
| Direccion               | No     | ALTER TABLE + columna nueva    |
| Condicion IVA           | No     | ALTER TABLE + columna nueva    |
| Multiples contactos     | No     | Nueva tabla contactos_cliente  |
| Notas                   | No     | Nueva tabla notas_cliente      |
| Saldo / cuenta corriente| No     | NO implementar aun             |
| Historial de pagos      | No     | NO implementar (sin modulo)    |

---

## F. Nuevas Tablas y Columnas Recomendadas

### F.1 - Columnas a agregar a clientes (migracion idempotente)

    ALTER TABLE clientes ADD COLUMN activo INTEGER DEFAULT 1;
    ALTER TABLE clientes ADD COLUMN ciudad TEXT;
    ALTER TABLE clientes ADD COLUMN direccion TEXT;
    ALTER TABLE clientes ADD COLUMN condicion_iva TEXT DEFAULT 'Consumidor Final';

### F.2 - Nueva tabla contactos_cliente

    CREATE TABLE IF NOT EXISTS contactos_cliente (
        id_contacto INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente  INTEGER NOT NULL,
        nombre      TEXT NOT NULL,
        cargo       TEXT,
        telefono    TEXT,
        email       TEXT,
        principal   INTEGER DEFAULT 0,
        FOREIGN KEY(id_cliente) REFERENCES clientes(id_cliente) ON DELETE CASCADE
    );

### F.3 - Nueva tabla notas_cliente

    CREATE TABLE IF NOT EXISTS notas_cliente (
        id_nota    INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER NOT NULL,
        contenido  TEXT NOT NULL,
        fecha_hora TEXT NOT NULL,
        FOREIGN KEY(id_cliente) REFERENCES clientes(id_cliente) ON DELETE CASCADE
    );

### F.4 - Indices de rendimiento

    CREATE INDEX IF NOT EXISTS idx_doc_cliente ON documentos(id_cliente, tipo, estado);
    CREATE INDEX IF NOT EXISTS idx_contactos_cliente ON contactos_cliente(id_cliente);
    CREATE INDEX IF NOT EXISTS idx_notas_cliente ON notas_cliente(id_cliente);

---

## G. Arquitectura Propuesta

    ui/clientes.py          <- Clase principal: PestanaClientes(QWidget)
    ui/dialogs_clientes.py  <- Dialogos modales: Crear/Editar/Contactos/Notas
    db/queries_clientes.py  <- Consultas SQL centralizadas de clientes
    db/conexion.py          <- Migracion segura (UNICO lugar con DDL)
    ui/ventana_principal.py <- Swap del placeholder en indice 2

Principios:
- ui/clientes.py NO ejecuta DDL (ningún ALTER TABLE ni CREATE TABLE).
- Toda migracion se ejecuta en db/conexion.py con guardas idempotentes.
- SQL centralizado en db/queries_clientes.py.
- Colores importados desde ui/theme.py.

---

## H. Componentes y Clases Propuestas

### ui/clientes.py

    PestanaClientes(QWidget)
      _init_ui()                 - Layout principal
      _init_metricas()           - Tarjetas: Total, Activos, Con Compras, Ventas Mes, Ticket Prom
      _init_tabla()              - QTableWidget con columnas
      _init_panel_lateral()      - Panel de detalle al seleccionar fila
      cargar_clientes()          - Carga paginada
      filtrar()                  - Busqueda por texto
      on_seleccion_cambiada(row) - Carga detalle lateral
      abrir_dialogo_nuevo()
      abrir_dialogo_editar(id_cliente)
      desactivar_cliente(id_cliente)

### ui/dialogs_clientes.py

    DialogoNuevoCliente(QDialog)  - Crear cliente con todos los campos
    DialogoEditarCliente(QDialog) - Editar cliente existente
    DialogoNuevoContacto(QDialog) - Agregar/editar contacto
    DialogoNuevaNota(QDialog)     - Agregar/editar nota

### db/queries_clientes.py

    obtener_clientes(conn, filtro, pagina, por_pagina)  -> list[dict]
    obtener_metricas_clientes(conn)                     -> dict
    obtener_detalle_cliente(conn, id_cliente)           -> dict
    obtener_historial_cliente(conn, id_cliente)         -> list[dict]
    obtener_contactos_cliente(conn, id_cliente)         -> list[dict]
    obtener_notas_cliente(conn, id_cliente)             -> list[dict]
    guardar_cliente(conn, datos)                        -> int
    actualizar_cliente(conn, id_cliente, datos)         -> bool
    desactivar_cliente(conn, id_cliente)                -> bool
    guardar_contacto(conn, id_cliente, datos)           -> int
    eliminar_contacto(conn, id_contacto)                -> bool
    guardar_nota(conn, id_cliente, datos)               -> int
    eliminar_nota(conn, id_nota)                        -> bool

---

## I. Consultas Necesarias

### Metricas del encabezado

    SELECT
        COUNT(*) AS total,
        SUM(activo) AS activos,
        (SELECT COUNT(DISTINCT id_cliente) FROM documentos
         WHERE tipo='VENTA' AND estado='CONFIRMADO' AND id_cliente IS NOT NULL) AS con_compras,
        (SELECT IFNULL(SUM(total_final), 0.0) FROM documentos
         WHERE tipo='VENTA' AND estado='CONFIRMADO'
           AND strftime('%Y-%m', fecha_emision) = strftime('%Y-%m', 'now', 'localtime')
           AND id_cliente IS NOT NULL) AS ventas_mes,
        (SELECT IFNULL(AVG(total_final), 0.0) FROM documentos
         WHERE tipo='VENTA' AND estado='CONFIRMADO' AND id_cliente IS NOT NULL) AS ticket_promedio
    FROM clientes;

### Lista paginada con busqueda

    SELECT id_cliente, nombre_completo, cuit_dni, email, telefono, ciudad, activo,
           (SELECT COUNT(*) FROM documentos
            WHERE id_cliente = c.id_cliente AND tipo='VENTA' AND estado='CONFIRMADO') AS total_compras,
           (SELECT IFNULL(SUM(total_final), 0.0) FROM documentos
            WHERE id_cliente = c.id_cliente AND tipo='VENTA' AND estado='CONFIRMADO') AS total_gastado
    FROM clientes c
    WHERE nombre_completo LIKE ? OR cuit_dni LIKE ?
    ORDER BY nombre_completo
    LIMIT ? OFFSET ?;

### Historial de cliente

    SELECT d.id_documento, d.numero_interno, d.tipo, d.estado,
           d.fecha_emision, d.total_final
    FROM documentos d
    WHERE d.id_cliente = ?
      AND d.tipo IN ('VENTA', 'PRESUPUESTO')
    ORDER BY d.fecha_emision DESC
    LIMIT 50;

---

## J. Flujo de Seleccion de Cliente

    Usuario hace clic en fila de la tabla
      -> on_seleccion_cambiada(row)
        -> extrae id_cliente de la fila
        -> llama obtener_detalle_cliente(conn, id_cliente)
        -> pobla el panel lateral con:
            - Nombre, CUIT, ciudad, telefono, email
            - Condicion IVA
            - Total compras, total gastado, ticket promedio
            - Lista de contactos asociados
            - Ultimas 5 notas
            - Actividad reciente (ultimos 5 documentos)
            - Botones: Editar | Historial Completo | Desactivar

---

## K. Integracion con Nueva Venta

Estado actual en nueva_venta.py:

    cursor.execute("SELECT id_cliente, nombre_completo, cuit_dni, telefono FROM clientes")

Debe corregirse a:

    cursor.execute("SELECT id_cliente, nombre_completo, cuit_dni, telefono FROM clientes WHERE activo = 1")

IMPORTANTE: Aplicar DESPUES de la migracion (Fase 6).
La funcion modal_nuevo_cliente() sigue funcionando sin cambios (campos nuevos tienen DEFAULT).

---

## L. Estrategia de Migracion Segura

Toda migracion en db/conexion.py > inicializar_base_datos() con guardas idempotentes:

    def _migrar_clientes(cursor):
        cursor.execute("PRAGMA table_info(clientes)")
        columnas = {row[1] for row in cursor.fetchall()}
        
        if "activo" not in columnas:
            cursor.execute("ALTER TABLE clientes ADD COLUMN activo INTEGER DEFAULT 1")
        if "ciudad" not in columnas:
            cursor.execute("ALTER TABLE clientes ADD COLUMN ciudad TEXT")
        if "direccion" not in columnas:
            cursor.execute("ALTER TABLE clientes ADD COLUMN direccion TEXT")
        if "condicion_iva" not in columnas:
            cursor.execute("ALTER TABLE clientes ADD COLUMN condicion_iva TEXT DEFAULT 'Consumidor Final'")
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS contactos_cliente (...)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS notas_cliente (...)""")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_cliente ...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contactos_cliente ...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notas_cliente ...")

Llamar al final de inicializar_base_datos(), antes del conn.commit().

---

## M. Riesgos Encontrados

| ID | Riesgo                                             | Severidad | Mitigacion                                   |
|----|----------------------------------------------------|-----------|----------------------------------------------|
| R1 | 6 de 7 ventas sin cliente asignado                 | MEDIO     | Aclarar en UI que historial requiere cliente  |
| R2 | nueva_venta.py no filtra clientes inactivos        | BAJO      | Corregir en Fase 6 post-migracion            |
| R3 | Posible import circular ui/clientes <- ui/nv       | ALTO      | Nunca importar nueva_venta desde clientes    |
| R4 | from ui.stock import PestanaStock duplicado (ln 6-7)| MUY BAJO  | Advertencia de calidad, no bloqueo           |
| R5 | modal_nuevo_cliente no redirige a tab Clientes     | BAJO      | Comportamiento correcto, no es un bug        |
| R6 | Eliminacion de cliente pone NULL en documentos     | BAJO      | Mostrar advertencia antes de eliminar        |

---

## N. Orden Exacto de Implementacion

### Fase 1 - Migracion de base de datos (db/conexion.py)
1. Agregar _migrar_clientes(cursor) con guardas idempotentes.
2. Llamarla al final de inicializar_base_datos().
3. Verificar con py_compile y smoke test.

### Fase 2 - Consultas (nuevo db/queries_clientes.py)
1. Crear archivo con todas las funciones de la Seccion H.
2. No importar de ui/ para evitar circulares.

### Fase 3 - Dialogos (nuevo ui/dialogs_clientes.py)
1. DialogoNuevoCliente
2. DialogoEditarCliente
3. DialogoNuevoContacto
4. DialogoNuevaNota

### Fase 4 - Pestana principal (ui/clientes.py)
1. PestanaClientes completa con todos los componentes.
2. Metricas, tabla, panel lateral, paginacion, CRUD.

### Fase 5 - Integracion (ui/ventana_principal.py)
1. Importar PestanaClientes.
2. Reemplazar QLabel placeholder por PestanaClientes(conn) en indice 2.

### Fase 6 - Correccion Nueva Venta (ui/nueva_venta.py)
1. Agregar WHERE activo = 1 al autocomplete de clientes.

---

## O. Archivos por Fase

| Fase | Modificados          | Nuevos                  |
|------|----------------------|-------------------------|
| 1    | db/conexion.py       | —                       |
| 2    | —                    | db/queries_clientes.py  |
| 3    | —                    | ui/dialogs_clientes.py  |
| 4    | ui/clientes.py       | —                       |
| 5    | ui/ventana_principal.py | —                    |
| 6    | ui/nueva_venta.py    | —                       |

---

## RESUMEN EJECUTIVO

Archivos analizados: ui/clientes.py, ui/ventana_principal.py, ui/nueva_venta.py,
ui/theme.py, db/conexion.py, db/queries.py, requirements.txt + inspeccion SQL directa.

Estado actual: ui/clientes.py vacio. QLabel placeholder en indice 2.
Tabla clientes existe con 5 campos basicos y 1 registro de prueba.

Cambios de BD: 4 columnas en clientes + 2 tablas nuevas + 3 indices.
Todo idempotente y centralizado en db/conexion.py.

Nuevas tablas: contactos_cliente, notas_cliente.

Integraciones: ventana_principal.py (swap), nueva_venta.py (1 linea), db/conexion.py (migracion).

Riesgos principales:
- Ventas historicas sin cliente (normal, no bug).
- Import circular si se diseña mal (evitable).
- nueva_venta mostrara inactivos hasta Fase 6 (cosmético).

Plan: 6 fases secuenciales comenzando por la migracion de BD.
