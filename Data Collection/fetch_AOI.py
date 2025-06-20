import ee, os, json

# 1. Initialize Earth Engine
ee.Initialize(project='')

# 2. Load global mining polygons
mines = ee.FeatureCollection(
    "projects/sat-io/open-datasets/global-mining/global_mining_polygons"
)

# 3. Define country filters
na_codes = ["USA", "CAN", "MEX"]
sa_codes = ["ZAF"]

filter_na = mines.filter(ee.Filter.inList("ISO3_CODE", na_codes))
filter_sa = mines.filter(ee.Filter.inList("ISO3_CODE", sa_codes))
sites = filter_na.merge(filter_sa)

# 4. Prepare output folder
out_dir = "data/aois"
os.makedirs(out_dir, exist_ok=True)

# 5. Export each AOI as GeoJSON
features = sites.getInfo()["features"]
for f in features:
    iso = f["properties"]["ISO3_CODE"]
    fid = f["id"]
    geom = f["geometry"]
    path = os.path.join(out_dir, f"mine_{iso}_{fid}.geojson")
    with open(path, "w") as fp:
        json.dump({"type":"Feature","geometry":geom,"properties":f["properties"]}, fp)

print(f"Exported {len(features)} mining AOIs (~{out_dir}/)")