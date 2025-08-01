#!/usr/bin/env python3
"""Logging configuration for Presidio Desktop Redactor"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path


class LoggingConfig:
    """Centralized logging configuration"""
    
    def __init__(self):
        self.log_dir = Path.home() / "Documents" / "PresidioDesktopRedactor" / "logs"
        self.log_file = self.log_dir / "app.log"
        self.logger = None
        
    def setup_logging(self, debug_mode=False):
        """Setup application logging
        
        Args:
            debug_mode (bool): If True, set DEBUG level; otherwise INFO level
        """
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        
        # Clear any existing handlers
        root_logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Console handler for debug mode
        if debug_mode:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # Store logger reference
        self.logger = root_logger
        
        # Log startup information
        level_name = "DEBUG" if debug_mode else "INFO"
        self.logger.info(f"Logging initialized at {level_name} level")
        self.logger.info(f"Log file: {self.log_file}")
        self.logger.info(f"Python version: {sys.version}")
        self.logger.info(f"Platform: {sys.platform}")
        
        return self.logger
    
    def setup_exception_handler(self):
        """Setup global exception handler that logs and shows user dialog"""
        
        def handle_exception(exc_type, exc_value, exc_traceback):
            """Handle uncaught exceptions"""
            # Don't handle KeyboardInterrupt
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # Log the exception with full traceback
            logger = logging.getLogger(__name__)
            logger.critical(
                "Uncaught exception occurred",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
            
            # Show user-friendly error dialog
            error_msg = (
                f"An unexpected error occurred:\n\n"
                f"{exc_type.__name__}: {exc_value}\n\n"
                f"Please check the log file for more details:\n"
                f"{self.log_file}"
            )
            
            try:
                # Try to show QMessageBox if Qt is available and there's an active QApplication
                from PyQt5.QtWidgets import QApplication, QMessageBox
                if QApplication.instance() is not None:
                    msg_box = QMessageBox()
                    msg_box.setIcon(QMessageBox.Critical)
                    msg_box.setWindowTitle("Presidio Desktop Redactor - Error")
                    msg_box.setText("An unexpected error occurred")
                    msg_box.setDetailedText(error_msg)
                    msg_box.exec_()
                else:
                    # No QApplication available, just print to stderr
                    print(f"CRITICAL ERROR: {error_msg}", file=sys.stderr)
            except Exception as e:
                # Fallback to print if Qt is not available or fails
                print(f"CRITICAL ERROR: {error_msg}", file=sys.stderr)
                print(f"Failed to show error dialog: {e}", file=sys.stderr)
        
        # Install the exception handler
        sys.excepthook = handle_exception
        
        if self.logger:
            self.logger.info("Global exception handler installed")


def get_logger(name=None):
    """Get a logger instance
    
    Args:
        name (str): Logger name, defaults to caller's module name
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


def check_debug_flag():
    """Check if --debug flag is present in command line arguments
    
    Returns:
        bool: True if --debug flag is present
    """
    return '--debug' in sys.argv