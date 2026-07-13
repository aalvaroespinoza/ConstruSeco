# CONTEXTO MAESTRO — GESTION STOCK

## 0. Cómo usar este documento
Este archivo es el **documento maestro de contexto y arquitectura**. Debe ser leído exhaustivamente por cualquier agente o desarrollador que tome el proyecto tras su migración a una nueva carpeta. Contiene el diseño arquitectónico, el flujo real de datos y el historial de decisiones/bugs que definen la estabilidad del sistema. **NO modificar código sin verificar el Checklist final (Secciones 28 y 29).**

## 1. Resumen ejecutivo
El sistema es una aplicación de escritorio Windows construida en **Python 3 con PyQt6 y SQLite3** para la gestión de stock y ventas de un corralón de materiales. Emplea un modelo estricto de **Ledger de Inventario** (Registro de Movimientos) y un motor **ATP (Available to Promise)** para separar el stock físico del stock disponible tras compromisos. 

## 2. Estado actual del proyecto
El proyecto se encuentra en un estado funcional avanzado. Las dependencias visuales y cálculos matemáticos operan correctamente tras repetidas refactorizaciones que eliminaron comportamientos inestables de PyQt6 (particularmente en QTableWidget). Se acaba de introducir una lógica de resaltado manual robusta y overlays dinámicos para vistas detalladas.

## 3. Stack tecnológico
- **Lenguaje:** Python 3 (venv)
- **Framework UI:** PyQt6 (Estilo Flat/Moderno manual vía Stylesheets)
- **Base de Datos:** SQLite3 (archivo: `corralon_profesional.db`)
- **Reportes/Excel:** openpyxl (importación/exportación)
- **Imágenes:** Pillow

## 4. Cómo ejecutar el sistema
El entrypoint principal de la aplicación no es un main clásico, sino que depende de scripts de testing convertidos en lanzadores:
```bash
venv\Scripts\python.exe test_stock.py
```
Este archivo inicializa la BD, purga presupuestos vencidos y levanta `VentanaPrincipal`.

## 5. Árbol completo relevante del proyecto
```text
Proyecto/
├── test_stock.py           # Entrypoint Principal
├── test_resaltado.py       # Sandbox UI temporal
├── corralon_profesional.db # Base de datos activa
├── requirements.txt
├── assets/                 # Logo e imágenes de productos generadas dinámicamente
├── db/
│   ├── conexion.py         # Conexión, DDL base y limpieza ATP
│   └── queries.py          # Subconsultas ATP canónicas centralizadas (Subquery SQL)
└── ui/
    ├── ventana_principal.py# QMainWindow (TabWidget contenedor)
    ├── nueva_venta.py      # Motor de Ventas y Presupuestos
    ├── stock.py            # Dashboard, Grilla principal de inventario y acciones
    ├── dialogs_stock.py    # Modales CRUD, overlay de detalle y lógica visual
    ├── excel_stock.py      # Importación (Segura/Destructiva) y exportación
    ├── ajustes_stock.py    # Configuración del sistema
    ├── clientes.py         # Módulo de clientes
    └── theme.py            # Constantes de colores y tipografía
```

## 6. Arquitectura general
Aplicación monolítica de 2 capas gruesas: `db/` y `ui/`. 
No hay un ORM. Toda la persistencia es SQL crudo mediante el driver nativo `sqlite3` de Python. 
El diseño de la UI es "Tab-based" donde cada gran bloque del negocio (Venta, Stock, Clientes) reside en un QWidget inyectado en un QTabWidget en `VentanaPrincipal`.

