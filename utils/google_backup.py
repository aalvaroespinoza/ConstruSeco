import os
import socket
import datetime
import shutil
import sqlite3
from utils.paths import get_data_path, get_resource_path

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    GOOGLE_API_DISPONIBLE = True
except ImportError:
    GOOGLE_API_DISPONIBLE = False

# Permisos para gestionar archivos creados por esta app (mejor práctica)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def obtener_credenciales_google():
    """
    Gestiona el flujo OAuth de Google para obtener o renovar las credenciales.
    Guarda el token localmente para evitar autenticaciones repetidas.
    Requiere un archivo 'credentials.json' en el directorio de datos de la app.
    """
    if not GOOGLE_API_DISPONIBLE:
        raise ImportError("Las dependencias de Google no están instaladas. Ejecutá pip install -r requirements.txt")

    creds = None
    # Usamos get_data_path para guardar el token en la misma carpeta de datos
    token_path = get_data_path('token_google.json')
    credentials_path = get_resource_path('secrets/credentials.json')

    # Intentar cargar credenciales guardadas previamente
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # Si no hay credenciales válidas, realizar el flujo de autorización
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"No se encontró el archivo de credenciales en: {credentials_path}\n"
                    "Por favor, descargue sus credenciales OAuth de Google Cloud Console "
                    "y guárdelas con el nombre 'credentials.json' en esa ruta."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Guardar las credenciales para el próximo uso
        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())

    return creds

def verificar_conexion_internet(host="8.8.8.8", port=53, timeout=3):
    """
    Verifica si hay conexión a internet intentando conectar a un servidor conocido.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

def agregar_fila_operacion(datos, sheet_id=None):
    """
    Agrega una fila al Google Sheet configurado con los datos de la operación.
    Falla en silencio retornando False si ocurre algún error.
    """
    if not GOOGLE_API_DISPONIBLE:
        return False, "Las dependencias de Google no están instaladas."

    if not verificar_conexion_internet():
        return False, "No hay conexión a internet."
        
    if not sheet_id:
        from PyQt6.QtCore import QSettings
        settings = QSettings("ConstruSeco", "ERP")
        sheet_id = settings.value("google_sheet_id", "")
        
    if not sheet_id:
        return False, "ID de Google Sheet no configurado."
        
    try:
        creds = obtener_credenciales_google()
        if not creds:
            return False, "No se obtuvieron credenciales."
            
        service = build('sheets', 'v4', credentials=creds)
        
        fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tipo = "Venta" if datos.get('tipo') == "VENTA" else ("Presupuesto" if datos.get('tipo') == "PRESUPUESTO" else datos.get('tipo', 'Desconocido'))
        
        cliente_info = datos.get('cliente')
        cliente_nombre = cliente_info['nombre'] if cliente_info else "Cons. Final"
        
        items = datos.get('items', 0)
        total = datos.get('total', 0.0)
        
        valores = [[fecha_hora, tipo, cliente_nombre, items, total]]
        
        body = {'values': valores}
        
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range="Historial!A:Z",
            valueInputOption="RAW",
            body=body
        ).execute()
        
        return True, "Fila agregada correctamente."
        
    except Exception as e:
        return False, f"Error al sincronizar con Sheets: {str(e)}"

def desvincular_cuenta_google():
    """
    Elimina el token de acceso local, desvinculando la cuenta de Google.
    """
    token_path = get_data_path('token_google.json')
    try:
        if os.path.exists(token_path):
            os.remove(token_path)
        return True
    except Exception:
        return False
