#!/usr/bin/env python3
"""Test script for ProcessingThread functionality"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add src to path
sys.path.append('src')

from ui.main_window import ProcessingThread
from core.presidio_manager import PresidioManager
from core.file_processor import FileProcessor

def test_processing_thread():
    """Test ProcessingThread with a simple CSV file"""
    print("Testing ProcessingThread...")
    
    # Initialize app (required for QThread)
    app = QApplication([])
    
    try:
        # Initialize core components
        presidio_manager = PresidioManager()
        file_processor = FileProcessor(presidio_manager)
        
        # Test parameters
        test_file = "tests/sample_files/test_simple.csv"
        output_dir = "tests/sample_files"
        entities = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"]
        confidence = 0.7
        operation_config = presidio_manager.get_default_operator_config("replace")
        
        if not os.path.exists(test_file):
            print(f"❌ Test file not found: {test_file}")
            return False
        
        # Create processing thread
        thread = ProcessingThread(
            file_processor=file_processor,
            file_path=test_file,
            file_type="csv",
            output_dir=output_dir,
            entities=entities,
            confidence=confidence,
            operator_config=operation_config,
            columns=None,
            paths=None
        )
        
        # Connect signals for testing
        success = []
        errors = []
        progress_values = []
        
        def on_progress(value):
            progress_values.append(value)
            print(f"Progress: {value}%")
        
        def on_status(message):
            print(f"Status: {message}")
        
        def on_error(error):
            errors.append(error)
            print(f"Error: {error}")
        
        def on_finished(success_flag, output_path):
            success.append((success_flag, output_path))
            print(f"Finished: success={success_flag}, path={output_path}")
            app.quit()
        
        thread.progress.connect(on_progress)
        thread.status.connect(on_status)
        thread.error.connect(on_error)
        thread.finished.connect(on_finished)
        
        # Start thread
        print(f"Starting processing of {test_file}...")
        thread.start()
        
        # Run event loop with timeout
        QTimer.singleShot(10000, app.quit)  # 10 second timeout
        app.exec_()
        
        # Check results
        if errors:
            print(f"❌ Processing failed with errors: {errors}")
            return False
        
        if not success or not success[0][0]:
            print("❌ Processing did not complete successfully")
            return False
        
        success_flag, output_path = success[0]
        if not os.path.exists(output_path):
            print(f"❌ Output file not created: {output_path}")
            return False
        
        print(f"✅ ProcessingThread test passed!")
        print(f"   Output file: {output_path}")
        print(f"   Progress updates: {progress_values}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_processing_thread()
    sys.exit(0 if success else 1)