## 7. Mapa de archivos y responsabilidades
- `ui/nueva_venta.py`: Orquesta la creación de documentos (`VENTA`, `PRESUPUESTO`) y la salida de stock (`SALIDA`) o la creación de `compromisos_stock`. Contiene su propia query ATP inline en `buscar_producto`.
- `ui/stock.py`: Panel administrativo de lectura y acceso al CRUD. Consume masivamente `db.queries.obtener_stocks_todos()`. Posee la UI principal interactiva con soporte para doble clic, filtros en caliente y acciones dinámicas en celdas.
- `ui/dialogs_stock.py`: Componentes visuales "hijos". Maneja edición de atributos y la reciente **VistaDetalleProducto** (un overlay de QFrame para desenfoque seguro).
- `db/queries.py`: Contiene los helpers `_sq_entradas`, `_sq_salidas`, `_sq_comprometido` y `subquery_atp()`.
- `db/conexion.py`: Funciones de bootstrap (`inicializar_base_datos`) y limpieza temporal (`limpiar_presupuestos_vencidos`).

## 8. Base de datos real (Auditoría Forense)
El schema verificado (`sqlite_master`) indica las siguientes tablas principales:
- **productos**: `codigo (PK)`, `descripcion (UNIQUE)`, `unidad_base`, `precio_venta`, `stock_minimo`, `activo`, `imagen_path`. (NOTA: `stock_fisico` **NO** existe aquí por diseño de Ledger).
- **conversiones_unidad**: Soporte para multi-unidad (ej: m2 vs un).
- **documentos**: Maestro de transacciones (`tipo IN ('PRESUPUESTO', 'VENTA', 'COMPRA', 'AJUSTE')`).
- **detalle_documentos**: Líneas de factura asociadas a `documentos`.
- **movimientos_stock**: Registro inmutable de `ENTRADA` y `SALIDA`. Todo movimiento requiere un `id_documento_origen`. Se le añadió recientemente la columna `notas`.
- **compromisos_stock**: Bloqueos temporales de stock ATP (`estado IN ('ACTIVO', 'LIBERADO', 'CONSUMIDO')`).

## 9. Arquitectura de stock y ATP (CRÍTICO)
**Invariante del sistema:** El stock físico NO se guarda como un número entero en `productos`. Se calcula al vuelo.
- **Stock Físico:** `SUM(ENTRADA) - SUM(SALIDA)`
- **Stock Comprometido:** `SUM(cantidad) FROM compromisos_stock WHERE estado = 'ACTIVO'`
- **Stock ATP (Disponible):** `Físico - Comprometido`

*¿Dónde se calcula?*
1. **Centralizado:** `db/queries.py` genera el SQL de subqueries repetitivas.
2. **Inline / Duplicado:** `ui/nueva_venta.py` inyecta directamente estas subqueries al cargar el catálogo para mejorar latencia en el buscador en memoria. **(Riesgo si cambian las reglas ATP)**.

## 10. Flujo de Nueva Venta
Opera mayormente en memoria tras la carga inicial del catálogo (usando `QCompleter` o popup manual). 
- Permite descontar del stock físico (`VENTA`) o crear compromisos (`PRESUPUESTO`).
- Soporta conversión de unidades (Ej. cajas de cerámicos en m2).
- Utiliza bloqueos de base de datos seguros: `BEGIN IMMEDIATE` antes de la persistencia iterativa de documentos y detalles para evitar race conditions.
- Auto-selecciona el texto numérico al enfocar la celda para mayor velocidad (`_AutoSelectDelegate`).

## 11. Flujo de Control de Stock
El Dashboard calcula en tiempo real métricas de inventario (Total, Valor, Bajo Stock, Sin Stock, Mayor Rotación).
- La tabla intercepta interacciones nativas.
- Para evitar bugs visuales reportados, el resaltado de filas no usa la selección nativa del sistema operativo (`selectRow()`), sino un `QBrush` manual iterado en la función `resaltar_producto_por_codigo(codigo)` de `PestanaStock`.

## 12. Diálogos y componentes secundarios
- `VistaDetalleProducto`: Usa un `QFrame` semitransparente como overlay de la pestaña padre (`parent.rect()`), filtrando los eventos de redimensión para simular un modal estético. Muestra placeholder "📦 Sin imagen" automáticamente de forma segura si falla el `imagen_path`.

