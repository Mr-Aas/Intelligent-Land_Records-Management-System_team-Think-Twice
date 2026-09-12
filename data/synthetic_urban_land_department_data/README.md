# Synthetic Urban Land Department Data

Synthetic prototype data for the land-geospatial-data-smart-system.

## Included
- `municipal_buildings.geojson` — synthetic Urban Local Body / Meerut Nagar Nigam building data
- `bhu_naksha_parcels.geojson` — synthetic Directorate of Land Records / Bhu-Naksha parcel data
- `ai_extracted_expected.geojson` — deterministic expected AI-extraction fixture; this is NOT a YOLO output
- `revenue_department.csv`
- `urban_local_body.csv`
- `urban_development_authority.csv`
- `registration_stamps.csv`
- `directorate_land_records.csv`
- `manifest.json`

## Intentionally omitted
The synthetic `.geotiff` is intentionally not included in this ZIP, as requested.

## CRS
GeoJSON is WGS84 (`EPSG:4326`) for interoperability. Synthetic geometry was constructed in `EPSG:32644` (UTM Zone 44N). Reproject to a suitable projected CRS before metric geometry calculations.

## Important
All records are synthetic. They are for development, testing, demonstration, and pipeline validation only.
