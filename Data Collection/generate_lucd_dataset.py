import ee
import geemap
import os
import json
import glob
import subprocess

# Initialize Earth Engine
ee.Initialize(project='')

AOI_DIR = "data/aois"
OUTPUT_DIR = "data/lucd2"
START_YEAR = 2015
END_YEAR = 2024
MAX_SITES = 5

def compress_tif(input_path, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cmd = [
        "gdal_translate",
        input_path,
        output_path,
        "-co", "COMPRESS=DEFLATE",
        "-co", "PREDICTOR=2",
        "-co", "TILED=YES",
        "-co", "BIGTIFF=IF_SAFER"
    ]
    try:
        print(f"Compressing: {input_path} -> {output_path}")
        subprocess.run(cmd, check=True)
        os.remove(input_path)
    except subprocess.CalledProcessError as e:
        print(f"Error compressing {input_path}: {e}")

def get_nearest_image(collection, target_date):
    target = ee.Date(target_date)
    with_diff = collection.map(lambda img: img.set("diff", img.date().difference(target, "day").abs()))
    return with_diff.sort("diff").first()

def export_image(image, out_path, region):
    try:
        if image is None or image.bandNames().size().getInfo() == 0:
            print(f" Skipping export: No usable bands for {out_path}")
            return

        # Export raw image
        geemap.ee_export_image(
            image,
            filename=out_path,
            scale=10,
            region=region,
            file_per_band=False
        )
        print(f"Downloaded to {out_path}")

        # Compress to _compressed.tif
        base, ext = os.path.splitext(out_path)
        compressed_path = base + "_comp" + ext
        compress_tif(out_path, compressed_path)

    except Exception as e:
        print(f" Skipping export: {out_path} → {e}")

def generate_dataset_for_site(aoi_path, out_root, start_year=START_YEAR, end_year=END_YEAR):
    with open(aoi_path) as f:
        geo = json.load(f)

    if geo["properties"].get("downloaded") is True:
        print(f"⏭ Skipping {aoi_path} (already downloaded)")
        return False

    site_id = os.path.splitext(os.path.basename(aoi_path))[0]
    aoi = ee.Geometry.Polygon(geo['geometry']['coordinates'])
    site_dir = os.path.join(out_root, site_id)
    os.makedirs(os.path.join(site_dir, 'sentinel'), exist_ok=True)
    os.makedirs(os.path.join(site_dir, 'labels'), exist_ok=True)
    os.makedirs(os.path.join(site_dir, 'change_labels'), exist_ok=True)

    for year in range(start_year, end_year):
        print(f"🔄 Processing {site_id} for year {year}...")

        date = f"{year}-01-01"
        next_date = f"{year+1}-01-01"

        # Sentinel-2
        sentinel_col = (
            ee.ImageCollection("COPERNICUS/S2_HARMONIZED")
            .filterBounds(aoi)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
            .select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12'])
        )
        sentinel_img = get_nearest_image(sentinel_col, date)
        sentinel_out = os.path.join(site_dir, 'sentinel', f"{year}.tif")
        export_image(sentinel_img, sentinel_out, aoi)

        # Dynamic World Label
        label_col = (
            ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
            .filterBounds(aoi)
            .select('label')
        )
        label_img = get_nearest_image(label_col, date)
        label_out = os.path.join(site_dir, 'labels', f"{year}_label.tif")
        export_image(label_img, label_out, aoi)

        # Change label
        if year > start_year:
            prev_label_img = get_nearest_image(label_col, f"{year-1}-01-01")
            change_label = prev_label_img.multiply(100).add(label_img).rename("change")
            change_out = os.path.join(site_dir, 'change_labels', f"{year-1}_{year}.tif")
            export_image(change_label, change_out, aoi)

    # Update AOI GeoJSON with "downloaded": true
    geo["properties"]["downloaded"] = True
    with open(aoi_path, "w") as f:
        json.dump(geo, f, indent=2)
    print(f" Marked {site_id} as downloaded.")

    return True

def main():
    aoi_files = sorted(glob.glob(os.path.join(AOI_DIR, "*.geojson")))
    count = 0
    
    for aoi_path in aoi_files:
        if count >= MAX_SITES:
            break
        if generate_dataset_for_site(aoi_path, OUTPUT_DIR):
            count += 1

    print(f"\n Completed download + compression for {count} sites.")

if __name__ == "__main__":
    main()
