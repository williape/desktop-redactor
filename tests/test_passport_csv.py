#!/usr/bin/env python3
"""
Test AU_PASSPORT recognizer with actual CSV data
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.presidio_manager import PresidioManager
from src.core.file_processor import FileProcessor

def test_passport_in_csv():
    """Test passport detection in the actual CSV file"""
    print("=== Testing AU_PASSPORT with CSV Data ===")
    
    try:
        # Initialize PresidioManager
        presidio = PresidioManager()
        
        # Read the test CSV file directly
        csv_file = "tests/sample_files/test_australian_data.csv"
        
        print(f"Reading CSV file: {csv_file}")
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        # Take first 1000 characters for analysis
        text_to_analyze = csv_content[:1000]
        
        print(f"Analyzing text excerpt:\n{text_to_analyze[:300]}...\n")
        
        # Analyze for passport numbers
        results, findings = presidio.analyze_text_with_findings(
            text_to_analyze,
            ["AU_PASSPORT"],
            confidence=0.5
        )
        
        print(f"Found {len(results)} passport number(s) in CSV content:")
        for result in results:
            detected_text = text_to_analyze[result.start:result.end]
            print(f"  - '{detected_text}' (confidence: {result.score:.2f})")
        
        # Also test specific passport values we know are in the data
        known_passports = ["N1234567", "PA1234567", "P9876543", "L5678901", "M2345678"]
        
        print(f"\nTesting known passport values:")
        for passport in known_passports:
            test_text = f"Document number: {passport}"
            results, _ = presidio.analyze_text_with_findings(
                test_text,
                ["AU_PASSPORT"],
                confidence=0.5
            )
            status = "✓ DETECTED" if results else "✗ NOT DETECTED"
            print(f"  {passport}: {status}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_passport_in_csv()