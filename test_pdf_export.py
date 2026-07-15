import sqlite3
import sys
import os
from PyQt6.QtWidgets import QApplication
from utils.pdf_generator import generar_html_presupuesto, guardar_pdf_presupuesto
import db.queries_presupuestos as qp

def test():
    app = QApplication(sys.argv)
    conn = sqlite3.connect('corralon_profesional.db')
    c = conn.cursor()
    c.execute("SELECT id_documento FROM documentos WHERE tipo='PRESUPUESTO' LIMIT 1")
    row = c.fetchone()
    if not row:
        print("No active budget found")
        sys.exit(0)
        
    det = qp.obtener_detalle_presupuesto(conn, row[0])
    
    out_file = os.path.join(os.getcwd(), "test_presupuesto.pdf")
    try:
        guardar_pdf_presupuesto(det, out_file)
        print(f"PDF generated correctly at: {out_file}")
    except Exception as e:
        print(f"Crash during PDF gen: {e}")

if __name__ == '__main__':
    test()
