import sqlite3
import sys
import traceback
from PyQt6.QtWidgets import QApplication
from ui.modules.presupuestos.tab_presupuestos import DialogoEditarPresupuesto

def test():
    app = QApplication(sys.argv)
    conn = sqlite3.connect('corralon_profesional.db')
    c = conn.cursor()
    c.execute("SELECT id_documento FROM documentos WHERE tipo='PRESUPUESTO' LIMIT 1")
    row = c.fetchone()
    if not row:
        print("No active budget found")
        sys.exit(0)
    
    d = DialogoEditarPresupuesto(conn, row[0])
    try:
        print("Saving...")
        d.pestana_venta.confirmar_operacion('PRESUPUESTO')
        print("Saved!")
    except Exception as e:
        print("Crash during save!")
        traceback.print_exc()

if __name__ == '__main__':
    test()
