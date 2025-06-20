import os
import shutil
import random
import json
from glob import glob

# Config
AOI_DIR = "data/aois"
RASTER_DIR = "data/lucd2"
OUTPUT_DIR = "data/lucd_split"
RATIOS = (0.7, 0.15, 0.15)
SEED = 42

def get_site_ids():
    geojson_files = glob(os.path.join(AOI_DIR, "*.geojson"))
    site_ids = []
    for file_path in geojson_files:
        with open(file_path, 'r') as f:
            geo = json.load(f)
        if geo['properties']['downloaded']==True:
            site_ids.append(os.path.splitext(os.path.basename(file_path))[0])
        
    # site_ids = [os.path.splitext(os.path.basename(f))[0] for f in geojson_files]
    return sorted(site_ids)

def split_list(site_ids, ratios):
    random.seed(SEED)
    random.shuffle(site_ids)
    total = len(site_ids)
    train_end = int(ratios[0] * total)
    val_end = train_end + int(ratios[1] * total)

    return site_ids[:train_end], site_ids[train_end:val_end], site_ids[val_end:]

def copy_sites(site_ids, dest_folder):
    for site_id in site_ids:
        src_path = os.path.join(RASTER_DIR, site_id)
        dest_path = os.path.join(dest_folder, site_id)
        if os.path.exists(src_path):
            shutil.copytree(src_path, dest_path)
        else:
            print(f"⚠️ {site_id} not found in lucd/")

def main():
    site_ids = get_site_ids()
    train, val, test = split_list(site_ids, RATIOS)

    for split_name, split_list_ in zip(["train", "val", "test"], [train, val, test]):
        split_path = os.path.join(OUTPUT_DIR, split_name)
        os.makedirs(split_path, exist_ok=True)
        copy_sites(split_list_, split_path)
        print(f"✅ Copied {len(split_list_)} sites to {split_name}/")

    print("\n🎉 Dataset splitting complete.")

if __name__ == "__main__":
    main()