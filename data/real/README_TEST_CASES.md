# Stage 2 Synthetic Real-Data Test Pack

These are synthetic GeoJSON files designed to look like separate departmental
sources while remaining safe to use for development/testing. They are NOT
government land records and must not be treated as real cadastral evidence.

All coordinates are WGS84 / CRS84 and are around a Meerut/NCR-like urban area.
Your Stage 1 ingestion should normalize them to your working CRS (EPSG:32643
for the current Meerut pilot).

Files
-----
- zoningdata.geojson
  Dense Urban zoning for all test parcels. The configured Dense Urban tolerance
  is 0.10 m (10 cm).

- gnssdata.geojson
  Priority-1 NAKSHA/GNSS anchor polygons for P001-P004 only.
  P005 and P006 intentionally have no GNSS anchor.

- cadastrialdata.geojson
  Priority-3 legacy cadastral polygons with deliberately different errors.

- ai_extracteddata.geojson
  Priority-2 drone/CV extracted polygons with deliberately different errors.

Test cases
----------
P001  Exact match              -> intended VERIFIED
P002  ~0.08 m discrepancy      -> intended VERIFIED (inside 10 cm)
P003  ~0.30 m discrepancy      -> intended AUDIT_PENDING (middle-error case)
P004  ~1.50 m discrepancy      -> intended LOCKED_DISPUTE (large conflict)
P005  No GNSS + overlapping    -> intended PENDING_SURVEY
P006  No GNSS + isolated/new   -> intended VERIFIED via the new-parcel bypass

Important
---------
The exact final status is determined by your current Stage 2 implementation,
including its IoU, Hausdorff/densification, overlap and zoning logic. The
labels above describe the intended scenario, not a claim about the exact
numeric output of your code.

Recommended test
----------------
1. Put these files under:
   e:\projects\sih-2026-project-1\data\real\

2. In server/test_stage2.py use:
   zoning_path = ".../zoningdata.geojson"
   ai_path = ".../ai_extracteddata.geojson"
   legacy_path = ".../cadastrialdata.geojson"
   naksha_path = ".../gnssdata.geojson"

3. Run:
   cd server
   uv run python test_stage2.py

4. Inspect at least:
   status, reason, distance_m

5. Open the four GeoJSON layers in QGIS together to visually inspect the
   anchor/legacy/AI offsets.

To test the missing-survey branch, run the same data with anchor_layer_path=None.
P005 should become PENDING_SURVEY while P006 should exercise the isolated-new-
parcel VERIFIED bypass.