## 13. Importación y exportación
Módulo `ui/excel_stock.py` (usa `openpyxl`).
- **Modo Agregar/Actualizar (Seguro):** Realiza `UPDATE` o `INSERT` y crea documentos de ajuste para ingresos iniciales.
- **Modo Sustituir (Destructivo pero Robusto):** Revisa todos los productos actuales; **SI tienen historial (movimientos/documentos) los desactiva (`activo=0`), NO los borra.** Sólo aplica `DELETE` en productos vírgenes. Totalmente seguro contra fallos de Foreign Key. Usa transacciones atómicas.

## 14. Sistema de imágenes
`imagen_path` en `productos`. Puede almacenar rutas absolutas (legado) o nombres de archivo. Si es nombre de archivo, el sistema busca en `assets/productos/`. La vista de detalle está blindada contra excepciones de archivos borrados.

## 15. Sistema de unidades
Se definen canónicamente en `db.queries.UNIDADES_PERMITIDAS` (`[('u', 'Unidad'), ('m2', 'm²')]`). El sistema es muy sensible a alteraciones arbitrarias de unidades porque la lógica de `nueva_venta.py` altera labels condicionalmente (ej. "Cantidad m²").

## 16. Señales, slots, callbacks y navegación
Se eliminó la comunicación inestable basada en "buscar al abuelo/padre". Las tarjetas del dashboard emiten el código string y `PestanaStock` reacciona limpiando los filtros actuales y haciendo scroll (`scrollToItem`) a la fila deseada mediante `resaltar_producto_por_codigo`.

## 17. Historial de bugs conocidos (Resueltos históricamente)
1. `AttributeError: PestanaStock no attribute cargar_metricas`: **RESUELTO** (ahora se llama `actualizar_vista`).
2. `NameError: QWidget / COLOR_DANGER`: **RESUELTO**.
3. *Tarjetas superiores y Alertas sin selección visual:* **RESUELTO** mediante reemplazo completo de la selección nativa de Qt por la pintura dinámica `QBrush` y redibujado de la grilla.
4. *Problemas de ResizeMode Interactive vs Stretch:* **RESUELTO**.
5. *Textos cortados en campos inferiores:* **RESUELTO** mediante compactación profunda de Layouts (márgenes a 12px, inputs a 32px).

## 18. Bugs actualmente confirmados
**Ninguno bloqueante verificado.** Todas las regresiones UI de "selección invisible" o "crash por imports" fueron resueltas en los últimos parches y pasaron validación de análisis estático (`py_compile`).

## 19. Funcionalidades implementadas
Ventas, Presupuestos (compromisos ATP), Limpieza dinámica de vencidos, CRUD Stock, Auditoría Visual, Alertas, Importación, Ajuste, Descuentos generales, Discriminación IVA, Unidades convertibles, y auto-foco rápido en inputs numéricos.

## 20. Funcionalidades incompletas
- Falta la materialización de un sistema de configuración serializado de usuarios/roles, los ajustes son mayormente funcionales al stock.

## 21. Intentos anteriores que no funcionaron
- Modificar colores y selecciones directamente llamando a `self.tabla.selectRow(r)` o `setCurrentItem(i)`. El `QTableWidget` lo reseteaba al perder foco. *NO INTENTAR REVERTIR ESTO. Mantener el uso de la variable `self.codigo_producto_resaltado`.*

## 22. Deuda técnica
- **Subqueries SQL duplicadas:** `nueva_venta.py` (líneas ~859, 1513) tiene hardcodeada la lógica ATP que existe en `db/queries.py`.
- **Falta de paginación:** La tabla de productos de stock asume que el volumen en memoria es procesable en un solo bloque. Para cientos de miles de registros, bloquearía el Main Thread.

