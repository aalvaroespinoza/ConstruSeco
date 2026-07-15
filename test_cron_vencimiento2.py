import sqlite3
import datetime
import os
import sys

from db.conexion import limpiar_presupuestos_vencidos

def test():
    conn = sqlite3.connect('corralon_profesional.db')
    c = conn.cursor()
    
    # Create mock client if not exists
    c.execute("INSERT OR IGNORE INTO clientes (nombre_completo) VALUES ('Mock Cron')")
    c.execute("SELECT id_cliente FROM clientes WHERE nombre_completo = 'Mock Cron'")
    id_cli = c.fetchone()[0]
    
    # Vencido
    past_date = (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    # Vigente
    future_date = (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    
    # Insert Vencido
    c.execute("""
        INSERT INTO documentos (tipo, id_cliente, fecha_emision, fecha_vencimiento, estado, subtotal_bruto, total_final, numero_interno)
        VALUES ('PRESUPUESTO', ?, datetime('now'), ?, 'ACTIVO', 100, 100, 'CRON-VENC')
    """, (id_cli, past_date))
    id_vencido = c.lastrowid
    
    # Insert Vigente
    c.execute("""
        INSERT INTO documentos (tipo, id_cliente, fecha_emision, fecha_vencimiento, estado, subtotal_bruto, total_final, numero_interno)
        VALUES ('PRESUPUESTO', ?, datetime('now'), ?, 'ACTIVO', 100, 100, 'CRON-VIG')
    """, (id_cli, future_date))
    id_vigente = c.lastrowid
    
    # Commit
    conn.commit()
    
    print(f"Created VENCIDO ID: {id_vencido}")
    print(f"Created VIGENTE ID: {id_vigente}")
    
    # Run cron
    afectados = limpiar_presupuestos_vencidos(conn)
    print(f"Cron afecto a: {afectados} presupuestos")
    
    # Verify
    c.execute("SELECT estado FROM documentos WHERE id_documento = ?", (id_vencido,))
    st_vencido = c.fetchone()[0]
    print(f"VENCIDO expected 'VENCIDO', got: '{st_vencido}'")
    
    c.execute("SELECT estado FROM documentos WHERE id_documento = ?", (id_vigente,))
    st_vigente = c.fetchone()[0]
    print(f"VIGENTE expected 'ACTIVO', got: '{st_vigente}'")
    
if __name__ == '__main__':
    test()
