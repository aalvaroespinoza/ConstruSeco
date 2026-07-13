import os, re
pattern = re.compile(r'(?:open|Path|sqlite3\.connect)\([\'\"]([^\'\"]+)[\'\"]\)')
for root, _, fs in os.walk('.'):
    if any(ignore in root for ignore in ['.git', 'venv', '.gemini', '__pycache__']):
        continue
    for f in fs:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            try:
                with open(p, 'r', encoding='utf-8') as file:
                    content = file.read()
                    matches = pattern.findall(content)
                    if matches:
                        print(f'{p}: {matches}')
            except Exception as e: 
                print(e)
