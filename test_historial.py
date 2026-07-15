import sqlite3
import sys
from PyQt6.QtWidgets import QApplication
from ui.modules.stock.ajustes_stock import DialogoHistorialMovimientos

def test():
    app = QApplication(sys.argv)
    conn = sqlite3.connect('corralon_profesional.db')
    d = DialogoHistorialMovimientos(conn)
    print("Test OK")
    
if __name__ == '__main__':
    test()
