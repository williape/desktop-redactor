#!/usr/bin/env python3
"""
Test UI Components: Preview System and Findings Table
"""
import sys
import os
sys.path.insert(0, 'src')

from PyQt5.QtWidgets import QApplication
from ui.components.preview_panel import PreviewPanel, SourcePreviewPanel, OutputPreviewPanel
from ui.components.findings_table import FindingsTable
from core.preview_manager import PreviewManager
from core.findings_model import Finding, FindingsCollection
from core.presidio_manager import PresidioManager
import json
import pandas as pd

def test_preview_panels():
    """Test the preview panel components"""
    print("=== Testing Preview Panel Components ===")
    
    # Create QApplication if not exists
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        # Test basic PreviewPanel
        preview_panel = PreviewPanel("Test Preview")
        assert preview_panel.header_label.text() == "Test Preview"
        print("✓ Basic PreviewPanel created successfully")
        
        # Test SourcePreviewPanel
        source_panel = SourcePreviewPanel()
        assert "Source" in source_panel.header_label.text()
        print("✓ SourcePreviewPanel created successfully")
        
        # Test OutputPreviewPanel
        output_panel = OutputPreviewPanel()
        assert "Output" in output_panel.header_label.text()
        print("✓ OutputPreviewPanel created successfully")
        
        # Test setting content
        test_content = "Sample CSV Data:\nname,email\nJohn,john@email.com"
        source_panel.set_content(test_content)
        assert test_content in source_panel.text_edit.toPlainText()
        print("✓ Preview content update working")
        
        return True
        
    except Exception as e:
        print(f"✗ Preview panel test failed: {e}")
        return False

def test_findings_table():
    """Test the findings table component"""
    print("\n=== Testing Findings Table Component ===")
    
    # Create QApplication if not exists
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        # Create findings table
        findings_table = FindingsTable()
        print("✓ FindingsTable created successfully")
        
        # Create test findings
        test_findings = [
            Finding(
                entity_type="PERSON",
                text="John Smith",
                start=0,
                end=10,
                confidence=0.95,
                recognizer="SpacyRecognizer",
                pattern_name="PERSON",
                pattern="NER"
            ),
            Finding(
                entity_type="EMAIL_ADDRESS",
                text="john@email.com",
                start=20,
                end=35,
                confidence=0.89,
                recognizer="EmailRecognizer",
                pattern_name="EMAIL",
                pattern="regex"
            )
        ]
        
        # Add findings to table (convert to dict format)
        findings_dicts = [f.to_dict() for f in test_findings]
        findings_table.add_findings(findings_dicts)
        row_count = findings_table.rowCount()
        assert row_count == 2, f"Expected 2 rows, got {row_count}"
        print("✓ Findings table populated with test data")
        
        # Test filtering by confidence
        findings_table.filter_by_confidence(0.90)
        visible_rows = sum(1 for i in range(row_count) if not findings_table.isRowHidden(i))
        assert visible_rows == 1, f"Expected 1 visible row after filtering, got {visible_rows}"
        print("✓ Confidence filtering working")
        
        return True
        
    except Exception as e:
        print(f"✗ Findings table test failed: {e}")
        return False

def test_preview_manager():
    """Test the preview manager functionality"""
    print("\n=== Testing Preview Manager ===")
    
    try:
        # Create preview manager
        presidio_manager = PresidioManager()
        preview_manager = PreviewManager(presidio_manager)
        print("✓ PreviewManager created successfully")
        
        # Test CSV preview generation
        csv_file = "tests/sample_files/test_simple.csv"
        if os.path.exists(csv_file):
            success, source_data = preview_manager.load_file_sample(csv_file)
            assert success and source_data is not None
            assert "name" in source_data  # Should contain CSV headers
            print("✓ CSV source preview generated")
            
            # Test output preview
            entities = ['PERSON', 'EMAIL_ADDRESS']
            confidence = 0.7
            method = 'replace'
            preview_manager.process_preview(entities, confidence, method)
            output_data = preview_manager.get_processed_data()
            assert output_data is not None
            print("✓ CSV output preview generated")
        else:
            print("! CSV test file not found, skipping CSV preview test")
        
        # Test JSON preview generation
        json_file = "tests/sample_files/test_nested.json"
        if os.path.exists(json_file):
            success, source_data = preview_manager.load_file_sample(json_file)
            assert success and source_data is not None
            print("✓ JSON source preview generated")
            
            # Test output preview
            preview_manager.process_preview(entities, confidence, method)
            output_data = preview_manager.get_processed_data()
            assert output_data is not None
            print("✓ JSON output preview generated")
        else:
            print("! JSON test file not found, skipping JSON preview test")
        
        return True
        
    except Exception as e:
        print(f"✗ Preview manager test failed: {e}")
        return False

def test_findings_model():
    """Test the findings data model"""
    print("\n=== Testing Findings Data Model ===")
    
    try:
        # Create findings collection
        findings_collection = FindingsCollection()
        print("✓ FindingsCollection created successfully")
        
        # Create test findings
        findings = [
            Finding("PERSON", "John Doe", 0, 8, 0.95, "SpacyRecognizer", "PERSON", "NER"),
            Finding("EMAIL_ADDRESS", "john@test.com", 15, 28, 0.92, "EmailRecognizer", "EMAIL", "regex"),
            Finding("PHONE_NUMBER", "555-1234", 35, 43, 0.88, "PhoneRecognizer", "PHONE", "regex")
        ]
        
        # Add findings
        findings_collection.add_findings(findings)
        
        assert len(findings_collection.findings) == 3
        print("✓ Findings added to collection")
        
        # Test filtering by confidence
        high_confidence = findings_collection.filter_by_confidence(0.90)
        assert len(high_confidence) == 2
        print("✓ Confidence filtering working")
        
        # Test filtering by entity type
        person_findings = findings_collection.filter_by_entity_types(["PERSON"])
        assert len(person_findings) == 1
        assert person_findings[0].entity_type == "PERSON"
        print("✓ Entity type filtering working")
        
        # Test statistics
        stats = findings_collection.get_statistics()
        assert stats['total_count'] == 3
        assert 'PERSON' in stats['entity_counts']
        print("✓ Statistics generation working")
        
        return True
        
    except Exception as e:
        print(f"✗ Findings model test failed: {e}")
        return False

