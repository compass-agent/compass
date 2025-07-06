"""
Direct test of SAP2000 optimization workflow - bypasses agent/LLM completely
"""
import os
import sys
import comtypes.client
import comtypes.gen.SAP2000v1

# Add the parent directory to sys.path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from compass.tools.sap2000.core import CustomSAP2000Model
from compass.tools.sap2000.core.config_manager import ModelConfig

def main():
    print("=== Direct SAP2000 Workflow Test ===")
    
    # Step 1: Connect to SAP2000
    print("1. Connecting to SAP2000...")
    helper = comtypes.client.CreateObject('SAP2000v1.Helper')
    helper = helper.QueryInterface(comtypes.gen.SAP2000v1.cHelper)
    sap_object = helper.GetObject("CSI.SAP2000.API.SapObject")
    sap_model = sap_object.SapModel
    
    # Step 2: Load configuration
    print("2. Loading configuration...")
    config_path = r"C:\Users\sp_za\Desktop\kazem\compass\models\.sapConfig.yml"
    config = ModelConfig.from_yaml(config_path)
    
    # Step 3: Create custom model
    print("3. Initializing custom SAP model...")
    # Use relative path to models directory in project root (avoid Save As dialogs)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))  # Go up to compass root
    model_path = os.path.join(project_root, "models", "compass_model.sdb")
    print(f"Using model path: {model_path}")
    custom_model = CustomSAP2000Model(sap_model, config)
    
    # Set model path separately if the custom model needs it
    if hasattr(custom_model, 'model_path'):
        custom_model.model_path = model_path
    
    print("\n=== Running Workflow Steps ===")
    
    # STEP 1: Get all frames
    print("STEP 1: Getting all frames...")
    frames = custom_model.get_all_frames()
    print(f"✓ Found {len(frames)} frames")
    
    # STEP 2: Add base restraints
    print("STEP 2: Adding base restraints...")
    restrained_joints, restraint_status = custom_model.add_base_restraints(frames)
    print(f"✓ Added restraints to {len(restrained_joints)} joints")
    
    # STEP 3: Add area loads
    print("STEP 3: Adding area loads...")
    areas, area_status = custom_model.add_area_loads(frames)
    print(f"✓ Created {len(areas)} floor areas with loads")
    
    # STEP 4: Add section candidates
    print("STEP 4: Adding section candidates...")
    frames = custom_model.add_section_candidates_to_frames(frames)
    total_candidates = sum(len(f.get('sections', [])) for f in frames.values())
    print(f"✓ Added {total_candidates} section candidates to {len(frames)} frames")
    
    # STEP 5: Calculate usage ratios
    print("STEP 5: Calculating usage ratios...")
    print(" This step may take several minutes and includes the sleep delays...")
    frames = custom_model.calculate_section_usage_ratios(frames, model_path)
    max_usage = max([max([s.get('usage_ratio', 0) for s in f.get('sections', [])]) for f in frames.values()])
    print(f"✓ Usage ratios calculated. Max usage ratio: {max_usage:.3f}")
    
    # STEP 6: Create section groups
    print("STEP 6: Creating optimized section groups...")
    frames = custom_model.create_section_groups(frames)
    group_count = len(set([f.get('optimum_design', {}).get('group_id') for f in frames.values()]))
    print(f"✓ Optimization complete: Used {group_count} unique section groups")
    
    print("\n=== Workflow Complete ===")
    print("All 6 steps completed successfully!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc() 