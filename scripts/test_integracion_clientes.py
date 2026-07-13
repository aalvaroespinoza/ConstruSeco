import sys, shutil, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import sqlite3
from db.conexion import _migrar_clientes
from db import queries_clientes as qc

DB_PROD = ROOT / "corralon_profesional.db"
DB_TEST = ROOT / "test_integracion_clientes.db"

ok_count = 0
fail_count = 0

def check(desc, cond):
    global ok_count, fail_count
    if cond:
        print(f"  OK  {desc}")
        ok_count += 1
    else:
        print(f"  FAIL  {desc}  <-- FALLO")
        fail_count += 1

print("\n=== SUITE INTEGRACIÓN CLIENTES <-> NUEVA VENTA ===\n")

shutil.copy2(DB_PROD, DB_TEST)
conn = sqlite3.connect(DB_TEST)
conn.execute("PRAGMA foreign_keys = ON")
c = conn.cursor()
_migrar_clientes(c)
conn.commit()

# [1] NUEVO CLIENTE "DESDE CLIENTES"
print("[1] Crear cliente A (Flujo Clientes)")
id_a = qc.guardar_cliente(conn, {"nombre_completo": "Cliente Creado en Clientes"})

# En Nueva Venta, cargar_autocompletado_clientes hace:
c.execute("SELECT id_cliente, nombre_completo FROM clientes WHERE activo = 1")
lista_nv = {row[0]: row[1] for row in c.fetchall()}
check("Cliente A visible en autocompletado de Nueva Venta", id_a in lista_nv)

# [2] NUEVO CLIENTE "DESDE NUEVA VENTA"
print("\n[2] Crear cliente B (Flujo Nueva Venta - ahora usa mismo DialogoFormularioCliente)")
# Simular guardado desde DialogoFormularioCliente
id_b = qc.guardar_cliente(conn, {"nombre_completo": "Cliente Creado en Nueva Venta"})

# En Clientes, se lo puede listar
res_clientes = qc.obtener_clientes(conn, filtro="Nueva Venta")
check("Cliente B se encuentra en listado de Clientes", any(f["id_cliente"] == id_b for f in res_clientes["filas"]))

# [3] ASOCIAR UNA VENTA Y COMPROBAR MÉTRICAS
print("\n[3] Asociar una venta al Cliente A y probar historial")
# Simular venta. El esquema de documentos requiere id_cliente, tipo='VENTA', total_final, estado='CONFIRMADO'
# Para test_integracion_clientes.db, simplemente insertamos un doc
try:
    c.execute("""
        INSERT INTO documentos (id_cliente, tipo, numero_interno, estado, fecha_emision, total_final, total_descuento)
        VALUES (?, 'VENTA', 'V-0001', 'CONFIRMADO', date('now'), 15000.50, 0.0)
    """, (id_a,))
    id_doc = c.lastrowid
    conn.commit()
    check("Venta asociada correctamente", id_doc > 0)
except Exception as e:
    print(f"Error insertando doc: {e}")
    fail_count += 1

# Comprobar métricas del cliente (Actividad reciente)
act = qc.obtener_actividad_reciente_cliente(conn, id_a, limite=5)
check("Actividad reciente muestra la venta", len(act) == 1 and act[0]["tipo"] == "VENTA" and act[0]["total_final"] == 15000.5)

# Comprobar historial completo
hist = qc.obtener_historial_cliente(conn, id_a)
check("Historial completo contiene la venta", len(hist) == 1 and hist[0]["numero_interno"] == "V-0001")

# Comprobar métricas generales del panel
met = qc.obtener_metricas_clientes(conn)
check("Métricas globales reflejan la compra (ventas_mes)", met["ventas_mes"] >= 15000.5)

# [4] CLIENTES INACTIVOS EN NUEVA VENTA
print("\n[4] Comprobar comportamiento de cliente inactivo")
qc.desactivar_cliente(conn, id_a)
check("Cliente A desactivado", qc.obtener_detalle_cliente(conn, id_a)["activo"] == False)

c.execute("SELECT id_cliente FROM clientes WHERE activo = 1")
activos = [r[0] for r in c.fetchall()]
check("Cliente inactivo YA NO aparece en autocompletado de Nueva Venta", id_a not in activos)

hist_inactivo = qc.obtener_historial_cliente(conn, id_a)
check("Cliente inactivo CONSERVA su historial", len(hist_inactivo) == 1)

conn.close()
DB_TEST.unlink()

print(f"\n=== RESULTADO: {ok_count} OK  |  {fail_count} FALLO(S) ===\n")
sys.exit(fail_count)
