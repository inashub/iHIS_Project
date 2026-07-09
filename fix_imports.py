import os
import re

# List of folders to scan (adjust if needed)
folders = ['routes', 'models', 'database']
extensions = ('.py')

for folder in folders:
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(extensions):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Replace 'from app import db' with 'from extensions import db'
                new_content = re.sub(r'from app import db', 'from extensions import db', content)
                # Also handle 'from app import login_manager' if present
                new_content = re.sub(r'from app import login_manager', 'from extensions import login_manager', new_content)
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f'Updated: {filepath}')
print('Import fixes applied.')