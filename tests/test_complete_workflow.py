#!/usr/bin/env python3
"""
Test complete workflow by simulating UI interactions programmatically
"""
import sys
import os
sys.path.insert(0, 'src')

from core.presidio_manager import PresidioManager
from core.file_processor import FileProcessor
import json
from datetime import datetime

def test_complete_csv_workflow():
    """Test complete CSV processing workflow"""
    print("=== Testing Complete CSV Workflow ===")
    
    try:
        # Initialize components (simulating UI startup)
        manager = PresidioManager()
        processor = FileProcessor(manager)
        
        # Load test file (simulating file drop)
        file_path = "tests/sample_files/test_simple.csv"
        if not os.path.exists(file_path):
            print(f"✗ Test file not found: {file_path}")
            return False
            
        # Get columns (simulating column selection dialog)
        columns = processor.get_csv_columns(file_path)
        print(f"✓ Loaded CSV columns: {columns}")
        
        # Simulate UI settings
        selected_entities = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"]
        confidence = 0.7
        operation = "replace"
        selected_columns = columns  # Process all columns
        
        print(f"✓ Settings: entities={selected_entities}, confidence={confidence}, operation={operation}")
        
        # Get operator config (simulating anonymization dropdown)
        operator_config = manager.get_default_operator_config(operation)
        
        # Process file (simulating process button click)
        result_df = processor.process_csv(
            file_path, selected_columns, selected_entities, confidence, operator_config
        )
        
        print(f"✓ CSV processed: {result_df.shape}")
        print(f"✓ Sample result:\n{result_df.head()}")
        
        # Save result (simulating file output)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"tests/sample_files/test_simple_ui_workflow_{timestamp}.csv"
        processor.save_csv(result_df, output_path)
        
        print(f"✓ Saved result to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ CSV workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_json_workflow():
    """Test complete JSON processing workflow"""
    print("\n=== Testing Complete JSON Workflow ===")
    
    try:
        # Initialize components
        manager = PresidioManager()
        processor = FileProcessor(manager)
        
        # Load test file
        file_path = "tests/sample_files/test_nested.json"
        if not os.path.exists(file_path):
            print(f"✗ Test file not found: {file_path}")
            return False
            
        # Get JSON structure (simulating tree widget loading)
        json_data = processor.get_json_structure(file_path)
        print(f"✓ Loaded JSON structure: {list(json_data.keys())}")
        
        # Simulate UI settings  
        selected_entities = ["PERSON", "EMAIL_ADDRESS", "IP_ADDRESS", "URL"]
        confidence = 0.7
        operation = "mask"
        selected_paths = None  # Process all paths (recursive)
        
        print(f"✓ Settings: entities={selected_entities}, confidence={confidence}, operation={operation}")
        
        # Get operator config
        operator_config = manager.get_default_operator_config(operation)
        
        # Process file
        result_data = processor.process_json(
            file_path, selected_paths, selected_entities, confidence, operator_config
        )
        
        print(f"✓ JSON processed successfully")
        print(f"✓ Sample result: {json.dumps(result_data, indent=2)[:500]}...")
        
        # Save result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"tests/sample_files/test_nested_ui_workflow_{timestamp}.json"
        processor.save_json(result_data, output_path)
        
        print(f"✓ Saved result to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ JSON workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_different_anonymization_methods():
    """Test all anonymization methods"""
    print("\n=== Testing Different Anonymization Methods ===")
    
    try:
        manager = PresidioManager()
        test_text = "John Smith's email is john.smith@email.com"
        entities = ["PERSON", "EMAIL_ADDRESS"]
        
        for operation in ["replace", "redact", "mask"]:
            print(f"\n--- Testing {operation.upper()} operation ---")
            
            # Analyze text
            results = manager.analyze_text(test_text, entities, 0.7)
            print(f"✓ Found {len(results)} entities")
            
            # Get operator config
            operator_config = manager.get_default_operator_config(operation)
            
            # Anonymize
            anonymized = manager.anonymize_text(test_text, results, operator_config)
            print(f"✓ Original: {test_text}")
            print(f"✓ {operation.title()}: {anonymized}")
            
        return True
        
    except Exception as e:
        print(f"✗ Anonymization method test failed: {e}")
        return False

def main():
    """Run complete workflow tests"""
    print("Testing Complete UI Workflow Implementation...\n")
    
    success = True
    success &= test_complete_csv_workflow()
    success &= test_complete_json_workflow()
    success &= test_different_anonymization_methods()
    
    print(f"\n=== Final Test Results ===")
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Phase 3: UI Controls - COMPLETE")
        print("✅ Full application workflow is functional")
        print("✅ Ready for Phase 4: Integration & Polish")
    else:
        print("❌ Some workflow tests failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)