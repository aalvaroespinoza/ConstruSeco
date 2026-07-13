import sys
import sqlite3
import datetime
from pathlib import Path

from db.queries import obtener_stocks_todos
from ui.dialogs_stock import ASSETS_PROD_DIR, ImageSelectorWidget

def run_tests():
    conn = sqlite3.connect('corralon_profesional.db')
    c = conn.cursor()
    
    # [Test 1] Create dummy image
    ASSETS_PROD_DIR.mkdir(parents=True, exist_ok=True)
    dummy_img = ASSETS_PROD_DIR / "dummy_test.jpg"
    with open(dummy_img, "w") as f:
        f.write("fake image data")
        
    print(f"Dummy img exists: {dummy_img.exists()}")
    
    # Simulate saving a new product with this image using ImageSelectorWidget logic
    sel = ImageSelectorWidget(current_image_path=str(dummy_img))
    final_path = sel.get_final_path("TEST-001")
    print(f"final_path returned: {final_path}")
    
    # Save into DB
    c.execute("""
        INSERT INTO productos (codigo, descripcion, precio_venta, imagen_path)
        VALUES ('TEST-001', 'Test', 100.0, ?)
        ON CONFLICT(codigo) DO UPDATE SET imagen_path=excluded.imagen_path
    """, (final_path,))
    conn.commit()
    
    # Verify retrieval
    productos = obtener_stocks_todos(conn)
    prod = next((p for p in productos if p['codigo'] == 'TEST-001'), None)
    print(f"Product retrieved: {prod['codigo']}")
    print(f"Image path from DB: {prod['imagen_path']}")
    
    # Delete test product
    c.execute("DELETE FROM productos WHERE codigo='TEST-001'")
    conn.commit()
    dummy_img.unlink()
    
    # Clean copied images
    for f in ASSETS_PROD_DIR.glob("TEST-001_*.jpg"):
        f.unlink()

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    run_tests()
    print("ALL TESTS COMPLETED SUCCESSFULLY")
