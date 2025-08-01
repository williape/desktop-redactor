"""
Model Import Dialog for importing NER models.

This dialog allows users to import models from various frameworks
into the Presidio Desktop Redactor application.
"""

import logging
from pathlib import Path
from typing import Optional
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QLineEdit, QPushButton, QTextEdit,
                            QProgressBar, QFileDialog, QMessageBox, QGroupBox,
                            QCheckBox, QSpinBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from core.model_manager import ModelManager
from ui.styles import COLORS, get_primary_button_style, get_small_button_style


class ModelImportThread(QThread):
    """Thread for importing models without blocking the UI"""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    import_completed = pyqtSignal(bool, str)
    
    def __init__(self, model_manager: ModelManager, source_path: Path, 
                 framework: str, model_name: str = None):
        super().__init__()
        self.model_manager = model_manager
        self.source_path = source_path
        self.framework = framework
        self.model_name = model_name
    
    def run(self):
        """Import the model in a separate thread"""
        try:
            self.status_updated.emit("Validating model...")
            self.progress_updated.emit(25)
            
            # Validate the model
            if not self.model_manager.validate_model(self.source_path, self.framework):
                self.import_completed.emit(False, "Model validation failed")
                return
            
            self.status_updated.emit("Copying model files...")
            self.progress_updated.emit(50)
            
            # Import the model
            success = self.model_manager.import_model(
                source_path=self.source_path,
                framework=self.framework,
                model_name=self.model_name
            )
            
            self.progress_updated.emit(100)
            
            if success:
                self.status_updated.emit("Import completed successfully")
                self.import_completed.emit(True, "Model imported successfully")
            else:
                self.import_completed.emit(False, "Import operation failed")
                
        except Exception as e:
            self.import_completed.emit(False, f"Import error: {str(e)}")


