import sys
import os
import fcntl
import tempfile
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from ui.main_window import PresidioRedactorMainWindow
from utils.logging_config import LoggingConfig, check_debug_flag

# Global lock file for singleton behavior
_lock_file = None

def acquire_singleton_lock():
    """Acquire a file lock to ensure only one instance runs"""
    global _lock_file
    lock_path = os.path.join(tempfile.gettempdir(), 'presidio_desktop_redactor.lock')
    
    try:
        _lock_file = open(lock_path, 'w')
        fcntl.flock(_lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_file.write(str(os.getpid()))
        _lock_file.flush()
        return True
    except (IOError, OSError):
        if _lock_file:
            _lock_file.close()
            _lock_file = None
        return False

# Prevent multiple instances when frozen with PyInstaller
if getattr(sys, 'frozen', False):
    import multiprocessing
    # This prevents child processes from re-executing the main application
    multiprocessing.freeze_support()
    
    # Additional guard: if this is not in the main process, exit immediately
    if __name__ != '__main__':
        sys.exit(0)
    
    # Singleton lock for PyInstaller apps
    if not acquire_singleton_lock():
        print("Another instance is already running.")
        sys.exit(0)

def main():
    # Initialize logging before anything else
    debug_mode = check_debug_flag()
    logging_config = LoggingConfig()
    logger = logging_config.setup_logging(debug_mode)
    logging_config.setup_exception_handler()
    
    logger.info("=== Presidio Desktop Redactor Starting ===")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info(f"Command line args: {sys.argv}")
    # Enable High DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Presidio Desktop Redactor")
    app.setOrganizationName("YourOrganization")
    
    # Set application style for macOS
    app.setStyle('Fusion')
    
    # Force light theme to override macOS dark mode
    light_palette = QPalette()
    
    # Window colors
    light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
    light_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    
    # Base colors (for input fields, etc.)
    light_palette.setColor(QPalette.Base, QColor(255, 255, 255))
    light_palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    
    # Text colors
    light_palette.setColor(QPalette.Text, QColor(0, 0, 0))
    light_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    
    # Button colors
    light_palette.setColor(QPalette.Button, QColor(225, 225, 225))
    light_palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    
    # Highlight colors
    light_palette.setColor(QPalette.Highlight, QColor(76, 163, 224))
    light_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    
    # Disabled state colors
    light_palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(120, 120, 120))
    light_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(120, 120, 120))
    light_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(120, 120, 120))
    
    app.setPalette(light_palette)
    
    try:
        window = PresidioRedactorMainWindow()
        window.show()
        
        logger.info("Application window created and shown")
        result = app.exec_()
        logger.info("=== Presidio Desktop Redactor Exiting ===")
        sys.exit(result)
        
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    # Critical for preventing multiple app instances on macOS with PyInstaller
    if getattr(sys, 'frozen', False):
        import multiprocessing
        multiprocessing.freeze_support()
        
        # Additional safety: set spawn method to prevent fork issues
        try:
            multiprocessing.set_start_method('spawn', force=True)
        except RuntimeError:
            # Method already set, ignore
            pass
    
    # Only run main if we're really in the main process
    main()