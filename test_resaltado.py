import sys
import sqlite3
from PyQt6.QtWidgets import QApplication
from ui.stock import PestanaStock

def run_test():
    app = QApplication(sys.argv)
    conn = sqlite3.connect('corralon_profesional.db')

    ventana = PestanaStock(conn)
    ventana.show()
    
    # We will pick a valid codigo from the db
    c = conn.cursor()
    c.execute("SELECT codigo FROM productos LIMIT 1")
    res = c.fetchone()
    if res:
        codigo = res[0]
        print(f"--- LLAMADA DE PRUEBA TEMPORAL: {codigo} ---")
        ventana.resaltar_producto_por_codigo(codigo)
        
    sys.exit(0)

if __name__ == '__main__':
    run_test()
