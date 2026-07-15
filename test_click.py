import sqlite3
import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt6.QtCore import QTimer
from ui.modules.presupuestos.tab_presupuestos import PestanaPresupuestos

def my_excepthook(type, value, tback):
    print("CRASH DETECTED!")
    traceback.print_exception(type, value, tback)
    sys.exit(1)

sys.excepthook = my_excepthook

def test():
    app = QApplication(sys.argv)
    conn = sqlite3.connect('corralon_profesional.db')
    
    win = QMainWindow()
    win.resize(1024, 768)
    p = PestanaPresupuestos(conn)
    win.setCentralWidget(p)
    win.show()

    c = conn.cursor()
    c.execute("SELECT id_documento FROM documentos WHERE tipo='PRESUPUESTO' LIMIT 1")
    row = c.fetchone()
    if not row:
        print("No active budget found")
        sys.exit(0)
    
    def trigger():
        try:
            print("Clicking edit...")
            # Simulamos el click de la celda de acciones
            p._editar_presupuesto(row[0])
            print("Edit dialog finished successfully")
        except Exception as e:
            print("EXCEPTION CAUGHT!")
            traceback.print_exc()
        finally:
            app.quit()
            
    QTimer.singleShot(1000, trigger)
    app.exec()

if __name__ == '__main__':
    test()
