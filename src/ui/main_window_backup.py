from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton,
                            QGroupBox, QCheckBox, QSlider,
                            QComboBox, QLineEdit, QTextEdit,
                            QFileDialog, QMessageBox, QProgressBar,
                            QDialogButtonBox, QDialog, QFrame,
                            QTreeWidget, QTreeWidgetItem, QScrollArea,
                            QToolButton, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont, QPixmap
import os
import sys
import logging
from pathlib import Path

# Import core processing classes
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.presidio_manager import PresidioManager
from core.file_processor import FileProcessor
from core.list_manager import ListManager
from core.encryption_manager import EncryptionManager
from ui.widgets.dialogs import ColumnSelectionDialog
from ui.widgets.list_widget import ListWidget
from ui.widgets.encryption_widget import EncryptionWidget
from utils.config_manager import ConfigManager

class ProcessingThread(QThread):
    """Background thread for file processing"""
    
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, output_path
    
    def __init__(self, file_processor, file_path, file_type, output_dir,
                 entities, confidence, operator_config, columns=None, paths=None):
        super().__init__()
        self.file_processor = file_processor
        self.file_path = file_path
        self.file_type = file_type
        self.output_dir = output_dir
        self.entities = entities
        self.confidence = confidence
        self.operator_config = operator_config
        self.columns = columns
        self.paths = paths
        
    def run(self):
        """Execute the file processing in background thread"""
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Starting file processing: {self.file_path}")
            logger.info(f"Entities: {self.entities}")
            logger.info(f"Confidence: {self.confidence}")
            logger.info(f"File type: {self.file_type}")
            
            self.status.emit("Starting file processing...")
            self.progress.emit(10)
            
            # Import datetime here to avoid import in main thread
            from datetime import datetime
            
            if self.file_type == 'csv':
                self.status.emit("Processing CSV file...")
                self.progress.emit(25)
                logger.info("Starting CSV processing")
                
                result = self.file_processor.process_csv(
                    self.file_path, self.columns, self.entities,
                    self.confidence, self.operator_config
                )
                
                self.progress.emit(75)
                self.status.emit("Saving processed CSV file...")
                
                # Generate output filename
                path = Path(self.file_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{path.stem}_redacted_{timestamp}.csv"
                output_path = os.path.join(self.output_dir, output_filename)
                
                logger.info(f"Saving CSV to: {output_path}")
                self.file_processor.save_csv(result, output_path)
                
            elif self.file_type == 'json':
                self.status.emit("Processing JSON file...")
                self.progress.emit(25)
                logger.info("Starting JSON processing")
                
                result = self.file_processor.process_json(
                    self.file_path, self.paths, self.entities,
                    self.confidence, self.operator_config
                )
                
                self.progress.emit(75)
                self.status.emit("Saving processed JSON file...")
                
                # Generate output filename
                path = Path(self.file_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{path.stem}_redacted_{timestamp}.json"
                output_path = os.path.join(self.output_dir, output_filename)
                
                logger.info(f"Saving JSON to: {output_path}")
                self.file_processor.save_json(result, output_path)
            
            else:
                raise ValueError(f"Unsupported file type: {self.file_type}")
                
            self.progress.emit(100)
            self.status.emit(f"Processing complete! Saved to: {output_filename}")
            logger.info(f"File processing completed successfully: {output_path}")
            self.finished.emit(True, output_path)
            
        except Exception as e:
            import traceback
            error_msg = f"Processing error: {str(e)}"
            traceback_msg = traceback.format_exc()
            
            # Log the full traceback
            logger.error(f"Processing failed: {error_msg}")
            logger.error(f"Traceback: {traceback_msg}")
            
            self.error.emit(error_msg)
            self.finished.emit(False, "")

class DropArea(QFrame):
    """Custom widget for drag-and-drop file input"""
    
    file_dropped = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setAcceptDrops(True)
        self.setMinimumHeight(70)  # Reduced from 150
        self.setMaximumHeight(80)  # Add maximum height constraint
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #aaa;
                border-radius: 6px;
                background-color: #f9f9f9;
            }
            QFrame:hover {
                border-color: #007acc;
                background-color: #f0f8ff;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins
        layout.setSpacing(3)  # Reduce spacing
        
        # Main label
        self.label = QLabel("Drag and drop CSV or JSON file here\nor click to browse")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 11px; color: #666; border: none;")  # Smaller font
        layout.addWidget(self.label)
        
        # Browse button
        self.browse_button = QPushButton("Browse Files...")
        self.browse_button.setMaximumWidth(120)  # Smaller button
        self.browse_button.setMaximumHeight(25)  # Height constraint
        self.browse_button.setStyleSheet("font-size: 10px; padding: 2px 6px;")  # Smaller font and padding
        self.browse_button.clicked.connect(self.browse_file)
        layout.addWidget(self.browse_button, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith(('.csv', '.json')):
                    event.acceptProposedAction()
                    self.setStyleSheet("""
                        QFrame {
                            border: 2px dashed #007acc;
                            border-radius: 10px;
                            background-color: #e6f3ff;
                        }
                    """)
                    return
        event.ignore()
        
    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
            QFrame:hover {
                border-color: #007acc;
                background-color: #f0f8ff;
            }
        """)
        
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.file_dropped.emit(file_path)
        self.dragLeaveEvent(None)
        
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "CSV Files (*.csv);;JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.file_dropped.emit(file_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.file_path = None
        self.output_dir = os.path.expanduser("~/Desktop")
        self.selected_columns = []
        self.selected_paths = []
        self.file_type = None
        
        # Initialize core processing components
        self.presidio_manager = None
        self.file_processor = None
        self.list_manager = None
        self.config_manager = None
        self.entity_checkboxes = {}
        
        # List widget references
        self.allowlist_widget = None
        self.denylist_widget = None
        self.lists_enabled_cb = None
        
        # Initialize core components
        self.init_core_components()
        self.init_ui()
        
        # Load configuration and lists after UI is created
        self.load_ui_state_from_config()
        
        self.logger.info("MainWindow initialized successfully")
        
    def init_core_components(self):
        """Initialize Presidio manager, list manager, config manager and file processor"""
        try:
            self.logger.info("Initializing core components...")
            
            # Initialize config manager
            self.config_manager = ConfigManager()
            
            # Initialize list manager
            self.list_manager = ListManager()
            
            # Initialize Presidio manager and connect list manager
            self.presidio_manager = PresidioManager()
            self.presidio_manager.set_list_manager(self.list_manager)
            
            # Initialize file processor
            self.file_processor = FileProcessor(self.presidio_manager)
            
            # Load lists from configuration
            self.load_lists_from_config()
            
            self.logger.info("Core components initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize core components: {e}", exc_info=True)
            QMessageBox.critical(self, "Initialization Error", 
                               f"Failed to initialize core components: {str(e)}")
        
    def init_ui(self):
        self.setWindowTitle("Presidio Desktop Redactor")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)  # Slightly reduce spacing to save vertical space
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add sections with stretch factors to allocate vertical space
        self._create_file_section(main_layout)  # Compact - no stretch
        self._create_detection_section(main_layout)  # Medium size - stretch factor 1
        
        # Add stretch before de-identification to push it down and give it more space
        main_layout.addStretch(0)
        
        self._create_deidentification_section(main_layout)  # Large - stretch factor 2
        
        # Add minimal stretch before actions to allow de-identification to expand
        main_layout.addStretch(0)
        
        self._create_action_section(main_layout)  # Compact - no stretch
        self._create_status_bar()
        
    def _create_file_section(self, parent_layout):
        """Create file input/output section"""
        file_section = QHBoxLayout()
        
        # Input area
        input_group = QGroupBox("File Input")
        input_group.setMaximumHeight(120)  # Limit height to make it more compact
        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(10, 10, 10, 10)  # Reduce margins
        input_layout.setSpacing(5)  # Reduce spacing
        
        self.drop_area = DropArea()
        self.drop_area.setMaximumHeight(80)  # Reduce drop area height
        self.drop_area.file_dropped.connect(self.load_file)
        input_layout.addWidget(self.drop_area)
        
        # File info display
        self.file_info_label = QLabel("No file selected")
        self.file_info_label.setStyleSheet("font-size: 11px; color: #666; padding: 3px;")  # Smaller font and padding
        self.file_info_label.setMaximumHeight(20)
        input_layout.addWidget(self.file_info_label)
        
        # Warning label for large files
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: #ff6b35; font-weight: bold; padding: 2px; font-size: 11px;")
        self.warning_label.setMaximumHeight(15)
        self.warning_label.hide()
        input_layout.addWidget(self.warning_label)
        
        input_group.setLayout(input_layout)
        file_section.addWidget(input_group)
        
        # Output settings
        output_group = QGroupBox("Output Settings")
        output_group.setMaximumHeight(120)  # Limit height to make it more compact
        output_layout = QVBoxLayout()
        output_layout.setContentsMargins(10, 10, 10, 10)  # Reduce margins
        output_layout.setSpacing(5)  # Reduce spacing
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Save to:"))
        self.output_path_label = QLabel(self.output_dir)
        self.output_path_label.setStyleSheet("background-color: #f0f0f0; padding: 3px; border: 1px solid #ccc; font-size: 11px;")  # Smaller padding and font
        path_layout.addWidget(self.output_path_label)
        browse_btn = QPushButton("Browse...")
        browse_btn.setMaximumHeight(30)  # Smaller button
        browse_btn.setStyleSheet("font-size: 11px; padding: 4px 8px;")  # Smaller font and padding
        browse_btn.clicked.connect(self.select_output_dir)
        path_layout.addWidget(browse_btn)
        
        output_layout.addLayout(path_layout)
        output_group.setLayout(output_layout)
        file_section.addWidget(output_group)
        
        parent_layout.addLayout(file_section)
        
    def _create_detection_section(self, parent_layout):
        """Create entity selection section with multi-select dropdown"""
        detection_group = QGroupBox("Choose entities to look for")
        detection_layout = QVBoxLayout()
        
        # Multi-select dropdown for entities
        entity_layout = QHBoxLayout()
        entity_layout.addWidget(QLabel("Entities:"))
        
        # Create a custom multi-select widget using checkboxes in a dropdown-style
        self.entity_combo = QComboBox()
        self.entity_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 13px;
                min-width: 200px;
            }
        """)
        
        # We'll use checkboxes for multi-select functionality
        self.entity_checkboxes = {}
        entity_container = QWidget()
        entity_container_layout = QVBoxLayout(entity_container)
        entity_container_layout.setContentsMargins(10, 10, 10, 10)
        entity_container_layout.setSpacing(5)
        
        # Select All checkbox
        self.select_all_cb = QCheckBox("Select All")
        self.select_all_cb.setChecked(True)
        self.select_all_cb.stateChanged.connect(self.toggle_select_all)
        self.select_all_cb.setStyleSheet("font-weight: bold; color: #000000; padding: 3px;")
        entity_container_layout.addWidget(self.select_all_cb)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #cccccc;")
        entity_container_layout.addWidget(separator)
        
        # Individual entity checkboxes
        entities = [
            ("PERSON", "Person names"),
            ("EMAIL_ADDRESS", "Email addresses"), 
            ("PHONE_NUMBER", "Phone numbers"),
            ("CREDIT_CARD", "Credit card numbers"),
            ("IP_ADDRESS", "IP addresses"),
            ("URL", "URLs"),
            ("AU_ABN", "Australian Business Number (ABN)"),
            ("AU_ACN", "Australian Company Number (ACN)"),
            ("AU_TFN", "Australian Tax File Number (TFN)"),
            ("AU_MEDICARE", "Australian Medicare Number"),
            ("AU_MEDICAREPROVIDER", "Australian Medicare Provider Number"),
            ("AU_DVA", "Australian DVA File Number"),
            ("AU_CRN", "Australian Centrelink Customer Reference Number")
        ]
        
        for entity_key, display_name in entities:
            cb = QCheckBox(display_name)
            cb.setChecked(True)
            cb.stateChanged.connect(self.update_entity_selection)
            cb.setStyleSheet("color: #000000; padding: 2px; margin-left: 10px;")
            self.entity_checkboxes[entity_key] = cb
            entity_container_layout.addWidget(cb)
        
        # Create a scroll area for the entity selection
        scroll_area = QScrollArea()
        scroll_area.setWidget(entity_container)
        scroll_area.setFixedHeight(200)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
            }
        """)
        
        entity_layout.addWidget(scroll_area)
        entity_layout.addStretch()
        detection_layout.addLayout(entity_layout)
        
        # Acceptance threshold slider
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Acceptance threshold:"))
        
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setRange(0, 100)
        self.confidence_slider.setValue(70)
        self.confidence_slider.setTickPosition(QSlider.TicksBelow)
        self.confidence_slider.setTickInterval(10)
        
        self.confidence_label = QLabel("0.70")
        self.confidence_slider.valueChanged.connect(
            lambda v: self.confidence_label.setText(f"{v/100:.2f}")
        )
        
        threshold_layout.addWidget(self.confidence_slider)
        threshold_layout.addWidget(self.confidence_label)
        threshold_layout.addStretch()
        
        detection_layout.addLayout(threshold_layout)
        detection_group.setLayout(detection_layout)
        
        # Create horizontal layout for detection section and lists section
        detection_horizontal_layout = QHBoxLayout()
        detection_horizontal_layout.setSpacing(20)  # Add spacing between sections
        
        # Add detection group (left side)
        detection_horizontal_layout.addWidget(detection_group)
        
        # Create separate lists section (right side)
        self._create_lists_section(detection_horizontal_layout)
        
        parent_layout.addLayout(detection_horizontal_layout)
    
    def _create_lists_section(self, parent_layout):
        """Create separate Custom Detection Lists section"""
        # Create lists group box
        lists_group = QGroupBox("Custom Detection Lists")
        lists_group.setMinimumWidth(400)  # Ensure adequate width for the lists
        lists_layout = QVBoxLayout()
        
        # Enable/disable checkbox for list functionality  
        self.lists_enabled_cb = QCheckBox("Enable Custom Detection Lists")
        self.lists_enabled_cb.setStyleSheet("font-weight: bold; color: #333; padding: 5px 0px;")
        self.lists_enabled_cb.stateChanged.connect(self.on_lists_enabled_changed)
        lists_layout.addWidget(self.lists_enabled_cb)
        
        # Lists container (initially hidden)
        self.lists_container = QWidget()
        lists_container_layout = QVBoxLayout(self.lists_container)
        lists_container_layout.setContentsMargins(5, 5, 5, 5)
        lists_container_layout.setSpacing(10)
        
        # Allowlist widget
        self.allowlist_widget = ListWidget("Allowlist (ignore these words):")
        self.allowlist_widget.list_changed.connect(self.on_allowlist_changed)
        lists_container_layout.addWidget(self.allowlist_widget)
        
        # Denylist widget  
        self.denylist_widget = ListWidget("Denylist (always redact these words):", allow_entity_types=True)
        self.denylist_widget.list_changed.connect(self.on_denylist_changed)
        lists_container_layout.addWidget(self.denylist_widget)
        
        lists_layout.addWidget(self.lists_container)
        
        # Initially hide the lists container
        self.lists_container.setVisible(False)
        
        lists_group.setLayout(lists_layout)
        parent_layout.addWidget(lists_group)
    
    def _create_deidentification_section(self, parent_layout):
        """Create de-identification approach section"""
        deident_group = QGroupBox("De-identification approach")
        deident_group.setMinimumHeight(300)  # Ensure minimum height for encryption settings
        deident_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Allow expansion
        
        # Main horizontal layout for method selection and encryption settings
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.setSpacing(20)  # Add spacing between left and right sections
        
        # Left side - Method selection
        method_section = QWidget()
        method_section.setMaximumWidth(300)  # Limit width to give more space to encryption
        method_layout = QVBoxLayout(method_section)
        method_layout.setContentsMargins(0, 0, 0, 0)
        
        # Approach selection dropdown
        approach_layout = QHBoxLayout()
        approach_layout.addWidget(QLabel("Method:"))
        
        self.deident_combo = QComboBox()
        self.deident_combo.addItems(["Replace", "Redact", "Hash", "Mask", "Encrypt"])
        self.deident_combo.setCurrentText("Replace")  # Default selection
        self.deident_combo.currentTextChanged.connect(self.update_deidentification_method)
        self.deident_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 13px;
                min-width: 150px;
            }
        """)
        
        approach_layout.addWidget(self.deident_combo)
        approach_layout.addStretch()
        method_layout.addLayout(approach_layout)
        
        # Description label
        self.deident_desc = QLabel("Replace: Replaces detected PII with '<REDACTED>' placeholder")
        self.deident_desc.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        self.deident_desc.setWordWrap(True)  # Allow text wrapping
        method_layout.addWidget(self.deident_desc)
        
        # Add vertical stretch to push content to top
        method_layout.addStretch()
        
        # Add method section to left side
        main_horizontal_layout.addWidget(method_section)
        
        # Right side - Encryption settings (initially hidden)
        self.encryption_widget = EncryptionWidget()
        self.encryption_widget.setVisible(False)
        self.encryption_widget.setMinimumWidth(700)  # Increased width even more
        self.encryption_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Allow expansion
        main_horizontal_layout.addWidget(self.encryption_widget, 3)  # Give encryption widget even more space (stretch factor 3)
        
        deident_group.setLayout(main_horizontal_layout)
        parent_layout.addWidget(deident_group)
        
    # REMOVED: Old anonymization and format-specific sections
        
    def _create_action_section(self, parent_layout):
        """Create action buttons and progress section"""
        action_group = QGroupBox("Actions")
        action_layout = QVBoxLayout()
        
        # Process button
        button_layout = QHBoxLayout()
        self.process_button = QPushButton("Process File")
        self.process_button.setEnabled(False)  # Disabled until file is loaded
        self.process_button.setMinimumHeight(40)
        self.process_button.clicked.connect(self.process_file)
        self.process_button.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a99;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        button_layout.addWidget(self.process_button)
        button_layout.addStretch()
        
        action_layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        action_layout.addWidget(self.progress_bar)
        
        action_group.setLayout(action_layout)
        parent_layout.addWidget(action_group)
        
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - Select a file to begin")
        
    def load_file(self, file_path):
        """Load and validate the selected file"""
        self.logger.info(f"Loading file: {file_path}")
        try:
            path = Path(file_path)
            
            # Validate file exists
            if not path.exists():
                QMessageBox.warning(self, "File Error", "File does not exist.")
                return
                
            # Validate file format
            if path.suffix.lower() not in ['.csv', '.json']:
                QMessageBox.warning(self, "File Error", 
                                  "Please select a CSV or JSON file.")
                return
                
            # Get file info
            file_size = path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            # Store file info
            self.file_path = file_path
            self.file_type = path.suffix.lower().lstrip('.')
            
            # Update file info display
            info_text = f"File: {path.name}\\nSize: {file_size_mb:.1f} MB\\nType: {self.file_type.upper()}"
            self.file_info_label.setText(info_text)
            
            # Check file size and show warning if > 10MB (but don't block)
            if file_size_mb > 10:
                self.warning_label.setText(
                    f"⚠️ Warning: File size ({file_size_mb:.1f} MB) exceeds 10 MB. "
                    "Processing may be slow but will continue."
                )
                self.warning_label.show()
            else:
                self.warning_label.hide()
                
            # Format-specific options removed - process all data
            if self.file_type == 'csv':
                # Will process all CSV columns
                if self.file_processor:
                    columns = self.file_processor.get_csv_columns(file_path)
                    self.selected_columns = columns  # Default to all columns
            elif self.file_type == 'json':
                # Will process all JSON paths
                if self.file_processor:
                    try:
                        # JSON structure will be processed entirely
                        json_data = self.file_processor.get_json_structure(file_path)
                    except Exception as e:
                        QMessageBox.warning(self, "JSON Error", f"Could not parse JSON structure: {str(e)}")
            
            # Enable process button
            self.process_button.setEnabled(True)
            
            # Update status
            self.status_bar.showMessage(f"File loaded: {path.name}")
            
            # Update drop area label
            self.drop_area.label.setText(f"File loaded: {path.name}\\nDrop another file to replace")
            
            self.logger.info(f"File loaded successfully: {path.name} ({file_size_mb:.1f} MB)")
            
        except Exception as e:
            self.logger.error(f"Failed to load file: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
            
    def select_output_dir(self):
        """Select output directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.output_dir
        )
        if directory:
            self.output_dir = directory
            self.output_path_label.setText(directory)
            self.status_bar.showMessage(f"Output directory: {directory}")
            self.logger.info(f"Output directory changed to: {directory}")
            
    def update_entity_selection(self):
        """Handle entity checkbox state changes"""
        # Update UI based on entity selection
        pass
    
    def toggle_select_all(self):
        """Toggle all entity checkboxes when Select All is changed"""
        select_all_state = self.select_all_cb.isChecked()
        for cb in self.entity_checkboxes.values():
            cb.setChecked(select_all_state)
    
    def update_deidentification_method(self, method):
        """Update de-identification method description and show/hide encryption widget"""
        descriptions = {
            "Replace": "Replace: Replaces detected PII with '<REDACTED>' placeholder",
            "Redact": "Redact: Removes detected PII completely from the text",
            "Hash": "Hash: Replaces detected PII with a cryptographic hash value",
            "Mask": "Mask: Replaces detected PII with asterisks (****)",
            "Encrypt": "Encrypt: Encrypts detected PII with a secure encryption key"
        }
        self.deident_desc.setText(descriptions.get(method, ""))
        
        # Show/hide encryption widget based on selected method
        if hasattr(self, 'encryption_widget'):
            self.encryption_widget.setVisible(method == "Encrypt")
        
    def update_anonymization_method(self, method):
        """Update anonymization method description"""
        descriptions = {
            "Replace": "Replace: Replaces detected PII with '<REDACTED>' placeholder",
            "Redact": "Redact: Removes detected PII completely",
            "Mask": "Mask: Replaces detected PII with asterisks (****)"
        }
        self.operation_desc.setText(descriptions.get(method, ""))
        
    def show_column_selection(self):
        """Show CSV column selection dialog"""
        if not self.file_processor or not self.file_path:
            return
            
        try:
            columns = self.file_processor.get_csv_columns(self.file_path)
            dialog = ColumnSelectionDialog(columns, self)
            if dialog.exec_() == QDialog.Accepted:
                self.selected_columns = dialog.get_selected_columns()
                # Update CSV status label
                if len(self.selected_columns) == len(columns):
                    self.csv_status_label.setText("All columns selected")
                else:
                    self.csv_status_label.setText(f"{len(self.selected_columns)} of {len(columns)} columns selected")
                self.status_bar.showMessage(f"Selected {len(self.selected_columns)} columns for processing")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load CSV columns: {str(e)}")
    
    def process_file(self):
        """Process the loaded file using background thread"""
        if not self.file_path or not self.presidio_manager:
            QMessageBox.warning(self, "No File", "Please load a file first")
            return
            
        # Get selected entities
        selected_entities = [
            entity for entity, cb in self.entity_checkboxes.items()
            if cb.isChecked()
        ]
        
        if not selected_entities:
            QMessageBox.warning(self, "No Entities", 
                              "Please select at least one entity type")
            return
            
        # Get configuration
        confidence = self.confidence_slider.value() / 100.0
        operation = self.deident_combo.currentText().lower()
        
        # Handle encryption configuration separately
        if operation == "encrypt":
            if not hasattr(self, 'encryption_widget'):
                QMessageBox.warning(self, "Encryption Error", "Encryption widget not available")
                return
            
            # Check if encryption is enabled and has a valid key
            if not self.encryption_widget.is_encryption_enabled():
                QMessageBox.warning(self, "Encryption Error", 
                                  "Please enable encryption first")
                return
                
            if not self.encryption_widget.has_valid_key():
                QMessageBox.warning(self, "Encryption Error", 
                                  "Please enter a valid encryption key")
                return
            
            # Get encryption manager and set it on the presidio manager
            encryption_manager = self.encryption_widget.get_encryption_manager()
            
            # Ensure the key is properly set on the encryption manager
            key = self.encryption_widget.key_input.text()
            if key and encryption_manager.set_encryption_key(key):
                self.presidio_manager.set_encryption_manager(encryption_manager)
                # Get the proper operator config from presidio manager
                operator_config = self.presidio_manager.get_default_operator_config("encrypt")
                self.logger.info("Encryption configuration set successfully")
            else:
                QMessageBox.warning(self, "Encryption Error", 
                                  "Failed to configure encryption. Please check your key.")
                return
        else:
            operator_config = self.presidio_manager.get_default_operator_config(operation)
        
        # Process all columns/paths since format-specific options are removed
        columns = None  # Process all CSV columns
        paths = None    # Process all JSON paths
        
        # Disable UI during processing
        self.process_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create and start processing thread
        self.processing_thread = ProcessingThread(
            self.file_processor,
            self.file_path,
            self.file_type,
            self.output_dir,
            selected_entities,
            confidence,
            operator_config,
            columns,
            paths
        )
        
        # Connect thread signals
        self.processing_thread.progress.connect(self.progress_bar.setValue)
        self.processing_thread.status.connect(self.status_bar.showMessage)
        self.processing_thread.error.connect(self.handle_processing_error)
        self.processing_thread.finished.connect(self.handle_processing_finished)
        
        # Start processing
        self.processing_thread.start()
    
    def handle_processing_error(self, error_message):
        """Handle processing errors from background thread"""
        QMessageBox.critical(self, "Processing Error", error_message)
        
    def handle_processing_finished(self, success, output_path):
        """Handle processing completion from background thread"""
        # Re-enable UI
        self.process_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            # Extract filename from path for display
            output_filename = os.path.basename(output_path) if output_path else "processed file"
            
            QMessageBox.information(self, "Success", 
                                  f"File processed successfully!\nSaved as: {output_filename}")
            
            # Update status bar with success message
            self.status_bar.showMessage(f"Processing complete! Saved to: {output_filename}")
        else:
            # Error handling was already done in handle_processing_error
            self.status_bar.showMessage("Processing failed")
            
        # Clean up thread
        if hasattr(self, 'processing_thread'):
            self.processing_thread.deleteLater()
            delattr(self, 'processing_thread')
    
    def closeEvent(self, event):
        """Handle application closing - clean up any running threads"""
        if hasattr(self, 'processing_thread') and self.processing_thread.isRunning():
            # Give the thread a chance to finish gracefully
            self.processing_thread.terminate()
            self.processing_thread.wait(3000)  # Wait up to 3 seconds
        event.accept()
    
    def json_select_all(self):
        """Select all JSON paths"""
        if hasattr(self, 'json_tree'):
            self.json_tree.select_all_items()
            self.json_status_label.setText("All paths selected")
            
    def json_clear_all(self):
        """Clear all JSON path selections"""
        if hasattr(self, 'json_tree'):
            self.json_tree.clear_all_items()
            self.json_status_label.setText("No paths selected")
            
    def json_select_text_fields(self):
        """Select only text/string fields in JSON"""
        if hasattr(self, 'json_tree'):
            self.json_tree.select_text_fields_only()
            selected_count = len(self.json_tree.get_selected_paths())
            self.json_status_label.setText(f"{selected_count} text fields selected")
    
    def on_lists_enabled_changed(self, state):
        """Handle enable/disable of list functionality"""
        enabled = state == Qt.Checked
        if self.lists_container:
            self.lists_container.setVisible(enabled)
        
        # Update config
        if self.config_manager:
            self.config_manager.detection_settings.enable_custom_lists = enabled
            self.config_manager.save_config()
        
        self.logger.info(f"List functionality {'enabled' if enabled else 'disabled'}")
    
    def on_allowlist_changed(self):
        """Handle allowlist changes"""
        if self.allowlist_widget and self.list_manager:
            # Update list manager with current allowlist entries
            self.list_manager.clear_allowlist()
            for entry in self.allowlist_widget.get_entries():
                self.list_manager.add_to_allowlist(entry)
            
            # Save to configuration
            self.save_lists_to_config()
            self.logger.debug(f"Allowlist updated: {len(self.allowlist_widget.get_entries())} entries")
    
    def on_denylist_changed(self):
        """Handle denylist changes"""
        if self.denylist_widget and self.list_manager:
            # Update list manager with current denylist entries
            self.list_manager.clear_denylist()
            for entry in self.denylist_widget.get_entries():
                # For now, use default entity type - in future this could be configurable per entry
                self.list_manager.add_to_denylist(entry, "CUSTOM_DENY")
            
            # Save to configuration
            self.save_lists_to_config()
            self.logger.debug(f"Denylist updated: {len(self.denylist_widget.get_entries())} entries")
    
    def load_lists_from_config(self):
        """Load lists from configuration"""
        if not self.config_manager or not self.list_manager:
            return
        
        try:
            success, lists_data = self.config_manager.load_lists()
            if success and lists_data:
                # Load to list manager
                self.list_manager.from_dict(lists_data)
                
                # Update UI widgets if they exist
                if self.allowlist_widget and 'allowlist' in lists_data:
                    allowlist_words = lists_data['allowlist'].get('words', [])
                    self.allowlist_widget.set_entries(allowlist_words)
                
                if self.denylist_widget and 'denylist' in lists_data:
                    denylist_entries = lists_data['denylist'].get('entries', [])
                    # Extract just the words for the UI
                    denylist_words = [entry['word'] for entry in denylist_entries if 'word' in entry]
                    self.denylist_widget.set_entries(denylist_words)
                
                self.logger.info(f"Loaded lists from configuration: {len(self.list_manager.allowlist)} allowlist, {len(self.list_manager.denylist)} denylist entries")
        except Exception as e:
            self.logger.error(f"Failed to load lists from configuration: {e}")
    
    def save_lists_to_config(self):
        """Save current lists to configuration"""
        if not self.config_manager or not self.list_manager:
            return
        
        try:
            lists_data = self.list_manager.to_dict()
            self.config_manager.save_lists(lists_data)
            self.logger.debug("Saved lists to configuration")
        except Exception as e:
            self.logger.error(f"Failed to save lists to configuration: {e}")
    
    def load_ui_state_from_config(self):
        """Load UI state from configuration after UI is created"""
        if not self.config_manager:
            return
        
        try:
            # Load lists functionality state
            if self.lists_enabled_cb:
                enabled = self.config_manager.detection_settings.enable_custom_lists
                self.lists_enabled_cb.setChecked(enabled)
                if self.lists_container:
                    self.lists_container.setVisible(enabled)
            
            # Load list data (this will call load_lists_from_config again but with UI widgets available)
            self.load_lists_from_config()
            
            self.logger.info("UI state loaded from configuration")
        except Exception as e:
            self.logger.error(f"Failed to load UI state from configuration: {e}")

    def _get_timestamp(self):
        """Generate timestamp for output files"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def _get_display_name(self, entity_type):
        """Convert entity type to display name"""
        display_names = {
            "PERSON": "Person Names",
            "EMAIL_ADDRESS": "Email Addresses", 
            "PHONE_NUMBER": "Phone Numbers",
            "CREDIT_CARD": "Credit Card Numbers",
            "IBAN": "IBAN Numbers",
            "IP_ADDRESS": "IP Addresses",
            "URL": "URLs"
        }
        return display_names.get(entity_type, entity_type)