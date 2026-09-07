from app.engine.stage1_vision import run_stage1_ingestion
import os

def test_stage1():
    print("Testing Stage 1 Ingestion Pipeline...")
    
    # Path to synthetic data generated previously
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic'))
    zoning_path = os.path.join(base_dir, "mock_zoning.geojson")
    ai_path = os.path.join(base_dir, "mock_ai_extracted.geojson")
    legacy_path = os.path.join(base_dir, "mock_legacy_cadastral.geojson")
    
    result = run_stage1_ingestion(
        zoning_layer_path=zoning_path,
        ai_extracted_layer_path=ai_path,
        legacy_cadastral_layer_path=legacy_path,
        target_epsg=32643 # Explicitly requesting 32643 as requested
    )
    
    print("\n[SUCCESS] Ingestion completed.")
    print("Standardized CRS:", result["target_epsg"])
    
    # Verify outputs
    zoning = result["zoning"]
    ai = result["ai_extracted"]
    legacy = result["legacy_cadastral"]
    
    print(f"\nZoning layer crs: {zoning.crs}")
    print(f"Zoning rows: {len(zoning)}")
    
    print(f"\nAI layer crs: {ai.crs}")
    print(f"AI layer rows: {len(ai)}")
    
    print(f"\nLegacy layer crs: {legacy.crs}")
    print(f"Legacy layer rows (should be 1 because the invalid bow-tie polygon was dropped or fixed! Actually make_valid fixes it): {len(legacy)}")
    
if __name__ == "__main__":
    test_stage1()
