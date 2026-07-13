"""
Suite de validación de la infraestructura de datos de Clientes.

Ejecuta todas las pruebas sobre una COPIA temporal de la BD productiva.
NO modifica corralon_profesional.db.
"""
import sys
import shutil
import sqlite3
from pathlib import Path

# Forzar UTF-8 en la salida del script (consola Windows puede usar cp1252)
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Agrega la raíz del proyecto al path para importar db/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db.conexion import inicializar_base_datos, obtener_conexion
from db import queries_clientes as qc

DB_PROD  = ROOT / "corralon_profesional.db"
DB_TEST  = ROOT / "test_clientes_suite.db"

OK   = "  ✓"
FAIL = "  ✗"
errores = 0

def check(desc, condicion):
    global errores
    if condicion:
        print(f"{OK}  {desc}")
    else:
        print(f"{FAIL}  {desc}  ← FALLO")
        errores += 1

print("\n══════════════════════════════════════════")
print("  SUITE DE VALIDACIÓN — MÓDULO CLIENTES")
print("══════════════════════════════════════════")

# ── Setup: copia de la BD ─────────────────────────────────────────────────
shutil.copy2(DB_PROD, DB_TEST)
conn = sqlite3.connect(DB_TEST)
conn.execute("PRAGMA foreign_keys = ON")

# ── PRUEBA 1: migración idempotente ───────────────────────────────────────
print("\n[1] Migración idempotente")
from db.conexion import _migrar_clientes
cursor = conn.cursor()
_migrar_clientes(cursor)   # primera vez
_migrar_clientes(cursor)   # segunda vez → no debe fallar
conn.commit()

cursor.execute("PRAGMA table_info(clientes)")
cols = {row[1] for row in cursor.fetchall()}
check("columna activo",        "activo" in cols)
check("columna ciudad",        "ciudad" in cols)
check("columna direccion",     "direccion" in cols)
check("columna condicion_iva", "condicion_iva" in cols)

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tablas = {r[0] for r in cursor.fetchall()}
check("tabla contactos_cliente", "contactos_cliente" in tablas)
check("tabla notas_cliente",     "notas_cliente" in tablas)

cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
indices = {r[0] for r in cursor.fetchall()}
check("indice idx_doc_cliente",       "idx_doc_cliente" in indices)
check("indice idx_contactos_cliente", "idx_contactos_cliente" in indices)
check("indice idx_notas_cliente",     "idx_notas_cliente" in indices)

# ── PRUEBA 2: métricas globales ───────────────────────────────────────────
print("\n[2] Métricas globales")
m = qc.obtener_metricas_clientes(conn)
check("total >= 0",           m["total"] >= 0)
check("activos >= 0",         m["activos"] >= 0)
check("con_compras >= 0",     m["con_compras"] >= 0)
check("ventas_mes float",     isinstance(m["ventas_mes"], float))
check("ticket_promedio float",isinstance(m["ticket_promedio"], float))
print(f"     → Métricas: {m}")

# ── PRUEBA 3: listado paginado ─────────────────────────────────────────────
print("\n[3] Listado paginado")
pag = qc.obtener_clientes(conn, filtro="", pagina=1, por_pagina=10)
check("dict con keys esperadas", all(k in pag for k in ("filas","total_filas","pagina","por_pagina","total_paginas")))
check("pagina = 1",   pag["pagina"] == 1)
check("por_pagina=10",pag["por_pagina"] == 10)
check("total_paginas >= 1", pag["total_paginas"] >= 1)
print(f"     → {pag['total_filas']} clientes, {pag['total_paginas']} páginas")

# ── PRUEBA 4: búsqueda ────────────────────────────────────────────────────
print("\n[4] Búsqueda y filtro")
busq = qc.obtener_clientes(conn, filtro="ZZZNOEXISTE")
check("búsqueda sin resultados", busq["total_filas"] == 0)
check("filas vacías",            busq["filas"] == [])

# ── PRUEBA 5: CRUD de clientes ────────────────────────────────────────────
print("\n[5] CRUD clientes")
id_nuevo = qc.guardar_cliente(conn, {
    "nombre_completo": "Cliente Test Suite",
    "cuit_dni": "20-99999999-9",
    "telefono": "3512001122",
    "email": "test@suite.com",
    "ciudad": "Córdoba",
    "direccion": "Av. Test 123",
    "condicion_iva": "Responsable Inscripto",
})
check("guardar_cliente retorna ID > 0", id_nuevo > 0)

det = qc.obtener_detalle_cliente(conn, id_nuevo)
check("detalle no es None",          det is not None)
check("nombre correcto",             det["nombre"] == "Cliente Test Suite")
check("ciudad correcta",             det["ciudad"] == "Córdoba")
check("condicion_iva correcta",      det["condicion_iva"] == "Responsable Inscripto")
check("activo = True por defecto",   det["activo"] is True)

ok_upd = qc.actualizar_cliente(conn, id_nuevo, {
    "nombre_completo": "Cliente Test Modificado",
    "cuit_dni": "20-99999999-9",
    "ciudad": "Río Cuarto",
    "condicion_iva": "Consumidor Final",
})
check("actualizar_cliente OK", ok_upd)
det2 = qc.obtener_detalle_cliente(conn, id_nuevo)
check("nombre actualizado", det2["nombre"] == "Cliente Test Modificado")
check("ciudad actualizada",  det2["ciudad"] == "Río Cuarto")

