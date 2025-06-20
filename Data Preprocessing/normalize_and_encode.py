import os
import numpy as np
import rasterio
from glob import glob
from tqdm import tqdm

def normalize_sentinel(image_array):
    """Normalize Sentinel-2 values from 0–10000 to 0–1."""
    return image_array.astype(np.float32) / 10000.0

def load_raster_as_array(path, normalize=False, is_label=False):
    with rasterio.open(path) as src:
        array = src.read()
        if normalize:
            array = normalize_sentinel(array)
        if is_label:
            array = array[0]  # For single-band label
        return array

def preprocess_split(split):
    input_split_dir = os.path.join("data","lucd_split", split)
    output_split_dir = os.path.join("data", "processed_numpy", split)
    os.makedirs(output_split_dir, exist_ok=True)

    site_dirs = [d for d in os.listdir(input_split_dir) if os.path.isdir(os.path.join(input_split_dir, d))]

    for site_id in tqdm(site_dirs, desc=f"Processing {split}"):
        site_input_dir = os.path.join(input_split_dir, site_id)
        sentinel_dir = os.path.join(site_input_dir, "sentinel")
        label_dir = os.path.join(site_input_dir, "change_labels")

        sentinel_files = sorted(glob(os.path.join(sentinel_dir, "*.tif")))
        label_files = sorted(glob(os.path.join(label_dir, "*.tif")))

        site_output_dir = os.path.join(output_split_dir, site_id)
        os.makedirs(site_output_dir, exist_ok=True)

        # Process Sentinel Images
        for s_file in sentinel_files:
            s_array = load_raster_as_array(s_file, normalize=True)
            s_base = os.path.splitext(os.path.basename(s_file))[0].replace('_comp', '')
            out_path = os.path.join(site_output_dir, f"{s_base}_img.npy")
            np.save(out_path, s_array)

        # Process Change Labels
        for l_file in label_files:
            l_array = load_raster_as_array(l_file, is_label=True)
            l_base = os.path.splitext(os.path.basename(l_file))[0].replace('_comp', '')
            out_path = os.path.join(site_output_dir, f"{l_base}_label.npy")
            np.save(out_path, l_array)

if __name__ == "__main__":
    for split in ["train", "val", "test"]:
        preprocess_split(split)