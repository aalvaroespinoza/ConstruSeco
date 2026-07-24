import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                             QSpacerItem, QSizePolicy, QFrame,
                             QLineEdit, QFormLayout, QPushButton, QFileDialog)
from PyQt6.QtCore import Qt, QSettings
from utils.paths import get_data_path
from ui.core.modal import DialogoModalIntegrado

class DialogoMensaje(DialogoModalIntegrado):
    def __init__(self, titulo, mensaje, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(350)
        
        ly = QVBoxLayout(self)
        lbl = QLabel(mensaje)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 13px; color: #334155; border: none;")
        
        btn_ok = QPushButton("Aceptar")
        btn_ok.setFixedSize(120, 32)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        btn_ok.clicked.connect(self.accept)
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        
        ly.addWidget(lbl)
        ly.addSpacing(15)
        ly.addWidget(btn_ok, alignment=Qt.AlignmentFlag.AlignCenter)

class PestanaAjustes(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pestana_ajustes")
        self.setStyleSheet("background-color: #f8fafc;")
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(20)

        self.tarjeta = QFrame()
        self.tarjeta.setObjectName("tarjeta_blanca")
        self.tarjeta.setStyleSheet("""
            QFrame#tarjeta_blanca {
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
            }
        """)
        
        layout_tarjeta = QVBoxLayout(self.tarjeta)
        layout_tarjeta.setContentsMargins(25, 25, 25, 25)
        layout_tarjeta.setSpacing(15)

        lbl_titulo = QLabel("Ajustes")
        lbl_titulo.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1e293b;
            font-family: 'Segoe UI', sans-serif;
            border: none;
        """)
        
        layout_tarjeta.addWidget(lbl_titulo)
        
        self.layout_secciones = QVBoxLayout()
        self.layout_secciones.setSpacing(15)
        
        self.settings = QSettings("ConstruSeco", "ERP")
        
        # --- SECCIÓN: Datos de la Empresa ---
        lbl_seccion_empresa = QLabel("Datos de la Empresa")
        lbl_seccion_empresa.setStyleSheet("font-weight: bold; color: #475569; font-size: 14px; margin-top: 10px; border: none;")
        
        frame_empresa = QFrame()
        frame_empresa.setStyleSheet("QFrame { background-color: #f8fafc; border-radius: 6px; border: 1px solid #e2e8f0; }")
        layout_empresa = QFormLayout(frame_empresa)
        layout_empresa.setContentsMargins(15, 15, 15, 15)
        layout_empresa.setSpacing(15)
        
        estilo_input = """
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                color: #1e293b;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
        """
        
        self.input_cuit = QLineEdit()
        self.input_cuit.setStyleSheet(estilo_input)
        self.input_cuit.setText(self.settings.value("empresa_cuit", "", type=str))
        
        self.input_direccion = QLineEdit()
        self.input_direccion.setStyleSheet(estilo_input)
        self.input_direccion.setText(self.settings.value("empresa_direccion", "", type=str))
        
        self.input_telefono = QLineEdit()
        self.input_telefono.setStyleSheet(estilo_input)
        self.input_telefono.setText(self.settings.value("empresa_telefono", "", type=str))
        
        layout_empresa.addRow("CUIT:", self.input_cuit)
        layout_empresa.addRow("Dirección:", self.input_direccion)
        layout_empresa.addRow("Teléfono:", self.input_telefono)
        
        self.input_cuit.editingFinished.connect(lambda: self.settings.setValue("empresa_cuit", self.input_cuit.text().strip()))
        self.input_direccion.editingFinished.connect(lambda: self.settings.setValue("empresa_direccion", self.input_direccion.text().strip()))
        self.input_telefono.editingFinished.connect(lambda: self.settings.setValue("empresa_telefono", self.input_telefono.text().strip()))
        
        self.layout_secciones.addWidget(lbl_seccion_empresa)
        self.layout_secciones.addWidget(frame_empresa)
        
        # --- SECCIÓN: Copia de Seguridad ---
        lbl_seccion_backup = QLabel("Copia de Seguridad")
        lbl_seccion_backup.setStyleSheet("font-weight: bold; color: #475569; font-size: 14px; margin-top: 10px; border: none;")
        
        frame_backup = QFrame()
        frame_backup.setStyleSheet("QFrame { background-color: #f8fafc; border-radius: 6px; border: 1px solid #e2e8f0; }")
        layout_backup = QVBoxLayout(frame_backup)
        layout_backup.setContentsMargins(15, 15, 15, 15)
        layout_backup.setSpacing(10)
        
        lbl_desc_backup = QLabel("Realiza un respaldo manual de la base de datos actual.")
        lbl_desc_backup.setStyleSheet("color: #64748b; font-size: 12px; border: none;")
        
        self.btn_backup = QPushButton("Guardar copia de seguridad ahora")
        self.btn_backup.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_backup.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 8px 16px;
                color: #0f172a;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        self.btn_backup.clicked.connect(self.realizar_backup)
        
        layout_backup.addWidget(lbl_desc_backup)
        layout_backup.addWidget(self.btn_backup, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.layout_secciones.addWidget(lbl_seccion_backup)
        self.layout_secciones.addWidget(frame_backup)
        
        layout_tarjeta.addLayout(self.layout_secciones)
        layout_tarjeta.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        layout_principal.addWidget(self.tarjeta)

    def realizar_backup(self):
        fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_sugerido = f"backup_construseco_{fecha_actual}.db"
        
        ruta_destino, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Copia de Seguridad",
            nombre_sugerido,
            "Base de datos SQLite (*.db)"
        )
        
        if ruta_destino:
            try:
                ruta_origen = get_data_path()
                shutil.copy(ruta_origen, ruta_destino)
                dlg = DialogoMensaje("Backup Exitoso", f"La copia de seguridad se guardó correctamente en:\n{ruta_destino}", self.window())
                dlg.exec()
            except Exception as e:
                dlg = DialogoMensaje("Error de Backup", f"No se pudo crear la copia de seguridad:\n{str(e)}", self.window())
                dlg.exec()