def test_integration():
    """Test integration between preview and findings systems"""
    print("\n=== Testing Preview-Findings Integration ===")
    
    try:
        # Create managers
        presidio_manager = PresidioManager()
        preview_manager = PreviewManager(presidio_manager)
        
        # Test with sample data
        test_text = "Contact John Smith at john.smith@email.com or call 555-123-4567"
        
        # Generate findings from text
        analyzer_results = presidio_manager.analyze_text(
            test_text, 
            ['PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER'], 
            0.7
        )
        
        findings = []
        for result in analyzer_results:
            finding = Finding(
                entity_type=result.entity_type,
                text=test_text[result.start:result.end],
                start=result.start,
                end=result.end,
                confidence=result.score,
                recognizer=result.recognition_metadata.get('recognizer_name', 'Unknown'),
                pattern_name=result.entity_type,
                pattern="NER" if "spacy" in result.recognition_metadata.get('recognizer_name', '').lower() else "regex"
            )
            findings.append(finding)
        
        assert len(findings) >= 2  # Should find at least PERSON and EMAIL
        print(f"✓ Found {len(findings)} entities in test text")
        
        # Test that findings contain expected entities
        entity_types = [f.entity_type for f in findings]
        assert 'PERSON' in entity_types or 'EMAIL_ADDRESS' in entity_types
        print("✓ Expected entity types detected")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

def test_findings_table_selection_highlighting():
    """Test the improved row selection highlighting in FindingsTable"""
    print("\n=== Testing Findings Table Selection Highlighting ===")
    
    # Create QApplication if not exists
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        findings_table = FindingsTable()
        
        # Add test finding
        test_finding = {
            'entity_type': 'EMAIL_ADDRESS',
            'text': 'test@example.com',
            'start': 0,
            'end': 16,
            'confidence': 0.95,
            'recognizer': 'EmailRecognizer',
            'pattern_name': 'Email Pattern',
            'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        }
        
        findings_table.add_finding(test_finding)
        
        # Test that the row is added
        assert findings_table.rowCount() == 1
        
        # Test selection behavior
        findings_table.setSelectionBehavior(findings_table.SelectRows)
        findings_table.setSelectionMode(findings_table.SingleSelection)
        
        # Verify styling includes improved selection CSS
        stylesheet = findings_table.styleSheet()
        assert "!important" in stylesheet, "Selection styling should include !important declarations"
        assert "item:selected" in stylesheet, "Should have item:selected styling"
        
        print("✓ Findings table selection highlighting configured correctly")
        return True
        
    except Exception as e:
        print(f"✗ Findings table selection test failed: {e}")
        return False

def test_detailed_analysis_integration():
    """Test detailed analysis integration with existing components"""
    print("\n=== Testing Detailed Analysis Integration ===")
    
    try:
        # Create managers
        presidio_manager = PresidioManager()
        preview_manager = PreviewManager(presidio_manager)
        
        # Test text with entities
        test_text = "Contact support at help@company.com for assistance"
        
        # Test basic analysis
        success_basic, processed_basic, findings_basic = preview_manager.process_preview(
            entities=['EMAIL_ADDRESS'],
            confidence=0.5,
            operation='replace',
            detailed_analysis=False
        )
        
        # Test detailed analysis
        success_detailed, processed_detailed, findings_detailed = preview_manager.process_preview(
            entities=['EMAIL_ADDRESS'],
            confidence=0.5,
            operation='replace',
            detailed_analysis=True
        )
        
        # Both should succeed
        assert success_basic and success_detailed
        
        # Should find the same entities
        assert len(findings_basic.findings) == len(findings_detailed.findings)
        
        # Detailed analysis might have additional metadata
        if findings_detailed.findings:
            detailed_finding = findings_detailed.findings[0]
            basic_finding = findings_basic.findings[0]
            
            # Core fields should match
            assert detailed_finding.entity_type == basic_finding.entity_type
            assert detailed_finding.text == basic_finding.text
            assert detailed_finding.confidence == basic_finding.confidence
            
            print(f"✓ Basic finding: {basic_finding.entity_type} = '{basic_finding.text}'")
            print(f"✓ Detailed finding: {detailed_finding.entity_type} = '{detailed_finding.text}'")
            
            # Check if detailed analysis added any decision process info
            if detailed_finding.decision_process or detailed_finding.textual_explanation:
                print("✓ Detailed analysis added decision process information")
        
        return True
        
    except Exception as e:
        print(f"✗ Detailed analysis integration test failed: {e}")
        return False

def main():
    """Run all Phase 3 component tests"""
    print("Testing Phase 3 UI Components Implementation...\n")
    
    tests = [
        test_preview_panels,
        test_findings_table,
        test_preview_manager,
        test_findings_model,
        test_integration,
        test_findings_table_selection_highlighting,
        test_detailed_analysis_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print(f"\n📊 Phase 3 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All Phase 3 tests passed!")
        return True
    else:
        print("❌ Some Phase 3 tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)