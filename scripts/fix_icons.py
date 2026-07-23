import os
import re

directory = r'C:\Users\alvar\Documents\Sistema ConstruSeco\ui'

# Definir reglas de reemplazo
replacements = [
    # Reemplazar emojis mal formados o inconsistentes
    (r'"\+\s+', '"➕ '),
    (r'"\+"', '"➕"'),
    (r'"✏\s+', '"✏️ '),
    (r'"⚙\s+', '"⚙️ '),
    (r'"⋯"', '"⋮"'),
    (r'"←\s+', '"◀ '),
    (r'\s+→"', ' ▶"'),
    
    # Agregar iconos a botones comunes que no tienen
    (r'QPushButton\("Cerrar"\)', 'QPushButton("✕ Cerrar")'),
    (r'QPushButton\("Cerrar Ayuda"\)', 'QPushButton("✕ Cerrar Ayuda")'),
    (r'QPushButton\("Cancelar"\)', 'QPushButton("✕ Cancelar")'),
    (r'QPushButton\("Aceptar"\)', 'QPushButton("✓ Aceptar")'),
    (r'QPushButton\("Guardar"\)', 'QPushButton("💾 Guardar")'),
    (r'QPushButton\("Guardar Configuración"\)', 'QPushButton("💾 Guardar Configuración")'),
    (r'QPushButton\("Guardar Producto"\)', 'QPushButton("💾 Guardar Producto")'),
    (r'QPushButton\("Agregar"\)', 'QPushButton("➕ Agregar")'),
    (r'QPushButton\("Limpiar"\)', 'QPushButton("🧹 Limpiar")'),
    (r'QPushButton\("Vista Previa"\)', 'QPushButton("👁️ Vista Previa")'),
    (r'QPushButton\("Ver detalle"\)', 'QPushButton("👁️ Ver Detalle")'),
    (r'QPushButton\("Generar PDF"\)', 'QPushButton("📄 Generar PDF")'),
    (r'QPushButton\("Exportar PDF"\)', 'QPushButton("📤 Exportar PDF")'),
    (r'QPushButton\("PDF"\)', 'QPushButton("📄 PDF")'),
    (r'QPushButton\("Editar"\)', 'QPushButton("✏️ Editar")'),
    (r'QPushButton\("Anular"\)', 'QPushButton("✕ Anular")'),
    (r'QPushButton\("Confirmar Venta"\)', 'QPushButton("✓ Confirmar Venta")'),
    (r'QPushButton\("Anterior"\)', 'QPushButton("◀ Anterior")'),
    (r'QPushButton\("Siguiente"\)', 'QPushButton("Siguiente ▶")'),
    
    # Arreglar mayúsculas inconsistentes en botones
    (r'QPushButton\("✏️ Editar cliente"\)', 'QPushButton("✏️ Editar Cliente")'),
    (r'QPushButton\("📋 Ver historial completo"\)', 'QPushButton("📋 Ver Historial Completo")'),
    (r'QPushButton\("Vaciar \[F11\]"\)', 'QPushButton("🗑️ Vaciar [F11]")'),
]

for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            new_content = content
            for old, new in replacements:
                new_content = re.sub(old, new, new_content)
                
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Modified: {path}')

print("Done.")
