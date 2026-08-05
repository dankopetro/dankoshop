import os
import hashlib
from collections import defaultdict

BASE = "/home/claudio/Descargas/dankoshop/data/organized_images"
EXTS = {'.jpg', '.jpeg', '.png', '.webp'}

def file_hash(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()

total_removed = 0
products_affected = 0

for product_dir in sorted(os.listdir(BASE)):
    product_path = os.path.join(BASE, product_dir)
    if not os.path.isdir(product_path):
        continue
    
    # Group files by hash
    hash_map = defaultdict(list)
    for fname in sorted(os.listdir(product_path)):
        ext = os.path.splitext(fname)[1].lower()
        if ext in EXTS:
            fpath = os.path.join(product_path, fname)
            h = file_hash(fpath)
            hash_map[h].append(fpath)
    
    # Find duplicates
    removed = 0
    for h, files in hash_map.items():
        if len(files) > 1:
            # Keep first, remove rest
            for fpath in files[1:]:
                os.remove(fpath)
                removed += 1
    
    if removed > 0:
        products_affected += 1
        total_removed += removed
        remaining = len([f for f in os.listdir(product_path) if os.path.splitext(f)[1].lower() in EXTS])
        print(f"  {product_dir}: eliminados {removed} duplicados, quedan {remaining} únicos")

print(f"\nTotal: {total_removed} archivos eliminados en {products_affected} productos")
