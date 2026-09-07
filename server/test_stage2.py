import os
from app.engine.stage1_vision import run_stage1_ingestion
from app.engine.stage2_semantic import run_stage2_matching

def test_stage2():
    print("Testing Stage 2 Semantic Pipeline...")
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic_v2'))
    zoning_path = os.path.join(base_dir, "mock_zoning.geojson")
    ai_path = os.path.join(base_dir, "mock_ai_extracted.geojson")
    legacy_path = os.path.join(base_dir, "mock_legacy_cadastral.geojson")
    anchor_path = os.path.join(base_dir, "mock_anchor.geojson")
    
    print("\n--- TEST 1: Priority 1 (Anchor) is PRESENT ---")
    stage1_results = run_stage1_ingestion(
        zoning_layer_path=zoning_path,
        ai_extracted_layer_path=ai_path,
        legacy_cadastral_layer_path=legacy_path,
        target_epsg=32643
    )
    
    stage2_results = run_stage2_matching(stage1_results, anchor_layer_path=anchor_path)
    
    print("Stage 2 Results:")
    for idx, row in stage2_results.iterrows():
        print(f"Status: {row.status} | Reason: {row.reason}")
        if "attributes" in row:
            # Check if owner attribute merged
            if "owner" in row.attributes:
                print(f"  -> Owner preserved: {row.attributes['owner']}")
            if "bhu_aadhar_ulpin" in row.attributes:
                print(f"  -> ULPIN merged: {row.attributes['bhu_aadhar_ulpin']}")
                
    print("\n--- TEST 2: Priority 1 (Anchor) is ABSENT ---")
    stage2_results_missing = run_stage2_matching(stage1_results, anchor_layer_path=None)
    
    print("Stage 2 Results (Missing Anchor):")
    for idx, row in stage2_results_missing.iterrows():
        print(f"Status: {row.status} | Reason: {row.reason}")

if __name__ == "__main__":
    test_stage2()
