import sqlite3
import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton
from ui.modules.presupuestos.tab_presupuestos import PestanaPresupuestos

def my_excepthook(type, value, tback):
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
    
    # Try triggering it directly using QTimer so the event loop is running
    from PyQt6.QtCore import QTimer
    def trigger():
        try:
            print("Triggering edit...")
            p._editar_presupuesto(row[0])
            print("Edit dialog closed normally")
        except Exception as e:
            traceback.print_exc()
        finally:
            app.quit()
            
    QTimer.singleShot(500, trigger)
    app.exec()

if __name__ == '__main__':
    test()
