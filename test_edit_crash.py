import sqlite3
import sys
from PyQt6.QtWidgets import QApplication
from ui.modules.presupuestos.tab_presupuestos import DialogoEditarPresupuesto

def test():
    conn = sqlite3.connect('corralon_profesional.db')
    c = conn.cursor()
    c.execute("SELECT id_documento FROM documentos WHERE tipo='PRESUPUESTO' AND estado='ACTIVO' LIMIT 1")
    row = c.fetchone()
    if not row:
        print("No active budget found")
        sys.exit(0)
    
    app = QApplication(sys.argv)
    d = DialogoEditarPresupuesto(conn, row[0])
    print("Dialog instantiated")

if __name__ == '__main__':
    test()
