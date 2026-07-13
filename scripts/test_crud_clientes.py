"""
Suite de pruebas de la logica CRUD de Clientes.
Sobre copia temporal de la BD. No toca datos productivos.
"""
import sys, shutil, io, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import sqlite3
from db.conexion import _migrar_clientes
from db import queries_clientes as qc
from ui.clientes import _fmt_moneda, _iniciales
import ui.dialogs_clientes as dlg_mod
import ui.dialogs_contactos_notas as sec_mod

DB_PROD = ROOT / "corralon_profesional.db"
DB_TEST = ROOT / "test_crud_clientes.db"

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

print("\n=== SUITE CRUD CLIENTES ===\n")

shutil.copy2(DB_PROD, DB_TEST)
conn = sqlite3.connect(DB_TEST)
conn.execute("PRAGMA foreign_keys = ON")
c = conn.cursor()
_migrar_clientes(c)
conn.commit()

print("[1] Crear cliente (datos minimos)")
id1 = qc.guardar_cliente(conn, {"nombre_completo": "Proveedor Minimo"})
check("ID generado > 0", id1 > 0)
det = qc.obtener_detalle_cliente(conn, id1)

print("\n[2] Crear cliente (datos completos)")
id2 = qc.guardar_cliente(conn, {
    "nombre_completo": "Distribuidora El Sur S.A.",
    "cuit_dni": "30-71234567-9",
    "telefono": "3512001122",
    "email": "ventas@elsur.com",
    "ciudad": "Cordoba",
    "direccion": "Av. Colon 1234",
    "condicion_iva": "Responsable Inscripto",
})

print("\n[3] Editar cliente")
qc.actualizar_cliente(conn, id2, {
    "nombre_completo": "Distribuidora El Sur (Actualizada)",
    "cuit_dni": "30-71234567-9",
    "telefono": "3512009999",
    "email": "nuevo@elsur.com",
    "ciudad": "Villa Maria",
    "direccion": "Calle Nueva 555",
    "condicion_iva": "Monotributista",
})

print("\n[4] Desactivar y reactivar")
qc.desactivar_cliente(conn, id2)
r_solo_act = qc.obtener_clientes(conn, estado="ACTIVOS")
ids_activos = [f["id_cliente"] for f in r_solo_act["filas"]]
check("no aparece en solo_activos", id2 not in ids_activos)
qc.reactivar_cliente(conn, id2)

print("\n[5] Contactos")
id_cont = qc.guardar_contacto(conn, id2, {"nombre": "Juan", "cargo": "Ventas", "telefono": "123", "email": "j@j.com", "principal": True})
check("contacto guardado", id_cont > 0)
conts = qc.obtener_contactos_cliente(conn, id2)
check("contacto listado", len(conts) == 1 and conts[0]["nombre"] == "Juan")
qc.actualizar_contacto(conn, id_cont, {"nombre": "Juan Pablo", "cargo": "Ventas", "telefono": "123", "email": "j@j.com", "principal": True})
conts = qc.obtener_contactos_cliente(conn, id2)
check("contacto editado", conts[0]["nombre"] == "Juan Pablo")
qc.eliminar_contacto(conn, id_cont)
conts = qc.obtener_contactos_cliente(conn, id2)
check("contacto eliminado", len(conts) == 0)

print("\n[6] Notas")
id_nota = qc.guardar_nota(conn, id2, "Nota de prueba")
check("nota guardada", id_nota > 0)
notas = qc.obtener_notas_cliente(conn, id2)
check("nota listada", len(notas) == 1 and notas[0]["contenido"] == "Nota de prueba")
qc.actualizar_nota(conn, id_nota, "Nota modificada")
notas = qc.obtener_notas_cliente(conn, id2)
check("nota editada", notas[0]["contenido"] == "Nota modificada")
qc.eliminar_nota(conn, id_nota)
notas = qc.obtener_notas_cliente(conn, id2)
check("nota eliminada", len(notas) == 0)

print("\n[7] Filtros")
f_iva = qc.obtener_clientes(conn, condicion_iva="Monotributista")
check("filtro condicion_iva", any(f["id_cliente"] == id2 for f in f_iva["filas"]))

conn.close()
DB_TEST.unlink()

print(f"\n=== RESULTADO: {ok_count} OK  |  {fail_count} FALLO(S) ===\n")
sys.exit(fail_count)