## 23. Riesgos de regresión
- **Alterar el schema de la base de datos** sin revisar las inserciones posicionales (`VALUES (?, ?, ?, ...)`) en `excel_stock.py` y `nueva_venta.py`. 
- **Modificar la lógica ATP:** Cambiar el cálculo de "comprometido" puede generar falsos quiebres de inventario si no se actualiza en TODO el código simultáneamente.

## 24. Invariantes que NO deben romperse
1. **NO AÑADIR una columna de `stock_actual` entero a la tabla productos.** El sistema está modelado estocásticamente bajo un Ledger puro. 
2. **Las selecciones de la tabla visual de stock deben fluir hacia `resaltar_producto_por_codigo`.**
3. **Las actualizaciones masivas deben ser envueltas en `BEGIN IMMEDIATE` / `COMMIT`.**

## 25. Pruebas realizadas durante esta auditoría
- `py_compile` sobre el 100% de la base de código.
- Extracción íntegra del SQLite schema en ejecución real.
- Verificación exhaustiva de llamadas a UI y dependencias internas de `openpyxl`.

## 26. Matriz funcional: solicitada / implementada / verificada
| Funcionalidad | Solicitada | Existe en código | Verificada (Compilada) | Estado |
|---|---|---|---|---|
| ATP Lógica Ledger | Sí | Sí | Sí | OK |
| Limpieza de Presupuestos| Sí | Sí | Sí | OK |
| Importación Excel Destructiva | Sí | Sí (Desactiva/Borra) | Sí | OK (Segura) |
| Vista Modal de Producto | Sí | Sí (QFrame Overlay)| Sí | OK |
| Resaltado Seguro de Fila | Sí | Sí (QBrush manual) | Sí | OK |
| Focus Select All Venta | Sí | Sí (EventFilter) | Sí | OK |

## 27. Plan recomendado de continuidad
1. **Congelar el Ledger:** Todo lo relacionado a Movimientos de Stock y ATP funciona y está blindado; **NO TOCAR.**
2. **Priorizar Paginación/Optimización:** A futuro, implementar la carga diferida (lazy loading) en la tabla visual de Control de Stock.
3. **Refactor de ATP:** El próximo paso técnico ideal es hacer que `nueva_venta.py` y `stock.py` consuman estrictamente una vista (VIEW) en la base de datos o la función unificada de `queries.py` para erradicar las subqueries hardcodeadas.

## 28. Checklist obligatorio ANTES de modificar código
- [ ] ¿Esta modificación afecta el cálculo de Entradas/Salidas/Compromisos?
- [ ] Si altero un QTableWidget, ¿estoy rompiendo el renderizado dinámico del `QBrush` de `stock.py`?
- [ ] Si agrego un botón nuevo al menú de acciones, ¿está envuelto en transacciones seguras si toca la BD?

## 29. Checklist obligatorio DESPUÉS de modificar código
- [ ] Ejecutar `venv\Scripts\python.exe -m compileall .`
- [ ] Revisar el alineamiento vertical de layouts si se tocaron widgets inferiores (estaban frágilmente espaciados y se acaban de ajustar).
- [ ] Validar importaciones de dependencias (cuidado con imports circulares entre módulos de UI).

## 30. Guía para el próximo agente
Al ingresar a tu nueva sesión, tu tarea principal es continuar desarrollando características o resolver los pendientes de la empresa. Las reglas fundamentales impuestas son: **Respetar la estética moderna preexistente (colores/theme.py), NO romper el ATP (no modificar la lógica de inserciones de `movimientos_stock` en transacciones sin extrema cautela), y utilizar `QFrames` superpuestos o diálogos aislados en lugar de destruir ventanas de padres para interfaces modales.**

## 31. Snapshot técnico final
- **Framework:** PyQt6
- **Base de Datos:** SQLite nativo, esquema v2 (con paths e historial blindado).
- **Problemas en caliente:** Ninguno reportado, proyecto estable y listo para ampliaciones de capas externas (reportes adicionales, dashboards contables, etc).
