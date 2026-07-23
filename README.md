# ConstruSeco Pereyra

Sistema de gestión comercial (POS + stock) para una casa de materiales de construcción
(PVC). Desarrollado a medida para uso local en un único puesto de trabajo.

## Stack

- **Python 3** + **PyQt6** para la interfaz de escritorio.
- **SQLite** como base de datos local (un único archivo, sin servidor).
- **openpyxl** para importación/exportación de stock a Excel.
- **ReportLab** / **PyMuPDF** para generación y visualización de PDFs (presupuestos).

## Funcionalidades

- **Venta**: carrito rápido con búsqueda de productos por código o descripción, cálculo
  de descuentos e IVA, control de stock disponible (ATP).
- **Presupuestos**: mismo flujo que Venta, con reserva temporal de stock (48hs) y
  vencimiento automático.
- **Múltiples operaciones simultáneas**: se pueden tener varias ventas y/o presupuestos
  abiertos a la vez (sección "En curso" en la barra lateral), sin perder el progreso de
  ninguno al cambiar de pantalla.
- **Control de Stock**: catálogo de productos, conversión de unidades, alertas de stock
  bajo/agotado, importación/exportación por Excel.
- **Clientes**: ficha de cliente, contactos, notas, historial de operaciones.
- **Inicio**: pantalla de resumen con indicadores de stock, presupuestos por vencer y
  productos más vendidos.

## Instalación (entorno de desarrollo)

Requiere Python 3.11+.

```bash
git clone https://github.com/aalvaroespinoza/ConstruSeco.git
cd ConstruSeco
pip install -r requirements.txt
python main.py
```

La base de datos (`corralon_profesional.db`) se crea automáticamente en el primer
arranque, en la misma carpeta del proyecto (o del ejecutable, si es una versión
empaquetada). **No se versiona en git** — cada instalación tiene su propia base local.

## Generar un ejecutable (Windows)

```bash
pip install pyinstaller
pyinstaller --windowed --onedir --name ConstruSecoPereyra --icon=assets/logo.ico main.py --add-data "assets;assets"
```

Esto genera una carpeta portable en `dist/ConstruSecoPereyra/`. La base de datos se crea
junto al ejecutable, así que conviene ubicar esa carpeta en un lugar con permisos de
escritura normales (Escritorio, Documentos) y no dentro de `Program Files`.

**Backup**: al no haber respaldo automático todavía, se recomienda copiar el archivo
`corralon_profesional.db` a un pendrive o a la nube de forma periódica (al menos
semanal) hasta que se implemente un backup automático.

## Estructura del proyecto

```
db/          Acceso a datos y queries organizadas por módulo (ventas, stock, clientes, presupuestos)
ui/
  core/      Tema visual, componentes modales base
  components/ Widgets reutilizables (buscador, carrito, encabezados)
  modules/   Una carpeta por pantalla (ventas, stock, clientes, presupuestos, inicio)
utils/       Utilidades generales (rutas de archivos, generación de PDF)
assets/      Íconos, logo, imágenes de productos
```

## Estado del proyecto

Primera versión en uso real. Sin suite de tests automatizada todavía. Se recomienda
acompañamiento cercano durante las primeras semanas de uso y reportar cualquier
comportamiento inesperado.
