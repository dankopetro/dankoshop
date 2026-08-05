#!/usr/bin/env python3
"""
Upload product images to Cloudinary.
Run: python3 scripts/upload_cloudinary.py
"""

import json
import os
import sys
import time
import cloudinary
import cloudinary.uploader
from pathlib import Path

# Config
cloudinary.config(
    cloud_name="xjuisove",
    api_key="645939449555487",
    api_secret="DPIa5BGkcboaHCMAV1U4MY-oL6s",
)

IMAGES_BASE = Path("/home/claudio/Descargas/dankoshop/data/organized_images")
PRODUCTS_JSON = Path("/home/claudio/Descargas/dankoshop/data/products.json")
OUTPUT_JSON = Path("/home/claudio/Descargas/dankoshop/data/image_urls.json")


def find_images_for_sku(sku: str) -> list[Path]:
    """Find all image files for a given SKU"""
    images = []
    for folder in IMAGES_BASE.iterdir():
        if not folder.is_dir():
            continue
        # Match folder name that starts with SKU
        folder_sku = folder.name.split("_")[0]
        if folder_sku == sku:
            for f in sorted(folder.iterdir()):
                if f.suffix.lower() in (".jpeg", ".jpg", ".png", ".webp"):
                    images.append(f)
    return images


def upload_image(local_path: Path, sku: str, index: int) -> str | None:
    """Upload a single image to Cloudinary and return URL"""
    public_id = f"{sku}_{index}"
    try:
        result = cloudinary.uploader.upload(
            str(local_path),
            public_id=public_id,
            folder="dankoshop",
            overwrite=True,
            resource_type="image",
            format="jpg",
            quality="auto:good",
            fetch_format="auto",
        )
        return result["secure_url"]
    except Exception as e:
        print(f"  Error uploading {local_path.name}: {e}")
        return None


def main():
    print("=" * 60)
    print("DankoShop - Upload Images to Cloudinary")
    print("=" * 60)

    with open(PRODUCTS_JSON) as f:
        products = json.load(f)

    # Load existing URLs if any
    if OUTPUT_JSON.exists():
        with open(OUTPUT_JSON) as f:
            url_map = json.load(f)
    else:
        url_map = {}

    total = len(products)
    uploaded = 0
    skipped = 0
    failed = 0

    for i, product in enumerate(products, 1):
        sku = product["sku"]
        name = product["name"][:50]

        # Skip if already uploaded
        if sku in url_map and url_map[sku]:
            print(f"  [{i}/{total}] SKIP {sku} ({len(url_map[sku])} images)")
            skipped += 1
            continue

        images = find_images_for_sku(sku)
        if not images:
            print(f"  [{i}/{total}] NO IMG {sku}: {name}")
            failed += 1
            continue

        urls = []
        for idx, img_path in enumerate(images, 1):
            url = upload_image(img_path, sku, idx)
            if url:
                urls.append(url)
                print(f"  [{i}/{total}] OK {sku} img {idx}/{len(images)}: {img_path.name}")
            else:
                print(f"  [{i}/{total}] FAIL {sku} img {idx}: {img_path.name}")

        if urls:
            url_map[sku] = urls
            uploaded += 1
        else:
            failed += 1

        # Save progress every 10 products
        if i % 10 == 0:
            with open(OUTPUT_JSON, "w") as f:
                json.dump(url_map, f, indent=2)

        time.sleep(0.05)

    # Final save
    with open(OUTPUT_JSON, "w") as f:
        json.dump(url_map, f, indent=2)

    print("-" * 60)
    print(f"Done! Uploaded: {uploaded}, Skipped: {skipped}, Failed: {failed}")
    print(f"URLs saved to: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
