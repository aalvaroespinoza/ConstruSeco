with open('ui/modules/clientes/dialogs_contactos_notas.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('self.setStyleSheet(f"QDialog {{ background-color: {COLOR_CARD_BG}; }}")', '')

with open('ui/modules/clientes/dialogs_contactos_notas.py', 'w', encoding='utf-8') as f:
    f.write(text)

with open('ui/modules/clientes/dialogs_historial.py', 'r', encoding='utf-8') as f:
    text2 = f.read()

text2 = text2.replace('self.setStyleSheet(f"QDialog {{ background-color: {COLOR_CARD_BG}; }}")', '')

with open('ui/modules/clientes/dialogs_historial.py', 'w', encoding='utf-8') as f:
    f.write(text2)
