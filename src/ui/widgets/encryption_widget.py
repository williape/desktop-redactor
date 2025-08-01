"""
Encryption Widget for Presidio Desktop Redactor

Provides UI components for encryption key management including:
- Masked key input with show/hide toggle
- Key strength indicator
- Key generation, import, and export functionality
- Security warnings and instructions
"""

import logging
from typing import Optional, Callable
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QProgressBar, QCheckBox, QFileDialog, QMessageBox, QGroupBox,
    QTextEdit, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
# Removed import of non-existent dialog functions
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from core.encryption_manager import EncryptionManager


class EncryptionWidget(QWidget):
    """
    Widget for encryption key management and configuration
    """
    
    # Signals
    encryption_enabled_changed = pyqtSignal(bool)
    key_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize EncryptionWidget"""
        super().__init__(parent)
        
        self.encryption_manager = EncryptionManager()
        self.logger = logging.getLogger(__name__)
        
        # UI state
        self._key_visible = False
        self._last_key_strength = 0.0
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Setup the UI layout and components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)  # Increased spacing between sections
        
        # Main encryption group
        encryption_group = QGroupBox("Encryption Settings")
        encryption_layout = QVBoxLayout(encryption_group)
        encryption_layout.setSpacing(15)  # More spacing between components
        
        # Key input section
        key_section = self.create_key_input_section()
        encryption_layout.addWidget(key_section)
        
        # Key management buttons
        button_section = self.create_button_section()
        encryption_layout.addWidget(button_section)
        
        # Options section (removed warning section)
        options_section = self.create_options_section()
        encryption_layout.addWidget(options_section)
        
        layout.addWidget(encryption_group)
        # Remove addStretch() to allow encryption group to expand fully
        
        # Enable encryption sections by default since widget is only shown when needed
        self.update_encryption_ui_state(True)
    
    def create_key_input_section(self) -> QWidget:
        """Create the key input section with strength indicator"""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setSpacing(8)
        
        # Key input label
        key_label = QLabel("Encryption Key:")
        key_label.setFont(QFont("", 10, QFont.Bold))
        layout.addWidget(key_label)
        
        # Key input row
        key_row = QWidget()
        key_layout = QHBoxLayout(key_row)
        key_layout.setContentsMargins(0, 0, 0, 0)
        
        # Key input field
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.Password)
        self.key_input.setPlaceholderText("Enter encryption key...")
        self.key_input.setMinimumHeight(40)  # Increased height
        self.key_input.setStyleSheet("font-size: 14px; padding: 8px;")  # Larger font and padding
        key_layout.addWidget(self.key_input, 1)
        
        # Show/hide toggle button
        self.toggle_visibility_btn = QPushButton("👁")
        self.toggle_visibility_btn.setFixedSize(40, 40)  # Larger button
        self.toggle_visibility_btn.setToolTip("Show/hide key")
        self.toggle_visibility_btn.setStyleSheet("font-size: 16px;")  # Larger icon
        key_layout.addWidget(self.toggle_visibility_btn)
        
        layout.addWidget(key_row)
        
        # Key strength indicator
        strength_row = QWidget()
        strength_layout = QHBoxLayout(strength_row)
        strength_layout.setContentsMargins(0, 0, 0, 0)
        
        strength_layout.addWidget(QLabel("Key Strength:"))
        
        self.strength_bar = QProgressBar()
        self.strength_bar.setMaximum(100)
        self.strength_bar.setValue(0)
        self.strength_bar.setMinimumHeight(25)  # Increased height
        self.strength_bar.setStyleSheet("font-size: 12px;")  # Larger text
        strength_layout.addWidget(self.strength_bar, 1)
        
        self.strength_label = QLabel("Enter a key")
        self.strength_label.setMinimumWidth(80)
        strength_layout.addWidget(self.strength_label)
        
        layout.addWidget(strength_row)
        
        return section
    
    def create_button_section(self) -> QWidget:
        """Create the key management buttons section"""
        section = QWidget()
        layout = QHBoxLayout(section)
        layout.setSpacing(8)  # Compact spacing like list widget buttons
        
        # Compact button style matching list widget Add buttons
        button_style = """
            QPushButton {
                font-size: 11px;
                padding: 4px 8px;
                min-height: 24px;
                max-height: 28px;
                border-radius: 3px;
                border: 1px solid #ccc;
                background-color: #f8f9fa;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #007acc;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """
        
        # Generate key button
        self.generate_btn = QPushButton("Generate Key")
        self.generate_btn.setToolTip("Generate a cryptographically secure random key")
        self.generate_btn.setStyleSheet(button_style)
        layout.addWidget(self.generate_btn)
        
        # Import key button
        self.import_btn = QPushButton("Import")
        self.import_btn.setToolTip("Import encryption key from file")
        self.import_btn.setStyleSheet(button_style)
        layout.addWidget(self.import_btn)
        
        # Export key button
        self.export_btn = QPushButton("Export")
        self.export_btn.setToolTip("Export current key to file")
        self.export_btn.setStyleSheet(button_style)
        layout.addWidget(self.export_btn)
        
        # Test encryption button
        self.test_btn = QPushButton("Test")
        self.test_btn.setToolTip("Test encryption configuration")
        self.test_btn.setStyleSheet(button_style)
        layout.addWidget(self.test_btn)
        
        layout.addStretch()
        
        return section
    
    def create_options_section(self) -> QWidget:
        """Create the encryption options section"""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setSpacing(8)
        
        # Checkbox style for better visibility
        checkbox_style = """
            QCheckBox {
                font-size: 13px;
                padding: 4px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """
        
        # Save key option
        self.save_key_checkbox = QCheckBox("Save key for future sessions")
        self.save_key_checkbox.setToolTip("Store encrypted key locally for convenience (less secure)")
        self.save_key_checkbox.setStyleSheet(checkbox_style)
        layout.addWidget(self.save_key_checkbox)
        
        # Include instructions option
        self.include_instructions_checkbox = QCheckBox("Include decryption instructions in output")
        self.include_instructions_checkbox.setToolTip("Add instructions for decrypting the processed file")
        self.include_instructions_checkbox.setChecked(True)
        self.include_instructions_checkbox.setStyleSheet(checkbox_style)
        layout.addWidget(self.include_instructions_checkbox)
        
        return section
    
    def connect_signals(self):
        """Connect UI signals to handlers"""
        self.key_input.textChanged.connect(self.on_key_changed)
        self.toggle_visibility_btn.clicked.connect(self.toggle_key_visibility)
        self.generate_btn.clicked.connect(self.generate_key)
        self.import_btn.clicked.connect(self.import_key)
        self.export_btn.clicked.connect(self.export_key)
        self.test_btn.clicked.connect(self.test_encryption)
        
    
    def update_encryption_ui_state(self, enabled: bool):
        """Update UI state based on encryption enabled status"""
        # Enable/disable all encryption controls
        controls = [
            self.key_input, self.toggle_visibility_btn, self.generate_btn,
            self.import_btn, self.export_btn, self.test_btn,
            self.save_key_checkbox, self.include_instructions_checkbox
        ]
        
        for control in controls:
            control.setEnabled(enabled)
        
        # Update strength indicator
        if not enabled:
            self.strength_bar.setValue(0)
            self.strength_label.setText("Encryption disabled")
    
    def on_key_changed(self):
        """Handle key input changes"""
        key = self.key_input.text()
        
        if not key:
            self.strength_bar.setValue(0)
            self.strength_label.setText("Enter a key")
            self._last_key_strength = 0.0
            return
        
        # Validate key and update strength indicator
        is_valid, message, strength = self.encryption_manager.validate_key(key)
        
        # Update strength bar
        strength_percent = int(strength * 100)
        self.strength_bar.setValue(strength_percent)
        
        # Update strength label with color coding
        self.strength_label.setText(message.split(": ")[-1] if ": " in message else message)
        
        # Color code the strength bar
        if strength < 0.3:
            color = "#dc3545"  # Red
        elif strength < 0.6:
            color = "#ffc107"  # Yellow
        elif strength < 0.8:
            color = "#28a745"  # Green
        else:
            color = "#007bff"  # Blue
        
        self.strength_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)
        
        self._last_key_strength = strength
        
        # Update encryption manager if key is valid
        if is_valid:
            success = self.encryption_manager.set_encryption_key(key)
            if success:
                self.key_changed.emit()
    
    def toggle_key_visibility(self):
        """Toggle key visibility in input field"""
        self._key_visible = not self._key_visible
        
        if self._key_visible:
            self.key_input.setEchoMode(QLineEdit.Normal)
            self.toggle_visibility_btn.setText("🙈")
        else:
            self.key_input.setEchoMode(QLineEdit.Password)
            self.toggle_visibility_btn.setText("👁")
    
    def generate_key(self):
        """Generate a random encryption key"""
        try:
            # Ask user for key length
            reply = QMessageBox.question(
                self,
                "Generate Encryption Key",
                "Generate a strong random encryption key?\n\n"
                "This will replace any existing key.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                key = self.encryption_manager.generate_key(32)
                self.key_input.setText(key)
                
                # Show key briefly, then hide
                if not self._key_visible:
                    self.toggle_key_visibility()
                    self.update()
                
                QMessageBox.information(
                    self,
                    "Key Generated",
                    "A strong encryption key has been generated.\n\n"
                    "Please save this key securely - you will need it to decrypt processed files."
                )
                
        except Exception as e:
            self.logger.error(f"Error generating key: {e}")
            QMessageBox.warning(self, "Error generating encryption key", str(e))
    
    def import_key(self):
        """Import encryption key from file"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Encryption Key",
                "",
                "Key files (*.key *.txt);;All files (*)"
            )
            
            if file_path:
                success = self.encryption_manager.import_key_from_file(file_path)
                if success:
                    # Get the imported key and display it
                    key_info = self.encryption_manager.get_key_info()
                    if key_info.get("has_key"):
                        # We need to get the actual key text - for now just show success
                        QMessageBox.information(
                            self,
                            "Key Imported",
                            f"Encryption key imported successfully from {file_path}"
                        )
                else:
                    QMessageBox.warning(self, "Import Failed", "Failed to import encryption key")
                    
        except Exception as e:
            self.logger.error(f"Error importing key: {e}")
            QMessageBox.warning(self, "Import Error", str(e))
    
    def export_key(self):
        """Export current encryption key to file"""
        try:
            if not self.key_input.text().strip():
                QMessageBox.warning(self, "No Key", "Please enter an encryption key first")
                return
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Encryption Key",
                "encryption_key.key",
                "Key files (*.key);;Text files (*.txt);;All files (*)"
            )
            
            if file_path:
                success = self.encryption_manager.export_key_to_file(file_path)
                if success:
                    QMessageBox.information(
                        self,
                        "Key Exported",
                        f"Encryption key exported to {file_path}\n\n"
                        "Keep this file secure and accessible for future decryption."
                    )
                else:
                    QMessageBox.warning(self, "Export Failed", "Failed to export encryption key")
                    
        except Exception as e:
            self.logger.error(f"Error exporting key: {e}")
            QMessageBox.warning(self, "Export Error", str(e))
    
    def test_encryption(self):
        """Test encryption configuration"""
        try:
            if not self.key_input.text().strip():
                QMessageBox.warning(self, "No Key", "Please enter an encryption key first")
                return
            
            # Update encryption manager with current key
            key = self.key_input.text()
            success = self.encryption_manager.set_encryption_key(key)
            
            if not success:
                QMessageBox.warning(self, "Invalid Key", "Current encryption key is invalid")
                return
            
            # Test encryption round trip
            test_success = self.encryption_manager.test_encryption_round_trip()
            
            if test_success:
                QMessageBox.information(
                    self,
                    "Encryption Test Passed",
                    "Encryption configuration is working correctly."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Encryption Test Failed",
                    "Encryption configuration test failed. Please check your key."
                )
                
        except Exception as e:
            self.logger.error(f"Error testing encryption: {e}")
            QMessageBox.warning(self, "Test Error", str(e))
    
    def get_encryption_manager(self) -> EncryptionManager:
        """Get the encryption manager instance"""
        return self.encryption_manager
    
    def is_encryption_enabled(self) -> bool:
        """Check if encryption is enabled"""
        return True  # Always enabled when widget is visible
    
    def has_valid_key(self) -> bool:
        """Check if a valid encryption key is set"""
        key = self.key_input.text()
        if not key:
            return False
        
        is_valid, _, _ = self.encryption_manager.validate_key(key)
        return is_valid
    
    def get_encryption_config(self) -> dict:
        """Get current encryption configuration"""
        return {
            "enabled": self.is_encryption_enabled(),
            "has_valid_key": self.has_valid_key(),
            "save_key": self.save_key_checkbox.isChecked(),
            "include_instructions": self.include_instructions_checkbox.isChecked(),
            "key_strength": self._last_key_strength
        }
    
    def set_encryption_config(self, config: dict):
        """Set encryption configuration"""
        self.save_key_checkbox.setChecked(config.get("save_key", False))
        self.include_instructions_checkbox.setChecked(config.get("include_instructions", True))
        
        # Note: We don't restore the actual key for security reasons
    
    def clear_key(self):
        """Clear the encryption key"""
        self.key_input.clear()
        self.encryption_manager.secure_cleanup()
    
    def closeEvent(self, event):
        """Handle widget close event"""
        # Secure cleanup when widget is closed
        self.encryption_manager.secure_cleanup()
        super().closeEvent(event)