class ModelImportDialog(QDialog):
    """Dialog for importing NER models"""
    
    def __init__(self, model_manager: ModelManager, parent=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self.import_thread = None
        
        self.setWindowTitle("Import NER Model")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        # Set dialog background to match application theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_primary']};
            }}
            QLabel {{
                background: transparent;
                color: {COLORS['text_primary']};
            }}
        """)
        
        self.setup_ui()
        self.populate_framework_info()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Title
        title_label = QLabel("Import NER Model")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; margin-bottom: 8px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Import a pre-trained NER model from various frameworks to expand entity detection capabilities.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-bottom: 16px;")
        layout.addWidget(desc_label)
        
        # Framework selection group
        framework_group = QGroupBox("Framework")
        framework_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 500;
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
            }}
        """)
        framework_layout = QVBoxLayout(framework_group)
        
        # Framework dropdown
        self.framework_combo = QComboBox()
        self.framework_combo.addItems(["spacy", "transformers", "flair", "stanza"])
        self.framework_combo.setStyleSheet(f"""
            QComboBox {{
                background: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                color: {COLORS['text_primary']};
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                selection-background-color: {COLORS['primary']};
                selection-color: white;
            }}
        """)
        self.framework_combo.currentTextChanged.connect(self.on_framework_changed)
        framework_layout.addWidget(self.framework_combo)
        
        # Framework info
        self.framework_info = QLabel("")
        self.framework_info.setWordWrap(True)
        self.framework_info.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 11px;
            background: {COLORS['background']};
            padding: 8px;
            border-radius: 4px;
            margin-top: 4px;
        """)
        framework_layout.addWidget(self.framework_info)
        
        layout.addWidget(framework_group)
        
        # Model path group
        path_group = QGroupBox("Model Location")
        path_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 500;
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
            }}
        """)
        path_layout = QVBoxLayout(path_group)
        
        # Path selection
        path_selection_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select model directory or file...")
        self.path_input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                color: {COLORS['text_primary']};
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """)
        path_selection_layout.addWidget(self.path_input)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setStyleSheet(get_small_button_style())
        self.browse_btn.clicked.connect(self.browse_model_path)
        path_selection_layout.addWidget(self.browse_btn)
        
        path_layout.addLayout(path_selection_layout)
        
        # Optional model name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Model Name (optional):"))
        self.model_name_input = QLineEdit()
        self.model_name_input.setPlaceholderText("Custom name for the model...")
        self.model_name_input.setStyleSheet(self.path_input.styleSheet())
        name_layout.addWidget(self.model_name_input)
        path_layout.addLayout(name_layout)
        
        layout.addWidget(path_group)
        
        # Progress section (initially hidden)
        self.progress_group = QGroupBox("Import Progress")
        self.progress_group.setStyleSheet(path_group.styleSheet())
        self.progress_group.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.status_label = QLabel("Ready to import...")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        progress_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                background: {COLORS['background']};
                text-align: center;
                font-size: 12px;
                color: {COLORS['text_primary']};
            }}
            QProgressBar::chunk {{
                background: {COLORS['primary']};
                border-radius: 3px;
            }}
        """)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.progress_group)
        
        # Validation info
        self.validation_info = QTextEdit()
        self.validation_info.setMaximumHeight(80)
        self.validation_info.setVisible(False)
        self.validation_info.setStyleSheet(f"""
            QTextEdit {{
                background: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                color: {COLORS['text_secondary']};
                padding: 8px;
                border-radius: 4px;
                font-size: 11px;
                font-family: monospace;
            }}
        """)
        layout.addWidget(self.validation_info)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.validate_btn = QPushButton("Validate")
        self.validate_btn.setStyleSheet(get_small_button_style())
        self.validate_btn.clicked.connect(self.validate_model)
        button_layout.addWidget(self.validate_btn)
        
        self.import_btn = QPushButton("Import")
        self.import_btn.setStyleSheet(get_primary_button_style())
        self.import_btn.clicked.connect(self.import_model)
        self.import_btn.setEnabled(False)
        button_layout.addWidget(self.import_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(get_small_button_style())
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def populate_framework_info(self):
        """Populate framework information"""
        framework_info = {
            "spacy": "spaCy models support multiple languages and entity types. Look for models with 'ner' in the name.",
            "transformers": "Hugging Face Transformers models for token classification. Requires PyTorch installation.",
            "flair": "Flair NLP models for sequence labeling. Supports pre-trained and custom models.",
            "stanza": "Stanford NLP models for various languages. Requires model download for each language."
        }
        
        framework = self.framework_combo.currentText()
        info_text = framework_info.get(framework, "")
        self.framework_info.setText(info_text)
    
    def on_framework_changed(self, framework: str):
        """Handle framework selection change"""
        self.populate_framework_info()
        
        # Clear validation info
        self.validation_info.setVisible(False)
        self.import_btn.setEnabled(False)
    
    def browse_model_path(self):
        """Browse for model path"""
        framework = self.framework_combo.currentText()
        
        if framework in ["spacy", "transformers", "flair"]:
            # These typically use directories
            path = QFileDialog.getExistingDirectory(
                self, f"Select {framework.title()} Model Directory"
            )
        else:
            # Allow both files and directories
            path = QFileDialog.getExistingDirectory(
                self, f"Select {framework.title()} Model Directory"
            )
        
        if path:
            self.path_input.setText(path)
            # Clear previous validation
            self.validation_info.setVisible(False)
            self.import_btn.setEnabled(False)
    
    def validate_model(self):
        """Validate the selected model"""
        path_str = self.path_input.text().strip()
        if not path_str:
            QMessageBox.warning(self, "Validation Error", "Please select a model path first.")
            return
        
        framework = self.framework_combo.currentText()
        model_path = Path(path_str)
        
        if not model_path.exists():
            QMessageBox.warning(self, "Validation Error", f"Path does not exist: {path_str}")
            return
        
        try:
            # Validate using model manager
            is_valid = self.model_manager.validate_model(model_path, framework)
            
            if is_valid:
                self.validation_info.setText(f"✓ Valid {framework} model detected\n✓ Ready for import")
                self.validation_info.setStyleSheet(self.validation_info.styleSheet().replace(
                    COLORS['text_secondary'], COLORS['success']
                ))
                self.import_btn.setEnabled(True)
            else:
                self.validation_info.setText(f"✗ Invalid {framework} model\n✗ Check model format and structure")
                self.validation_info.setStyleSheet(self.validation_info.styleSheet().replace(
                    COLORS['success'], COLORS['error']
                ))
                self.import_btn.setEnabled(False)
            
            self.validation_info.setVisible(True)
            
        except Exception as e:
            self.validation_info.setText(f"✗ Validation error: {str(e)}")
            self.validation_info.setStyleSheet(self.validation_info.styleSheet().replace(
                COLORS['success'], COLORS['error']
            ))
            self.validation_info.setVisible(True)
            self.import_btn.setEnabled(False)
    
    def import_model(self):
        """Import the validated model"""
        path_str = self.path_input.text().strip()
        if not path_str:
            QMessageBox.warning(self, "Import Error", "Please select a model path first.")
            return
        
        framework = self.framework_combo.currentText()
        model_name = self.model_name_input.text().strip() or None
        model_path = Path(path_str)
        
        # Show progress
        self.progress_group.setVisible(True)
        self.import_btn.setEnabled(False)
        self.validate_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        
        # Start import thread
        self.import_thread = ModelImportThread(
            self.model_manager, model_path, framework, model_name
        )
        self.import_thread.progress_updated.connect(self.progress_bar.setValue)
        self.import_thread.status_updated.connect(self.status_label.setText)
        self.import_thread.import_completed.connect(self.on_import_completed)
        self.import_thread.start()
    
    def on_import_completed(self, success: bool, message: str):
        """Handle import completion"""
        self.import_thread = None
        
        # Re-enable buttons
        self.import_btn.setEnabled(True)
        self.validate_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Import Successful", message)
            self.accept()
        else:
            QMessageBox.warning(self, "Import Failed", message)
            self.progress_group.setVisible(False)
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.import_thread and self.import_thread.isRunning():
            reply = QMessageBox.question(
                self, "Import in Progress",
                "An import is currently in progress. Do you want to cancel it?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.import_thread.terminate()
                self.import_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()