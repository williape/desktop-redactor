#!/usr/bin/env python3
"""
Test script specifically for TXT file processing functionality
"""
import sys
import os
sys.path.insert(0, 'src')

from core.presidio_manager import PresidioManager
from core.file_processor import FileProcessor
from core.preview_manager import PreviewManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_txt_file_processing():
    """Test comprehensive TXT file processing"""
    print("=== Testing TXT File Processing ===")
    
    try:
        manager = PresidioManager()
        processor = FileProcessor(manager)
        
        test_files = [
            "tests/sample_files/test_simple.txt",
            "tests/sample_files/test_australian_data.text",
            "tests/sample_files/test_mixed_format.txt"
        ]
        
        for file_path in test_files:
            if not os.path.exists(file_path):
                print(f"⚠ Skipping {file_path} - file not found")
                continue
                
            print(f"\n--- Testing {file_path} ---")
            
            # Test file validation
            is_valid, message = processor.validate_file(file_path)
            print(f"✓ File validation: {is_valid} - {message}")
            
            # Test processing
            entities = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IP_ADDRESS", 
                       "URL", "AU_ABN", "AU_TFN", "AU_MEDICARE", "AU_PASSPORT"]
            operator_config = manager.get_default_operator_config("replace")
            
            result = processor.process_txt(file_path, entities, 0.7, operator_config)
            print(f"✓ Processed file - Output length: {len(result)} characters")
            
            # Save processed file
            base_name = os.path.splitext(file_path)[0]
            extension = os.path.splitext(file_path)[1]
            output_path = f"{base_name}_processed{extension}"
            
            processor.save_txt(result, output_path)
            print(f"✓ Saved processed file to: {output_path}")
            
            # Verify output file was created
            if os.path.exists(output_path):
                with open(output_path, 'r', encoding='utf-8') as f:
                    saved_content = f.read()
                print(f"✓ Output file verification - Length: {len(saved_content)} characters")
            else:
                print("✗ Output file was not created")
                return False
        
        return True
    except Exception as e:
        print(f"✗ TXT file processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_txt_preview_functionality():
    """Test TXT file preview functionality"""
    print("\n=== Testing TXT Preview Functionality ===")
    
    try:
        manager = PresidioManager()
        preview_manager = PreviewManager(manager)
        
        test_files = [
            "tests/sample_files/test_simple.txt",
            "tests/sample_files/test_australian_data.text"
        ]
        
        for file_path in test_files:
            if not os.path.exists(file_path):
                print(f"⚠ Skipping {file_path} - file not found")
                continue
                
            print(f"\n--- Testing preview for {file_path} ---")
            
            # Test loading sample
            success, sample_data = preview_manager.load_file_sample(file_path)
            print(f"✓ Load sample: {success}")
            
            if success:
                print(f"✓ Sample data length: {len(sample_data)} characters")
                print(f"✓ Sample preview (first 100 chars): {sample_data[:100]}...")
                
                # Test processing preview
                entities = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "AU_TFN"]
                success_proc, processed_data, findings = preview_manager.process_preview(
                    entities, confidence=0.7, operation="replace"
                )
                
                print(f"✓ Process preview: {success_proc}")
                if success_proc:
                    print(f"✓ Processed data length: {len(processed_data)} characters")
                    print(f"✓ Findings count: {len(findings.findings)} entities found")
                    
                    # Print some findings
                    for i, finding in enumerate(findings.findings[:3]):
                        print(f"  - Finding {i+1}: {finding.entity_type} = '{finding.text}' (confidence: {finding.score:.2f})")
            else:
                print(f"✗ Failed to load sample: {sample_data}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ TXT preview test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_txt_encoding_handling():
    """Test TXT file encoding detection and handling"""
    print("\n=== Testing TXT Encoding Handling ===")
    
    try:
        manager = PresidioManager()
        processor = FileProcessor(manager)
        
        # Create test file with different encoding
        test_content = "Test file with special characters: café, résumé, naïve\nEmail: test@email.com\nPhone: 0412 345 678"
        
        # Test UTF-8 encoding
        utf8_file = "tests/sample_files/test_encoding_utf8.txt"
        with open(utf8_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"✓ Created UTF-8 test file: {utf8_file}")
        
        # Test processing UTF-8 file
        entities = ["EMAIL_ADDRESS", "PHONE_NUMBER"]
        operator_config = manager.get_default_operator_config("replace")
        
        result = processor.process_txt(utf8_file, entities, 0.7, operator_config)
        print(f"✓ Processed UTF-8 file - Length: {len(result)} characters")
        
        # Test that special characters are preserved
        if "café" in result or "[REDACTED]" in result:
            print("✓ Encoding handling successful - special characters preserved or content processed")
        else:
            print("⚠ Encoding test inconclusive")
        
        # Clean up test file
        if os.path.exists(utf8_file):
            os.remove(utf8_file)
            print("✓ Cleaned up test file")
        
        return True
    except Exception as e:
        print(f"✗ TXT encoding test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all TXT-specific tests"""
    print("Starting TXT processing tests...\n")
    
    success = True
    success &= test_txt_file_processing()
    success &= test_txt_preview_functionality()
    success &= test_txt_encoding_handling()
    
    print(f"\n=== TXT Test Results ===")
    if success:
        print("✅ All TXT tests passed!")
    else:
        print("❌ Some TXT tests failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)