ok_des = qc.desactivar_cliente(conn, id_nuevo)
check("desactivar_cliente OK", ok_des)
det3 = qc.obtener_detalle_cliente(conn, id_nuevo)
check("activo = False tras desactivar", det3["activo"] is False)

ok_reac = qc.reactivar_cliente(conn, id_nuevo)
check("reactivar_cliente OK", ok_reac)

# ── PRUEBA 6: Contactos ───────────────────────────────────────────────────
print("\n[6] CRUD contactos")
id_c1 = qc.guardar_contacto(conn, id_nuevo, {
    "nombre": "Juan Perez",
    "cargo": "Gerente",
    "telefono": "3515000000",
    "email": "juan@test.com",
    "principal": True,
})
check("guardar_contacto retorna ID > 0", id_c1 > 0)

id_c2 = qc.guardar_contacto(conn, id_nuevo, {
    "nombre": "Ana Lopez",
    "cargo": "Administrativa",
    "principal": False,
})
check("segundo contacto guardado", id_c2 > 0)

contactos = qc.obtener_contactos_cliente(conn, id_nuevo)
check("2 contactos obtenidos",  len(contactos) == 2)
check("principal es Juan",      contactos[0]["nombre"] == "Juan Perez")
check("principal=True en Juan", contactos[0]["principal"] is True)

ok_upd_c = qc.actualizar_contacto(conn, id_c1, {
    "id_cliente": id_nuevo,
    "nombre": "Juan Perez Actualizado",
    "cargo": "Director",
    "principal": True,
})
check("actualizar_contacto OK", ok_upd_c)

ok_del_c = qc.eliminar_contacto(conn, id_c2)
check("eliminar_contacto OK", ok_del_c)
contactos2 = qc.obtener_contactos_cliente(conn, id_nuevo)
check("1 contacto tras eliminar", len(contactos2) == 1)

# ── PRUEBA 7: Notas ───────────────────────────────────────────────────────
print("\n[7] CRUD notas")
id_n1 = qc.guardar_nota(conn, id_nuevo, "Primera nota de prueba")
check("guardar_nota retorna ID > 0", id_n1 > 0)

id_n2 = qc.guardar_nota(conn, id_nuevo, "Segunda nota de prueba")

notas = qc.obtener_notas_cliente(conn, id_nuevo)
check("2 notas obtenidas",         len(notas) == 2)
check("contenido correcto n1",     any(n["contenido"] == "Primera nota de prueba" for n in notas))
check("fecha_hora no vacía",       all(n["fecha_hora"] for n in notas))

ok_upd_n = qc.actualizar_nota(conn, id_n1, "Nota modificada")
check("actualizar_nota OK", ok_upd_n)
notas2 = qc.obtener_notas_cliente(conn, id_nuevo)
check("nota modificada en BD", any(n["contenido"] == "Nota modificada" for n in notas2))

ok_del_n = qc.eliminar_nota(conn, id_n2)
check("eliminar_nota OK", ok_del_n)
notas3 = qc.obtener_notas_cliente(conn, id_nuevo)
check("1 nota tras eliminar", len(notas3) == 1)

# ── PRUEBA 8: Historial ───────────────────────────────────────────────────
print("\n[8] Historial y actividad reciente")
hist = qc.obtener_historial_cliente(conn, 1)   # usa el cliente de prod (id=1)
check("historial es lista", isinstance(hist, list))
act = qc.obtener_actividad_reciente_cliente(conn, 1, limite=3)
check("actividad reciente es lista", isinstance(act, list))
check("actividad <= 3 ítems",        len(act) <= 3)
print(f"     → {len(hist)} documentos históricos para cliente id=1")

# ── PRUEBA 9: Paginación edge cases ──────────────────────────────────────
print("\n[9] Paginación edge cases")
pag_vacia = qc.obtener_clientes(conn, pagina=9999)
check("página fuera de rango devuelve lista vacía", pag_vacia["filas"] == [])
check("total_paginas es int >= 1",                  pag_vacia["total_paginas"] >= 1)

# ── PRUEBA 10: Solo activos ───────────────────────────────────────────────
print("\n[10] Filtro solo_activos")
qc.desactivar_cliente(conn, id_nuevo)
todos     = qc.obtener_clientes(conn, solo_activos=False)
solo_act  = qc.obtener_clientes(conn, solo_activos=True)
check("solo_activos < todos (hay al menos 1 inactivo)", solo_act["total_filas"] < todos["total_filas"])

# ── Cleanup ───────────────────────────────────────────────────────────────
conn.close()
DB_TEST.unlink()

# ── Resumen ───────────────────────────────────────────────────────────────
print("\n══════════════════════════════════════════")
if errores == 0:
    print("  RESULTADO: TODAS LAS PRUEBAS PASARON")
else:
    print(f"  RESULTADO: {errores} PRUEBA(S) FALLARON")
print("══════════════════════════════════════════\n")
sys.exit(errores)
