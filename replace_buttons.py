import os

def replace_button_texts():
    replacements = [
        ('\"✅ Confirmar Importación\"', '\"Confirmar Importación\"'),
        ('\"📂 Seleccionar Excel\"', '\"Seleccionar Excel\"'),
        ('\"📂 Abrir Documento\"', '\"Abrir Documento\"'),
        ('\"📂 Abrir Archivo\"', '\"Abrir Archivo\"'),
        ('\"👁 Ver Detalle\"', '\"Ver Detalle\"'),
        ('\"👁 Ver detalle\"', '\"Ver detalle\"'),
        ('\"✎ Editar\"', '\"Editar\"'),
        ('\"⬇ Guardar como PDF\"', '\"Guardar como PDF\"'),
        ('\"❌ Anular Presupuesto\"', '\"✕ Anular Presupuesto\"'),
        ('\"📜 Historial\"', '\"Historial\"'),
        ('\"📊 Excel ▾\"', '\"Excel ▾\"'),
        ('\"📥 Importar...\"', '\"Importar...\"'),
        ('\"♻️\"', '\"🗘\"'),
        ('\"💲 Modificar precio\"', '\"Modificar precio\"'),
        ('\"📥 Entrada de stock\"', '\"Entrada de stock\"'),
        ('\"📖 Guía de Uso: Control de Stock\"', '\"Guía de Uso: Control de Stock\"'),
        ('\"⏸️ Desactivar producto\\n(Recomendado. Conserva historial.)\"', '\"Desactivar producto\\n(Recomendado. Conserva historial.)\"')
    ]

    for root, dirs, files in os.walk('ui'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for old, new in replacements:
                    new_content = new_content.replace(old, new)
                
                if new_content != content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f'Updated {path}')

replace_button_texts()
