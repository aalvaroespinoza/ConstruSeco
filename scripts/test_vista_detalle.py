import sys
import io
from PyQt6.QtWidgets import QApplication
from ui.dialogs_stock import VistaDetalleProducto

app = QApplication(sys.argv)

producto_con_imagen = {
    "codigo": "P-001",
    "descripcion": "Cemento Loma Negra",
    "unidad_base": "Bolsa",
    "precio_venta": 1500.50,
    "stock_minimo": 10.0,
    "activo": 1,
    "stock_fisico": 50.0,
    "comprometido": 5.0,
    "atp": 45.0,
    "imagen_path": "no_importa.jpg"
}

producto_sin_imagen = {
    "codigo": "P-002",
    "descripcion": "Arena",
    "unidad_base": "m3",
    "precio_venta": 8500.0,
    "stock_minimo": 5.0,
    "activo": 1,
    "stock_fisico": 20.0,
    "comprometido": 0.0,
    "atp": 20.0
}

try:
    from PyQt6.QtWidgets import QWidget
    dummy_parent = QWidget()
    
    print("Test producto con imagen...")
    v1 = VistaDetalleProducto(producto_con_imagen, dummy_parent)
    print("OK: Producto con imagen instanciado sin KeyError.")

    print("Test producto sin imagen...")
    v2 = VistaDetalleProducto(producto_sin_imagen, dummy_parent)
    print("OK: Producto sin imagen instanciado sin KeyError.")
    
    print("TODO OK")
except Exception as e:
    print(f"ERROR: {type(e).__name__} - {e}")
    sys.exit(1)

sys.exit(0)
