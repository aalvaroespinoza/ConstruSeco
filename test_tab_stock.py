import sys
import sqlite3
from PyQt6.QtWidgets import QApplication
from ui.modules.stock.tab_stock import PestanaStock

def test():
    app = QApplication(sys.argv)
    conn = sqlite3.connect('corralon_profesional.db')
    p = PestanaStock(conn)
    print("Test: PestanaStock instantiated successfully.")
    
if __name__ == "__main__":
    test()
