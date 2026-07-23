import os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

def contains_emoji(s):
    for char in s:
        if ord(char) > 0x2000 and char not in ['✕', 'ⓘ', '🗘', '＋', '✓', '▶', '◀', '📦', '⭐', '⚠️', '✔']:
            return True
    return False

for root, dirs, files in os.walk('ui'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            matches = re.findall(r'\"([^\"]*)\"|\'([^\']*)\'', content)
            for m1, m2 in matches:
                s = m1 or m2
                if contains_emoji(s):
                    print(f'{path}: {s}')
