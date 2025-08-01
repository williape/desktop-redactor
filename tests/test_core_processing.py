#!/usr/bin/env python3
"""
Simple test script to verify core processing functionality
"""
import sys
import os
sys.path.insert(0, 'src')

from core.presidio_manager import PresidioManager
from core.file_processor import FileProcessor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_presidio_manager():
    """Test PresidioManager functionality"""
    print("=== Testing PresidioManager ===")
    
    try:
        manager = PresidioManager()
        print(f"✓ PresidioManager initialized: {manager.is_initialized()}")
        
        # Test entity list
        entities = manager.get_supported_entities()
        print(f"✓ Supported entities: {entities}")
        
        # Test text analysis
        test_text = "John Smith's email is john.smith@email.com and phone is 555-123-4567"
        results = manager.analyze_text(test_text, ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"])
        print(f"✓ Analysis found {len(results)} entities")
        
        # Test anonymization
        if results:
            operator_config = manager.get_default_operator_config("replace")
            anonymized = manager.anonymize_text(test_text, results, operator_config)
            print(f"✓ Anonymized text: {anonymized}")
        
        return True
    except Exception as e:
        print(f"✗ PresidioManager test failed: {e}")
        return False

def test_file_processor():
    """Test FileProcessor functionality"""
    print("\n=== Testing FileProcessor ===")
    
    try:
        manager = PresidioManager()
        processor = FileProcessor(manager)
        
        # Test CSV processing
        csv_file = "tests/sample_files/test_simple.csv"
        if os.path.exists(csv_file):
            print(f"✓ Found test CSV: {csv_file}")
            
            # Get columns
            columns = processor.get_csv_columns(csv_file)
            print(f"✓ CSV columns: {columns}")
            
            # Process CSV
            entities = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"]
            operator_config = manager.get_default_operator_config("replace")
            
            df = processor.process_csv(csv_file, None, entities, 0.7, operator_config)
            print(f"✓ Processed CSV shape: {df.shape}")
            print(f"✓ Sample processed data:\n{df.head()}")
            
            # Save result
            output_csv = "tests/sample_files/test_simple_processed.csv"
            processor.save_csv(df, output_csv)
            print(f"✓ Saved processed CSV to: {output_csv}")
        
        # Test JSON processing  
        json_file = "tests/sample_files/test_nested.json"
        if os.path.exists(json_file):
            print(f"✓ Found test JSON: {json_file}")
            
            # Process JSON
            data = processor.process_json(json_file, None, entities, 0.7, operator_config)
            print(f"✓ Processed JSON structure")
            
            # Save result
            output_json = "tests/sample_files/test_nested_processed.json"
            processor.save_json(data, output_json)
            print(f"✓ Saved processed JSON to: {output_json}")
        
        return True
    except Exception as e:
        print(f"✗ FileProcessor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_txt_processor():
    """Test TXT file processing functionality"""
    print("\n=== Testing TXT FileProcessor ===")
    
    try:
        manager = PresidioManager()
        processor = FileProcessor(manager)
        
        # Test TXT processing with .txt extension
        txt_file = "tests/sample_files/test_simple.txt"
        if os.path.exists(txt_file):
            print(f"✓ Found test TXT: {txt_file}")
            
            # Process TXT
            entities = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "AU_ABN", "AU_TFN"]
            operator_config = manager.get_default_operator_config("replace")
            
            result = processor.process_txt(txt_file, entities, 0.7, operator_config)
            print(f"✓ Processed TXT length: {len(result)} characters")
            print(f"✓ Sample processed text (first 200 chars):\n{result[:200]}...")
            
            # Save result
            output_txt = "tests/sample_files/test_simple_processed.txt"
            processor.save_txt(result, output_txt)
            print(f"✓ Saved processed TXT to: {output_txt}")
        
        # Test TXT processing with .text extension
        text_file = "tests/sample_files/test_australian_data.text"
        if os.path.exists(text_file):
            print(f"✓ Found test TEXT: {text_file}")
            
            # Process TEXT with Australian entities
            au_entities = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "AU_TFN", "AU_ABN", "AU_MEDICARE", "AU_PASSPORT", "AU_DRIVERSLICENSE"]
            
            result = processor.process_txt(text_file, au_entities, 0.7, operator_config)
            print(f"✓ Processed TEXT length: {len(result)} characters")
            print(f"✓ Sample processed text (first 200 chars):\n{result[:200]}...")
            
            # Save result
            output_text = "tests/sample_files/test_australian_data_processed.text"
            processor.save_txt(result, output_text)
            print(f"✓ Saved processed TEXT to: {output_text}")
        
        # Test file validation
        validation_result, message = processor.validate_file("tests/sample_files/test_simple.txt")
        print(f"✓ TXT file validation: {validation_result} - {message}")
        
        validation_result2, message2 = processor.validate_file("tests/sample_files/test_australian_data.text")
        print(f"✓ TEXT file validation: {validation_result2} - {message2}")
        
        return True
    except Exception as e:
        print(f"✗ TXT FileProcessor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Starting core processing tests...\n")
    
    success = True
    success &= test_presidio_manager()
    success &= test_file_processor()
    success &= test_txt_processor()
    
    print(f"\n=== Test Results ===")
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)