import re

with open('ui/modules/clientes/tab_clientes.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('dlg.DialogCode.Accepted', 'QDialog.DialogCode.Accepted')
text = text.replace('formulario.DialogCode.Accepted', 'QDialog.DialogCode.Accepted')

with open('ui/modules/clientes/tab_clientes.py', 'w', encoding='utf-8') as f:
    f.write(text)

with open('ui/modules/clientes/dialogs_contactos_notas.py', 'r', encoding='utf-8') as f:
    text_notas = f.read()

text_notas = re.sub(r'\s*self\.setStyleSheet\(f\"QDialog [^\)]+\)\)', '', text_notas)
text_notas = re.sub(r'\s*self\.setStyleSheet\(\"QDialog [^\)]+\"\)', '', text_notas)

with open('ui/modules/clientes/dialogs_contactos_notas.py', 'w', encoding='utf-8') as f:
    f.write(text_notas)

with open('ui/modules/clientes/dialogs_historial.py', 'r', encoding='utf-8') as f:
    text_hist = f.read()
    
text_hist = re.sub(r'\s*self\.setStyleSheet\(f\"QDialog [^\)]+\)\)', '', text_hist)
text_hist = re.sub(r'\s*self\.setStyleSheet\(\"QDialog [^\)]+\"\)', '', text_hist)

with open('ui/modules/clientes/dialogs_historial.py', 'w', encoding='utf-8') as f:
    f.write(text_hist)
