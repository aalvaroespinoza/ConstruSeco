import sys
import sqlite3
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from ui.dialogs_stock import DialogoAgregarProducto, ASSETS_PROD_DIR
from ui.stock import PestanaStock

def run_gui_test():
    app = QApplication(sys.argv)
    conn = sqlite3.connect('corralon_profesional.db')
    
    # Pre-create an image
    dummy = Path("test_gui_img.png")
    if not dummy.exists():
        from PyQt6.QtGui import QPixmap
        p = QPixmap(200, 200)
        p.fill()
        p.save(str(dummy))
        
    dlg = DialogoAgregarProducto(conn)
    
    def step1():
        print("[TEST] Step 1: Set text")
        dlg.inp_codigo.setText("GUI-001")
        dlg.inp_desc.setText("Test GUI Product")
        dlg.inp_precio.setText("999.0")
        dlg.inp_stock_min.setText("5")
        QTimer.singleShot(500, step2)
        
    def step2():
        print("[TEST] Step 2: Simulate image selection")
        # Override file dialog to simulate user interaction
        from PyQt6.QtWidgets import QFileDialog
        QFileDialog.getOpenFileName = lambda *args, **kwargs: (str(dummy.resolve()), "")
        
        dlg.img_selector.btn_select.click()
        
        # Verify if preview is visible
        print(f"[TEST] lbl_preview visible? {dlg.img_selector.lbl_preview.isVisible()}")
        print(f"[TEST] image_path in selector: {dlg.img_selector.image_path}")
        
        QTimer.singleShot(500, step3)
        
    def step3():
        print("[TEST] Step 3: Save product")
        dlg.btn_guardar.click()
        # Since it calls QMessageBox on success, we need to bypass or mock it
        # Actually it's better to just call dlg.guardar() and mock QMessageBox
        # I'll just check the DB after closing
        
    # Mock QMessageBox to prevent blocking
    from PyQt6.QtWidgets import QMessageBox
    QMessageBox.information = lambda *args: print("[TEST] Mock QMessageBox information")
    QMessageBox.critical = lambda *args: print("[TEST] Mock QMessageBox critical")
    
    QTimer.singleShot(500, step1)
    
    # We close the dialog after 2 seconds
    QTimer.singleShot(2000, dlg.reject)
    
    dlg.exec()
    
    # Verify DB
    c = conn.cursor()
    c.execute("SELECT imagen_path FROM productos WHERE codigo='GUI-001'")
    row = c.fetchone()
    print(f"[TEST] Row in DB: {row}")
    if row and row[0]:
        print(f"[TEST] File exists in assets? {(ASSETS_PROD_DIR / row[0]).exists()}")
        
    c.execute("DELETE FROM productos WHERE codigo='GUI-001'")
    conn.commit()
    dummy.unlink(missing_ok=True)
    
    print("[TEST] GUI test finished")

if __name__ == '__main__':
    run_gui_test()
