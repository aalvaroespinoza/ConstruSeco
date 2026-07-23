import os, re
with open('output.txt', 'w', encoding='utf-8') as out:
    for root, _, files in os.walk(r'C:\Users\alvar\Documents\Sistema ConstruSeco\ui'):
        for f in files:
            if f.endswith('.py'):
                c = open(os.path.join(root, f), encoding='utf-8').read()
                for m in re.findall(r'QPushButton\([\'\"](.*?)[\'\"]\)', c):
                    if not m: continue
                    # Check if it doesn't start with an emoji or special symbol
                    if m[0].isalnum() or m[0] in ['[', '(']:
                        out.write(f'{f}: {m}\n')
