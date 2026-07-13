# AUDITORÍA ESTRUCTURAL PROFUNDA Y DE VALIDACIÓN
**Proyecto:** Sistema ConstruSeco
**Fecha:** 2026-07-13
**Tipo:** Inspección estricta de validación (Read-Only)

## 1. Inventario Real y Completo
Tras un barrido exhaustivo del árbol de directorios, se ha clasificado cada archivo existente:

### Directorio Raíz
- **`test_stock.py`** (1,3 KB): **ENTRY POINT PRINCIPAL**. Inicializa la DB (`corralon_profesional.db`), ejecuta limpieza de presupuestos vencidos y lanza la UI principal. No es un script de prueba.
- **`scratch_test.py`** (2,0 KB): **HERRAMIENTA DE DESARROLLO**. Verifica la validez de la nueva fórmula ATP frente a la antigua, comprobando la integridad matemática. Crea la base de datos temporal `test_corralon.db`.
- **`test_resaltado.py`** (0,6 KB): **HERRAMIENTA DE DESARROLLO**. Script aislado usado para testear comportamientos visuales en la tabla.
- **`corralon_profesional.db`** (70 KB): **BASE DE DATOS PRODUCCIÓN**. Fuente de verdad de SQLite.
- **`test_corralon.db`** (70 KB): **RESIDUO (SAFE TO DELETE)**. Copia generada por `scratch_test.py`.
- **`requirements.txt`**: Lista de dependencias. Contiene librerías sin uso actual.
- **`dump_schema.py`**: **HERRAMIENTA DE AUDITORÍA**. Creada temporalmente para la validación del esquema.

### Directorio `ui/`
- **`ventana_principal.py`** (8,4 KB): **CORE UI**. Enrutador de pestañas y layout general.
- **`nueva_venta.py`** (70 KB, ~1600 líneas): **CORE UI**. Lógica masiva de Punto de Venta.
- **`stock.py`** (34 KB, ~850 líneas): **CORE UI**. Visualización y gestión del inventario.
- **`dialogs_stock.py`** (42 KB, ~1000 líneas): **CORE UI**. Formularios modales CRUD de inventario.
- **`excel_stock.py`** (21 KB): **CORE UI**. Funciones de exportación/importación usando `openpyxl`.
- **`ajustes_stock.py`** (8,3 KB): **CORE UI**. Preferencias guardadas en `QSettings`.
- **`theme.py`** (3,3 KB): **SOPORTE UI**. Definiciones globales de PyQt6.
- **`clientes.py`** (0 bytes): **PLACEHOLDER DELIBERADO**. Preparado para que otro desarrollador ("Thomas", según un comentario en `ventana_principal.py`) trabaje en esta funcionalidad futura.

### Directorio `db/`
- **`conexion.py`** (10 KB): **CORE DB**. Crea las tablas originales e incluye crons (limpieza de presupuestos).
- **`queries.py`** (7,3 KB): **CORE DB**. Provee las funciones de centralización ATP.

## 2. Mapa Real de Dependencias y Falsas Alarmas
* El punto de entrada **es** `test_stock.py`.
* **Falsa Alarma del informe anterior:** La lógica ATP en `ui/nueva_venta.py` **SÍ** está usando las funciones centralizadas de `db/queries.py` (`subquery_atp` y `obtener_stock_producto`). La documentación interna de `db/queries.py` (línea 7) que afirma que `nueva_venta.py` usa subconsultas inline está **obsoleta y es engañosa**. El código fue correctamente refactorizado en la realidad.
* **Falsa Alarma sobre `ui/clientes.py`:** No es basura. El código en `ui/ventana_principal.py` dice: `self.vista_clientes_temp = QLabel("Pantalla de Clientes (Thomas)")`. El archivo vacío es un "espacio de trabajo reservado" para esa tarea en curso.

## 3. Validación de Candidatos a Eliminación
| Archivo | Clasificación | Evidencia |
| :--- | :--- | :--- |
| `test_corralon.db` | **SEGURO DE ELIMINAR** | Copia exacta 1:1 de `corralon_profesional.db` generada en runtime por `shutil.copy2` dentro de `scratch_test.py`. No tiene uso productivo. |
| `ui/clientes.py` | **CONSERVAR** | Es un andamiaje colaborativo (placeholder). Eliminarlo interrumpiría el desarrollo asignado a otro programador. |

## 4. Auditoría de Archivos Grandes y División
* **`ui/nueva_venta.py` (1600+ líneas):** 
  * *Estado:* Combina delegados de Qt, lógica de estado de carrito, recalculación recursiva y diseño visual extenso.
  * *Riesgo de división:* **ALTO**. Al estar tan acoplada con las señales de Qt (`itemChanged`, custom widgets), separar la lógica de negocio a otro archivo sin tener tests automatizados formales tiene altas chances de introducir regresiones visuales o romper actualizaciones en tiempo real de los campos.
  * *Recomendación:* **POSPONER**. No dividir hasta implementar un conjunto de tests de GUI (ej. `pytest-qt`).
* **`ui/stock.py` (844 líneas):**
  * *Estado:* Contiene la vista principal y dos widgets muy puros (`TarjetaMetrica`, `TarjetaFrecuente`).
  * *Riesgo de división:* **BAJO**. 
  * *Recomendación:* Es seguro mover esas dos clases a un archivo nuevo como `ui/components.py`.
* **`ui/dialogs_stock.py` (1042 líneas):**
  * *Estado:* Alto agrupamiento de modales.
  * *Recomendación:* **NO DIVIDIR**. Mantienen excelente cohesión conceptual al estar todos los diálogos referidos a Stock agrupados aquí.

