import sys
import shutil
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtGui import QPixmap
from ui.dialogs_stock import ImageSelectorWidget, ASSETS_PROD_DIR

def run_diagnostics():
    app = QApplication(sys.argv)
    
    # Create a dummy real image file to simulate user selecting from desktop
    dummy_src = Path("dummy_src.jpg")
    pix = QPixmap(100, 100)
    pix.fill()
    pix.save(str(dummy_src))
    
    # Mock QFileDialog
    def mock_getOpenFileName(*args, **kwargs):
        print(f"[IMG] Archivo seleccionado: {dummy_src.resolve()}")
        return str(dummy_src.resolve()), "Images (*.png *.jpg *.jpeg)"
    
    QFileDialog.getOpenFileName = mock_getOpenFileName
    
    selector = ImageSelectorWidget()
    print(f"[IMG] Estado inicial lbl_preview visible: {selector.lbl_preview.isVisible()}")
    
    # Simulate click
    selector.btn_select.click()
    
    print(f"[IMG] Atributo interno del selector: {selector.image_path}")
    
    # Verify Pixmap
    pm = selector.lbl_preview.pixmap()
    if pm:
        print(f"[IMG] QPixmap en label válido: {not pm.isNull()}, tamaño: {pm.size()}")
    else:
        print(f"[IMG] QPixmap en label es None")
        
    print(f"[IMG] lbl_preview visible despues de clic: {selector.lbl_preview.isVisible()}")
    
    # Simulate save
    final_val = selector.get_final_path("TEST-999")
    print(f"[IMG] Valor entregado al guardar: {final_val}")
    
    if final_val:
        dest_path = ASSETS_PROD_DIR / final_val
        print(f"[IMG] Archivo destino: {dest_path}")
        print(f"[IMG] Existe destino después de guardar: {dest_path.exists()}")
    
    # Clean up
    dummy_src.unlink(missing_ok=True)
    if final_val:
        (ASSETS_PROD_DIR / final_val).unlink(missing_ok=True)

if __name__ == "__main__":
    run_diagnostics()
