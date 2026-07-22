import shutil
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from ui.core.theme import COLOR_BORDER, COLOR_BG, COLOR_PRIMARY

# Rutas - PROJECT_ROOT está a 3 niveles (ui/components/image_selector.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_PROD_DIR = PROJECT_ROOT / "assets" / "productos"
ASSETS_PROD_DIR.mkdir(parents=True, exist_ok=True)


def resolver_ruta_imagen(imagen_path):
    """
    Función centralizada para resolver la ruta física de una imagen a partir de su referencia.
    Soporta: None, "", nombres de archivo relativos, y rutas absolutas antiguas.
    Devuelve un objeto Path si existe el archivo, o None.
    """
    if not imagen_path:
        return None
    p = Path(imagen_path)
    if not p.is_absolute():
        p = ASSETS_PROD_DIR / p.name
    return p if p.exists() else None


class ImageSelectorWidget(QFrame):
    """Widget reutilizable para seleccionar, previsualizar y eliminar imagen."""
    def __init__(self, current_image_path=None):
        super().__init__()
        self.setStyleSheet(f"border: 2px dashed {COLOR_BORDER}; border-radius: 6px; background-color: {COLOR_BG};")
        self.setFixedSize(120, 120)
        self.image_path = current_image_path

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)
        
        self.btn_select = QPushButton("+")
        self.btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select.setToolTip("Agregar Imagen")
        self.btn_select.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; font-size: 48px; color: #94a3b8; font-weight: bold; }}
            QPushButton:hover {{ color: {COLOR_PRIMARY}; background: transparent; border: none; }}
        """)
        self.btn_select.clicked.connect(self._select_image)
        
        self.lbl_preview = QLabel()
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setStyleSheet("border: none; background: transparent;")
        self.lbl_preview.setScaledContents(True)
        self.lbl_preview.hide()
        
        self.btn_clear = QPushButton("✕")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setToolTip("Eliminar Imagen")
        self.btn_clear.setStyleSheet(f"""
            QPushButton {{ background: white; border: 1px solid {COLOR_BORDER}; border-radius: 12px; font-family: "Segoe UI", Arial, sans-serif; font-size: 12px; font-weight: bold; padding: 0px; margin: 0px; color: red; }}
        """)
        self.btn_clear.setFixedSize(24, 24)
        self.btn_clear.clicked.connect(self._clear_image)
        
        # Superponer boton clear
        btns_layout = QHBoxLayout()
        btns_layout.setContentsMargins(0,0,0,0)
        btns_layout.addStretch()
        btns_layout.addWidget(self.btn_clear)
        
        self.layout.addLayout(btns_layout)
        self.layout.addWidget(self.btn_select, stretch=1)
        self.layout.addWidget(self.lbl_preview, stretch=1)
        
        self._update_preview()

    def _select_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Imagen del Producto", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_name:
            self.image_path = file_name
            self._update_preview()

    def _clear_image(self):
        self.image_path = None
        self._update_preview()

    def _update_preview(self):
        p = resolver_ruta_imagen(self.image_path)
        if p:
            pixmap = QPixmap(p.as_posix())
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
                self.lbl_preview.setPixmap(scaled_pixmap)
                self.btn_select.hide()
                self.lbl_preview.show()
                self.btn_clear.show()
                return
                
        self._hide_preview()

    def _hide_preview(self):
        self.lbl_preview.clear()
        self.lbl_preview.hide()
        self.btn_select.show()
        self.btn_clear.hide()

    def get_final_path(self, codigo_producto: str):
        if not self.image_path:
            return None
            
        p = Path(self.image_path)
        if not p.is_absolute():
            return p.name
            
        if ASSETS_PROD_DIR.resolve() in p.resolve().parents:
            return p.name
            
        ext = p.suffix.lower()
        new_name = f"{codigo_producto}_{int(datetime.now().timestamp())}{ext}"
        dest = ASSETS_PROD_DIR / new_name
        try:
            shutil.copy2(p, dest)
            return dest.name
        except Exception as e:
            print(f"Error copiando imagen: {e}")
            return None
