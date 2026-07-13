import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout
from ui.dialogs_stock import ImageSelectorWidget

def main():
    app = QApplication(sys.argv)
    
    dlg = QDialog()
    ly = QVBoxLayout(dlg)
    sel = ImageSelectorWidget()
    ly.addWidget(sel)
    
    # Pre-set image to see if it shows on load
    dummy_src = Path("dummy_src.jpg")
    if not dummy_src.exists():
        from PyQt6.QtGui import QPixmap
        pix = QPixmap(100, 100)
        pix.fill()
        pix.save(str(dummy_src))
        
    sel.image_path = str(dummy_src.resolve())
    sel._update_preview()
    
    print(f"Is preview visible? {sel.lbl_preview.isVisible()}")
    
    dlg.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
