import sqlite3
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from ui.modules.presupuestos.tab_presupuestos import PestanaPresupuestos

def test():
    app = QApplication(sys.argv)
    conn = sqlite3.connect('corralon_profesional.db')
    
    win = QMainWindow()
    win.resize(1024, 768)
    p = PestanaPresupuestos(conn)
    win.setCentralWidget(p)
    win.show()

    # Find an active budget
    c = conn.cursor()
    c.execute("SELECT id_documento FROM documentos WHERE tipo='PRESUPUESTO' AND estado='ACTIVO' LIMIT 1")
    row = c.fetchone()
    if not row:
        print("No active budget found")
        sys.exit(0)
        
    id_doc = row[0]
    print(f"Triggering edit for {id_doc}")
    
    # Try triggering it directly
    try:
        p._editar_presupuesto(id_doc)
        print("Edit dialog finished successfully")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test()