## 5. SQL y Responsabilidades de Base de Datos
* **Fuga DDL Detectada:** Existen funciones `migrar_esquema(...)` y `migrar_esquema_stock(...)` inyectadas en la parte superior de `ui/nueva_venta.py` y `ui/dialogs_stock.py`.
* **Evidencia:** Utilizan `PRAGMA table_info` y `ALTER TABLE` para agregar las columnas `imagen_path`, `notas`, `subtotal_bruto`, etc.
* **Riesgo y Problema:** Las interfaces gráficas no deberían ejecutar DDL (Data Definition Language) de SQLite al importarse. Esto causa condiciones de carrera en un entorno multi-proceso o si se instancia mal la interfaz.
* **Recomendación:** Estas modificaciones de esquema deben centralizarse exclusivamente en `db/conexion.py` (dentro de `inicializar_base_datos()`) o un archivo de migraciones puro.

## 6. Duplicación Real
* **Variables de Tema:** `COLOR_PRIMARY = "#2563eb"`, `COLOR_BG`, `COLOR_DANGER`, etc., están hardcodeadas al tope de casi todos los archivos en `ui/`. 
  * *Riesgo de centralizar:* **BAJO**. Moverlos a `ui/theme.py` mejorará la mantenibilidad global y habilitará futuros modos oscuros sin dolor.
* **SQL:** Las fórmulas ATP ya se han centralizado con éxito. La duplicación matemática ya fue erradicada.

## 7. Requirements y Dependencias
Tras auditar todos los archivos productivos con expresiones regulares estrictas:
* `PyQt6` -> **NECESARIA**
* `openpyxl` -> **NECESARIA** (en `excel_stock.py`)
* `fpdf2` -> **NO UTILIZADA**. No existe ni una sola referencia directa ni indirecta.
* `watchdog` -> **NO UTILIZADA**. No existe en código productivo.

## 8. Tests y Archivos de Diagnóstico
* `test_stock.py` -> **ENTRY POINT REAL**. En un futuro, renombrar a `main.py` o `app.py`.
* `scratch_test.py` -> **HERRAMIENTA DE DIAGNÓSTICO**. Muy útil. Debería moverse a un directorio `scripts/` o `dev/`.
* `test_resaltado.py` -> **RESIDUO**. Herramienta de un solo uso para probar estilos de tabla. Recomendación: Mover a `scripts/`.

## 9. Base de Datos
* Es un esquema maduro. Utiliza claves foráneas fuertemente restrictivas (`ON DELETE CASCADE`, `ON DELETE SET NULL`), modo `PRAGMA foreign_keys = ON` activado por sesión, y un diseño Ledger transaccional robusto en `movimientos_stock`. No se recomienda intervenir la estructura actual.

## 10. Validación Concluyente del Informe Anterior
1. `ui/clientes.py` es eliminable. ❌ **INCORRECTA.** (Es placeholder).
2. `test_corralon.db` es basura residual. ✅ **CONFIRMADA.**
3. `fpdf2` no se utiliza. ✅ **CONFIRMADA.**
4. `watchdog` no se utiliza. ✅ **CONFIRMADA.**
5. `nueva_venta.py` debe dividirse. ❌ **REQUIERE MÁS EVIDENCIA/RIESGO ALTO.**
6. `stock.py` debe dividirse. ✅ **PARCIALMENTE CONFIRMADA.** (Solo extraer componentes).
7. `dialogs_stock.py` debe dividirse. ❌ **INCORRECTA.** (Buena cohesión actual).
8. Los estilos deben centralizarse. ✅ **CONFIRMADA.**
9. Existen ALTER TABLE dentro de UI. ✅ **CONFIRMADA.**
10. `test_stock.py` es el entry point real. ✅ **CONFIRMADA.**

## 11. Plan de Optimización por Riesgo Recomendado

### NIVEL 0 — NO TOCAR
* La tabla transaccional y las consultas `db/queries.py` (El patrón ATP actual es excelente).
* `ui/dialogs_stock.py` (Los modales conviven bien ahí).

### NIVEL 1 — LIMPIEZA SEGURA (HACER)
* Eliminar `test_corralon.db`.
* Remover `fpdf2` y `watchdog` de `requirements.txt`.
* Eliminar los comentarios obsoletos en `db/queries.py` que afirmaban (falsamente) que la UI tenía su propio ATP inline.

### NIVEL 2 — ORGANIZACIÓN (HACER)
* Renombrar `test_stock.py` a `main.py`.
* Mover las funciones DDL de `ALTER TABLE` desde `ui/nueva_venta.py` y `ui/dialogs_stock.py` hacia `db/conexion.py`.
* Mover `COLOR_PRIMARY` y afines de cada módulo a `ui/theme.py`.
* Crear carpeta `scripts/` y mover los tests/diagnósticos allí.

### NIVEL 3 — REFACTOR MODERADO (HACER CON CUIDADO)
* Extraer las clases `TarjetaMetrica` y `TarjetaFrecuente` de `ui/stock.py` a un archivo nuevo llamado `ui/components.py`.

### NIVEL 4 — REFACTOR DE ALTO RIESGO (POSPONER)
* Dividir la arquitectura en capas (MVC/MVVM) completa de `ui/nueva_venta.py`. El riesgo de romper callbacks y estados del carrito es gigantesco frente al beneficio estético. Posponer hasta que haya testing E2E o integración continua.
