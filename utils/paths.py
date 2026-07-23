import sys
import os
from pathlib import Path

def get_resource_path(relative_path: str | Path) -> str:
    """
    Obtiene la ruta absoluta a un recurso estático (imágenes, iconos, fuentes),
    compatible con el ejecutable generado por PyInstaller (sys._MEIPASS).
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = Path(sys._MEIPASS)
    else:
        # En desarrollo, la raíz del proyecto (padre de la carpeta 'utils')
        base_path = Path(__file__).resolve().parent.parent

    return str(base_path / str(relative_path))

def get_data_path(relative_path: str | Path) -> str:
    """
    Obtiene la ruta absoluta a un archivo de datos persistente (como la base de datos),
    asegurando que se encuentre en el mismo directorio del ejecutable o script original,
    para evitar perder datos en la carpeta temporal de PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        # Si es un ejecutable de PyInstaller, la carpeta del ejecutable:
        base_path = Path(sys.executable).parent
    else:
        # Si es un script en desarrollo, la raíz del proyecto
        base_path = Path(__file__).resolve().parent.parent

    return str(base_path / str(relative_path))
