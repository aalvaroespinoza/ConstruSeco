import os

def replace_emojis():
    replacements = [
        ('\"👁️ ', '\"'), ('\'👁️ ', '\''),
        ('\"📄 ', '\"'), ('\'📄 ', '\''),
        ('\"🗑️ ', '\"'), ('\'🗑️ ', '\''),
        ('\"✏️ ', '\"'), ('\'✏️ ', '\''),
        ('\"💾 ', '\"'), ('\'💾 ', '\''),
        ('\"⚙️ ', '\"'), ('\'⚙️ ', '\''),
        ('\"🧹 ', '\"'), ('\'🧹 ', '\''),
        ('\"📋 ', '\"'), ('\'📋 ', '\''),
        ('\"📤 ', '\"'), ('\'📤 ', '\''),
        ('\"🛒 ', '\"'), ('\'🛒 ', '\''),
        ('\"🔍 ', '\"'), ('\'🔍 ', '\''),
        ('\"🔄 ', '\"🗘 '), ('\'🔄 ', '\'🗘 '),
        ('\"▶ ', '\"'), ('\'▶ ', '\''),
        ('\"◀ ', '\"'), ('\'◀ ', '\'')
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

replace_emojis()
