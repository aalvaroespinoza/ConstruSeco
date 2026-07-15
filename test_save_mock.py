import sqlite3
import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui.modules.presupuestos.tab_presupuestos import DialogoEditarPresupuesto
import ui.modules.ventas.tab_ventas as tv

# Mock modal_exito.exec
class DummyModal:
    def __init__(self, *args, **kwargs):
        pass
    def exec(self):
        print("MOCKED EXITO MODAL EXEC")

tv.DialogoVentaExitosa = DummyModal

# Mock QMessageBox to prevent blocking
def mock_critical(*args, **kwargs):
    print("MOCKED CRITICAL:", args, kwargs)

QMessageBox.critical = mock_critical
QMessageBox.warning = mock_critical
QMessageBox.information = mock_critical

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
    print("Saving...")
    d.pestana_venta.confirmar_operacion('PRESUPUESTO')
    print("Test finished.")

if __name__ == '__main__':
    test()
