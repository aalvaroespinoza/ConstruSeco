import os
import re

files = [
    "ui/core/theme.py",
    "ui/modules/clientes/tab_clientes.py",
    "ui/modules/stock/tab_stock.py",
    "ui/modules/presupuestos/tab_presupuestos.py"
]

for file_path in files:
    if not os.path.exists(file_path):
        continue
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # We need to replace different variations of QTableWidget::item:selected {{ ... }}
    # Variation 1: ui/core/theme.py
    content = re.sub(
        r'QTableWidget::item:selected\s*\{\{\s*background-color:\s*#[a-f0-9]+;\s*color:\s*\{COLOR_PRIMARY\};\s*\}\}',
        r'QTableWidget::item:selected {{\n            background-color: {COLOR_PRIMARY};\n            color: white;\n        }}',
        content,
        flags=re.IGNORECASE
    )

    # Variation 2: tab_clientes.py and tab_presupuestos.py (f-string with {COLOR_TEXT_MAIN})
    content = re.sub(
        r'QTableWidget::item:selected\s*\{\{\s*background-color:\s*#[a-f0-9]+;\s*color:\s*\{COLOR_TEXT_MAIN\};\s*\}\}',
        r'QTableWidget::item:selected {{ background-color: {COLOR_PRIMARY}; color: white; }}',
        content,
        flags=re.IGNORECASE
    )

    # Variation 3: tab_stock.py first definition
    content = re.sub(
        r'QTableWidget::item:selected\s*\{\{\s*background-color:\s*#[a-f0-9]+;\s*\}\}',
        r'QTableWidget::item:selected {{\n                background-color: {COLOR_PRIMARY}; color: white;\n            }}',
        content,
        flags=re.IGNORECASE
    )

    # Variation 4: tab_stock.py second definition (normal string)
    content = re.sub(
        r'QTableWidget::item:selected\s*\{\s*background-color:\s*#[a-f0-9]+;\s*color:\s*#[a-f0-9]+;\s*\}',
        r'QTableWidget::item:selected {\n                  background-color: #2563eb;\n                  color: white;\n              }',
        content,
        flags=re.IGNORECASE
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Updated table selection colors across all tabs and theme.")
