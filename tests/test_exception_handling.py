#!/usr/bin/env python3
"""Test script for exception handling and logging"""

import sys
import os

# Add src to path
sys.path.append('src')

from utils.logging_config import LoggingConfig, check_debug_flag

def test_exception_handling():
    """Test that uncaught exceptions are properly logged"""
    print("Testing exception handling and logging...")
    
    # Initialize logging
    debug_mode = check_debug_flag()
    logging_config = LoggingConfig()
    logger = logging_config.setup_logging(debug_mode)
    logging_config.setup_exception_handler()
    
    print(f"Debug mode: {debug_mode}")
    print(f"Log file: {logging_config.log_file}")
    
    # Log some test messages
    logger.info("Starting exception handling test")
    logger.warning("This is a test warning")
    logger.error("This is a test error")
    
    # Test that this triggers the exception handler
    print("About to raise an intentional exception...")
    raise ValueError("This is a test exception to verify logging works")

if __name__ == "__main__":
    test_exception_handling()