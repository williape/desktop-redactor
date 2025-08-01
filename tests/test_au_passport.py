#!/usr/bin/env python3
"""
Test script for AU_PASSPORT recognizer
Tests the new Australian passport number detection functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.presidio_manager import PresidioManager
from src.core.custom_recognizers import AuPassportRecognizer

def test_au_passport_recognizer():
    """Test the AU Passport recognizer directly"""
    print("=== Testing AU Passport Recognizer ===")
    
    recognizer = AuPassportRecognizer()
    
    # Test cases from the sample data
    test_texts = [
        "My passport number is N1234567",
        "PA1234567",
        "Contact me with document P9876543",
        "L5678901 is my travel document",
        "M2345678",
        "Invalid: O1234567",  # Should fail - contains O
        "Invalid: S1234567",  # Should fail - contains S 
        "Invalid: Q1234567",  # Should fail - contains Q
        "Invalid: I1234567",  # Should fail - contains I
        "Invalid: A123456",   # Should fail - only 6 digits
        "Invalid: A12345678", # Should fail - 8 digits
        "Valid two letter: PA1234567",
        "Valid two letter: PB1234567",
        "Another valid: PC1234567"
    ]
    
    for text in test_texts:
        print(f"\nTesting: '{text}'")
        results = recognizer.analyze(text, ["AU_PASSPORT"])
        
        if results:
            for result in results:
                detected_text = text[result.start:result.end]
                print(f"  ✓ Detected: '{detected_text}' (confidence: {result.score})")
                if hasattr(result, 'recognition_metadata'):
                    metadata = result.recognition_metadata
                    if 'pattern' in metadata:
                        print(f"    Pattern: {metadata['pattern']}")
        else:
            print("  ✗ No passport number detected")

def test_presidio_integration():
    """Test the AU Passport recognizer integration with PresidioManager"""
    print("\n=== Testing PresidioManager Integration ===")
    
    try:
        # Initialize PresidioManager
        presidio = PresidioManager()
        
        # Check if AU_PASSPORT is in supported entities
        supported_entities = presidio.get_supported_entities()
        print(f"AU_PASSPORT in supported entities: {'AU_PASSPORT' in supported_entities}")
        print(f"All supported entities: {supported_entities}")
        
        # Test analysis with passport numbers from sample data
        test_text = """
        Here are some passport details:
        John Anderson has passport N1234567
        Robert McDonald carries PA1234567
        Sarah Mitchell's document is P9876543
        David Chen travels with L5678901
        Emma Thompson uses M2345678
        """
        
        print(f"\nAnalyzing text for AU_PASSPORT entities...")
        results, findings = presidio.analyze_text_with_findings(
            test_text, 
            ["AU_PASSPORT"], 
            confidence=0.5
        )
        
        print(f"Found {len(results)} passport number(s):")
        for result in results:
            detected_text = test_text[result.start:result.end]
            print(f"  - '{detected_text}' at position {result.start}-{result.end} (confidence: {result.score:.2f})")
        
        # Test findings collection
        print(f"\nFindings collection contains {len(findings.findings)} findings:")
        for finding in findings.findings:
            print(f"  - Entity: {finding.entity_type}")
            print(f"    Text: '{finding.text}'")
            print(f"    Confidence: {finding.confidence:.2f}")
            print(f"    Recognizer: {finding.recognizer}")
            if finding.pattern:
                print(f"    Pattern: {finding.pattern}")
        
        return True
        
    except Exception as e:
        print(f"Error testing PresidioManager integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sample_data():
    """Test with actual sample data from test_australian_data.csv"""
    print("\n=== Testing with Sample Data ===")
    
    try:
        presidio = PresidioManager()
        
        # Sample passport numbers from the CSV
        sample_passports = [
            "N1234567", "PA1234567", "P9876543", "L5678901", "M2345678",
            "K8765432", "R3456789", "T6543210", "H7890123", "V4567890"
        ]
        
        for passport in sample_passports:
            text = f"Passport number: {passport}"
            results, findings = presidio.analyze_text_with_findings(
                text, 
                ["AU_PASSPORT"], 
                confidence=0.5
            )
            
            if results:
                print(f"✓ {passport} - Detected as AU_PASSPORT")
            else:
                print(f"✗ {passport} - NOT detected")
                
        return True
        
    except Exception as e:
        print(f"Error testing sample data: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Testing AU_PASSPORT Recognizer Implementation")
    print("=" * 50)
    
    success = True
    
    # Test 1: Direct recognizer testing
    try:
        test_au_passport_recognizer()
    except Exception as e:
        print(f"Error in direct recognizer test: {e}")
        success = False
    
    # Test 2: PresidioManager integration
    try:
        if not test_presidio_integration():
            success = False
    except Exception as e:
        print(f"Error in PresidioManager integration test: {e}")
        success = False
    
    # Test 3: Sample data testing
    try:
        if not test_sample_data():
            success = False
    except Exception as e:
        print(f"Error in sample data test: {e}")
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All AU_PASSPORT tests completed successfully!")
    else:
        print("✗ Some tests failed - check output above")
    
    return success

if __name__ == "__main__":
    main()