with open('ui/core/modal.py', 'r', encoding='utf-8') as f:
    text = f.read()

helper = '''

def preparar_combo_wayland(combo):
    """Fix z-order of QComboBox popups on Wayland inside Modals."""
    from PyQt6.QtCore import Qt
    combo.view().window().setParent(None)
    combo.view().window().setWindowFlag(Qt.WindowType.Popup)
    return combo
'''

if 'preparar_combo_wayland' not in text:
    with open('ui/core/modal.py', 'a', encoding='utf-8') as f:
        f.write(helper)

import re
import os

files_to_patch = [
    'ui/modules/clientes/dialogs_clientes.py',
    'ui/modules/clientes/dialogs_historial.py',
    'ui/modules/stock/dialogs_stock.py',
    'ui/modules/stock/ajustes_stock.py',
    'ui/modules/ventas/tab_ventas.py',
]

for filepath in files_to_patch:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if 'preparar_combo_wayland' not in content:
        # Import it at the top of the file
        content = re.sub(r'from PyQt6\.QtWidgets import \(?', r'from ui.core.modal import preparar_combo_wayland\nfrom PyQt6.QtWidgets import (', content)
        
        # In files that don't match the parens import format:
        if 'from ui.core.modal import preparar_combo_wayland' not in content:
            content = content.replace('from PyQt6.QtWidgets import', 'from ui.core.modal import preparar_combo_wayland\nfrom PyQt6.QtWidgets import')

        # Replace QComboBox() with preparar_combo_wayland(QComboBox())
        content = content.replace('QComboBox()', 'preparar_combo_wayland(QComboBox())')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
