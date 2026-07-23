import os, re
for root, _, files in os.walk(r'C:\Users\alvar\Documents\Sistema ConstruSeco\ui'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            if '➕' in content:
                new_content = content.replace('➕', '+')
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                print(f'Modified {f}')
