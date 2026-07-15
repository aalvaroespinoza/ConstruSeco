import sqlite3
import sys
from PyQt6.QtWidgets import QApplication, QTextBrowser, QDialog, QVBoxLayout
from utils.pdf_generator import generar_html_presupuesto
import db.queries_presupuestos as qp

def test():
    app = QApplication(sys.argv)
    conn = sqlite3.connect('corralon_profesional.db')
    det = qp.obtener_detalle_presupuesto(conn, 1) # Assuming ID 1 exists, or we fetch the first one
    if not det:
        c = conn.cursor()
        c.execute("SELECT id_documento FROM documentos WHERE tipo='PRESUPUESTO' LIMIT 1")
        row = c.fetchone()
        if row:
            det = qp.obtener_detalle_presupuesto(conn, row[0])
            
    html = generar_html_presupuesto(det)
    
    d = QDialog()
    d.resize(800, 900)
    l = QVBoxLayout(d)
    t = QTextBrowser()
    t.setHtml(html)
    l.addWidget(t)
    # d.exec() # Don't block
    print("HTML length:", len(html))

if __name__ == '__main__':
    test()
